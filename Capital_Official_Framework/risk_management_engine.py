#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風險管理引擎
移植OrderTester.py的精密風險管理邏輯
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

from multi_group_config import LotRule
from multi_group_database import MultiGroupDatabaseManager

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskManagementEngine:
    """風險管理引擎 - 移植OrderTester.py的精密邏輯"""

    def __init__(self, db_manager: MultiGroupDatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 收盤平倉控制開關 (預設關閉，適合測試階段)
        self.enable_eod_close = False
        self.eod_close_hour = 13
        self.eod_close_minute = 30

        self.logger.info("風險管理引擎初始化完成")

    def set_eod_close_settings(self, enable: bool, hour: int = 13, minute: int = 30):
        """設定收盤平倉參數"""
        self.enable_eod_close = enable
        self.eod_close_hour = hour
        self.eod_close_minute = minute

        status = "啟用" if enable else "停用"
        self.logger.info(f"收盤平倉設定: {status} ({hour:02d}:{minute:02d})")

    def check_all_exit_conditions(self, current_price: float, current_time: str) -> List[Dict]:
        """檢查所有活躍部位的出場條件"""
        exit_actions = []
        
        try:
            active_positions = self.db_manager.get_all_active_positions()

            # 🔧 過濾掉無效部位（PENDING狀態或entry_price為None的部位）
            valid_positions = []
            for position in active_positions:
                if (position.get('entry_price') is not None and
                    position.get('order_status') == 'FILLED'):
                    valid_positions.append(position)
                else:
                    self.logger.debug(f"跳過無效部位: ID={position.get('id')}, "
                                    f"entry_price={position.get('entry_price')}, "
                                    f"order_status={position.get('order_status')}")

            self.logger.debug(f"檢查 {len(valid_positions)}/{len(active_positions)} 個有效部位的出場條件")
            
            # 按組分組處理
            groups = {}
            for position in valid_positions:
                group_id = position['group_id']
                if group_id not in groups:
                    groups[group_id] = []
                groups[group_id].append(position)
            
            # 逐組檢查
            for group_id, positions in groups.items():
                group_exits = self._check_group_exit_conditions(positions, current_price, current_time)
                exit_actions.extend(group_exits)
            
            return exit_actions
            
        except Exception as e:
            self.logger.error(f"檢查出場條件失敗: {e}")
            return []
    
    def _check_group_exit_conditions(self, positions: List[Dict],
                                   current_price: float, current_time: str) -> List[Dict]:
        """檢查單組的出場條件"""
        exit_actions = []

        try:
            if not positions:
                return exit_actions

            # 🕐 檢查收盤平倉 (13:30) - 最高優先級
            eod_close_exits = self._check_eod_close_conditions(positions, current_price, current_time)
            if eod_close_exits:
                exit_actions.extend(eod_close_exits)
                return exit_actions

            # 檢查初始停損 (第二優先級)
            initial_stop_exits = self._check_initial_stop_loss(positions, current_price)
            if initial_stop_exits:
                # 初始停損觸發，全組出場
                for position in positions:
                    pnl = self._calculate_pnl(position, current_price)
                    exit_actions.append({
                        'position_id': position['id'],
                        'exit_price': current_price,
                        'exit_time': current_time,
                        'exit_reason': '初始停損',
                        'pnl': pnl
                    })
                
                self.logger.info(f"組 {positions[0]['group_id']} 觸發初始停損，全組出場")
                return exit_actions
            
            # 檢查各口的個別出場條件
            for position in positions:
                # 檢查保護性停損
                if self._check_protective_stop_loss(position, current_price):
                    pnl = self._calculate_pnl(position, current_price)
                    exit_actions.append({
                        'position_id': position['id'],
                        'exit_price': position['current_stop_loss'],
                        'exit_time': current_time,
                        'exit_reason': '保護性停損',
                        'pnl': pnl
                    })
                    continue
                
                # 檢查移動停利條件
                trailing_exit = self._check_trailing_stop_conditions(position, current_price, current_time)
                if trailing_exit:
                    exit_actions.append(trailing_exit)
                    continue
                
                # 更新峰值價格和風險管理狀態
                self._update_position_risk_state(position, current_price, current_time)
            
            return exit_actions

        except Exception as e:
            self.logger.error(f"檢查組出場條件失敗: {e}")
            return []

    def _check_eod_close_conditions(self, positions: List[Dict],
                                  current_price: float, current_time: str) -> List[Dict]:
        """檢查收盤平倉條件"""
        exit_actions = []

        try:
            # 如果收盤平倉功能未啟用，直接返回
            if not self.enable_eod_close:
                return exit_actions

            # 解析當前時間
            hour, minute, second = map(int, current_time.split(':'))

            # 檢查是否到達收盤時間
            if hour >= self.eod_close_hour and minute >= self.eod_close_minute:
                self.logger.info(f"觸發收盤平倉: {current_time} (設定: {self.eod_close_hour:02d}:{self.eod_close_minute:02d})")

                # 對所有部位執行收盤平倉
                for position in positions:
                    pnl = self._calculate_pnl(position, current_price)
                    exit_actions.append({
                        'position_id': position['id'],
                        'exit_price': current_price,
                        'exit_time': current_time,
                        'exit_reason': '收盤平倉',
                        'pnl': pnl,
                        'group_id': position['group_id']
                    })

                if exit_actions:
                    self.logger.info(f"收盤平倉: {len(exit_actions)} 個部位")

            return exit_actions

        except Exception as e:
            self.logger.error(f"檢查收盤平倉條件失敗: {e}")
            return []

    def _check_initial_stop_loss(self, positions: List[Dict], current_price: float) -> bool:
        """檢查初始停損條件"""
        try:
            if not positions:
                return False
            
            # 取得區間邊界停損價格
            first_position = positions[0]
            direction = first_position['direction']
            range_high = first_position['range_high']
            range_low = first_position['range_low']
            
            if direction == 'LONG':
                # 做多：價格跌破區間低點
                return current_price <= range_low
            else:  # SHORT
                # 做空：價格漲破區間高點
                return current_price >= range_high
                
        except Exception as e:
            self.logger.error(f"檢查初始停損失敗: {e}")
            return False
    
    def _check_protective_stop_loss(self, position: Dict, current_price: float) -> bool:
        """檢查保護性停損條件"""
        try:
            # 只有非初始停損的部位才檢查保護性停損
            if not position.get('current_stop_loss') or not position.get('protection_activated'):
                return False
            
            direction = position['direction']
            stop_loss_price = position['current_stop_loss']
            
            if direction == 'LONG':
                return current_price <= stop_loss_price
            else:  # SHORT
                return current_price >= stop_loss_price
                
        except Exception as e:
            self.logger.error(f"檢查保護性停損失敗: {e}")
            return False
    
    def _check_trailing_stop_conditions(self, position: Dict, 
                                       current_price: float, current_time: str) -> Optional[Dict]:
        """檢查移動停利條件"""
        try:
            # 解析規則配置
            rule_config = json.loads(position['rule_config'])
            rule = LotRule.from_json(position['rule_config'])
            
            if not rule.use_trailing_stop or not rule.trailing_activation or not rule.trailing_pullback:
                return None
            
            direction = position['direction']
            entry_price = position['entry_price']
            peak_price = position['peak_price'] or entry_price
            trailing_activated = position['trailing_activated']
            
            # 檢查移動停利啟動條件
            if not trailing_activated:
                activation_triggered = False
                
                if direction == 'LONG':
                    activation_triggered = current_price >= entry_price + float(rule.trailing_activation)
                else:  # SHORT
                    activation_triggered = current_price <= entry_price - float(rule.trailing_activation)
                
                if activation_triggered:
                    # 啟動移動停利
                    self.db_manager.update_risk_management_state(
                        position_id=position['id'],
                        trailing_activated=True,
                        update_time=current_time,
                        update_reason="移動停利啟動"
                    )
                    
                    self.logger.info(f"部位 {position['id']} 第{rule_config['lot_id']}口移動停利啟動")
                    return None
            
            # 檢查移動停利出場條件
            if trailing_activated:
                pullback_ratio = float(rule.trailing_pullback)
                
                if direction == 'LONG':
                    stop_price = peak_price - (peak_price - entry_price) * pullback_ratio
                    if current_price <= stop_price:
                        pnl = stop_price - entry_price
                        return {
                            'position_id': position['id'],
                            'exit_price': stop_price,
                            'exit_time': current_time,
                            'exit_reason': '移動停利',
                            'pnl': pnl
                        }
                else:  # SHORT
                    stop_price = peak_price + (entry_price - peak_price) * pullback_ratio
                    if current_price >= stop_price:
                        pnl = entry_price - stop_price
                        return {
                            'position_id': position['id'],
                            'exit_price': stop_price,
                            'exit_time': current_time,
                            'exit_reason': '移動停利',
                            'pnl': pnl
                        }
            
            return None
            
        except Exception as e:
            self.logger.error(f"檢查移動停利條件失敗: {e}")
            return None
    
    def _update_position_risk_state(self, position: Dict, current_price: float, current_time: str):
        """更新部位風險管理狀態"""
        try:
            # 🔧 檢查必要欄位
            if position.get('entry_price') is None:
                self.logger.debug(f"跳過部位{position.get('id')}風險狀態更新: entry_price為None")
                return

            direction = position['direction']
            current_peak = position['peak_price'] or position['entry_price']
            
            # 更新峰值價格
            peak_updated = False
            if direction == 'LONG':
                if current_price > current_peak:
                    current_peak = current_price
                    peak_updated = True
            else:  # SHORT
                if current_price < current_peak:
                    current_peak = current_price
                    peak_updated = True
            
            # 如果峰值有更新，更新資料庫
            if peak_updated:
                self.db_manager.update_risk_management_state(
                    position_id=position['id'],
                    peak_price=current_peak,
                    update_time=current_time,
                    update_reason="價格更新"
                )
                
        except Exception as e:
            self.logger.error(f"更新風險狀態失敗: {e}")
    
    def _calculate_pnl(self, position: Dict, exit_price: float) -> float:
        """計算損益"""
        try:
            direction = position['direction']
            entry_price = position['entry_price']
            
            if direction == 'LONG':
                return exit_price - entry_price
            else:  # SHORT
                return entry_price - exit_price
                
        except Exception as e:
            self.logger.error(f"計算損益失敗: {e}")
            return 0.0
    
    def update_protective_stop_loss(self, exited_position_id: int, group_id: int) -> bool:
        """更新保護性停損 - 移植OrderTester.py邏輯"""
        try:
            # 獲取該組的所有部位
            group_positions = self.db_manager.get_active_positions_by_group(group_id)
            
            # 找到下一口需要更新保護的部位
            exited_position = None
            next_position = None
            
            # 先找到已出場的部位資訊
            all_positions = self.db_manager.get_all_active_positions()
            for pos in all_positions:
                if pos['id'] == exited_position_id:
                    exited_position = pos
                    break
            
            if not exited_position:
                return False
            
            # 解析已出場部位的規則
            exited_rule = LotRule.from_json(exited_position['rule_config'])
            
            # 找到下一口部位
            for pos in group_positions:
                pos_rule = LotRule.from_json(pos['rule_config'])
                if pos_rule.lot_id == exited_rule.lot_id + 1:
                    next_position = pos
                    break
            
            if not next_position or not next_position.get('rule_config'):
                return False
            
            next_rule = LotRule.from_json(next_position['rule_config'])
            if not next_rule.protective_stop_multiplier:
                return False
            
            # 檢查前面所有口單是否都獲利
            all_previous_profitable = self._check_all_previous_lots_profitable(
                group_id, next_rule.lot_id
            )
            
            if not all_previous_profitable:
                self.logger.info(f"前面有口單虧損，第{next_rule.lot_id}口維持原始停損")
                return False
            
            # 計算累積獲利並設定保護性停損
            total_profit = self._calculate_cumulative_profit(group_id, next_rule.lot_id)
            
            if total_profit <= 0:
                self.logger.info(f"累積獲利不足({total_profit:.1f}點)，第{next_rule.lot_id}口維持原始停損")
                return False
            
            # 設定保護性停損
            direction = next_position['direction']
            entry_price = next_position['entry_price']
            stop_loss_amount = total_profit * float(next_rule.protective_stop_multiplier)
            
            if direction == 'LONG':
                new_stop_loss = entry_price - stop_loss_amount
            else:  # SHORT
                new_stop_loss = entry_price + stop_loss_amount
            
            # 更新風險管理狀態
            current_time = datetime.now().strftime("%H:%M:%S")
            self.db_manager.update_risk_management_state(
                position_id=next_position['id'],
                current_stop_loss=new_stop_loss,
                protection_activated=True,
                update_time=current_time,
                update_reason="保護性停損更新"
            )
            
            self.logger.info(f"第{next_rule.lot_id}口保護性停損更新: {new_stop_loss:.0f} (基於累積獲利 {total_profit:.0f})")
            return True
            
        except Exception as e:
            self.logger.error(f"更新保護性停損失敗: {e}")
            return False
    
    def _check_all_previous_lots_profitable(self, group_id: int, target_lot_id: int) -> bool:
        """檢查目標口單之前的所有口單是否都獲利"""
        try:
            # 這裡需要查詢已出場的部位記錄
            # 由於資料庫設計限制，這裡簡化實現
            return True  # 暫時返回True，實際應該查詢歷史記錄
            
        except Exception as e:
            self.logger.error(f"檢查前面口單獲利狀況失敗: {e}")
            return False
    
    def _calculate_cumulative_profit(self, group_id: int, target_lot_id: int) -> float:
        """計算累積獲利"""
        try:
            # 這裡需要查詢已出場的部位記錄並計算累積獲利
            # 由於資料庫設計限制，這裡簡化實現
            return 50.0  # 暫時返回固定值，實際應該查詢歷史記錄
            
        except Exception as e:
            self.logger.error(f"計算累積獲利失敗: {e}")
            return 0.0

if __name__ == "__main__":
    # 測試風險管理引擎
    print("🧪 測試風險管理引擎")
    print("=" * 50)
    
    from multi_group_database import MultiGroupDatabaseManager
    
    # 使用測試資料庫
    db_manager = MultiGroupDatabaseManager("test_risk_engine.db")
    
    # 創建風險管理引擎
    engine = RiskManagementEngine(db_manager)
    
    print("✅ 風險管理引擎創建成功")
    
    # 測試檢查出場條件（需要有測試數據）
    exit_actions = engine.check_all_exit_conditions(22540.0, "09:00:00")
    print(f"✅ 檢查出場條件: {len(exit_actions)} 個出場動作")
    
    print("✅ 風險管理引擎測試完成")
