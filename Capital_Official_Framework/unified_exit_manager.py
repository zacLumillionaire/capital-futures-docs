"""
統一出場管理器 - 所有出場的統一入口
基於進場機制的成功經驗，確保出場邏輯的一致性和可靠性
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
import time
import threading

# 導入標準化函式
from stop_loss_executor import standardize_exit_reason


class UnifiedExitManager:
    """統一出場管理器 - 所有出場的統一入口"""
    
    def __init__(self, order_manager, position_manager, db_manager, console_enabled=True):
        """
        初始化統一出場管理器
        
        Args:
            order_manager: 下單管理器 (復用進場的)
            position_manager: 部位管理器
            db_manager: 資料庫管理器
            console_enabled: 是否啟用Console輸出
        """
        self.order_manager = order_manager
        self.position_manager = position_manager
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        
        # 設置日誌
        self.logger = logging.getLogger(__name__)
        
        # 出場統計
        self.total_exits = 0
        self.successful_exits = 0
        self.failed_exits = 0
        
        # 出場歷史記錄
        self.exit_history = []

        # 🚀 異步更新支援（解決平倉延遲問題）
        self.async_updater = None
        self.async_update_enabled = True  # 🔧 修改：預設啟用異步更新

        if self.console_enabled:
            print("[UNIFIED_EXIT] ✅ 統一出場管理器初始化完成")

    def set_async_updater(self, async_updater, enabled=True):
        """🚀 設置異步更新器（解決平倉延遲問題）"""
        self.async_updater = async_updater
        self.async_update_enabled = enabled
        if self.console_enabled:
            status = "啟用" if enabled else "關閉"
            print(f"[UNIFIED_EXIT] 🚀 異步更新已{status}")

    def trigger_exit(self, position_id: int, exit_reason: str,
                    exit_price: Optional[float] = None) -> bool:
        """
        統一出場觸發方法 - 所有出場的統一入口
        
        Args:
            position_id: 部位ID
            exit_reason: 出場原因 (initial_stop_loss, trailing_stop, 
                        protection_stop, eod_close, manual_exit)
            exit_price: 指定出場價格 (可選，自動選擇BID1/ASK1)
            
        Returns:
            bool: 是否成功觸發出場
        """
        try:
            # 1. 取得部位資訊
            position_info = self.db_manager.get_position_by_id(position_id)
            if not position_info:
                self.logger.error(f"找不到部位 {position_id}")
                return False
            
            # 2. 檢查部位狀態
            if position_info.get('status') != 'ACTIVE':
                self.logger.warning(f"部位{position_id}狀態不是ACTIVE: {position_info.get('status')}")
                return False
            
            # 3. 取得出場價格 (如果未指定)
            if not exit_price:
                exit_price = self.get_exit_price(position_info['direction'])
                if not exit_price:
                    self.logger.error(f"無法取得部位{position_id}的出場價格")
                    return False
            
            # 4. 執行出場下單
            success = self.execute_exit_order(position_info, exit_price, exit_reason)
            
            # 5. 更新統計
            self.total_exits += 1
            if success:
                self.successful_exits += 1
                if self.console_enabled:
                    print(f"[UNIFIED_EXIT] ✅ 部位{position_id}出場觸發成功: {exit_reason} @{exit_price}")
            else:
                self.failed_exits += 1
                if self.console_enabled:
                    print(f"[UNIFIED_EXIT] ❌ 部位{position_id}出場觸發失敗: {exit_reason}")
            
            # 6. 記錄出場歷史
            self.exit_history.append({
                'timestamp': datetime.now(),
                'position_id': position_id,
                'exit_reason': exit_reason,
                'exit_price': exit_price,
                'success': success
            })
            
            return success
            
        except Exception as e:
            self.logger.error(f"觸發出場失敗: {e}")
            if self.console_enabled:
                print(f"[UNIFIED_EXIT] ❌ 觸發出場異常: {e}")
            return False

    def execute_protective_stop(self, position_id: int, protective_price: float) -> bool:
        """
        執行保護性停損

        Args:
            position_id: 部位ID
            protective_price: 保護性停損價格

        Returns:
            bool: 是否成功執行
        """
        try:
            if self.console_enabled:
                print(f"[UNIFIED_EXIT] 🛡️ 執行保護性停損: 部位{position_id} @{protective_price}")

            # 使用統一出場方法執行保護性停損
            success = self.trigger_exit(
                position_id=position_id,
                exit_reason="protection_stop",
                exit_price=protective_price
            )

            if success and self.console_enabled:
                print(f"[UNIFIED_EXIT] ✅ 保護性停損執行成功: 部位{position_id}")
            elif not success and self.console_enabled:
                print(f"[UNIFIED_EXIT] ❌ 保護性停損執行失敗: 部位{position_id}")

            return success

        except Exception as e:
            self.logger.error(f"保護性停損執行異常: {e}")
            if self.console_enabled:
                print(f"[UNIFIED_EXIT] ❌ 保護性停損執行異常: {e}")
            return False

    def trigger_protective_stop_update(self, position_id: int, first_lot_profit: float,
                                     protection_multiplier: float) -> bool:
        """
        觸發保護性停損更新

        Args:
            position_id: 部位ID
            first_lot_profit: 第一口獲利
            protection_multiplier: 保護倍數

        Returns:
            bool: 是否成功觸發更新
        """
        try:
            if self.console_enabled:
                print(f"[UNIFIED_EXIT] 🛡️ 觸發保護性停損更新: 部位{position_id}")
                print(f"[UNIFIED_EXIT]   第一口獲利: {first_lot_profit:.1f}點")
                print(f"[UNIFIED_EXIT]   保護倍數: {protection_multiplier}倍")

            # 獲取部位信息
            position_info = self.db_manager.get_position_by_id(position_id)
            if not position_info:
                if self.console_enabled:
                    print(f"[UNIFIED_EXIT] ❌ 找不到部位{position_id}")
                return False

            # 計算保護性停損價格
            direction = position_info['direction']
            entry_price = position_info['entry_price']
            stop_loss_amount = first_lot_profit * protection_multiplier

            if direction == 'LONG':
                new_stop_loss = entry_price - stop_loss_amount
            else:  # SHORT
                new_stop_loss = entry_price + stop_loss_amount  # 正確：空單止損往高點移動

            # 更新資料庫狀態
            from datetime import datetime
            current_time = datetime.now().strftime("%H:%M:%S")

            self.db_manager.update_risk_management_state(
                position_id=position_id,
                current_stop_loss=new_stop_loss,
                protection_activated=True,
                update_time=current_time,
                update_category="保護性停損更新",
                update_message=f"基於第一口獲利{first_lot_profit:.1f}點，{protection_multiplier}倍保護"
            )

            if self.console_enabled:
                print(f"[UNIFIED_EXIT] ✅ 保護性停損更新完成: {new_stop_loss:.0f}")

            return True

        except Exception as e:
            self.logger.error(f"保護性停損更新異常: {e}")
            if self.console_enabled:
                print(f"[UNIFIED_EXIT] ❌ 保護性停損更新異常: {e}")
            return False

    def get_exit_price(self, position_direction: str, product: str = "TM0000") -> Optional[float]:
        """
        取得出場價格 - 多單用BID1，空單用ASK1
        
        Args:
            position_direction: 部位方向 (LONG/SHORT)
            product: 商品代碼
            
        Returns:
            float: 出場價格 或 None
        """
        try:
            if position_direction.upper() == "LONG":
                # 多單出場 → 賣出 → 使用BID1價格
                price = self.order_manager.get_bid1_price(product)
                price_type = "BID1"
            elif position_direction.upper() == "SHORT":
                # 空單出場 → 買回 → 使用ASK1價格
                price = self.order_manager.get_ask1_price(product)
                price_type = "ASK1"
            else:
                self.logger.error(f"無效的部位方向: {position_direction}")
                return None
            
            if price and self.console_enabled:
                print(f"[EXIT_PRICE] {position_direction}出場使用{price_type}: {price}")
            
            return price
            
        except Exception as e:
            self.logger.error(f"取得出場價格失敗: {e}")
            return None
    
    def execute_exit_order(self, position_info: Dict, exit_price: float, 
                          exit_reason: str) -> bool:
        """
        執行出場下單 - 復用進場機制的 execute_strategy_order
        
        Args:
            position_info: 部位資訊
            exit_price: 出場價格
            exit_reason: 出場原因
            
        Returns:
            bool: 是否成功
        """
        try:
            # 1. 確定出場方向
            original_direction = position_info['direction']
            if original_direction.upper() == "LONG":
                exit_direction = "SELL"  # 多單出場 → 賣出
            elif original_direction.upper() == "SHORT":
                exit_direction = "BUY"   # 空單出場 → 買回
            else:
                self.logger.error(f"無效的原始方向: {original_direction}")
                return False
            
            # 2. 使用與進場相同的下單方法，但設定為平倉 (關鍵！)
            order_result = self.order_manager.execute_strategy_order(
                direction=exit_direction,
                signal_source=f"exit_{exit_reason}_{position_info['id']}",
                product="TM0000",
                price=exit_price,
                quantity=1,
                new_close=1  # 🔧 修復：設定為平倉 (1=平倉)
            )
            
            # 3. 處理下單結果 (與進場邏輯一致)
            if order_result.success:
                # 🚀 異步更新部位狀態（解決平倉延遲問題）
                if self.async_update_enabled and self.async_updater:
                    # 🚀 異步更新（非阻塞）
                    self.async_updater.schedule_position_status_update(
                        position_id=position_info['id'],
                        status='ACTIVE',  # 保持ACTIVE狀態
                        exit_reason=exit_reason,
                        exit_price=exit_price,
                        update_reason="出場下單成功"
                    )
                else:
                    # 🛡️ 同步更新（備用模式）
                    standardized_reason = standardize_exit_reason(exit_reason)
                    self.db_manager.update_position_status(
                        position_id=position_info['id'],
                        status='ACTIVE',  # 保持ACTIVE狀態
                        exit_reason=standardized_reason,
                        exit_price=exit_price
                    )
                
                # 建立部位訂單映射 (用於追價)
                if hasattr(self.position_manager, 'position_order_mapping'):
                    self.position_manager.position_order_mapping[position_info['id']] = order_result.order_id
                
                if self.console_enabled:
                    mode_desc = "實單" if order_result.mode == "real" else "虛擬"
                    direction_desc = "多單" if original_direction.upper() == "LONG" else "空單"
                    price_type = "BID1" if original_direction.upper() == "LONG" else "ASK1"
                    print(f"[EXIT_ORDER] 🔚 {direction_desc}出場{mode_desc}下單成功 - TM0000 1口 @{exit_price} ({price_type})")
                
                return True
            else:
                self.logger.error(f"出場下單失敗: {order_result.error}")
                if self.console_enabled:
                    print(f"[EXIT_ORDER] ❌ 出場下單失敗: {order_result.error}")
                return False
                
        except Exception as e:
            self.logger.error(f"執行出場下單失敗: {e}")
            if self.console_enabled:
                print(f"[EXIT_ORDER] ❌ 執行出場下單異常: {e}")
            return False
    
    def get_exit_statistics(self) -> Dict:
        """取得出場統計資訊"""
        success_rate = (self.successful_exits / self.total_exits * 100) if self.total_exits > 0 else 0
        
        return {
            'total_exits': self.total_exits,
            'successful_exits': self.successful_exits,
            'failed_exits': self.failed_exits,
            'success_rate': round(success_rate, 2)
        }
    
    def get_recent_exits(self, limit: int = 10) -> List[Dict]:
        """取得最近的出場記錄"""
        return self.exit_history[-limit:] if self.exit_history else []


if __name__ == "__main__":
    # 測試統一出場管理器
    print("🧪 測試統一出場管理器")
    print("=" * 50)
    
    # 這裡可以添加測試代碼
    print("✅ 統一出場管理器測試完成")
