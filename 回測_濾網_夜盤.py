# 台指期開盤策略回測_完整模組化版本_V6_雙報告與盤別選擇.py
import logging
from datetime import time, timedelta, date
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum, auto
from app_setup import init_all_db_pools
import shared

# --- 設定日誌 ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. 策略設定與輔助函式
# ==============================================================================
class StopLossType(Enum):
    RANGE_BOUNDARY = auto(); OPENING_PRICE = auto(); FIXED_POINTS = auto()

# 【新功能】新增盤別執行模式的選項
class SessionRunMode(Enum):
    BOTH = auto()       # 日盤和夜盤都跑
    DAY_ONLY = auto()   # 只跑日盤
    NIGHT_ONLY = auto() # 只跑夜盤

@dataclass
class StrategyConfig:
    # --- 【新功能】盤別選擇器 ---
    session_mode: SessionRunMode = SessionRunMode.BOTH

    # --- 濾網開關 ---
    use_range_size_filter: bool = False; use_volume_filter: bool = False; use_trailing_stop: bool = False
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    
    # --- 參數設定 ---
    max_opening_range_points: Decimal = Decimal(100); trailing_activation_points: Decimal = Decimal(25)
    trailing_pullback_percent: Decimal = Decimal('0.20'); fixed_take_profit_points: Decimal = Decimal(15)
    fixed_stop_loss_points: Decimal = Decimal(40)



def format_config_summary(config: StrategyConfig) -> str:
    summary_lines = ["\n📋======= 策略設定摘要 =======📋"]
    if config.use_trailing_stop:
        line = (f"  - 停利策略：移動停利 (啟用)\n"
                f"    - 觸發點數: {config.trailing_activation_points} 點\n"
                f"    - 回檔比例: {config.trailing_pullback_percent:%}")
    else:
        line = (f"  - 停利策略：固定停利\n"
                f"    - 停利點數: {config.fixed_take_profit_points} 點")
    summary_lines.append(line)
    sl_type_map = { StopLossType.RANGE_BOUNDARY: "區間邊緣停損", StopLossType.OPENING_PRICE: "8:46開盤價停損", StopLossType.FIXED_POINTS: "固定點數停損" }
    sl_line = f"  - 停損策略：{sl_type_map[config.stop_loss_type]}"
    if config.stop_loss_type == StopLossType.FIXED_POINTS: sl_line += f" ({config.fixed_stop_loss_points} 點)"
    summary_lines.append(sl_line)
    range_filter_status = "啟用" if config.use_range_size_filter else "停用"
    range_line = f"  - 區間大小濾網：{range_filter_status}"
    if config.use_range_size_filter: range_line += f" (上限: {config.max_opening_range_points} 點)"
    summary_lines.append(range_line)
    volume_filter_status = "啟用" if config.use_volume_filter else "停用"
    summary_lines.append(f"  - 成交量濾網：{volume_filter_status}")
    return "\n".join(summary_lines)


# 【新功能】建立一個可重用的報告產生器
def print_summary_report(title: str, total_days: int, wins: int, losses: int, pnl: Decimal, config: StrategyConfig):
    """印出格式化的績效總結報告"""
    logger.info(f"====== {title} ======")
    trade_count = wins + losses
    win_rate = (wins / trade_count * 100) if trade_count > 0 else 0
    logger.info(f"總交易天數: {total_days}")
    logger.info(f"總交易次數: {trade_count}")
    logger.info(f"獲利次數: {wins}")
    logger.info(f"虧損次數: {losses}")
    logger.info(f"勝率: {win_rate:.2f}%")
    logger.info(f"總損益: {pnl:.2f}")
    if title.startswith("回測結果總結"): # 只在最終總結報告顯示設定
        logger.info(format_config_summary(config))
    logger.info("======================================")



