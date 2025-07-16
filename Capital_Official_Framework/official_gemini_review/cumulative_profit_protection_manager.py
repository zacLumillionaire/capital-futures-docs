#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
累積獲利保護管理器
實現回測程式的保護邏輯，包含累積獲利計算和保護倍數邏輯
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProtectionUpdate:
    """保護性停損更新資訊"""
    position_id: int
    group_id: int
    lot_number: int
    direction: str
    old_stop_loss: float
    new_stop_loss: float
    cumulative_profit: float
    protection_multiplier: float
    update_category: str
    update_message: str
    update_time: str

class CumulativeProfitProtectionManager:
    """
    累積獲利保護管理器
    實現回測程式的保護邏輯
    """
    
    def __init__(self, db_manager, console_enabled: bool = True):
        """
        初始化累積獲利保護管理器
        
        Args:
            db_manager: 資料庫管理器
            console_enabled: 是否啟用Console日誌
        """
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        self.protection_updates: List[ProtectionUpdate] = []  # 保護更新歷史
        self.protection_callbacks: List = []  # 保護更新回調函數
        
        if self.console_enabled:
            print("[PROTECTION] ⚙️ 累積獲利保護管理器初始化完成")
    
    def add_protection_callback(self, callback):
        """
        添加保護更新回調函數
        
        Args:
            callback: 回調函數，接收 ProtectionUpdate 參數
        """
        self.protection_callbacks.append(callback)
        if self.console_enabled:
            print(f"[PROTECTION] 📞 添加保護回調函數: {callback.__name__}")
    
    def update_protective_stops_for_group(self, group_id: int, successful_exit_position_id: int) -> List[ProtectionUpdate]:
        """
        為策略組更新保護性停損
        當某個部位成功移動停利平倉後，更新其他部位的保護性停損
        
        Args:
            group_id: 策略組ID
            successful_exit_position_id: 成功平倉的部位ID
            
        Returns:
            List[ProtectionUpdate]: 保護更新列表
        """
        try:
            if self.console_enabled:
                print(f"[PROTECTION] 🛡️ 開始更新策略組 {group_id} 的保護性停損")
                print(f"[PROTECTION] 🎯 觸發部位: {successful_exit_position_id}")
            
            # 計算累積獲利
            cumulative_profit = self._calculate_cumulative_profit(group_id, successful_exit_position_id)
            
            if cumulative_profit <= 0:
                if self.console_enabled:
                    print(f"[PROTECTION] ⚠️ 累積獲利為 {cumulative_profit:.1f}，不更新保護性停損")
                return []
            
            if self.console_enabled:
                print(f"[PROTECTION] 💰 累積獲利: {cumulative_profit:.1f} 點")
            
            # 取得需要更新的部位
            remaining_positions = self._get_remaining_positions(group_id, successful_exit_position_id)
            
            if not remaining_positions:
                if self.console_enabled:
                    print(f"[PROTECTION] ℹ️ 策略組 {group_id} 沒有剩餘部位需要更新")
                return []
            
            protection_updates = []
            
            for position in remaining_positions:
                update = self._calculate_protective_stop_update(position, cumulative_profit)
                if update:
                    protection_updates.append(update)
            
            # 處理保護更新
            if protection_updates:
                self._process_protection_updates(protection_updates)
            
            return protection_updates
            
        except Exception as e:
            logger.error(f"更新保護性停損失敗: {e}")
            if self.console_enabled:
                print(f"[PROTECTION] ❌ 保護更新失敗: {e}")
            return []
    
    def _calculate_cumulative_profit(self, group_id: int, successful_exit_position_id: int) -> float:
        """
        計算累積獲利

        Args:
            group_id: 策略組ID
            successful_exit_position_id: 成功平倉的部位ID

        Returns:
            float: 累積獲利點數
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()

                # 🔧 修復：查詢該組所有已平倉部位的獲利（包含當前剛平倉的部位）
                # 移除 id <= ? 的限制，改為查詢所有已平倉的部位
                cursor.execute('''
                    SELECT id, realized_pnl, lot_id
                    FROM position_records
                    WHERE group_id = ?
                      AND status = 'EXITED'
                      AND realized_pnl IS NOT NULL
                    ORDER BY id
                ''', (group_id,))

                rows = cursor.fetchall()
                profits = []
                position_details = []

                for row in rows:
                    position_id, pnl, lot_id = row
                    if pnl is not None:
                        profits.append(pnl)
                        position_details.append({
                            'id': position_id,
                            'pnl': pnl,
                            'lot_id': lot_id
                        })

                cumulative_profit = sum(profits)

                if self.console_enabled:
                    print(f"[PROTECTION] 📊 累積獲利計算 (group_id={group_id}):")
                    print(f"[PROTECTION]   查詢到 {len(position_details)} 個已平倉部位")
                    for detail in position_details:
                        print(f"[PROTECTION]   部位{detail['id']} (lot_{detail['lot_id']}): {detail['pnl']:.1f} 點")
                    print(f"[PROTECTION]   總累積獲利: {cumulative_profit:.1f} 點")

                    # 🔍 診斷：如果累積獲利為0，額外檢查
                    if cumulative_profit == 0.0:
                        print(f"[PROTECTION] 🔍 診斷：累積獲利為0，檢查資料庫狀態...")
                        cursor.execute('''
                            SELECT id, status, realized_pnl, lot_id
                            FROM position_records
                            WHERE group_id = ?
                            ORDER BY id
                        ''', (group_id,))
                        all_positions = cursor.fetchall()
                        print(f"[PROTECTION] 🔍 該組所有部位狀態:")
                        for pos in all_positions:
                            print(f"[PROTECTION]     部位{pos[0]} (lot_{pos[3]}): status={pos[1]}, pnl={pos[2]}")

                return cumulative_profit

        except Exception as e:
            logger.error(f"計算累積獲利失敗: {e}")
            if self.console_enabled:
                print(f"[PROTECTION] ❌ 計算累積獲利異常: {e}")
            return 0.0
    
    def _get_remaining_positions(self, group_id: int, successful_exit_position_id: int) -> List[Dict]:
        """取得剩餘需要更新保護的部位"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pr.*, ler.protective_stop_multiplier
                    FROM position_records pr
                    LEFT JOIN lot_exit_rules ler ON pr.lot_rule_id = ler.lot_number
                    WHERE pr.group_id = ? 
                      AND pr.status = 'ACTIVE'
                      AND pr.id > ?
                      AND pr.is_initial_stop = TRUE
                    ORDER BY pr.lot_id
                ''', (group_id, successful_exit_position_id))
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"查詢剩餘部位失敗: {e}")
            return []
    
    def _calculate_protective_stop_update(self, position: Dict, cumulative_profit: float) -> Optional[ProtectionUpdate]:
        """
        計算保護性停損更新
        
        Args:
            position: 部位資料
            cumulative_profit: 累積獲利
            
        Returns:
            Optional[ProtectionUpdate]: 保護更新資訊 (如果需要更新)
        """
        position_id = None  # 🔧 修復：初始化變數避免異常處理時未定義錯誤
        try:
            # 🔧 修復：使用正確的鍵名，支援新舊格式
            position_id = position.get('position_pk') or position.get('id')
            if position_id is None:
                logger.error(f"部位資料缺少ID: {position}")
                return None

            direction = position['direction']
            entry_price = position['entry_price']
            current_stop_loss = position['current_stop_loss']
            protection_multiplier = position.get('protective_stop_multiplier', 2.0)  # 預設2.0倍
            lot_id = position.get('lot_id', 1)
            # 🔧 修復：使用正確的鍵名，支援新舊格式
            group_id = position.get('group_pk') or position.get('group_id')
            
            # 檢查是否有保護倍數設定
            if protection_multiplier is None:
                if self.console_enabled:
                    print(f"[PROTECTION] ℹ️ 部位 {position_id} (第{lot_id}口) 無保護倍數設定，跳過")
                return None
            
            # 計算保護性停損價格
            new_stop_loss = self._calculate_protective_stop_price(
                direction, entry_price, cumulative_profit, protection_multiplier
            )
            
            # 檢查是否需要更新 (保護性停損應該比當前停損更有利)
            should_update = self._should_update_protective_stop(
                direction, current_stop_loss, new_stop_loss
            )
            
            if should_update:
                update_category = "保護性停損更新"
                update_message = f"累積獲利{cumulative_profit:.1f}點 × {protection_multiplier}倍保護"

                if self.console_enabled:
                    print(f"[PROTECTION] 🛡️ 保護性停損更新:")
                    print(f"[PROTECTION]   部位ID: {position_id} (第{lot_id}口)")
                    print(f"[PROTECTION]   方向: {direction}")
                    print(f"[PROTECTION]   進場價格: {entry_price}")
                    print(f"[PROTECTION]   舊停損: {current_stop_loss}")
                    print(f"[PROTECTION]   新停損: {new_stop_loss}")
                    print(f"[PROTECTION]   累積獲利: {cumulative_profit:.1f} 點")
                    print(f"[PROTECTION]   保護倍數: {protection_multiplier}倍")
                    print(f"[PROTECTION]   改善幅度: {abs(new_stop_loss - current_stop_loss):.1f} 點")

                return ProtectionUpdate(
                    position_id=position_id,
                    group_id=group_id,
                    lot_number=lot_id,
                    direction=direction,
                    old_stop_loss=current_stop_loss,
                    new_stop_loss=new_stop_loss,
                    cumulative_profit=cumulative_profit,
                    protection_multiplier=protection_multiplier,
                    update_category=update_category,
                    update_message=update_message,
                    update_time=datetime.now().strftime('%H:%M:%S')
                )
            
            return None
            
        except Exception as e:
            logger.error(f"計算保護性停損更新失敗: {e}")
            if self.console_enabled:
                # 🔧 修復：安全地顯示position_id，避免未定義變數錯誤
                position_display = position_id if position_id is not None else "未知"
                print(f"[PROTECTION] ❌ 部位 {position_display} 保護性停損檢查失敗: {e}")
            return None
    
    def _calculate_protective_stop_price(self, direction: str, entry_price: float, 
                                       cumulative_profit: float, protection_multiplier: float) -> float:
        """
        計算保護性停損價格
        對應回測程式的 protective_stop_multiplier 邏輯
        
        Args:
            direction: 交易方向
            entry_price: 進場價格
            cumulative_profit: 累積獲利
            protection_multiplier: 保護倍數
            
        Returns:
            float: 保護性停損價格
        """
        protection_amount = cumulative_profit * protection_multiplier
        
        if direction == "LONG":
            # 做多：停損價格 = 進場價格 + 保護金額
            return entry_price + protection_amount
        elif direction == "SHORT":
            # 做空：停損價格 = 進場價格 - 保護金額
            return entry_price - protection_amount
        else:
            return entry_price
    
    def _should_update_protective_stop(self, direction: str, current_stop: float, new_stop: float) -> bool:
        """
        檢查是否應該更新保護性停損
        
        Args:
            direction: 交易方向
            current_stop: 當前停損
            new_stop: 新停損
            
        Returns:
            bool: 是否應該更新
        """
        if direction == "LONG":
            # 做多：新停損應該比當前停損更高 (更有利)
            return new_stop > current_stop
        elif direction == "SHORT":
            # 做空：新停損應該比當前停損更低 (更有利)
            return new_stop < current_stop
        
        return False
    
    def _process_protection_updates(self, protection_updates: List[ProtectionUpdate]):
        """
        處理保護更新
        
        Args:
            protection_updates: 保護更新列表
        """
        if self.console_enabled:
            print(f"[PROTECTION] ⚡ 處理 {len(protection_updates)} 個保護性停損更新")
        
        for update in protection_updates:
            try:
                # 更新資料庫
                self._update_protective_stop_in_database(update)
                
                # 記錄更新歷史
                self.protection_updates.append(update)
                
                # 觸發回調函數
                for callback in self.protection_callbacks:
                    try:
                        callback(update)
                    except Exception as e:
                        logger.error(f"保護更新回調函數執行失敗: {e}")
                        if self.console_enabled:
                            print(f"[PROTECTION] ❌ 回調函數 {callback.__name__} 執行失敗: {e}")
                
                if self.console_enabled:
                    print(f"[PROTECTION] ✅ 部位 {update.position_id} 保護性停損更新完成")
                    
            except Exception as e:
                logger.error(f"處理保護更新失敗: {e}")
                if self.console_enabled:
                    print(f"[PROTECTION] ❌ 部位 {update.position_id} 保護更新失敗: {e}")
    
    def _update_protective_stop_in_database(self, update: ProtectionUpdate):
        """
        更新資料庫中的保護性停損
        
        Args:
            update: 保護更新資訊
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 更新 position_records
                cursor.execute('''
                    UPDATE position_records 
                    SET current_stop_loss = ?,
                        is_initial_stop = FALSE,
                        cumulative_profit_before = ?,
                        last_price_update_time = ?
                    WHERE id = ?
                ''', (
                    update.new_stop_loss,
                    update.cumulative_profit,
                    update.update_time,
                    update.position_id
                ))
                
                # 更新 risk_management_states (如果存在)
                cursor.execute('''
                    UPDATE risk_management_states 
                    SET current_stop_loss = ?,
                        protection_activated = TRUE,
                        last_update_time = ?,
                        update_reason = ?
                    WHERE position_id = ?
                ''', (
                    update.new_stop_loss,
                    update.update_time,
                    update.update_reason,
                    update.position_id
                ))
                
                # 記錄保護事件
                event_id = f"protection_update_{update.position_id}_{int(time.time())}"
                cursor.execute('''
                    INSERT INTO exit_events 
                    (event_id, position_id, group_id, event_type, trigger_price, 
                     trigger_time, trigger_reason, execution_status)
                    VALUES (?, ?, ?, 'PROTECTIVE_STOP', ?, ?, ?, 'EXECUTED')
                ''', (
                    event_id,
                    update.position_id,
                    update.group_id,
                    update.new_stop_loss,
                    update.update_time,
                    update.update_reason
                ))
                
                conn.commit()
                
                if self.console_enabled:
                    print(f"[PROTECTION] 📝 部位 {update.position_id} 保護性停損已更新至 {update.new_stop_loss}")
                    
        except Exception as e:
            logger.error(f"更新資料庫保護性停損失敗: {e}")
    
    def get_protection_summary(self) -> Dict:
        """取得保護更新摘要"""
        total_updates = len(self.protection_updates)
        
        if total_updates == 0:
            return {
                'total_updates': 0,
                'average_improvement': 0,
                'max_improvement': 0,
                'callback_count': len(self.protection_callbacks)
            }
        
        improvements = [abs(update.new_stop_loss - update.old_stop_loss) for update in self.protection_updates]
        
        return {
            'total_updates': total_updates,
            'average_improvement': sum(improvements) / len(improvements),
            'max_improvement': max(improvements),
            'callback_count': len(self.protection_callbacks)
        }
    
    def print_protection_status(self):
        """列印保護狀態 (Console輸出)"""
        if not self.console_enabled:
            return
        
        summary = self.get_protection_summary()
        
        print(f"[PROTECTION] 📊 累積獲利保護狀態:")
        print(f"[PROTECTION]   總更新次數: {summary['total_updates']}")
        print(f"[PROTECTION]   平均改善: {summary['average_improvement']:.1f} 點")
        print(f"[PROTECTION]   最大改善: {summary['max_improvement']:.1f} 點")
        print(f"[PROTECTION]   回調函數: {summary['callback_count']} 個")
        
        if self.protection_updates:
            print(f"[PROTECTION] 🛡️ 最近保護更新:")
            for update in self.protection_updates[-3:]:  # 顯示最近3次更新
                improvement = abs(update.new_stop_loss - update.old_stop_loss)
                print(f"[PROTECTION]   部位{update.position_id}: {update.old_stop_loss} → {update.new_stop_loss} (+{improvement:.1f}點)")


def create_cumulative_profit_protection_manager(db_manager, console_enabled: bool = True) -> CumulativeProfitProtectionManager:
    """
    創建累積獲利保護管理器的工廠函數
    
    Args:
        db_manager: 資料庫管理器
        console_enabled: 是否啟用Console日誌
        
    Returns:
        CumulativeProfitProtectionManager: 保護管理器實例
    """
    return CumulativeProfitProtectionManager(db_manager, console_enabled)


if __name__ == "__main__":
    # 測試用途
    print("累積獲利保護管理器模組")
    print("請在主程式中調用 create_cumulative_profit_protection_manager() 函數")
