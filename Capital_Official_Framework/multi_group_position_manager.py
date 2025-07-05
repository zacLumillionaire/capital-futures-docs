#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多組部位管理器
統一管理多個策略組的生命週期和風險控制
"""

import logging
import threading
import time
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

from multi_group_config import (
    MultiGroupStrategyConfig, StrategyGroupConfig, LotRule,
    GroupStatus, PositionStatus, StopLossType
)
from multi_group_database import MultiGroupDatabaseManager
from simplified_order_tracker import SimplifiedOrderTracker
from total_lot_manager import TotalLotManager

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiGroupPositionManager:
    """多組部位管理器 - 核心業務邏輯控制器"""
    
    def __init__(self, db_manager: MultiGroupDatabaseManager,
                 strategy_config: MultiGroupStrategyConfig,
                 order_manager=None, order_tracker=None, simplified_tracker=None,
                 total_lot_manager=None):
        self.db_manager = db_manager
        self.strategy_config = strategy_config
        self.active_groups = {}  # {group_id: GroupState}

        # 🔧 新增：下單組件整合
        self.order_manager = order_manager  # VirtualRealOrderManager
        self.order_tracker = order_tracker  # UnifiedOrderTracker (舊版，保留相容性)
        self.simplified_tracker = simplified_tracker or SimplifiedOrderTracker()  # 簡化追蹤器(舊版)
        self.total_lot_manager = total_lot_manager or TotalLotManager()  # 🔧 新版總量追蹤管理器
        self.position_order_mapping = {}    # {position_id: order_id}

        # 🔧 新增：追價機制相關屬性
        self.retry_lock = threading.Lock()  # 重試操作鎖
        self.max_retry_count = 5  # 最大重試次數
        self.max_slippage_points = 5  # 最大滑價點數
        self.retry_time_window = 30  # 重試時間窗口（秒）

        # 初始化日誌
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("多組部位管理器初始化完成")

        # 設置回調
        self._setup_total_lot_manager_callbacks()  # 🔧 新版總量追蹤回調
        self._setup_simplified_tracker_callbacks()  # 保留舊版相容性
        if self.order_tracker:
            self._setup_order_callbacks()
    
    def create_entry_signal(self, direction: str, signal_time: str,
                           range_high: float, range_low: float) -> List[int]:
        """創建進場信號，支援動態 group_id 分配"""
        try:
            created_groups = []
            current_date = date.today().isoformat()

            # 🆕 取得下一批可用的 group_id
            active_groups = self.strategy_config.get_active_groups()
            next_group_ids = self._get_next_available_group_ids(len(active_groups))

            self.logger.info(f"創建進場信號: {direction} @ {signal_time}, 區間: {range_low}-{range_high}")
            self.logger.info(f"使用動態組別ID: {next_group_ids}")

            for i, group_config in enumerate(active_groups):
                # 🆕 使用動態分配的 group_id
                dynamic_group_id = next_group_ids[i]

                group_db_id = self.db_manager.create_strategy_group(
                    date=current_date,
                    group_id=dynamic_group_id,  # 使用新的 group_id
                    direction=direction,
                    signal_time=signal_time,
                    range_high=range_high,
                    range_low=range_low,
                    total_lots=group_config.lots_per_group
                )

                created_groups.append(group_db_id)

                # 🆕 更新配置中的 group_id（用於日誌顯示）
                original_group_id = group_config.group_id
                group_config.group_id = dynamic_group_id
                group_config.status = GroupStatus.WAITING

                self.logger.info(f"創建策略組 {dynamic_group_id} (原:{original_group_id}): DB_ID={group_db_id}")

            return created_groups

        except Exception as e:
            self.logger.error(f"創建進場信號失敗: {e}")
            return []

    def _get_next_available_group_ids(self, num_groups: int) -> List[int]:
        """取得下一批可用的 group_id"""
        try:
            # 查詢今天已存在的 group_id
            today_groups = self.db_manager.get_today_strategy_groups()
            existing_group_ids = [group['group_id'] for group in today_groups]

            if not existing_group_ids:
                # 今天沒有組，從1開始
                result = list(range(1, num_groups + 1))
                self.logger.info(f"今日首次執行，分配組別ID: {result}")
                return result
            else:
                # 從最大ID+1開始分配
                max_id = max(existing_group_ids)
                result = list(range(max_id + 1, max_id + num_groups + 1))
                self.logger.info(f"今日已有組別 {existing_group_ids}，分配新組別ID: {result}")
                return result

        except Exception as e:
            self.logger.error(f"取得可用組ID失敗: {e}")
            # 降級處理：使用時間戳確保唯一性
            import time
            timestamp_suffix = int(time.time()) % 10000
            result = [timestamp_suffix + i for i in range(num_groups)]
            self.logger.warning(f"降級處理，使用時間戳組別ID: {result}")
            return result
    
    def execute_group_entry(self, group_db_id: int, actual_price: float,
                           actual_time: str) -> bool:
        """執行特定組的進場 - 修復版本：先下單再記錄"""
        try:
            # 獲取組資訊
            group_info = self.db_manager.get_strategy_group_info(group_db_id)
            if not group_info:
                self.logger.error(f"找不到組資訊: {group_db_id}")
                return False

            group_config = self.strategy_config.get_group_by_id(group_info['group_id'])
            if not group_config or group_config.status != GroupStatus.WAITING:
                self.logger.warning(f"組 {group_info['group_id']} 不在等待狀態")
                return False

            self.logger.info(f"🚀 執行組 {group_info['group_id']} 進場: {group_info['total_lots']}口 @ {actual_price}")

            # 🔧 新增：創建總量追蹤器
            strategy_id = f"strategy_{group_info['group_id']}_{int(time.time())}"
            if self.total_lot_manager:
                success = self.total_lot_manager.create_strategy_tracker(
                    strategy_id=strategy_id,
                    total_target_lots=group_info['total_lots'],
                    lots_per_group=self.strategy_config.lots_per_group,
                    direction=group_info['direction'],
                    product="TM0000"
                )
                if success:
                    self.logger.info(f"✅ 總量追蹤器創建成功: {strategy_id}")

            # 🔧 保留：註冊策略組到簡化追蹤器 (向後相容)
            if self.simplified_tracker:
                self.simplified_tracker.register_strategy_group(
                    group_id=group_info['group_id'],
                    total_lots=group_info['total_lots'],
                    direction=group_info['direction'],
                    target_price=actual_price,
                    product="TM0000"  # 預設商品
                )

            # 🔧 修復：先創建PENDING部位記錄，再執行下單
            position_ids = []
            order_mappings = {}  # {position_id: order_id}

            for lot_rule in group_config.lot_rules:
                # 1. 先創建部位記錄（狀態為PENDING）
                position_id = self.db_manager.create_position_record(
                    group_id=group_db_id,
                    lot_id=lot_rule.lot_id,
                    direction=group_info['direction'],
                    entry_time=actual_time,
                    rule_config=lot_rule.to_json(),
                    order_status='PENDING'  # 🔧 初始狀態為PENDING
                )

                # 2. 執行下單
                order_result = self._execute_single_lot_order(
                    lot_rule, group_info['direction'], actual_price
                )

                # 3. 更新部位記錄的訂單資訊
                if order_result and order_result.get('success', False):
                    order_id = order_result.get('order_id')
                    api_seq_no = order_result.get('api_result', '')

                    # 更新訂單資訊
                    self.db_manager.update_position_order_info(
                        position_id=position_id,
                        order_id=order_id,
                        api_seq_no=str(api_seq_no)
                    )

                    # 建立映射關係
                    order_mappings[position_id] = order_id
                    self.position_order_mapping[position_id] = order_id

                    self.logger.info(f"✅ 第{lot_rule.lot_id}口下單成功: ID={position_id}, 訂單={order_id}")
                else:
                    # 下單失敗，立即標記為失敗
                    self.db_manager.mark_position_failed(
                        position_id=position_id,
                        failure_reason='下單失敗',
                        order_status='REJECTED'
                    )
                    self.logger.error(f"❌ 第{lot_rule.lot_id}口下單失敗: ID={position_id}")

                position_ids.append(position_id)

            # 4. 設置成交確認回調（如果有成功的訂單）
            if order_mappings:
                self._setup_fill_callbacks_for_group(group_db_id, order_mappings)

            # 更新組狀態（只有在有成功訂單時才設為ACTIVE）
            if order_mappings:
                group_config.status = GroupStatus.ACTIVE
                group_config.entry_price = Decimal(str(actual_price))
                group_config.entry_time = actual_time

                # 更新資料庫中的組狀態
                self.db_manager.update_group_status(group_db_id, GroupStatus.ACTIVE.value)

                # 記錄到活躍組管理
                self.active_groups[group_db_id] = {
                    'config': group_config,
                    'position_ids': position_ids,
                    'entry_price': actual_price,
                    'entry_time': actual_time,
                    'direction': group_info['direction']
                }

                self.logger.info(f"✅ 組 {group_info['group_id']} 進場完成: {len(order_mappings)}/{len(position_ids)}口成功")

                # 🔧 新增：更新總量追蹤器的已送出口數
                if self.total_lot_manager and 'strategy_id' in locals():
                    try:
                        self.total_lot_manager.update_strategy_submitted_lots(
                            strategy_id=strategy_id,
                            lots=len(order_mappings)
                        )
                    except Exception as e:
                        self.logger.error(f"更新總量追蹤器已送出口數失敗: {e}")

                # 🔧 保留：更新簡化追蹤器的已送出口數 (向後相容)
                if self.simplified_tracker:
                    try:
                        self.simplified_tracker.update_submitted_lots(
                            group_id=group_info['group_id'],
                            lots=len(order_mappings)
                        )
                    except Exception as e:
                        self.logger.error(f"更新簡化追蹤器已送出口數失敗: {e}")
            else:
                self.logger.error(f"❌ 組 {group_info['group_id']} 進場失敗: 所有訂單都失敗")
                return False

            return True

        except Exception as e:
            self.logger.error(f"組進場失敗: {e}")
            return False
    
    def get_next_available_group(self) -> Optional[int]:
        """取得下一個可用的等待進場組"""
        try:
            waiting_groups = self.db_manager.get_today_waiting_groups()
            if waiting_groups:
                return waiting_groups[0]['id']  # 返回第一個等待的組
            return None
        except Exception as e:
            self.logger.error(f"查詢可用組失敗: {e}")
            return None
    
    def get_all_active_positions(self) -> List[Dict]:
        """取得所有活躍部位"""
        try:
            return self.db_manager.get_all_active_positions()
        except Exception as e:
            self.logger.error(f"查詢活躍部位失敗: {e}")
            return []
    
    def get_group_active_positions(self, group_db_id: int) -> List[Dict]:
        """取得指定組的活躍部位"""
        try:
            return self.db_manager.get_active_positions_by_group(group_db_id)
        except Exception as e:
            self.logger.error(f"查詢組活躍部位失敗: {e}")
            return []
    
    def update_position_exit(self, position_id: int, exit_price: float, 
                           exit_time: str, exit_reason: str, pnl: float) -> bool:
        """更新部位出場"""
        try:
            self.db_manager.update_position_exit(
                position_id=position_id,
                exit_price=exit_price,
                exit_time=exit_time,
                exit_reason=exit_reason,
                pnl=pnl
            )
            
            self.logger.info(f"部位 {position_id} 出場: {exit_reason}, 損益={pnl:.1f}點")
            
            # 檢查組是否全部出場
            self._check_group_completion(position_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新部位出場失敗: {e}")
            return False
    
    def _check_group_completion(self, position_id: int):
        """檢查組是否全部出場完成"""
        try:
            # 通過部位ID找到組ID
            all_positions = self.get_all_active_positions()
            group_db_id = None
            
            for pos in all_positions:
                if pos['id'] == position_id:
                    group_db_id = pos['group_id']
                    break
            
            if group_db_id:
                # 檢查該組是否還有活躍部位
                group_positions = self.get_group_active_positions(group_db_id)
                
                if not group_positions:  # 沒有活躍部位了
                    self.db_manager.update_group_status(group_db_id, GroupStatus.COMPLETED.value)
                    
                    # 從活躍組管理中移除
                    if group_db_id in self.active_groups:
                        group_info = self.active_groups[group_db_id]
                        group_config = group_info['config']
                        group_config.status = GroupStatus.COMPLETED
                        del self.active_groups[group_db_id]
                        
                        self.logger.info(f"組 {group_config.group_id} 全部出場完成")
                        
        except Exception as e:
            self.logger.error(f"檢查組完成狀態失敗: {e}")
    
    def get_daily_summary(self, date_str: Optional[str] = None) -> Dict:
        """取得每日摘要"""
        try:
            return self.db_manager.get_daily_strategy_summary(date_str)
        except Exception as e:
            self.logger.error(f"取得每日摘要失敗: {e}")
            return {}
    
    def get_active_groups_count(self) -> int:
        """取得活躍組數量"""
        return len(self.active_groups)
    
    def get_total_active_positions_count(self) -> int:
        """取得總活躍部位數"""
        return len(self.get_all_active_positions())
    
    def get_strategy_status_summary(self) -> str:
        """取得策略狀態摘要"""
        try:
            active_groups = self.get_active_groups_count()
            active_positions = self.get_total_active_positions_count()
            daily_stats = self.get_daily_summary()
            
            return f"""策略狀態摘要:
