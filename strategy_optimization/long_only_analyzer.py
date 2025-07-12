#!/usr/bin/env python3
"""
做多專用分析工具
生成詳細的進場分析表格，專注於做多交易的表現
"""

import sys
import os
import importlib.util
import logging
from datetime import datetime, date, time
from decimal import Decimal
import pandas as pd
from typing import List, Dict, Any
import app_setup

# 設置日誌
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
logger = logging.getLogger(__name__)

class LongOnlyAnalyzer:
    """做多專用分析器"""
    
    def __init__(self):
        self.strategy_module = None
        self.trade_records = []
        
    def init_strategy_module(self):
        """初始化策略模塊"""
        logger.info("🔌 初始化數據庫連接池...")
        app_setup.init_all_db_pools()
        logger.info("✅ 數據庫連接池初始化成功")
        
        # 動態導入策略模塊
        strategy_path = os.path.join(os.path.dirname(__file__), "multi_Profit-Funded Risk_多口.py")
        spec = importlib.util.spec_from_file_location("strategy_module", strategy_path)
        self.strategy_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.strategy_module)
        logger.info("✅ 策略模塊導入成功")
        
    def run_long_only_analysis(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """執行做多專用分析"""
        logger.info("📈 開始做多專用回測分析...")
        
        # 創建三口做多配置
        config = self.strategy_module.StrategyConfig(
            trade_size_in_lots=3,
            stop_loss_type=self.strategy_module.StopLossType.RANGE_BOUNDARY,
            lot_rules=[
                self.strategy_module.LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(15),
                    trailing_pullback=Decimal('0.20')
                ),
                self.strategy_module.LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(40),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0')
                ),
                self.strategy_module.LotRule(
                    use_trailing_stop=True,
                    trailing_activation=Decimal(65),
                    trailing_pullback=Decimal('0.20'),
                    protective_stop_multiplier=Decimal('2.0')
                )
            ]
        )
        
        # 執行修改後的回測（只做多）
        self._run_long_only_backtest(config, start_date, end_date)
        
        # 轉換為DataFrame
        df = pd.DataFrame(self.trade_records)
        
        # 生成分析報告
        self._generate_analysis_report(df)
        
        return df
    
    def _run_long_only_backtest(self, config, start_date=None, end_date=None):
        """執行只做多的回測"""
        import shared
        
        self.trade_records = []
        
        try:
            with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
                # 獲取交易日
                base_query = "SELECT DISTINCT trade_datetime::date as trade_day FROM stock_prices"
                conditions = []
                params = []
                
                if start_date:
                    conditions.append("trade_datetime::date >= %s")
                    params.append(start_date)
                if end_date:
                    conditions.append("trade_datetime::date <= %s")
                    params.append(end_date)
                
                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)
                base_query += " ORDER BY trade_day"
                
                cur.execute(base_query, params)
                trade_days = [row['trade_day'] for row in cur.fetchall()]
                
                logger.info(f"🔍 找到 {len(trade_days)} 個交易日進行回測。")
                
                for day in trade_days:
                    self._analyze_single_day(cur, day, config)
                    
        except Exception as e:
            logger.error(f"回測執行錯誤: {e}")
            raise
    
    def _analyze_single_day(self, cur, day: date, config):
        """分析單日交易"""
        # 獲取當日K線數據
        cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", (day,))
        day_session_candles = [c for c in cur.fetchall() if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)]
        
        if len(day_session_candles) < 3:
            return
        
        # 計算開盤區間
        candles_846_847 = [c for c in day_session_candles if c['trade_datetime'].time() in [time(8, 46), time(8, 47)]]
        if len(candles_846_847) != 2:
            logger.warning(f"⚠️ {day}: 找不到開盤區間K棒")
            return
        
        range_high = max(c['high_price'] for c in candles_846_847)
        range_low = min(c['low_price'] for c in candles_846_847)
        range_size = range_high - range_low
        
        # 尋找做多進場點
        trade_candles = [c for c in day_session_candles if c['trade_datetime'].time() >= time(8, 48)]
        
        long_entry = None
        for i, candle in enumerate(trade_candles):
            if candle['close_price'] > range_high:
                long_entry = {
                    'candle_index': i,
                    'entry_time': candle['trade_datetime'].time(),
                    'entry_price': candle['close_price'],
                    'entry_candle': candle
                }
                break
        
        # 記錄交易信息
        trade_record = {
            'date': day,
            'range_high': float(range_high),
            'range_low': float(range_low),
            'range_size': float(range_size),
            'range_midpoint': float((range_high + range_low) / 2),
            'has_long_entry': long_entry is not None,
            'entry_time': long_entry['entry_time'] if long_entry else None,
            'entry_price': float(long_entry['entry_price']) if long_entry else None,
            'breakout_strength': float(long_entry['entry_price'] - range_high) if long_entry else None,
        }
        
        if long_entry:
            # 計算交易結果
            pnl_result = self._calculate_long_trade_result(trade_candles, long_entry, config, range_high, range_low)
            trade_record.update(pnl_result)
        else:
            # 沒有做多進場
            trade_record.update({
                'total_pnl': 0,
                'lot1_pnl': 0,
                'lot2_pnl': 0,
                'lot3_pnl': 0,
                'lot1_exit_type': 'no_entry',
                'lot2_exit_type': 'no_entry',
                'lot3_exit_type': 'no_entry',
                'lot1_exit_time': None,
                'lot2_exit_time': None,
                'lot3_exit_time': None,
                'lot1_exit_price': None,
                'lot2_exit_price': None,
                'lot3_exit_price': None,
                'max_favorable': 0,
                'max_adverse': 0,
                'trade_duration_minutes': 0
            })
        
        self.trade_records.append(trade_record)
        
        # 記錄日誌
        if long_entry:
            logger.info(f"--- {day} | 區間: {range_low}-{range_high} ({range_size}點) | 📈 做多進場: {long_entry['entry_time']} @ {long_entry['entry_price']} | 總損益: {trade_record['total_pnl']:.1f}")
        else:
            logger.info(f"--- {day} | 區間: {range_low}-{range_high} ({range_size}點) | ❌ 無做多進場")
    
    def _calculate_long_trade_result(self, trade_candles, long_entry, config, range_high, range_low):
        """計算做多交易結果"""
        entry_price = long_entry['entry_price']
        entry_index = long_entry['candle_index']
        
        # 初始化三口部位
        lots = []
        for i in range(3):
            lot_rule = config.lot_rules[i]
            lots.append({
                'id': i + 1,
                'entry_price': entry_price,
                'stop_loss': range_low,  # 初始停損在區間下軌
                'trailing_activated': False,
                'trailing_high': entry_price,
                'status': 'active',
                'pnl': 0,
                'exit_time': None,
                'exit_price': None,
                'exit_type': None,
                'rule': lot_rule
            })
        
        # 追蹤最大有利/不利變動
        max_favorable = 0
        max_adverse = 0
        
        # 逐K線處理
        for candle in trade_candles[entry_index + 1:]:
            current_price = candle['close_price']
            current_time = candle['trade_datetime'].time()
            
            # 更新最大有利/不利變動
            unrealized_pnl = current_price - entry_price
            max_favorable = max(max_favorable, unrealized_pnl)
            max_adverse = min(max_adverse, unrealized_pnl)
            
            # 處理每一口
            active_lots = [lot for lot in lots if lot['status'] == 'active']
            if not active_lots:
                break
                
            for lot in active_lots:
                self._process_lot_exit(lot, candle, lots)
        
        # 收盤平倉剩餘部位
        for lot in lots:
            if lot['status'] == 'active':
                last_candle = trade_candles[-1]
                lot['exit_price'] = last_candle['close_price']
                lot['exit_time'] = last_candle['trade_datetime'].time()
                lot['exit_type'] = 'eod_close'
                lot['pnl'] = lot['exit_price'] - lot['entry_price']
                lot['status'] = 'exited'
        
        # 計算交易持續時間
        if lots[0]['exit_time']:
            entry_dt = datetime.combine(date.today(), long_entry['entry_time'])
            exit_dt = datetime.combine(date.today(), lots[-1]['exit_time'])
            duration_minutes = (exit_dt - entry_dt).total_seconds() / 60
        else:
            duration_minutes = 0
        
        return {
            'total_pnl': sum(lot['pnl'] for lot in lots),
            'lot1_pnl': lots[0]['pnl'],
            'lot2_pnl': lots[1]['pnl'],
            'lot3_pnl': lots[2]['pnl'],
            'lot1_exit_type': lots[0]['exit_type'],
            'lot2_exit_type': lots[1]['exit_type'],
            'lot3_exit_type': lots[2]['exit_type'],
            'lot1_exit_time': lots[0]['exit_time'],
            'lot2_exit_time': lots[1]['exit_time'],
            'lot3_exit_time': lots[2]['exit_time'],
            'lot1_exit_price': lots[0]['exit_price'],
            'lot2_exit_price': lots[1]['exit_price'],
            'lot3_exit_price': lots[2]['exit_price'],
            'max_favorable': float(max_favorable),
            'max_adverse': float(max_adverse),
            'trade_duration_minutes': duration_minutes
        }

    def _process_lot_exit(self, lot, candle, all_lots):
        """處理單口出場邏輯"""
        current_price = candle['close_price']
        current_time = candle['trade_datetime'].time()

        # 檢查初始停損
        if current_price <= lot['stop_loss']:
            lot['exit_price'] = lot['stop_loss']
            lot['exit_time'] = current_time
            lot['exit_type'] = 'initial_stop_loss'
            lot['pnl'] = lot['exit_price'] - lot['entry_price']
            lot['status'] = 'exited'
            return

        # 更新trailing high
        if current_price > lot['trailing_high']:
            lot['trailing_high'] = current_price

        # 檢查移動停利觸發
        if not lot['trailing_activated']:
            unrealized_pnl = current_price - lot['entry_price']
            if unrealized_pnl >= lot['rule'].trailing_activation:
                lot['trailing_activated'] = True
                logger.info(f"  🔔 第{lot['id']}口移動停利啟動 | 時間: {current_time}")

        # 移動停利出場檢查
        if lot['trailing_activated']:
            # 正確的移動停利計算：從最高點回檔指定比例
            pullback_threshold = lot['trailing_high'] - (lot['trailing_high'] - lot['entry_price']) * lot['rule'].trailing_pullback
            if current_price <= pullback_threshold:
                lot['exit_price'] = pullback_threshold
                lot['exit_time'] = current_time
                lot['exit_type'] = 'trailing_stop'
                lot['pnl'] = lot['exit_price'] - lot['entry_price']
                lot['status'] = 'exited'
                logger.info(f"  ✅ 第{lot['id']}口移動停利 | 時間: {current_time}, 價格: {int(round(lot['exit_price']))}, 損益: {int(round(lot['pnl']))}")

                # 更新後續口數的保護性停損
                self._update_protective_stops(lot, all_lots)
                return

        # 檢查保護性停損
        if hasattr(lot['rule'], 'protective_stop_multiplier') and lot['rule'].protective_stop_multiplier:
            if lot['id'] > 1:  # 第2、3口才有保護性停損
                cumulative_profit = sum(l['pnl'] for l in all_lots[:lot['id']-1] if l['status'] == 'exited')
                if cumulative_profit > 0:
                    protective_stop = lot['entry_price'] - (cumulative_profit * lot['rule'].protective_stop_multiplier)
                    if current_price <= protective_stop:
                        lot['exit_price'] = protective_stop
                        lot['exit_time'] = current_time
                        lot['exit_type'] = 'protective_stop'
                        lot['pnl'] = lot['exit_price'] - lot['entry_price']
                        lot['status'] = 'exited'
                        logger.info(f"  🛡️ 第{lot['id']}口保護性停損 | 時間: {current_time}, 出場價: {int(round(lot['exit_price']))}, 損益: {int(round(lot['pnl']))}")
                        return

    def _update_protective_stops(self, exited_lot, all_lots):
        """更新後續口數的保護性停損"""
        cumulative_profit = sum(l['pnl'] for l in all_lots if l['status'] == 'exited')

        for lot in all_lots:
            if lot['status'] == 'active' and lot['id'] > exited_lot['id']:
                if hasattr(lot['rule'], 'protective_stop_multiplier') and lot['rule'].protective_stop_multiplier:
                    new_stop = lot['entry_price'] - (cumulative_profit * lot['rule'].protective_stop_multiplier)
                    lot['stop_loss'] = max(lot['stop_loss'], new_stop)
                    logger.info(f"     - 第{lot['id']}口單停損點更新為: {int(round(lot['stop_loss']))} (基於累積獲利 {int(round(cumulative_profit))})")

    def _generate_analysis_report(self, df: pd.DataFrame):
        """生成分析報告"""
        logger.info("\n" + "="*80)
        logger.info("📊 做多交易詳細分析報告")
        logger.info("="*80)

        # 基本統計
        total_days = len(df)
        long_entry_days = len(df[df['has_long_entry'] == True])
        no_entry_days = total_days - long_entry_days

        logger.info(f"📅 總交易日數: {total_days}")
        logger.info(f"📈 有做多進場日數: {long_entry_days} ({long_entry_days/total_days*100:.1f}%)")
        logger.info(f"❌ 無做多進場日數: {no_entry_days} ({no_entry_days/total_days*100:.1f}%)")

        if long_entry_days > 0:
            # 做多交易分析
            long_trades = df[df['has_long_entry'] == True]
            winning_trades = len(long_trades[long_trades['total_pnl'] > 0])
            losing_trades = len(long_trades[long_trades['total_pnl'] < 0])
            breakeven_trades = len(long_trades[long_trades['total_pnl'] == 0])

            logger.info(f"\n💰 做多交易損益分析:")
            logger.info(f"  獲利交易: {winning_trades} ({winning_trades/long_entry_days*100:.1f}%)")
            logger.info(f"  虧損交易: {losing_trades} ({losing_trades/long_entry_days*100:.1f}%)")
            logger.info(f"  平手交易: {breakeven_trades} ({breakeven_trades/long_entry_days*100:.1f}%)")
            logger.info(f"  總損益: {long_trades['total_pnl'].sum():.1f} 點")
            logger.info(f"  平均損益: {long_trades['total_pnl'].mean():.1f} 點")
            logger.info(f"  最大獲利: {long_trades['total_pnl'].max():.1f} 點")
            logger.info(f"  最大虧損: {long_trades['total_pnl'].min():.1f} 點")

            # 各口分析
            logger.info(f"\n🎯 各口損益分析:")
            for i in range(1, 4):
                lot_pnl = long_trades[f'lot{i}_pnl']
                lot_wins = len(lot_pnl[lot_pnl > 0])
                logger.info(f"  第{i}口: 總損益 {lot_pnl.sum():.1f}點, 平均 {lot_pnl.mean():.1f}點, 獲利次數 {lot_wins}/{long_entry_days}")

            # 區間大小分析
            logger.info(f"\n📏 開盤區間分析:")
            logger.info(f"  平均區間大小: {df['range_size'].mean():.1f} 點")
            logger.info(f"  區間大小範圍: {df['range_size'].min():.1f} - {df['range_size'].max():.1f} 點")

            # 突破強度分析
            logger.info(f"\n🚀 突破強度分析:")
            breakout_strength = long_trades['breakout_strength'].dropna()
            logger.info(f"  平均突破強度: {breakout_strength.mean():.1f} 點")
            logger.info(f"  突破強度範圍: {breakout_strength.min():.1f} - {breakout_strength.max():.1f} 點")

            # 時間分析
            logger.info(f"\n⏰ 進場時間分析:")
            entry_times = long_trades['entry_time'].dropna()
            logger.info(f"  最早進場: {min(entry_times)}")
            logger.info(f"  最晚進場: {max(entry_times)}")
            logger.info(f"  平均交易持續: {long_trades['trade_duration_minutes'].mean():.1f} 分鐘")

        logger.info("="*80)

    def save_detailed_csv(self, df: pd.DataFrame, filename: str = None):
        """保存詳細CSV報告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"long_only_analysis_{timestamp}.csv"

        filepath = os.path.join(os.path.dirname(__file__), filename)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        logger.info(f"📄 詳細分析報告已保存: {filepath}")
        return filepath


def main():
    """主執行函數"""
    analyzer = LongOnlyAnalyzer()
    analyzer.init_strategy_module()

    # 執行做多分析
    df = analyzer.run_long_only_analysis()

    # 保存詳細報告
    analyzer.save_detailed_csv(df)

    logger.info("🎉 做多專用分析完成！")


if __name__ == "__main__":
    main()
