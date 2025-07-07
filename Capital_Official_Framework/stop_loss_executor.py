#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
停損執行器
負責執行停損平倉邏輯，整合現有下單系統
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class StopLossExecutionResult:
    """停損執行結果"""
    position_id: int
    success: bool
    order_id: Optional[str] = None
    execution_price: Optional[float] = None
    execution_time: Optional[str] = None
    error_message: Optional[str] = None
    pnl: Optional[float] = None

class StopLossExecutor:
    """
    停損執行器
    負責執行停損平倉邏輯
    """

    def __init__(self, db_manager, virtual_real_order_manager=None, console_enabled: bool = True):
        """
        初始化停損執行器

        Args:
            db_manager: 資料庫管理器
            virtual_real_order_manager: 虛實單管理器 (可選)
            console_enabled: 是否啟用Console日誌
        """
        self.db_manager = db_manager
        self.virtual_real_order_manager = virtual_real_order_manager
        self.console_enabled = console_enabled
        self.execution_history: List[StopLossExecutionResult] = []
        self.protection_manager = None  # 累積獲利保護管理器 (稍後設定)
        self.success_callbacks: List = []  # 成功平倉回調函數

        # 🔧 新增：FIFO追蹤器支援
        self.order_tracker = None  # 統一追蹤器 (稍後設定)
        self.simplified_tracker = None  # 簡化追蹤器 (稍後設定)

        if self.console_enabled:
            print("[STOP_EXECUTOR] ⚙️ 停損執行器初始化完成")
            if virtual_real_order_manager:
                print("[STOP_EXECUTOR] 🔗 已連接虛實單管理器")
            else:
                print("[STOP_EXECUTOR] ⚠️ 未連接虛實單管理器，將使用模擬模式")

    def set_trackers(self, order_tracker=None, simplified_tracker=None):
        """
        設定FIFO追蹤器

        Args:
            order_tracker: 統一追蹤器
            simplified_tracker: 簡化追蹤器
        """
        self.order_tracker = order_tracker
        self.simplified_tracker = simplified_tracker

        if self.console_enabled:
            if order_tracker:
                print("[STOP_EXECUTOR] 🔗 已連接統一追蹤器")
            if simplified_tracker:
                print("[STOP_EXECUTOR] 🔗 已連接簡化追蹤器")

    def set_protection_manager(self, protection_manager):
        """
        設定累積獲利保護管理器

        Args:
            protection_manager: 累積獲利保護管理器實例
        """
        self.protection_manager = protection_manager
        if self.console_enabled:
            print("[STOP_EXECUTOR] 🛡️ 已連接累積獲利保護管理器")

    def add_success_callback(self, callback):
        """
        添加成功平倉回調函數

        Args:
            callback: 回調函數，接收 (trigger_info, execution_result) 參數
        """
        self.success_callbacks.append(callback)
        if self.console_enabled:
            print(f"[STOP_EXECUTOR] 📞 添加成功回調函數: {callback.__name__}")
    
    def execute_stop_loss(self, trigger_info) -> StopLossExecutionResult:
        """
        執行停損平倉
        
        Args:
            trigger_info: 停損觸發資訊 (StopLossTrigger)
            
        Returns:
            StopLossExecutionResult: 執行結果
        """
        try:
            position_id = trigger_info.position_id
            current_price = trigger_info.current_price
            
            # 🔍 DEBUG: 停損執行開始 (重要事件，立即輸出)
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 🚨 開始執行停損平倉")
                print(f"[STOP_EXECUTOR]   部位ID: {position_id}")
                print(f"[STOP_EXECUTOR]   觸發價格: {current_price}")
                print(f"[STOP_EXECUTOR]   方向: {trigger_info.direction}")
                print(f"[STOP_EXECUTOR]   觸發原因: {getattr(trigger_info, 'trigger_reason', 'N/A')}")
                print(f"[STOP_EXECUTOR]   組別: {getattr(trigger_info, 'group_id', 'N/A')}")

            # 取得部位詳細資訊
            position_info = self._get_position_info(position_id)
            if not position_info:
                error_msg = f"無法取得部位 {position_id} 的詳細資訊"
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ❌ {error_msg}")
                return StopLossExecutionResult(position_id, False, error_message=error_msg)

            # 🔍 DEBUG: 部位資訊驗證
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 📋 部位資訊驗證:")
                print(f"[STOP_EXECUTOR]   進場價: {position_info.get('entry_price', 'N/A')}")
                print(f"[STOP_EXECUTOR]   部位方向: {position_info.get('direction', 'N/A')}")
                print(f"[STOP_EXECUTOR]   部位狀態: {position_info.get('status', 'N/A')}")
                print(f"[STOP_EXECUTOR]   組別: {position_info.get('group_id', 'N/A')}")

            # 計算平倉參數
            exit_direction = "SHORT" if trigger_info.direction == "LONG" else "LONG"
            quantity = 1  # 每次平倉1口

            # 🔍 DEBUG: 平倉參數計算
            if self.console_enabled:
                entry_price = position_info.get('entry_price', 0)
                if trigger_info.direction == "LONG":
                    expected_pnl = current_price - entry_price
                else:
                    expected_pnl = entry_price - current_price

                print(f"[STOP_EXECUTOR] 📋 平倉參數:")
                print(f"[STOP_EXECUTOR]   平倉方向: {exit_direction}")
                print(f"[STOP_EXECUTOR]   平倉數量: {quantity} 口")
                print(f"[STOP_EXECUTOR]   預期價格: {current_price}")
                print(f"[STOP_EXECUTOR]   進場價格: {entry_price}")
                print(f"[STOP_EXECUTOR]   預期損益: {expected_pnl:+.0f}點")
            
            # 🔍 DEBUG: 開始執行平倉下單
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 🚀 開始執行平倉下單...")

            # 執行平倉下單
            execution_result = self._execute_exit_order(
                position_info, exit_direction, quantity, current_price, trigger_info
            )

            # 🔍 DEBUG: 下單結果追蹤 (重要結果，立即輸出)
            if self.console_enabled:
                if execution_result.success:
                    print(f"[STOP_EXECUTOR] ✅ 平倉下單成功:")
                    print(f"[STOP_EXECUTOR]   訂單ID: {execution_result.order_id}")
                    print(f"[STOP_EXECUTOR]   執行價格: {execution_result.execution_price}")
                    print(f"[STOP_EXECUTOR]   執行時間: {execution_result.execution_time}")
                    print(f"[STOP_EXECUTOR]   實際損益: {execution_result.pnl:+.1f}點")
                else:
                    print(f"[STOP_EXECUTOR] ❌ 平倉下單失敗:")
                    print(f"[STOP_EXECUTOR]   錯誤訊息: {execution_result.error_message}")

            # 更新資料庫
            if execution_result.success:
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] 💾 更新資料庫狀態...")

                self._update_position_exit_status(position_id, execution_result, trigger_info)

                # 🛡️ 觸發保護性停損更新 (如果是移動停利成功平倉)
                if self.console_enabled:
                    trigger_reason = getattr(trigger_info, 'trigger_reason', '')
                    pnl = getattr(execution_result, 'pnl', 0) or 0
                    if '移動停利' in trigger_reason and pnl > 0:
                        print(f"[STOP_EXECUTOR] 🛡️ 移動停利獲利平倉，檢查保護性停損更新...")
                    else:
                        print(f"[STOP_EXECUTOR] ℹ️ 非移動停利獲利平倉，跳過保護性停損更新")

                self._trigger_protection_update_if_needed(trigger_info, execution_result)

                # 觸發成功回調函數
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] 📞 觸發成功回調函數...")

                self._trigger_success_callbacks(trigger_info, execution_result)
            else:
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ⚠️ 平倉失敗，跳過後續處理")

            # 記錄執行歷史
            self.execution_history.append(execution_result)

            # 🔍 DEBUG: 最終執行結果摘要
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 📊 執行結果摘要:")
                if execution_result.success:
                    print(f"[STOP_EXECUTOR]   ✅ 停損平倉執行成功")
                    print(f"[STOP_EXECUTOR]   訂單ID: {execution_result.order_id}")
                    print(f"[STOP_EXECUTOR]   執行價格: {execution_result.execution_price}")
                    print(f"[STOP_EXECUTOR]   損益: {execution_result.pnl:+.1f}點")
                else:
                    print(f"[STOP_EXECUTOR]   ❌ 停損平倉執行失敗")
                    print(f"[STOP_EXECUTOR]   錯誤訊息: {execution_result.error_message}")
                print(f"[STOP_EXECUTOR] ═══════════════════════════════════════")

            return execution_result
            
        except Exception as e:
            error_msg = f"停損執行過程發生錯誤: {e}"
            logger.error(error_msg)
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] ❌ {error_msg}")
            return StopLossExecutionResult(trigger_info.position_id, False, error_message=error_msg)
    
    def _get_position_info(self, position_id: int) -> Optional[Dict]:
        """取得部位詳細資訊"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT pr.*, sg.range_high, sg.range_low, sg.direction as group_direction
                    FROM position_records pr
                    JOIN strategy_groups sg ON pr.group_id = sg.id
                    WHERE pr.id = ? AND pr.status = 'ACTIVE'
                ''', (position_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            logger.error(f"查詢部位資訊失敗: {e}")
            return None
    
    def _execute_exit_order(self, position_info: Dict, exit_direction: str, 
                          quantity: int, current_price: float, trigger_info) -> StopLossExecutionResult:
        """
        執行平倉下單
        
        Args:
            position_info: 部位資訊
            exit_direction: 平倉方向
            quantity: 平倉數量
            current_price: 當前價格
            trigger_info: 觸發資訊
            
        Returns:
            StopLossExecutionResult: 執行結果
        """
        position_id = position_info['id']
        
        try:
            if self.virtual_real_order_manager:
                # 使用真實下單系統
                result = self._execute_real_exit_order(
                    position_info, exit_direction, quantity, current_price
                )
            else:
                # 使用模擬下單
                result = self._execute_simulated_exit_order(
                    position_info, exit_direction, quantity, current_price
                )
            
            return result
            
        except Exception as e:
            error_msg = f"平倉下單執行失敗: {e}"
            logger.error(error_msg)
            return StopLossExecutionResult(position_id, False, error_message=error_msg)
    
    def _execute_real_exit_order(self, position_info: Dict, exit_direction: str, 
                               quantity: int, current_price: float) -> StopLossExecutionResult:
        """執行真實平倉下單"""
        position_id = position_info['id']
        
        try:
            # 使用虛實單管理器執行平倉
            signal_source = f"stop_loss_exit_{position_id}"
            
            order_result = self.virtual_real_order_manager.execute_strategy_order(
                direction=exit_direction,
                quantity=quantity,
                signal_source=signal_source,
                order_type="FOK",  # 使用FOK確保立即成交或取消
                price=current_price
            )
            
            if order_result and hasattr(order_result, 'success') and order_result.success:
                # 🔧 新增：註冊平倉訂單到FIFO追蹤器
                order_id = getattr(order_result, 'order_id', None)

                if self.order_tracker and order_id:
                    self.order_tracker.register_order(
                        order_id=order_id,
                        product="TM0000",
                        direction=exit_direction,
                        quantity=quantity,
                        price=current_price,
                        signal_source=f"exit_{position_id}",
                        is_virtual=(getattr(order_result, 'mode', 'virtual') == "virtual")
                    )

                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR] 📝 平倉訂單已註冊到統一追蹤器: {order_id}")

                # 🔧 新增：註冊到簡化追蹤器
                if self.simplified_tracker and order_id:
                    self.simplified_tracker.register_exit_order(
                        position_id=position_id,
                        order_id=order_id,
                        direction=exit_direction,
                        quantity=quantity,
                        price=current_price,
                        product="TM0000"
                    )

                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR] 📝 平倉訂單已註冊到簡化追蹤器: {order_id}")

                # 計算損益
                entry_price = position_info.get('entry_price', current_price)
                pnl = self._calculate_pnl(
                    position_info['direction'], entry_price, current_price
                )

                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ✅ 真實平倉下單成功:")
                    print(f"[STOP_EXECUTOR]   訂單ID: {order_id}")
                    print(f"[STOP_EXECUTOR]   執行模式: {getattr(order_result, 'mode', 'unknown')}")

                return StopLossExecutionResult(
                    position_id=position_id,
                    success=True,
                    order_id=order_id,
                    execution_price=current_price,
                    execution_time=datetime.now().strftime('%H:%M:%S'),
                    pnl=pnl
                )
            else:
                error_msg = getattr(order_result, 'error_message', '下單失敗')
                return StopLossExecutionResult(position_id, False, error_message=error_msg)
                
        except Exception as e:
            return StopLossExecutionResult(position_id, False, error_message=str(e))
    
    def _execute_simulated_exit_order(self, position_info: Dict, exit_direction: str, 
                                    quantity: int, current_price: float) -> StopLossExecutionResult:
        """執行模擬平倉下單"""
        position_id = position_info['id']
        
        try:
            # 模擬下單成功
            order_id = f"SIM_STOP_{position_id}_{int(time.time())}"
            
            # 計算損益
            entry_price = position_info.get('entry_price', current_price)
            pnl = self._calculate_pnl(
                position_info['direction'], entry_price, current_price
            )
            
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 🎭 模擬平倉執行:")
                print(f"[STOP_EXECUTOR]   模擬訂單ID: {order_id}")
                print(f"[STOP_EXECUTOR]   進場價格: {entry_price}")
                print(f"[STOP_EXECUTOR]   平倉價格: {current_price}")
                print(f"[STOP_EXECUTOR]   模擬損益: {pnl:.1f} 點")
            
            return StopLossExecutionResult(
                position_id=position_id,
                success=True,
                order_id=order_id,
                execution_price=current_price,
                execution_time=datetime.now().strftime('%H:%M:%S'),
                pnl=pnl
            )
            
        except Exception as e:
            return StopLossExecutionResult(position_id, False, error_message=str(e))
    
    def _calculate_pnl(self, direction: str, entry_price: float, exit_price: float) -> float:
        """
        計算損益點數
        
        Args:
            direction: 交易方向
            entry_price: 進場價格
            exit_price: 出場價格
            
        Returns:
            float: 損益點數
        """
        if direction == "LONG":
            return exit_price - entry_price
        elif direction == "SHORT":
            return entry_price - exit_price
        else:
            return 0.0
    
    def _update_position_exit_status(self, position_id: int, execution_result: StopLossExecutionResult, 
                                   trigger_info):
        """更新部位出場狀態"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # 更新 position_records
                cursor.execute('''
                    UPDATE position_records 
                    SET status = 'EXITED',
                        exit_price = ?,
                        exit_time = ?,
                        exit_reason = 'INITIAL_STOP',
                        exit_trigger_type = 'INITIAL_STOP',
                        exit_order_id = ?,
                        realized_pnl = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    execution_result.execution_price,
                    execution_result.execution_time,
                    execution_result.order_id,
                    execution_result.pnl,
                    position_id
                ))
                
                # 更新 exit_events
                cursor.execute('''
                    UPDATE exit_events 
                    SET execution_status = 'EXECUTED',
                        exit_price = ?,
                        execution_time = ?,
                        pnl = ?,
                        order_id = ?
                    WHERE position_id = ? AND event_type = 'INITIAL_STOP' AND execution_status = 'PENDING'
                ''', (
                    execution_result.execution_price,
                    execution_result.execution_time,
                    execution_result.pnl,
                    execution_result.order_id,
                    position_id
                ))
                
                conn.commit()
                
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] 📝 部位 {position_id} 出場狀態已更新")
                    
        except Exception as e:
            logger.error(f"更新部位出場狀態失敗: {e}")
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] ❌ 更新部位狀態失敗: {e}")

    def _trigger_protection_update_if_needed(self, trigger_info, execution_result):
        """
        如果需要，觸發保護性停損更新

        Args:
            trigger_info: 觸發資訊
            execution_result: 執行結果
        """
        try:
            # 檢查是否為移動停利平倉且有獲利
            if (execution_result.pnl and execution_result.pnl > 0 and
                hasattr(trigger_info, 'trigger_reason') and
                "移動停利" in trigger_info.trigger_reason):

                if self.protection_manager:
                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR] 🛡️ 觸發保護性停損更新")
                        print(f"[STOP_EXECUTOR]   成功平倉部位: {trigger_info.position_id}")
                        print(f"[STOP_EXECUTOR]   獲利: {execution_result.pnl:.1f} 點")

                    # 更新策略組的保護性停損
                    protection_updates = self.protection_manager.update_protective_stops_for_group(
                        trigger_info.group_id, trigger_info.position_id
                    )

                    if protection_updates and self.console_enabled:
                        print(f"[STOP_EXECUTOR] ✅ 已更新 {len(protection_updates)} 個保護性停損")
                else:
                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR] ⚠️ 未設定保護管理器，跳過保護更新")

        except Exception as e:
            logger.error(f"觸發保護更新失敗: {e}")
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] ❌ 保護更新觸發失敗: {e}")

    def _trigger_success_callbacks(self, trigger_info, execution_result):
        """
        觸發成功平倉回調函數

        Args:
            trigger_info: 觸發資訊
            execution_result: 執行結果
        """
        for callback in self.success_callbacks:
            try:
                callback(trigger_info, execution_result)
            except Exception as e:
                logger.error(f"成功回調函數執行失敗: {e}")
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ❌ 回調函數 {callback.__name__} 執行失敗: {e}")

    def get_execution_summary(self) -> Dict:
        """取得執行摘要"""
        total_executions = len(self.execution_history)
        successful_executions = len([r for r in self.execution_history if r.success])
        
        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': total_executions - successful_executions,
            'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0
        }
    
    def print_execution_summary(self):
        """列印執行摘要 (Console輸出)"""
        if not self.console_enabled:
            return
        
        summary = self.get_execution_summary()
        
        print(f"[STOP_EXECUTOR] 📊 停損執行摘要:")
        print(f"[STOP_EXECUTOR]   總執行次數: {summary['total_executions']}")
        print(f"[STOP_EXECUTOR]   成功次數: {summary['successful_executions']}")
        print(f"[STOP_EXECUTOR]   失敗次數: {summary['failed_executions']}")
        print(f"[STOP_EXECUTOR]   成功率: {summary['success_rate']:.1f}%")


def create_stop_loss_executor(db_manager, virtual_real_order_manager=None, 
                            console_enabled: bool = True) -> StopLossExecutor:
    """
    創建停損執行器的工廠函數
    
    Args:
        db_manager: 資料庫管理器
        virtual_real_order_manager: 虛實單管理器 (可選)
        console_enabled: 是否啟用Console日誌
        
    Returns:
        StopLossExecutor: 停損執行器實例
    """
    return StopLossExecutor(db_manager, virtual_real_order_manager, console_enabled)


# 🔧 為StopLossExecutor類添加平倉追價方法
def add_exit_retry_methods():
    """為StopLossExecutor類動態添加平倉追價方法"""

    def execute_exit_retry(self, position_id: int, exit_order: dict, retry_count: int = 1) -> bool:
        """
        執行平倉追價重試

        Args:
            position_id: 部位ID
            exit_order: 平倉訂單信息
            retry_count: 重試次數

        Returns:
            bool: 追價是否成功
        """
        try:
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 🔄 開始平倉追價:")
                print(f"[STOP_EXECUTOR]   部位ID: {position_id}")
                print(f"[STOP_EXECUTOR]   重試次數: {retry_count}")
                print(f"[STOP_EXECUTOR]   原始價格: {exit_order.get('price', 'N/A')}")

            # 檢查重試次數限制
            max_retries = 5
            if retry_count > max_retries:
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ⚠️ 超過最大重試次數({max_retries})，放棄追價")
                return False

            # 取得部位資訊
            position_info = self.db_manager.get_position_by_id(position_id)
            if not position_info:
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ❌ 找不到部位{position_id}資訊")
                return False

            # 計算追價價格
            retry_price = self._calculate_exit_retry_price(
                position_info['direction'],
                retry_count
            )

            if retry_price is None:
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ❌ 無法計算追價價格")
                return False

            # 檢查滑價限制
            original_price = exit_order.get('price', 0)
            max_slippage = 5  # 最大滑價5點
            actual_slippage = abs(retry_price - original_price)

            if actual_slippage > max_slippage:
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ⚠️ 滑價超出限制: {actual_slippage:.0f}點 > {max_slippage}點")
                return False

            # 執行追價下單
            exit_direction = exit_order['direction']
            quantity = exit_order['quantity']

            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 🚀 執行追價下單:")
                print(f"[STOP_EXECUTOR]   方向: {exit_direction}")
                print(f"[STOP_EXECUTOR]   數量: {quantity}口")
                print(f"[STOP_EXECUTOR]   追價: {retry_price:.0f} (第{retry_count}次)")

            # 使用虛實單管理器執行追價下單
            if hasattr(self, 'virtual_real_order_manager') and self.virtual_real_order_manager:
                order_result = self.virtual_real_order_manager.execute_strategy_order(
                    direction=exit_direction,
                    quantity=quantity,
                    signal_source=f"exit_retry_{position_id}_{retry_count}",
                    order_type="FOK",
                    price=retry_price
                )

                if order_result.success:
                    # 註冊新的平倉訂單到追蹤器
                    if hasattr(self, 'simplified_tracker') and self.simplified_tracker:
                        self.simplified_tracker.register_exit_order(
                            position_id=position_id,
                            order_id=order_result.order_id,
                            direction=exit_direction,
                            quantity=quantity,
                            price=retry_price,
                            product="TM0000"
                        )

                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR] ✅ 平倉追價下單成功:")
                        print(f"[STOP_EXECUTOR]   訂單ID: {order_result.order_id}")
                        print(f"[STOP_EXECUTOR]   追價: {retry_price:.0f}")

                    return True
                else:
                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR] ❌ 平倉追價下單失敗: {order_result.error_message}")
                    return False
            else:
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ❌ 虛實單管理器未初始化")
                return False

        except Exception as e:
            logger.error(f"執行平倉追價失敗: {e}")
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] ❌ 平倉追價異常: {e}")
            return False

    def _calculate_exit_retry_price(self, position_direction: str, retry_count: int) -> float:
        """
        計算平倉追價價格

        Args:
            position_direction: 部位方向 (LONG/SHORT)
            retry_count: 重試次數

        Returns:
            float: 追價價格
        """
        try:
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 🧮 計算平倉追價價格:")
                print(f"[STOP_EXECUTOR]   部位方向: {position_direction}")
                print(f"[STOP_EXECUTOR]   重試次數: {retry_count}")

            # 獲取當前市價
            if hasattr(self, 'virtual_real_order_manager') and self.virtual_real_order_manager:
                current_ask1 = getattr(self.virtual_real_order_manager, 'current_ask1', 0)
                current_bid1 = getattr(self.virtual_real_order_manager, 'current_bid1', 0)

                if position_direction == "LONG":
                    # 多單平倉：使用BID1，向下追價
                    retry_price = current_bid1 - retry_count
                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR]   多單平倉: BID1({current_bid1:.0f}) - {retry_count} = {retry_price:.0f}")
                elif position_direction == "SHORT":
                    # 空單平倉：使用ASK1，向上追價
                    retry_price = current_ask1 + retry_count
                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR]   空單平倉: ASK1({current_ask1:.0f}) + {retry_count} = {retry_price:.0f}")
                else:
                    if self.console_enabled:
                        print(f"[STOP_EXECUTOR] ❌ 未知的部位方向: {position_direction}")
                    return None

                return retry_price
            else:
                if self.console_enabled:
                    print(f"[STOP_EXECUTOR] ❌ 無法獲取當前市價")
                return None

        except Exception as e:
            logger.error(f"計算平倉追價價格失敗: {e}")
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] ❌ 計算追價價格異常: {e}")
            return None

    # 動態添加方法到StopLossExecutor類
    StopLossExecutor.execute_exit_retry = execute_exit_retry
    StopLossExecutor._calculate_exit_retry_price = _calculate_exit_retry_price

# 自動執行方法添加
add_exit_retry_methods()


if __name__ == "__main__":
    # 測試用途
    print("停損執行器模組")
    print("請在主程式中調用 create_stop_loss_executor() 函數")