🎯 配置: {self.strategy_config.total_groups}組×{self.strategy_config.lots_per_group}口
📊 活躍組數: {active_groups}
📊 活躍部位: {active_positions}
📊 今日總組數: {daily_stats.get('total_groups', 0)}
📊 完成組數: {daily_stats.get('completed_groups', 0)}
📊 今日損益: {daily_stats.get('total_pnl', 0):.1f}點
📊 勝率: {daily_stats.get('win_rate', 0):.1f}%"""
            
        except Exception as e:
            self.logger.error(f"取得狀態摘要失敗: {e}")
            return "狀態摘要取得失敗"
    
    def reset_daily_state(self):
        """重置每日狀態"""
        try:
            self.active_groups.clear()
            
            # 重置組配置狀態
            for group in self.strategy_config.groups:
                group.status = GroupStatus.WAITING
                group.entry_price = None
                group.entry_time = None
            
            self.logger.info("每日狀態已重置")

        except Exception as e:
            self.logger.error(f"重置每日狀態失敗: {e}")

    # 🔧 新增：下單相關方法

    def _execute_single_lot_order(self, lot_rule, direction: str, price: float) -> Optional[Dict]:
        """執行單口下單"""
        try:
            if not self.order_manager:
                self.logger.warning("下單管理器未設置，跳過實際下單")
                return None

            # 使用下單管理器執行下單
            result = self.order_manager.execute_strategy_order(
                direction=direction,
                quantity=1,  # 每口都是1口
                price=price,  # 🔧 明確傳入價格，避免依賴報價管理器
                signal_source=f"多組策略-第{lot_rule.lot_id}口"
            )

            if result and result.success:
                # 🔧 保留：註冊訂單到統一追蹤器（向後相容）
                if self.order_tracker and result.order_id:
                    try:
                        # 取得API序號（如果是實單）
                        api_seq_no = None
                        if result.api_result and isinstance(result.api_result, tuple) and len(result.api_result) >= 1:
                            api_seq_no = str(result.api_result[0])  # 只取第一個元素並轉換為字串
                            self.logger.info(f"🔍 API序號提取: {result.api_result} -> {api_seq_no}")

                        # 註冊到統一追蹤器
                        self.order_tracker.register_order(
                            order_id=result.order_id,
                            product="TM0000",  # 預設商品
                            direction=direction,
                            quantity=1,
                            price=price,
                            api_seq_no=api_seq_no,
                            signal_source=f"多組策略-第{lot_rule.lot_id}口",
                            is_virtual=(result.mode == "virtual")
                        )

                        self.logger.info(f"📝 已註冊訂單到追蹤器: {result.order_id} (API序號: {api_seq_no})")

                    except Exception as e:
                        self.logger.error(f"註冊訂單到追蹤器失敗: {e}")

                # 🔧 新增：更新簡化追蹤器的已送出口數
                if self.simplified_tracker:
                    try:
                        # 從lot_rule中獲取group_id（需要從上下文推斷）
                        # 這裡需要傳入group_id，暫時使用日誌記錄
                        self.logger.info(f"📤 [簡化追蹤] 下單成功，需要更新已送出口數")
                    except Exception as e:
                        self.logger.error(f"更新簡化追蹤器失敗: {e}")

                return {
                    'success': True,
                    'order_id': result.order_id,
                    'api_result': result.api_result or '',
                    'mode': result.mode  # 添加模式資訊
                }
            else:
                return {
                    'success': False,
                    'error': result.error if result else '下單失敗'
                }

        except Exception as e:
            self.logger.error(f"執行單口下單失敗: {e}")
            return {'success': False, 'error': str(e)}

    def _setup_order_callbacks(self):
        """設置訂單回調機制"""
        try:
            if not self.order_tracker:
                return

            # 添加成交回調
            self.order_tracker.add_fill_callback(self._on_order_filled)

            # 添加取消回調（如果支援）
            if hasattr(self.order_tracker, 'add_cancel_callback'):
                self.order_tracker.add_cancel_callback(self._on_order_cancelled)

            self.logger.info("✅ 訂單回調機制設置完成")

        except Exception as e:
            self.logger.error(f"設置訂單回調失敗: {e}")

    def _setup_simplified_tracker_callbacks(self):
        """設置簡化追蹤器回調機制"""
        try:
            if not self.simplified_tracker:
                return

            # 添加成交回調
            self.simplified_tracker.add_fill_callback(self._on_simplified_fill)

            # 添加追價回調
            self.simplified_tracker.add_retry_callback(self._on_simplified_retry)

            self.logger.info("✅ 簡化追蹤器回調機制設置完成")

        except Exception as e:
            self.logger.error(f"設置簡化追蹤器回調失敗: {e}")

    def _setup_total_lot_manager_callbacks(self):
        """設置總量追蹤管理器回調機制"""
        try:
            if not self.total_lot_manager:
                return

            # 添加全局回調
            self.total_lot_manager.add_global_fill_callback(self._on_total_lot_fill)
            self.total_lot_manager.add_global_retry_callback(self._on_total_lot_retry)
            self.total_lot_manager.add_global_complete_callback(self._on_total_lot_complete)

            self.logger.info("✅ 總量追蹤管理器回調機制設置完成")

        except Exception as e:
            self.logger.error(f"設置總量追蹤管理器回調失敗: {e}")

    def _setup_fill_callbacks_for_group(self, group_db_id: int, order_mappings: Dict[int, str]):
        """為特定組設置成交確認回調"""
        # 這個方法暫時不需要特殊處理，因為回調是全局的
        # 實際的回調處理在 _on_order_filled 中
        pass

    def _on_order_filled(self, order_info):
        """訂單成交回調"""
        try:
            # 根據訂單ID找到對應的部位ID
            position_id = self._get_position_id_by_order_id(order_info.order_id)
            if position_id:
                # 確認部位成交
                success = self.db_manager.confirm_position_filled(
                    position_id=position_id,
                    actual_fill_price=order_info.fill_price,
                    fill_time=order_info.fill_time.strftime('%H:%M:%S') if order_info.fill_time else '',
                    order_status='FILLED'
                )

                if success:
                    # 初始化風險管理狀態（成交後才初始化）
                    self.db_manager.create_risk_management_state(
                        position_id=position_id,
                        peak_price=order_info.fill_price,
                        current_time=order_info.fill_time.strftime('%H:%M:%S') if order_info.fill_time else '',
                        update_reason="成交初始化"
                    )

                    self.logger.info(f"✅ 部位{position_id}成交確認: @{order_info.fill_price}")

        except Exception as e:
            self.logger.error(f"處理成交回調失敗: {e}")

    def _on_simplified_fill(self, group_id: int, price: float, qty: int,
                          filled_lots: int, total_lots: int):
        """簡化追蹤器成交回調"""
        try:
            # 更新資料庫中該組的部位狀態
            self._update_group_positions_on_fill(group_id, price, qty, filled_lots, total_lots)

            self.logger.info(f"✅ [簡化追蹤] 組{group_id}成交: {qty}口 @{price}, "
                           f"進度: {filled_lots}/{total_lots}")

            # 如果組完全成交，觸發完成處理
            if filled_lots >= total_lots:
                self._on_group_complete(group_id)

        except Exception as e:
            self.logger.error(f"處理簡化成交回調失敗: {e}")

    def _on_simplified_retry(self, group_id: int, qty: int, price: float, retry_count: int):
        """簡化追蹤器追價回調"""
        try:
            self.logger.info(f"🔄 [簡化追蹤] 組{group_id}觸發追價: {qty}口 @{price}, "
                           f"第{retry_count}次重試")

            # 觸發追價邏輯
            self._execute_group_retry(group_id, qty, price, retry_count)

        except Exception as e:
            self.logger.error(f"處理簡化追價回調失敗: {e}")

    def _update_group_positions_on_fill(self, group_id: int, price: float, qty: int,
                                      filled_lots: int, total_lots: int):
        """更新組內部位的成交狀態"""
        try:
            self.logger.info(f"📊 [簡化追蹤] 組{group_id}成交統計更新: "
                           f"{qty}口 @{price}, 總進度: {filled_lots}/{total_lots}")

            # 🔧 新增：實際更新資料庫部位狀態
            # 查找該組的PENDING部位並按FIFO順序確認成交
            try:
                # 獲取今日等待組，找到對應的資料庫組ID
                waiting_groups = self.db_manager.get_today_waiting_groups()
                group_db_id = None

                for group in waiting_groups:
                    if group['group_id'] == group_id:
                        group_db_id = group['id']
                        break

                if group_db_id:
                    # 獲取該組的所有部位（包括PENDING狀態）
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            SELECT id, lot_id, status, order_status
                            FROM position_records
                            WHERE group_id = ? AND status = 'PENDING'
                            ORDER BY lot_id
                            LIMIT ?
                        ''', (group_db_id, qty))

                        pending_positions = cursor.fetchall()

                        # 確認成交
                        for position in pending_positions:
                            success = self.db_manager.confirm_position_filled(
                                position_id=position[0],  # id
                                actual_fill_price=price,
                                fill_time=datetime.now().strftime('%H:%M:%S'),
                                order_status='FILLED'
                            )

                            if success:
                                # 初始化風險管理狀態
                                self.db_manager.create_risk_management_state(
                                    position_id=position[0],
                                    peak_price=price,
                                    current_time=datetime.now().strftime('%H:%M:%S'),
                                    update_reason="簡化追蹤成交確認"
                                )

                                self.logger.info(f"✅ [簡化追蹤] 部位{position[0]}成交確認: @{price}")

            except Exception as db_error:
                self.logger.error(f"資料庫部位更新失敗: {db_error}")

        except Exception as e:
            self.logger.error(f"更新組部位成交狀態失敗: {e}")

    def _on_group_complete(self, group_id: int):
        """組完成處理"""
        try:
            self.logger.info(f"🎉 [簡化追蹤] 組{group_id}建倉完成!")

            # 可以在這裡添加組完成後的處理邏輯
            # 例如：啟動風險管理、發送通知等

        except Exception as e:
            self.logger.error(f"處理組完成失敗: {e}")

    def _execute_group_retry(self, group_id: int, qty: int, price: float, retry_count: int):
        """執行組追價重試"""
        try:
            self.logger.info(f"🔄 [簡化追蹤] 組{group_id}觸發追價重試: "
                           f"{qty}口 @{price}, 第{retry_count}次")

            # 簡化實現：記錄追價事件
            # 實際的追價下單邏輯可以在後續階段實現
            # 這裡主要確保追價事件能被正確識別和記錄

        except Exception as e:
            self.logger.error(f"執行組追價重試失敗: {e}")

    def _on_total_lot_fill(self, strategy_id: str, price: float, qty: int,
                         filled_lots: int, total_lots: int):
        """總量追蹤成交回調"""
        try:
            self.logger.info(f"✅ [總量追蹤] 策略{strategy_id}成交: {qty}口 @{price}, "
                           f"進度: {filled_lots}/{total_lots}")

            # 更新資料庫部位狀態
            self._update_database_from_total_tracker(strategy_id)

        except Exception as e:
            self.logger.error(f"處理總量追蹤成交回調失敗: {e}")

    def _on_total_lot_retry(self, strategy_id: str, qty: int, price: float, retry_count: int):
        """總量追蹤追價回調"""
        try:
            self.logger.info(f"🔄 [總量追蹤] 策略{strategy_id}觸發追價: {qty}口 @{price}, "
                           f"第{retry_count}次重試")

            # 觸發追價邏輯
            self._execute_total_lot_retry(strategy_id, qty, price, retry_count)

        except Exception as e:
            self.logger.error(f"處理總量追蹤追價回調失敗: {e}")

    def _on_total_lot_complete(self, strategy_id: str, fill_records: List):
        """總量追蹤完成回調"""
        try:
            self.logger.info(f"🎉 [總量追蹤] 策略{strategy_id}建倉完成! 共{len(fill_records)}口")

            # 完成後處理：記錄到資料庫、初始化風險管理等
            self._finalize_strategy_positions(strategy_id, fill_records)

        except Exception as e:
            self.logger.error(f"處理總量追蹤完成回調失敗: {e}")

    def _update_database_from_total_tracker(self, strategy_id: str):
        """從總量追蹤器更新資料庫"""
        try:
            tracker = self.total_lot_manager.get_tracker(strategy_id)
            if not tracker:
                return

            # 獲取成交記錄
            fill_records = tracker.get_fill_records_for_database()

            # 這裡可以添加資料庫更新邏輯
            # 暫時只記錄日誌
            self.logger.info(f"📊 [總量追蹤] 策略{strategy_id}資料庫更新: {len(fill_records)}筆記錄")

        except Exception as e:
            self.logger.error(f"從總量追蹤器更新資料庫失敗: {e}")

    def _execute_total_lot_retry(self, strategy_id: str, qty: int, price: float, retry_count: int):
        """執行總量追蹤追價重試"""
        try:
            self.logger.info(f"🔄 [總量追蹤] 策略{strategy_id}執行追價: "
                           f"{qty}口 @{price}, 第{retry_count}次")

            # 這裡可以添加實際的追價下單邏輯
            # 暫時只記錄日誌

        except Exception as e:
            self.logger.error(f"執行總量追蹤追價重試失敗: {e}")

    def _finalize_strategy_positions(self, strategy_id: str, fill_records: List):
        """完成策略部位處理"""
        try:
            self.logger.info(f"🎯 [總量追蹤] 策略{strategy_id}完成處理: {len(fill_records)}口")

            # 獲取追蹤器
            tracker = self.total_lot_manager.get_tracker(strategy_id)
            if not tracker:
                return

            # 獲取資料庫記錄格式的數據
            db_records = tracker.get_fill_records_for_database()

            # 這裡可以添加：
            # 1. 記錄到資料庫
            # 2. 初始化風險管理狀態
            # 3. 觸發後續處理

            self.logger.info(f"✅ [總量追蹤] 策略{strategy_id}完成處理完畢")

        except Exception as e:
            self.logger.error(f"完成策略部位處理失敗: {e}")

    def _on_order_cancelled(self, order_info):
        """訂單取消回調 - 增加事件驅動追價觸發"""
        try:
            # 根據訂單ID找到對應的部位ID
            position_id = self._get_position_id_by_order_id(order_info.order_id)
            if position_id:
                # 設定原始價格（如果還沒設定）
                position_info = self.db_manager.get_position_by_id(position_id)
                if position_info and not position_info.get('original_price'):
                    original_price = order_info.price if hasattr(order_info, 'price') else position_info.get('entry_price')
                    if original_price:
                        self.db_manager.set_original_price(position_id, original_price)

                # 標記部位失敗
                success = self.db_manager.mark_position_failed(
                    position_id=position_id,
                    failure_reason='FOK失敗',
                    order_status='CANCELLED'
                )

                if success:
                    self.logger.info(f"❌ 部位{position_id}下單失敗: FOK取消")

                    # 🔧 新增: 事件驅動追價觸發（避免GIL風險）
                    self._trigger_retry_if_allowed(position_id)

        except Exception as e:
            self.logger.error(f"處理取消回調失敗: {e}")

    def _trigger_retry_if_allowed(self, position_id: int):
        """觸發追價重試（如果允許）- 事件驅動，避免GIL風險"""
        try:
            # 使用Timer延遲執行，避免立即重試
            # 這樣可以讓市場價格有時間更新
            retry_timer = threading.Timer(2.0, self._execute_delayed_retry, args=[position_id])
            retry_timer.daemon = True  # 設為守護線程
            retry_timer.start()

            self.logger.info(f"⏰ 已排程部位{position_id}的延遲追價（2秒後執行）")

        except Exception as e:
            self.logger.error(f"觸發追價重試失敗: {e}")

    def _execute_delayed_retry(self, position_id: int):
        """延遲執行追價重試 - 在獨立線程中安全執行"""
        try:
            self.logger.info(f"🔄 開始執行部位{position_id}的延遲追價")

            # 檢查部位是否仍然需要重試
            position_info = self.db_manager.get_position_by_id(position_id)
            if not position_info:
                self.logger.warning(f"部位{position_id}不存在，取消追價")
                return

            if position_info.get('status') != 'FAILED':
                self.logger.info(f"部位{position_id}狀態已變更({position_info.get('status')})，取消追價")
                return

            # 執行追價重試
            if self.is_retry_allowed(position_info):
                success = self.retry_failed_position(position_id)
                if success:
                    self.logger.info(f"✅ 部位{position_id}延遲追價執行成功")
                else:
                    self.logger.warning(f"⚠️ 部位{position_id}延遲追價執行失敗")
            else:
                self.logger.info(f"📋 部位{position_id}不符合追價條件，跳過")

        except Exception as e:
            self.logger.error(f"延遲追價執行失敗: {e}")

    def _get_position_id_by_order_id(self, order_id: str) -> Optional[int]:
        """根據訂單ID查詢部位ID"""
        try:
            # 從映射中查找
            for position_id, mapped_order_id in self.position_order_mapping.items():
                if mapped_order_id == order_id:
                    return position_id

            # 從資料庫查找
            position = self.db_manager.get_position_by_order_id(order_id)
            if position:
                return position['id']

            return None

        except Exception as e:
            self.logger.error(f"根據訂單ID查詢部位ID失敗: {e}")
            return None

    # 🔧 新增：追價機制核心方法
    def monitor_failed_positions(self):
        """監控失敗部位並觸發追價（事件驅動，無定時線程）"""
        try:
            failed_positions = self.db_manager.get_failed_positions_for_retry(
                max_retry_count=self.max_retry_count,
                time_window_seconds=self.retry_time_window
            )

            for position in failed_positions:
                if self.is_retry_allowed(position):
                    self.logger.info(f"🔄 觸發部位{position['id']}追價重試")
                    self.retry_failed_position(position['id'])

        except Exception as e:
            self.logger.error(f"監控失敗部位錯誤: {e}")

    def retry_failed_position(self, position_id: int) -> bool:
        """執行單一部位的追價補單"""
        try:
            with self.retry_lock:
                # 1. 取得部位資訊
                position_info = self.db_manager.get_position_by_id(position_id)
                if not position_info:
                    self.logger.error(f"找不到部位{position_id}")
                    return False

                # 2. 檢查重試條件
                if not self.is_retry_allowed(position_info):
                    self.logger.warning(f"部位{position_id}不符合重試條件")
                    return False

                # 3. 計算新價格
                retry_count = position_info.get('retry_count', 0) + 1
                new_price = self.calculate_retry_price(position_info, retry_count)

                if new_price is None:
                    self.logger.error(f"無法計算部位{position_id}的重試價格")
                    return False

                # 4. 檢查滑價限制
                original_price = position_info.get('original_price') or position_info.get('entry_price')
                if original_price and not self.validate_slippage(original_price, new_price, self.max_slippage_points):
                    self.logger.warning(f"部位{position_id}滑價超出限制: {abs(new_price - original_price)}點")
                    return False

                # 5. 執行重試下單
                success = self._execute_retry_order(position_info, new_price, retry_count)

                if success:
                    # 6. 更新重試記錄
                    position_direction = position_info.get('direction', 'UNKNOWN')
                    if position_direction.upper() == "LONG":
                        retry_reason = f"多單進場ASK1+{retry_count}點追價"
                    elif position_direction.upper() == "SHORT":
                        retry_reason = f"空單進場BID1-{retry_count}點追價"
                    else:
                        retry_reason = f"進場追價第{retry_count}次"

                    self.db_manager.update_retry_info(
                        position_id=position_id,
                        retry_count=retry_count,
                        retry_price=new_price,
                        retry_reason=retry_reason
                    )
                    self.logger.info(f"✅ 部位{position_id}第{retry_count}次追價成功: @{new_price}")
                else:
                    self.logger.error(f"❌ 部位{position_id}第{retry_count}次追價失敗")

                return success

        except Exception as e:
            self.logger.error(f"執行追價重試失敗: {e}")
            return False

    def calculate_retry_price(self, position_info: Dict, retry_count: int) -> Optional[float]:
        """計算進場追價價格 - 根據方向選擇正確價格"""
        try:
            # 取得當前商品（從策略配置或預設）
            product = "TM0000"  # 預設使用微型台指
            position_direction = position_info.get('direction')

            if not position_direction:
                self.logger.error("無法取得部位方向")
                return None

            current_price = None
            price_type = ""

            if position_direction.upper() == "LONG":
                # 多單進場：使用ASK1 + retry_count點 (向上追價)
                if self.order_manager and hasattr(self.order_manager, 'get_ask1_price'):
                    try:
                        current_ask1 = self.order_manager.get_ask1_price(product)
                        if current_ask1:
                            current_price = current_ask1 + retry_count
                            price_type = "ASK1"
                            self.logger.info(f"多單進場追價: ASK1({current_ask1}) + {retry_count}點 = {current_price}")
                    except:
                        pass

            elif position_direction.upper() == "SHORT":
                # 空單進場：使用BID1 - retry_count點 (向下追價)
                if self.order_manager and hasattr(self.order_manager, 'get_bid1_price'):
                    try:
                        current_bid1 = self.order_manager.get_bid1_price(product)
                        if current_bid1:
                            current_price = current_bid1 - retry_count
                            price_type = "BID1"
                            self.logger.info(f"空單進場追價: BID1({current_bid1}) - {retry_count}點 = {current_price}")
                    except:
                        pass

            # 備用方案：使用原始價格估算
            if current_price is None:
                original_price = position_info.get('original_price') or position_info.get('entry_price')
                if original_price:
                    if position_direction.upper() == "LONG":
                        current_price = original_price + 1 + retry_count
                        price_type = "估算ASK1"
                    else:
                        current_price = original_price - 1 - retry_count
                        price_type = "估算BID1"
                    self.logger.warning(f"⚠️ 無法取得即時{price_type}，使用估算價格: {current_price}")
                else:
                    self.logger.error("無法取得進場價格且無原始價格參考")
                    return None

            return current_price

        except Exception as e:
            self.logger.error(f"計算進場追價失敗: {e}")
            return None

    def calculate_exit_retry_price(self, position_info: Dict, retry_count: int) -> Optional[float]:
        """
        計算出場追價價格

        Args:
            position_info: 部位資訊
            retry_count: 重試次數

        Returns:
            float: 追價價格 或 None
        """
        try:
            product = "TM0000"  # 預設使用微型台指
            position_direction = position_info.get('direction')

            if not position_direction:
                self.logger.error("無法取得部位方向")
                return None

            current_price = None

            if position_direction.upper() == "LONG":
                # 多單出場：使用BID1 - retry_count點 (更積極賣出)
                if self.order_manager and hasattr(self.order_manager, 'get_bid1_price'):
                    try:
                        current_bid1 = self.order_manager.get_bid1_price(product)
                        if current_bid1:
                            current_price = current_bid1 - retry_count
                            self.logger.info(f"多單出場追價: BID1({current_bid1}) - {retry_count}點 = {current_price}")
                    except:
                        pass

            elif position_direction.upper() == "SHORT":
                # 空單出場：使用ASK1 + retry_count點 (更積極買回)
                if self.order_manager and hasattr(self.order_manager, 'get_ask1_price'):
                    try:
                        current_ask1 = self.order_manager.get_ask1_price(product)
                        if current_ask1:
                            current_price = current_ask1 + retry_count
                            self.logger.info(f"空單出場追價: ASK1({current_ask1}) + {retry_count}點 = {current_price}")
                    except:
                        pass

            # 備用方案：使用原始價格估算
            if current_price is None:
                original_price = position_info.get('entry_price')
                if original_price:
                    if position_direction.upper() == "LONG":
                        current_price = original_price - 1 - retry_count
                    else:
                        current_price = original_price + 1 + retry_count
                    self.logger.warning(f"⚠️ 使用估算出場價格: {current_price}")
                else:
                    self.logger.error("無法取得出場價格且無原始價格參考")
                    return None

            return current_price

        except Exception as e:
            self.logger.error(f"計算出場追價失敗: {e}")
            return None

    def is_retry_allowed(self, position_info: Dict) -> bool:
        """檢查是否允許重試"""
        try:
            # 檢查重試次數
            retry_count = position_info.get('retry_count', 0)
            if retry_count >= self.max_retry_count:
                self.logger.info(f"部位{position_info['id']}已達最大重試次數({self.max_retry_count})")
                return False

            # 檢查狀態
            if position_info.get('status') != 'FAILED':
                self.logger.info(f"部位{position_info['id']}狀態不是FAILED")
                return False

            if position_info.get('order_status') != 'CANCELLED':
                self.logger.info(f"部位{position_info['id']}訂單狀態不是CANCELLED")
                return False

            # 檢查時間窗口（在資料庫查詢中已處理）

            # 檢查下單管理器可用性
            if not self.order_manager:
                self.logger.error("下單管理器未設置")
                return False

            return True

        except Exception as e:
            self.logger.error(f"檢查重試條件失敗: {e}")
            return False

    def validate_slippage(self, original_price: float, new_price: float, max_slippage: int) -> bool:
        """驗證滑價是否在容忍範圍內"""
        try:
            slippage = abs(new_price - original_price)
            is_valid = slippage <= max_slippage

            if not is_valid:
                self.logger.warning(f"滑價檢查失敗: {slippage}點 > {max_slippage}點")

            return is_valid

        except Exception as e:
            self.logger.error(f"滑價驗證失敗: {e}")
            return False

    def _execute_retry_order(self, position_info: Dict, retry_price: float, retry_count: int) -> bool:
        """執行重試下單"""
        try:
            if not self.order_manager:
                self.logger.error("下單管理器未設置")
                return False

            # 準備下單參數
            direction = position_info['direction']
            product = "TM0000"  # 預設使用微型台指
            quantity = 1  # 每次都是1口

            # 執行下單
            order_result = self.order_manager.execute_strategy_order(
                direction=direction,
                signal_source=f"retry_{retry_count}_{position_info['id']}",
                product=product,
                price=retry_price,
                quantity=quantity
            )

            if order_result.success:
                # 註冊訂單追蹤
                if self.order_tracker and order_result.order_id:
                    try:
                        # 取得API序號（如果是實單）
                        api_seq_no = None
                        if order_result.api_result and isinstance(order_result.api_result, tuple) and len(order_result.api_result) >= 1:
                            api_seq_no = str(order_result.api_result[0])  # 只取第一個元素並轉換為字串
                            self.logger.info(f"🔍 重試API序號提取: {order_result.api_result} -> {api_seq_no}")

                        self.order_tracker.register_order(
                            order_id=order_result.order_id,
                            product=product,
                            direction=direction,
                            quantity=quantity,
                            price=retry_price,
                            api_seq_no=api_seq_no,
                            signal_source=f"retry_{retry_count}_{position_info['id']}",
                            is_virtual=(order_result.mode == "virtual")
                        )

                        # 更新部位訂單映射
                        self.position_order_mapping[position_info['id']] = order_result.order_id

                        self.logger.info(f"📝 重試訂單已註冊到追蹤器: {order_result.order_id} (API序號: {api_seq_no})")

                    except Exception as e:
                        self.logger.error(f"註冊重試訂單到追蹤器失敗: {e}")

                self.logger.info(f"🚀 重試下單成功: {direction} {product} 1口 @{retry_price}")
                return True
            else:
                self.logger.error(f"❌ 重試下單失敗: {order_result.error}")
                return False

        except Exception as e:
            self.logger.error(f"執行重試下單失敗: {e}")
            return False

    def execute_exit_retry(self, position_id: int) -> bool:
        """
        執行出場追價

        Args:
            position_id: 部位ID

        Returns:
            bool: 是否成功
        """
        try:
            # 1. 取得部位資訊
            position_info = self.db_manager.get_position_by_id(position_id)
            if not position_info:
                self.logger.error(f"找不到部位 {position_id}")
                return False

            # 2. 檢查重試條件
            retry_count = position_info.get('retry_count', 0) + 1
            if retry_count > self.max_retry_count:
                self.logger.warning(f"部位{position_id}出場重試次數已達上限")
                return False

            # 3. 計算追價價格
            new_price = self.calculate_exit_retry_price(position_info, retry_count)
            if not new_price:
                self.logger.error(f"無法計算部位{position_id}的出場追價")
                return False

            # 4. 檢查滑價限制
            original_price = position_info.get('entry_price')
            if original_price:
                max_slippage = 5  # 最大滑價5點
                actual_slippage = abs(new_price - original_price)
                if actual_slippage > max_slippage:
                    self.logger.warning(f"部位{position_id}出場滑價超出限制: {actual_slippage}點")
                    return False

            # 5. 執行出場重試下單
            success = self._execute_exit_retry_order(position_info, new_price, retry_count)

            if success:
                # 6. 更新重試記錄
                self.db_manager.update_retry_info(
                    position_id=position_id,
                    retry_count=retry_count,
                    retry_price=new_price,
                    retry_reason=f"出場追價第{retry_count}次"
                )
                self.logger.info(f"✅ 部位{position_id}出場第{retry_count}次追價成功: @{new_price}")
            else:
                self.logger.error(f"❌ 部位{position_id}出場第{retry_count}次追價失敗")

            return success

        except Exception as e:
            self.logger.error(f"執行出場追價失敗: {e}")
            return False

    def _execute_exit_retry_order(self, position_info: Dict, price: float, retry_count: int) -> bool:
        """
        執行出場重試下單 - 復用進場機制的 execute_strategy_order

        Args:
            position_info: 部位資訊
            price: 追價價格
            retry_count: 重試次數

        Returns:
            bool: 是否成功
        """
        try:
            if not self.order_manager:
                self.logger.error("下單管理器未設置")
                return False

            # 🔧 關鍵修正：確定出場方向
            original_direction = position_info['direction']
            if original_direction.upper() == "LONG":
                exit_direction = "SELL"  # 多單出場 → 賣出
            elif original_direction.upper() == "SHORT":
                exit_direction = "BUY"   # 空單出場 → 買回
            else:
                self.logger.error(f"無效的原始方向: {original_direction}")
                return False

            # 🔧 關鍵修正：使用與進場相同的下單方法
            order_result = self.order_manager.execute_strategy_order(
                direction=exit_direction,
                signal_source=f"exit_retry_{retry_count}_{position_info['id']}",
                product="TM0000",
                price=price,
                quantity=1
            )

            if order_result.success:
                self.logger.info(f"出場重試下單成功: {order_result.order_id}")

                # 註冊到訂單追蹤器 (與進場邏輯一致)
                if hasattr(self, 'order_tracker') and self.order_tracker:
                    try:
                        # 取得API序號（如果是實單）
                        api_seq_no = None
                        if order_result.api_result and isinstance(order_result.api_result, tuple) and len(order_result.api_result) >= 1:
                            api_seq_no = str(order_result.api_result[0])
                            self.logger.info(f"🔍 出場重試API序號提取: {order_result.api_result} -> {api_seq_no}")

                        self.order_tracker.register_order(
                            order_id=order_result.order_id,
                            direction=exit_direction,  # 使用轉換後的方向
                            product="TM0000",
                            quantity=1,
                            price=price,
                            api_seq_no=api_seq_no,
                            signal_source=f"exit_retry_{retry_count}_{position_info['id']}",
                            is_virtual=(order_result.mode == "virtual")
                        )

                        # 更新部位訂單映射
                        self.position_order_mapping[position_info['id']] = order_result.order_id

                        self.logger.info(f"📝 出場重試訂單已註冊到追蹤器: {order_result.order_id} (API序號: {api_seq_no})")

                    except Exception as e:
                        self.logger.error(f"註冊出場重試訂單到追蹤器失敗: {e}")

                return True
            else:
                self.logger.error(f"出場重試下單失敗: {order_result.error}")
                return False

        except Exception as e:
            self.logger.error(f"執行出場重試下單失敗: {e}")
            return False

if __name__ == "__main__":
    # 測試多組部位管理器
    print("🧪 測試多組部位管理器")
    print("=" * 50)
    
    from multi_group_config import create_preset_configs
    
    # 使用測試資料庫
    db_manager = MultiGroupDatabaseManager("test_position_manager.db")
    
    # 使用平衡配置 (2口×2組)
    presets = create_preset_configs()
    config = presets["平衡配置 (2口×2組)"]
    
    # 創建管理器
    manager = MultiGroupPositionManager(db_manager, config)
    
    print("✅ 管理器創建成功")
    print(manager.get_strategy_status_summary())
    
    # 測試創建進場信號
    group_ids = manager.create_entry_signal(
        direction="LONG",
        signal_time="08:48:15",
        range_high=22530.0,
        range_low=22480.0
    )
    
    print(f"\n✅ 創建進場信號: {len(group_ids)} 組")
    
    # 測試執行進場
    if group_ids:
        success = manager.execute_group_entry(
            group_db_id=group_ids[0],
            actual_price=22535.0,
            actual_time="08:48:20"
        )
        print(f"✅ 執行進場: {'成功' if success else '失敗'}")
    
    print("\n" + manager.get_strategy_status_summary())
    print("\n✅ 多組部位管理器測試完成")

# 🔧 新增：下單相關方法將在下一步直接添加到類中