# ==============================================================================
# 2. 核心交易邏輯函式
# ==============================================================================
def execute_trade_logic(session_candles: list, session_name: str, config: StrategyConfig, range_times: list, trade_start_time: time) -> tuple:
    if len(session_candles) < 3: return (Decimal(0), 0, 0)

    session_opening_candles = [c for c in session_candles if c['trade_datetime'].time() in range_times]
    if len(session_opening_candles) != 2:
        logger.warning(f"  - [{session_name}] 找不到完整的開盤區間K棒 {range_times}，跳過此盤別。")
        return (Decimal(0), 0, 0)

    range_high = max(c['high_price'] for c in session_opening_candles)
    range_low = min(c['low_price'] for c in session_opening_candles)
    opening_range_size = range_high - range_low
    logger.info(f"  - [{session_name}] 開盤區間: {range_low} - {range_high} (大小: {opening_range_size}點)")

    if config.use_range_size_filter and opening_range_size > config.max_opening_range_points:
        logger.warning(f"    🟡 [{session_name}] 跳過 | 開盤區間過大")
        return (Decimal(0), 0, 0)
    
    sl_level_opening_price = None
    if config.stop_loss_type == StopLossType.OPENING_PRICE:
        candle_range_start = next((c for c in session_opening_candles if c['trade_datetime'].time() == range_times[0]), None)
        if candle_range_start: sl_level_opening_price = candle_range_start['open_price']
        else: logger.error(f"  ❌ [{session_name}] 無法設定開盤價停損，找不到 {range_times[0]} K棒。"); return (Decimal(0), 0, 0)

    position, entry_price, pnl, entry_time = None, Decimal(0), Decimal(0), None
    for i, candle in enumerate(session_candles):
        current_time = candle['trade_datetime'].time()
        if current_time < trade_start_time or position: continue
        
        volume_condition_met = (not config.use_volume_filter) or (candle['volume'] > (max(c['volume'] for c in session_candles[:i]) if i > 0 else 0))
        if candle['close_price'] > range_high and volume_condition_met:
            position, entry_price, entry_time = 'LONG', candle['close_price'], current_time
            logger.info(f"    📈 [{session_name}] LONG  | 進場: {entry_time}, 價格: {entry_price}")
        elif candle['low_price'] < range_low and volume_condition_met:
            position, entry_price, entry_time = 'SHORT', candle['close_price'], current_time
            logger.info(f"    📉 [{session_name}] SHORT | 進場: {entry_time}, 價格: {entry_price}")

    if position:
        peak_price_after_entry = entry_price
        trailing_stop_activated = False

        for candle in session_candles:
            if candle['trade_datetime'].time() <= entry_time: continue
            
            current_time = candle['trade_datetime'].time()
            stop_loss_triggered = False
            
            # --- 1. 補完完整的出場邏輯 ---
            # 停損檢查
            if position == 'LONG':
                if config.stop_loss_type == StopLossType.RANGE_BOUNDARY and candle['close_price'] < range_low: stop_loss_triggered = True
                elif config.stop_loss_type == StopLossType.OPENING_PRICE and sl_level_opening_price and candle['close_price'] < sl_level_opening_price: stop_loss_triggered = True
                elif config.stop_loss_type == StopLossType.FIXED_POINTS and candle['low_price'] <= entry_price - config.fixed_stop_loss_points: stop_loss_triggered = True
            elif position == 'SHORT':
                if config.stop_loss_type == StopLossType.RANGE_BOUNDARY and candle['close_price'] > range_high: stop_loss_triggered = True
                elif config.stop_loss_type == StopLossType.OPENING_PRICE and sl_level_opening_price and candle['close_price'] > sl_level_opening_price: stop_loss_triggered = True
                elif config.stop_loss_type == StopLossType.FIXED_POINTS and candle['high_price'] >= entry_price + config.fixed_stop_loss_points: stop_loss_triggered = True
            
            if stop_loss_triggered:
                pnl = (candle['close_price'] - entry_price) if position == 'LONG' else (entry_price - candle['close_price'])
                logger.info(f"    ❌ [{session_name}] 停損 ({config.stop_loss_type.name}) | 出場: {current_time}, 價格: {candle['close_price']}, 損益: {pnl:.2f}"); break

            # 停利檢查
            if position == 'LONG':
                if config.use_trailing_stop:
                    peak_price_after_entry = max(peak_price_after_entry, candle['high_price'])
                    if not trailing_stop_activated and peak_price_after_entry >= entry_price + config.trailing_activation_points:
                        trailing_stop_activated = True; logger.info(f"    🔔 [{session_name}] 移動停利已啟動 | 時間: {current_time}")
                    if trailing_stop_activated:
                        stop_price = peak_price_after_entry - (peak_price_after_entry - entry_price) * config.trailing_pullback_percent
                        if candle['low_price'] <= stop_price:
                            pnl = stop_price - entry_price; logger.info(f"    ✅ [{session_name}] 移動停利 | 出場價格: {stop_price:.2f}, 損益: +{pnl}"); break
                else: # 固定停利
                    if candle['high_price'] >= entry_price + config.fixed_take_profit_points:
                        pnl = config.fixed_take_profit_points; logger.info(f"    ✅ [{session_name}] 固定停利 | 出場價格: {entry_price + pnl}, 損益: +{pnl}"); break
            elif position == 'SHORT':
                if config.use_trailing_stop:
                    peak_price_after_entry = min(peak_price_after_entry, candle['low_price'])
                    if not trailing_stop_activated and peak_price_after_entry <= entry_price - config.trailing_activation_points:
                        trailing_stop_activated = True; logger.info(f"    🔔 [{session_name}] 移動停利已啟動 | 時間: {current_time}")
                    if trailing_stop_activated:
                        stop_price = peak_price_after_entry + (entry_price - peak_price_after_entry) * config.trailing_pullback_percent
                        if candle['high_price'] >= stop_price:
                            pnl = entry_price - stop_price; logger.info(f"    ✅ [{session_name}] 移動停利 | 出場價格: {stop_price:.2f}, 損益: +{pnl}"); break
                else: # 固定停利
                    if candle['low_price'] <= entry_price - config.fixed_take_profit_points:
                        pnl = config.fixed_take_profit_points; logger.info(f"    ✅ [{session_name}] 固定停利 | 出場價格: {entry_price - pnl}, 損益: +{pnl}"); break

    if position and pnl == 0:
        exit_price = session_candles[-1]['close_price']
        pnl = (exit_price - entry_price) if position == 'LONG' else (entry_price - exit_price)
        logger.info(f"    ⚪️ [{session_name}] 收盤平倉 | 出場價格: {exit_price}, 損益: {pnl}")

    return (pnl, 1 if pnl > 0 else 0, 1 if pnl < 0 else 0)

# ==============================================================================
# 3. 【日盤回測函式】
# ==============================================================================
def run_day_session_backtest(day: date, config: StrategyConfig, cur) -> tuple:
    cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date = %s ORDER BY trade_datetime;", (day,))
    all_day_candles = cur.fetchall()
    day_session_candles = [c for c in all_day_candles if time(8, 45) <= c['trade_datetime'].time() <= time(13, 45)]
    return execute_trade_logic(day_session_candles, "日盤", config, [time(8, 46), time(8, 47)], time(8, 48))

# ==============================================================================
# 4. 【夜盤回測函式】
# ==============================================================================
def run_night_session_backtest(day: date, config: StrategyConfig, cur) -> tuple:
    start_dt, end_dt = day, day + timedelta(days=1)
    cur.execute("SELECT * FROM stock_prices WHERE trade_datetime::date >= %s AND trade_datetime::date <= %s ORDER BY trade_datetime;", (start_dt, end_dt))
    all_candles = cur.fetchall()
    night_session_candles = [c for c in all_candles if (c['trade_datetime'].date() == day and c['trade_datetime'].time() >= time(15, 0)) or (c['trade_datetime'].date() == end_dt and c['trade_datetime'].time() <= time(5, 0))]
    
    # --- 3. 修正夜盤時間邏輯 ---
    return execute_trade_logic(night_session_candles, "夜盤", config, [time(21, 31), time(21, 32)], time(21, 33))

# ==============================================================================
# 5. 【總指揮官】
# ==============================================================================
def run_backtest(config: StrategyConfig):
    logger.info(format_config_summary(config))
    try:
        with shared.get_conn_cur_from_pool_b(as_dict=True) as (conn, cur):
            cur.execute("SELECT DISTINCT trade_datetime::date as trade_day FROM stock_prices WHERE trade_datetime::time >= '08:45:00' ORDER BY trade_day;")
            trade_days = [row['trade_day'] for row in cur.fetchall()]
            logger.info(f"🔍 找到 {len(trade_days)} 個交易日進行回測。")

            # 【新功能】獨立追蹤日盤、夜盤、及總和的績效
            day_pnl, day_wins, day_losses = Decimal(0), 0, 0
            night_pnl, night_wins, night_losses = Decimal(0), 0, 0
            
            for day in trade_days:
                logger.info(f"--- 處理交易日: {day} ---")
                
                # 【新功能】根據 session_mode 決定是否執行
                if config.session_mode in [SessionRunMode.BOTH, SessionRunMode.DAY_ONLY]:
                    pnl, win, loss = run_day_session_backtest(day, config, cur)
                    day_pnl += pnl; day_wins += win; day_losses += loss
                
                if config.session_mode in [SessionRunMode.BOTH, SessionRunMode.NIGHT_ONLY]:
                    pnl, win, loss = run_night_session_backtest(day, config, cur)
                    night_pnl += pnl; night_wins += win; night_losses += loss

            # ---【新功能】產生分離的報告 ---
            total_wins = day_wins + night_wins
            total_losses = day_losses + night_losses
            total_pnl = day_pnl + night_pnl

            if config.session_mode == SessionRunMode.DAY_ONLY:
                print_summary_report("回測結果總結 (僅日盤)", len(trade_days), day_wins, day_losses, day_pnl, config)
            elif config.session_mode == SessionRunMode.NIGHT_ONLY:
                print_summary_report("回測結果總結 (僅夜盤)", len(trade_days), night_wins, night_losses, night_pnl, config)
            elif config.session_mode == SessionRunMode.BOTH:
                print_summary_report("日盤績效報告", len(trade_days), day_wins, day_losses, day_pnl, config)
                print_summary_report("夜盤績效報告", len(trade_days), night_wins, night_losses, night_pnl, config)
                print_summary_report("回測結果總結 (日盤+夜盤)", len(trade_days), total_wins, total_losses, total_pnl, config)

    except Exception as e:
        logger.error(f"❌ 執行回測時發生錯誤: {e}", exc_info=True)

def main():
    logger.info("▶️  回測程式開始執行...")
    try:
        init_all_db_pools(); logger.info("✅ 資料庫連線池初始化成功。")
    except Exception as e:
        logger.error(f"❌ 資料庫連線池初始化失敗: {e}", exc_info=True); return

    # --- 策略實驗室 ---
    # 範例1：只跑日盤
    config_day_only = StrategyConfig(
        session_mode=SessionRunMode.DAY_ONLY,
        use_trailing_stop=False, 
        fixed_take_profit_points=Decimal(15)
    )

    # 範例2：只跑夜盤
    config_night_only = StrategyConfig(
        session_mode=SessionRunMode.NIGHT_ONLY,
        use_trailing_stop=False, 
        fixed_take_profit_points=Decimal(15)
    )

    # 範例3：日盤和夜盤都跑 (預設行為)
    config_both = StrategyConfig(
        session_mode=SessionRunMode.BOTH,
        use_trailing_stop=True, 
        fixed_take_profit_points=Decimal(25)
    )
    
    # --- 選擇一個設定來執行回測 ---
    # logger.info("---------- 開始執行回測: config_both (日夜盤全跑) ----------")
    # run_backtest(config_both)
    
    logger.info("---------- 開始執行回測: config_day_only (僅日盤) ----------")
    run_backtest(config_day_only)

    logger.info("⏹️  回測程式執行完畢。")

if __name__ == '__main__':
    main()