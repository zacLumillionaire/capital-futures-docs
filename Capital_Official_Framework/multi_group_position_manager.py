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
from async_db_updater import AsyncDatabaseUpdater
from async_db_updater import AsyncDatabaseUpdater

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
        self.position_order_mapping = {}    # {position_pk: order_id}

        # 🔧 新增：追價機制相關屬性
        self.retry_lock = threading.Lock()  # 重試操作鎖
        self.max_retry_count = 5  # 最大重試次數
        self.max_slippage_points = 5  # 最大滑價點數
        self.retry_time_window = 30  # 重試時間窗口（秒）

        # 初始化日誌
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 🚀 新增：異步資料庫更新器（延遲更新方案）
        # 🔧 修復：不自動創建，等待外部設置全局異步更新器
        self.async_updater = None  # 將由外部設置
        self.async_update_enabled = True  # 可以動態開關

        self.logger.info("多組部位管理器初始化完成")

        # 設置回調
        self._setup_total_lot_manager_callbacks()  # 🔧 新版總量追蹤回調
        self._setup_simplified_tracker_callbacks()  # 保留舊版相容性
        if self.order_tracker:
            self._setup_order_callbacks()

    def set_async_updater(self, async_updater):
        """
        設置異步更新器

        Args:
            async_updater: AsyncDatabaseUpdater實例
        """
        self.async_updater = async_updater
        if async_updater:
            self.async_update_enabled = True
            self.logger.info("✅ 異步更新器已設置")
        else:
            self.async_update_enabled = False
            self.logger.warning("⚠️ 異步更新器已移除")
    
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
            # 查詢今天已存在的 logical_group_id
            today_groups = self.db_manager.get_today_strategy_groups()
            existing_group_ids = [strategy_group['logical_group_id'] for strategy_group in today_groups]

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
            # 🔧 修復：根據DB_ID獲取組資訊，然後用group_id查詢完整信息
            # 先用主鍵查詢基本信息
            group_basic_info = self.db_manager.get_strategy_group_by_db_id(group_db_id)
            if not group_basic_info:
                self.logger.error(f"找不到組資訊: DB_ID={group_db_id}")
                return False

            # 再用logical_group_id查詢完整信息（包含JOIN的數據）
            logical_group_id = group_basic_info['logical_group_id']
            group_info = self.db_manager.get_strategy_group_info(logical_group_id)
            if not group_info:
                self.logger.error(f"找不到組完整資訊: logical_group_id={logical_group_id}, DB_ID={group_db_id}")
                return False

            group_config = self.strategy_config.get_group_by_id(group_info['logical_group_id'])
            if not group_config or group_config.status != GroupStatus.WAITING:
                self.logger.warning(f"組 {group_info['logical_group_id']} 不在等待狀態")
                return False

            self.logger.info(f"🚀 執行組 {group_info['logical_group_id']} 進場: {group_info['total_lots']}口 @ {actual_price}")

            # 🔧 新增：創建總量追蹤器
            strategy_id = f"strategy_{group_info['logical_group_id']}_{int(time.time())}"
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
                    group_id=group_info['logical_group_id'],
                    total_lots=group_info['total_lots'],
                    direction=group_info['direction'],
                    target_price=actual_price,
                    product="TM0000"  # 預設商品
                )

            # 🔧 修復：先創建PENDING部位記錄，再執行下單
            position_pks = []
            order_mappings = {}  # {position_pk: order_id}

            for lot_rule in group_config.lot_rules:
                # 1. 先創建部位記錄（狀態為PENDING）
                position_pk = self.db_manager.create_position_record(
                    group_id=group_info['logical_group_id'],  # 🔧 修復：使用邏輯group_id而非DB_ID
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
                        position_id=position_pk,
                        order_id=order_id,
                        api_seq_no=str(api_seq_no)
                    )

                    # 建立映射關係
                    order_mappings[position_pk] = order_id
                    self.position_order_mapping[position_pk] = order_id

                    self.logger.info(f"✅ 第{lot_rule.lot_id}口下單成功: ID={position_pk}, 訂單={order_id}")
                else:
                    # 下單失敗，立即標記為失敗
                    self.db_manager.mark_position_failed(
                        position_id=position_pk,
                        failure_reason='下單失敗',
                        order_status='REJECTED'
                    )
                    self.logger.error(f"❌ 第{lot_rule.lot_id}口下單失敗: ID={position_pk}")

                position_pks.append(position_pk)

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
                    'position_pks': position_pks,
                    'entry_price': actual_price,
                    'entry_time': actual_time,
                    'direction': group_info['direction']
                }

                self.logger.info(f"✅ 組 {group_info['logical_group_id']} 進場完成: {len(order_mappings)}/{len(position_pks)}口成功")

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
                            group_id=group_info['logical_group_id'],
                            lots=len(order_mappings)
                        )
                    except Exception as e:
                        self.logger.error(f"更新簡化追蹤器已送出口數失敗: {e}")
            else:
                self.logger.error(f"❌ 組 {group_info['logical_group_id']} 進場失敗: 所有訂單都失敗")
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
                return waiting_groups[0]['group_pk']  # 返回第一個等待的組
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
    
    def update_position_exit(self, position_pk: int, exit_price: float,
                           exit_time: str, exit_reason: str, pnl: float) -> bool:
        """更新部位出場"""
        try:
            self.db_manager.update_position_exit(
                position_id=position_pk,  # 保持與資料庫管理器參數一致
                exit_price=exit_price,
                exit_time=exit_time,
                exit_reason=exit_reason,
                pnl=pnl
            )
            
            self.logger.info(f"部位 {position_pk} 出場: {exit_reason}, 損益={pnl:.1f}點")

            # 檢查組是否全部出場
            self._check_group_completion(position_pk)
            
            return True
            
        except Exception as e:
            self.logger.error(f"更新部位出場失敗: {e}")
            return False
    
    def _check_group_completion(self, position_pk: int):
        """檢查組是否全部出場完成"""
        try:
            # 通過部位ID找到組ID
            all_positions = self.get_all_active_positions()
            group_db_id = None
            
            for pos in all_positions:
                if pos['position_pk'] == position_pk:
                    group_db_id = pos['group_pk']
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

    # 🔧 新增：價格更新方法
    def update_current_price(self, current_price: float, current_time: str):
        """
        更新當前價格並觸發平倉機制檢查

        Args:
            current_price: 當前價格
            current_time: 當前時間
        """
        try:
            # 靜默處理，避免過多日誌輸出影響性能
            # 只在有活躍部位時才進行處理
            active_positions = self.get_all_active_positions()
            if not active_positions:
                return

            # 更新平倉機制系統（如果已整合）
            if hasattr(self, 'exit_mechanism_manager') and self.exit_mechanism_manager:
                try:
                    # 使用統一平倉管理器處理價格更新
                    self.exit_mechanism_manager.process_price_update(current_price, current_time)
                except Exception as e:
                    # 靜默處理平倉機制錯誤，不影響主流程
                    pass

            # 更新風險管理引擎（如果存在）
            if hasattr(self, 'risk_engine') and self.risk_engine:
                try:
                    self.risk_engine.update_current_price(current_price, current_time)
                except Exception as e:
                    # 靜默處理風險管理錯誤
                    pass

        except Exception as e:
            # 完全靜默處理，確保不影響報價流程
            pass

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

            # 🔧 啟用簡化版追價回調（避免重複下單）
            # 只註冊簡化追蹤器的追價回調，總量追蹤器已停用
            self.simplified_tracker.add_retry_callback(self._on_simplified_retry_simple)

            self.logger.info("✅ 簡化追蹤器回調機制設置完成（追價回調已暫停）")

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
            # 根據訂單ID找到對應的部位主鍵ID
            position_pk = self._get_position_pk_by_order_id(order_info.order_id)
            if position_pk:
                # 🚀 異步確認部位成交（解決建倉延遲問題）
                if self.async_update_enabled and self.async_updater:
                    # 🚀 異步更新（非阻塞）
                    fill_time_str = order_info.fill_time.strftime('%H:%M:%S') if order_info.fill_time else ''

                    # 異步確認成交
                    self.async_updater.schedule_position_fill_update(
                        position_id=position_pk,
                        fill_price=order_info.fill_price,
                        fill_time=fill_time_str,
                        order_status='FILLED'
                    )

                    # 異步初始化風險管理狀態
                    self.async_updater.schedule_risk_state_creation(
                        position_id=position_pk,
                        peak_price=order_info.fill_price,
                        current_time=fill_time_str,
                        update_category="成交初始化",
                        update_message="異步成交初始化"
                    )

                    self.logger.info(f"🚀 部位{position_pk}異步成交確認已排程: @{order_info.fill_price}")
                else:
                    # 🛡️ 同步更新（備用模式）
                    success = self.db_manager.confirm_position_filled(
                        position_id=position_pk,
                        actual_fill_price=order_info.fill_price,
                        fill_time=order_info.fill_time.strftime('%H:%M:%S') if order_info.fill_time else '',
                        order_status='FILLED'
                    )

                    if success:
                        # 初始化風險管理狀態（成交後才初始化）
                        self.db_manager.create_risk_management_state(
                            position_id=position_pk,
                            peak_price=order_info.fill_price,
                            current_time=order_info.fill_time.strftime('%H:%M:%S') if order_info.fill_time else '',
                            update_reason="成交初始化"
                        )

                        self.logger.info(f"✅ 部位{position_pk}成交確認: @{order_info.fill_price}")

        except Exception as e:
            self.logger.error(f"處理成交回調失敗: {e}")

    def _on_simplified_fill(self, logical_group_id: int, price: float, qty: int,
                          filled_lots: int, total_lots: int):
        """簡化追蹤器成交回調"""
        try:
            # 更新資料庫中該組的部位狀態
            self._update_group_positions_on_fill(logical_group_id, price, qty, filled_lots, total_lots)

            self.logger.info(f"✅ [簡化追蹤] 組{logical_group_id}成交: {qty}口 @{price}, "
                           f"進度: {filled_lots}/{total_lots}")

            # 如果組完全成交，觸發完成處理
            if filled_lots >= total_lots:
                self._on_group_complete(logical_group_id)

        except Exception as e:
            self.logger.error(f"處理簡化成交回調失敗: {e}")

    def _on_simplified_retry_simple(self, logical_group_id: int, qty: int, price: float, retry_count: int):
        """簡化版追價回調 - 避免重複下單"""
        try:
            self.logger.info(f"🔄 [簡化追蹤] 組{logical_group_id}觸發追價: {qty}口 @{price}, "
                           f"第{retry_count}次重試")

            # 🔧 簡化版：只執行單一追價，不重複
            self._execute_single_retry_for_group(group_id, qty, retry_count)

        except Exception as e:
            self.logger.error(f"處理簡化追價回調失敗: {e}")

    def _execute_single_retry_for_group(self, logical_group_id: int, qty: int, retry_count: int):
        """為特定組執行單一追價 - 避免重複下單"""
        try:
            # 獲取組信息
            group_info = self._get_group_info_for_retry(logical_group_id)
            if not group_info:
                self.logger.error(f"無法獲取組{logical_group_id}信息")
                return

            direction = group_info.get('direction')
            product = "TM0000"

            # 計算追價價格
            retry_price = self._calculate_retry_price_for_group(direction, retry_count)
            if not retry_price:
                self.logger.error(f"無法計算組{group_id}追價價格")
                return

            self.logger.info(f"🔄 [簡化追蹤] 組{group_id}追價參數: {direction} {qty}口 @{retry_price} (第{retry_count}次)")

            # 🔧 修復：執行單一下單 - 使用正確的方法
            if self.order_manager:
                # 🔧 修復：使用正確的execute_strategy_order方法
                order_result = self.order_manager.execute_strategy_order(
                    direction=direction,
                    product=product,
                    quantity=qty,
                    price=retry_price,
                    signal_source=f"group_{group_id}_retry_{retry_count}"
                )

                if order_result and order_result.success:
                    self.logger.info(f"✅ 組{group_id}追價下單成功: 第{qty}口 @{retry_price}")

                    # 🔧 修復：註冊到統一追蹤器 (與建倉邏輯一致)
                    if hasattr(self, 'order_tracker') and self.order_tracker:
                        try:
                            self.order_tracker.register_order(
                                order_id=order_result.order_id,
                                product=product,
                                direction=direction,
                                quantity=qty,
                                price=retry_price,
                                is_virtual=(order_result.mode == "virtual"),
                                signal_source=f"group_{group_id}_retry_{retry_count}",
                                api_seq_no=order_result.api_result if hasattr(order_result, 'api_result') else None
                            )
                            self.logger.info(f"📝 組{group_id}追價訂單已註冊到統一追蹤器: {order_result.order_id}")
                        except Exception as track_error:
                            self.logger.warning(f"⚠️ 組{group_id}追價訂單註冊失敗: {track_error}")

                    # 🔧 保留：同時註冊到FIFO匹配器 (向後相容)
                    if hasattr(self, 'simplified_tracker') and self.simplified_tracker:
                        if hasattr(self.simplified_tracker, 'fifo_matcher'):
                            try:
                                self.simplified_tracker.fifo_matcher.add_order(
                                    order_id=order_result.order_id,
                                    product=product,
                                    direction=direction,
                                    quantity=qty,
                                    price=retry_price
                                )
                                self.logger.info(f"📝 組{group_id}追價訂單已註冊到FIFO: {order_result.order_id}")
                            except Exception as fifo_error:
                                self.logger.warning(f"⚠️ 組{group_id}追價訂單FIFO註冊失敗: {fifo_error}")
                else:
                    error_msg = getattr(order_result, 'error', '未知錯誤') if order_result else '下單結果為空'
                    self.logger.error(f"❌ 組{group_id}追價下單失敗: {error_msg}")
            else:
                self.logger.error("下單管理器未初始化")

        except Exception as e:
            self.logger.error(f"執行組{group_id}單一追價失敗: {e}")

    def _get_group_info_for_retry(self, logical_group_id: int) -> Optional[Dict]:
        """獲取組信息用於追價"""
        try:
            # 🔧 修復：使用正確的資料庫方法名稱
            group_data = self.db_manager.get_strategy_group_info(logical_group_id)
            if group_data:
                return {
                    'direction': group_data['direction'],  # 使用字典鍵
                    'target_price': group_data.get('range_high', 0),  # 使用range_high作為目標價
                    'logical_group_id': logical_group_id
                }
            return None
        except Exception as e:
            self.logger.error(f"獲取組{group_id}信息失敗: {e}")
            return None

    def _calculate_retry_price_for_group(self, direction: str, retry_count: int) -> Optional[float]:
        """計算組追價價格"""
        try:
            product = "TM0000"

            # 獲取當前市價
            if self.order_manager:
                if direction == "LONG":
                    current_ask1 = self.order_manager.get_ask1_price(product)
                    if current_ask1:
                        retry_price = current_ask1 + retry_count
                        self.logger.info(f"🔄 [追價] LONG追價計算: ASK1({current_ask1}) + {retry_count} = {retry_price}")
                        return retry_price
                elif direction == "SHORT":
                    current_bid1 = self.order_manager.get_bid1_price(product)
                    if current_bid1:
                        retry_price = current_bid1 - retry_count
                        self.logger.info(f"🔄 [追價] SHORT追價計算: BID1({current_bid1}) - {retry_count} = {retry_price}")
                        return retry_price

            self.logger.warning(f"無法計算{direction}追價價格")
            return None

        except Exception as e:
            self.logger.error(f"計算追價價格失敗: {e}")
            return None

    def _update_group_positions_on_fill(self, logical_group_id: int, price: float, qty: int,
                                      filled_lots: int, total_lots: int):
        """更新組內部位的成交狀態"""
        try:
            self.logger.info(f"📊 [簡化追蹤] 組{logical_group_id}成交統計更新: "
                           f"{qty}口 @{price}, 總進度: {filled_lots}/{total_lots}")

            # 🔧 新增：防重複處理檢查
            processing_key = f"{logical_group_id}_{price}_{qty}_{filled_lots}"
            if not hasattr(self, '_processing_fills'):
                self._processing_fills = set()

            if processing_key in self._processing_fills:
                self.logger.warning(f"⚠️ [簡化追蹤] 組{logical_group_id}重複處理檢測，跳過: {processing_key}")
                return

            self._processing_fills.add(processing_key)
            self.logger.info(f"🔍 [簡化追蹤] 組{logical_group_id}開始處理: {processing_key}")

            # 🔧 修復：實際更新資料庫部位狀態
            # 查找該組的PENDING部位並按FIFO順序確認成交
            try:
                # 🔧 修復：查詢今日所有組（包括ACTIVE狀態），找到對應的資料庫組ID
                all_groups = self.db_manager.get_today_strategy_groups()
                group_db_id = None

                for strategy_group in all_groups:
                    if strategy_group['logical_group_id'] == logical_group_id:
                        group_db_id = strategy_group['group_pk']
                        break

                if group_db_id:
                    # 🔧 修復：獲取該組的PENDING部位，按lot_id順序處理
                    with self.db_manager.get_connection() as conn:
                        cursor = conn.cursor()
                        # 🔧 修復：查詢order_status='PENDING'而不是status='PENDING'
                        cursor.execute('''
                            SELECT id AS position_pk, group_id AS group_pk, lot_id, status, order_status
                            FROM position_records
                            WHERE group_id = ? AND order_status = 'PENDING'
                            ORDER BY lot_id
                            LIMIT ?
                        ''', (group_db_id, qty))

                        pending_positions = cursor.fetchall()

                        # 🔧 改善：智能調試信息輸出
                        if len(pending_positions) > 0:
                            self.logger.info(f"🔍 [簡化追蹤] 組{group_id}(DB_ID:{group_db_id}) 找到 {len(pending_positions)} 個PENDING部位")
                        else:
                            # 🔧 修復：檢查是否已經全部成交，避免無意義警告
                            cursor.execute('''
                                SELECT COUNT(*) as total_count,
                                       SUM(CASE WHEN order_status = 'FILLED' THEN 1 ELSE 0 END) as filled_count
                                FROM position_records
                                WHERE group_id = ?
                            ''', (group_db_id,))

                            count_result = cursor.fetchone()
                            total_count = count_result[0] if count_result else 0
                            filled_count = count_result[1] if count_result else 0

                            if filled_count >= total_count and total_count > 0:
                                # 所有部位已成交，這是正常情況
                                self.logger.info(f"✅ [簡化追蹤] 組{logical_group_id} 所有部位已成交 ({filled_count}/{total_count})，跳過重複處理")
                                return  # 直接返回，避免無意義警告
                            else:
                                self.logger.info(f"🔍 [簡化追蹤] 組{logical_group_id}(DB_ID:{group_db_id}) 無PENDING部位 (已成交:{filled_count}/{total_count})")

                        # 🔧 修復：確認成交，每次處理qty個部位
                        confirmed_count = 0
                        for position_record in pending_positions:
                            if confirmed_count >= qty:
                                break  # 只處理本次成交的數量

                            # ⏰ 記錄開始時間用於性能追蹤
                            start_time = time.time()
                            position_pk = position_record[0]
                            fill_time_str = datetime.now().strftime('%H:%M:%S')

                            # 🚀 延遲更新方案：優先使用異步更新（如果啟用）
                            if self.async_update_enabled and hasattr(self, 'async_updater'):
                                # 🔧 健康檢查：確保異步更新器正常運行
                                if not self.check_async_updater_health():
                                    self.restart_async_updater_if_needed()
                                try:
                                    # 🎯 立即排程異步更新（非阻塞）
                                    async_success_1 = True
                                    async_success_2 = True

                                    try:
                                        self.async_updater.schedule_position_fill_update(
                                            position_id=position_pk,
                                            fill_price=price,
                                            fill_time=fill_time_str,
                                            order_status='FILLED'
                                        )
                                    except Exception as e1:
                                        async_success_1 = False
                                        self.logger.warning(f"⚠️ [異步更新] 部位{position_pk}成交更新排程失敗: {e1}")

                                    try:
                                        # 🎯 立即排程風險狀態創建（非阻塞）
                                        # 🔧 修復：使用符合資料庫約束的 update_category 和 update_message
                                        self.async_updater.schedule_risk_state_creation(
                                            position_id=position_pk,
                                            peak_price=price,
                                            current_time=fill_time_str,
                                            update_category="成交初始化",
                                            update_message="同步成交初始化"
                                        )
                                    except Exception as e2:
                                        async_success_2 = False
                                        self.logger.warning(f"⚠️ [異步更新] 部位{position_pk}風險狀態排程失敗: {e2}")

                                    # 📊 記錄異步更新性能
                                    async_elapsed = (time.time() - start_time) * 1000

                                    # 🔧 改善：只有在兩個異步操作都成功時才跳過同步更新
                                    if async_success_1 and async_success_2:
                                        # 🔧 新增：註冊到統一移動停利計算器（如果啟用）
                                        self._register_position_to_trailing_calculator(
                                            position_pk, position, price, group_id
                                        )

                                        confirmed_count += 1
                                        self.logger.info(f"🚀 [異步更新] 部位{position_pk}成交確認 @{price} (耗時:{async_elapsed:.1f}ms)")
                                        continue  # 跳過同步更新
                                    else:
                                        self.logger.warning(f"⚠️ [異步更新] 部位{position_pk}部分失敗，回退到同步更新")
                                        # 繼續執行同步更新作為備份

                                except Exception as async_error:
                                    self.logger.warning(f"⚠️ [異步更新] 部位{position_pk}異步更新失敗: {async_error}，回退到同步更新")
                                    # 繼續執行同步更新作為備份

                            # 🛡️ 備份方案：同步更新（保留原有邏輯）
                            sync_start_time = time.time()
                            success = self.db_manager.confirm_position_filled(
                                position_id=position_pk,
                                actual_fill_price=price,
                                fill_time=fill_time_str,
                                order_status='FILLED'
                            )

                            if success:
                                # 初始化風險管理狀態
                                self.db_manager.create_risk_management_state(
                                    position_id=position_pk,
                                    peak_price=price,
                                    current_time=fill_time_str,
                                    update_reason="成交初始化"
                                )

                                # 🔧 新增：註冊到統一移動停利計算器（如果啟用）
                                self._register_position_to_trailing_calculator(
                                    position_pk, position, price, group_id
                                )

                                # 📊 記錄同步更新性能
                                sync_elapsed = (time.time() - sync_start_time) * 1000
                                confirmed_count += 1
                                self.logger.info(f"✅ [同步更新] 部位{position_pk}成交確認 @{price} (耗時:{sync_elapsed:.1f}ms)")
                            else:
                                sync_elapsed = (time.time() - sync_start_time) * 1000
                                self.logger.error(f"❌ [同步更新] 部位{position_pk}成交確認失敗 (耗時:{sync_elapsed:.1f}ms)")

                        # 🔧 改善：只在實際處理了部位時輸出成功信息
                        if confirmed_count > 0:
                            total_elapsed = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0
                            self.logger.info(f"🎉 [簡化追蹤] 組{group_id} 成功確認 {confirmed_count} 個部位成交 (總耗時:{total_elapsed:.1f}ms)")
                else:
                    self.logger.warning(f"⚠️ [簡化追蹤] 找不到組{group_id}的資料庫記錄")

            except Exception as db_error:
                self.logger.error(f"資料庫部位更新失敗: {db_error}")

        except Exception as e:
            self.logger.error(f"更新組部位成交狀態失敗: {e}")
        finally:
            # 🔧 清理處理標記
            if hasattr(self, '_processing_fills'):
                processing_key = f"{logical_group_id}_{price}_{qty}_{filled_lots}"
                self._processing_fills.discard(processing_key)
                self.logger.info(f"🧹 [簡化追蹤] 組{logical_group_id}處理完成，清理標記: {processing_key}")

    def _register_position_to_trailing_calculator(self, position_pk: int, position_data: tuple,
                                                 fill_price: float, logical_group_id: int):
        """
        註冊部位到統一移動停利計算器 - 🔧 新增：支援統一計算器架構

        Args:
            position_pk: 部位主鍵ID
            position_data: 部位資料元組
            fill_price: 成交價格
            logical_group_id: 邏輯組ID
        """
        try:
            # 檢查是否有統一移動停利計算器（使用弱引用）
            parent = getattr(self, '_parent_ref', lambda: None)()
            if not parent:
                return  # 父引用不存在，跳過註冊

            if not (hasattr(parent, 'unified_trailing_enabled') and parent.unified_trailing_enabled):
                return  # 未啟用統一計算器，跳過註冊

            if not (hasattr(parent, 'trailing_calculator') and parent.trailing_calculator):
                return  # 統一計算器不存在，跳過註冊

            # 從部位資料中提取信息
            direction = position_data[3]  # direction 在第4個位置
            lot_id = position_data[2]     # lot_id 在第3個位置

            # 獲取組配置以確定移動停利參數
            group_config = self._get_group_trailing_config(logical_group_id, lot_id)

            # 註冊到統一移動停利計算器
            success = parent.trailing_calculator.register_position(
                position_id=position_pk,
                direction=direction,
                entry_price=fill_price,
                activation_points=group_config.get('activation_points', 15.0),  # 預設15點啟動
                pullback_percent=group_config.get('pullback_percent', 0.2)     # 預設20%回撤
            )

            if success:
                self.logger.info(f"✅ [統一移動停利] 部位{position_pk}已註冊: {direction} @{fill_price:.0f}, "
                               f"啟動{group_config.get('activation_points', 15):.0f}點, "
                               f"回撤{group_config.get('pullback_percent', 0.2)*100:.0f}%")
            else:
                self.logger.warning(f"⚠️ [統一移動停利] 部位{position_pk}註冊失敗")

        except Exception as e:
            self.logger.error(f"註冊部位到統一移動停利計算器失敗: {e}")

    def _get_group_trailing_config(self, logical_group_id: int, lot_id: int) -> dict:
        """
        獲取組的移動停利配置 - 🔧 新增：支援分層移動停利

        Args:
            logical_group_id: 邏輯組ID
            lot_id: 口數ID

        Returns:
            dict: 移動停利配置
        """
        try:
            # 分層移動停利配置（與原有邏輯一致）
            if lot_id == 1:
                return {'activation_points': 15.0, 'pullback_percent': 0.2}  # 第1口：15點啟動，20%回撤
            elif lot_id == 2:
                return {'activation_points': 40.0, 'pullback_percent': 0.2}  # 第2口：40點啟動，20%回撤
            elif lot_id == 3:
                return {'activation_points': 65.0, 'pullback_percent': 0.2}  # 第3口：65點啟動，20%回撤
            else:
                return {'activation_points': 15.0, 'pullback_percent': 0.2}  # 預設配置

        except Exception as e:
            self.logger.error(f"獲取組移動停利配置失敗: {e}")
            return {'activation_points': 15.0, 'pullback_percent': 0.2}  # 預設配置

    def _on_group_complete(self, logical_group_id: int):
        """組完成處理"""
        try:
            self.logger.info(f"🎉 [簡化追蹤] 組{logical_group_id}建倉完成!")

            # 可以在這裡添加組完成後的處理邏輯
            # 例如：啟動風險管理、發送通知等

        except Exception as e:
            self.logger.error(f"處理組完成失敗: {e}")

    def _execute_group_retry(self, logical_group_id: int, qty: int, price: float, retry_count: int):
        """執行組追價重試"""
        try:
            self.logger.info(f"🔄 [簡化追蹤] 組{logical_group_id}觸發追價重試: "
                           f"{qty}口 @{price}, 第{retry_count}次")

            # 🔧 實際追價下單邏輯
            # 1. 獲取組的基本信息
            group_info = self._get_group_info_by_id(logical_group_id)
            if not group_info:
                self.logger.error(f"找不到組{logical_group_id}的信息")
                return

            direction = group_info.get('direction')
            # 🔧 修復：商品代碼從配置或預設值獲取
            product = getattr(self, 'current_product', 'TM0000')

            # 2. 計算追價價格
            retry_price = self._calculate_retry_price_for_group(direction, retry_count)
            if retry_price is None:
                self.logger.error(f"無法計算組{group_id}的追價價格")
                return

            self.logger.info(f"🔄 [簡化追蹤] 組{group_id}追價參數: "
                           f"{direction} {qty}口 @{retry_price} (第{retry_count}次)")

            # 3. 🔧 修復：執行追價下單 - 直接使用已初始化的下單管理器
            for i in range(qty):
                try:
                    # 🔧 修復：使用已設置的order_manager (實單階段)
                    if hasattr(self, 'order_manager') and self.order_manager:
                        # 🔧 修復：移除不支援的order_type參數
                        order_result = self.order_manager.execute_strategy_order(
                            direction=direction,
                            quantity=1,
                            signal_source=f"group_{group_id}_retry_{retry_count}",
                            price=retry_price
                        )

                        if order_result.success:
                            self.logger.info(f"✅ 組{group_id}追價下單成功: 第{i+1}口 @{retry_price}")

                            # 🔧 新增：註冊追價訂單到追蹤器
                            if hasattr(self, 'order_tracker') and self.order_tracker:
                                try:
                                    self.order_tracker.register_order(
                                        order_id=order_result.order_id,
                                        product=product,
                                        direction=direction,
                                        quantity=1,
                                        price=retry_price,
                                        is_virtual=(order_result.mode == "virtual"),
                                        signal_source=f"group_{group_id}_retry_{retry_count}",
                                        api_seq_no=order_result.api_result if order_result.api_result else None
                                    )
                                    self.logger.info(f"📝 組{group_id}追價訂單已註冊: {order_result.order_id}")
                                except Exception as track_error:
                                    self.logger.warning(f"⚠️ 組{group_id}追價訂單註冊失敗: {track_error}")
                        else:
                            self.logger.error(f"❌ 組{group_id}追價下單失敗: 第{i+1}口 - {order_result.error_message}")
                    else:
                        self.logger.warning(f"⚠️ 下單管理器未初始化，無法執行追價下單")

                except Exception as order_error:
                    self.logger.error(f"組{group_id}第{i+1}口追價下單異常: {order_error}")

        except Exception as e:
            self.logger.error(f"執行組追價重試失敗: {e}")

    def _get_group_info_by_id(self, logical_group_id: int) -> dict:
        """根據組ID獲取組信息"""
        try:
            # 🔧 修復：使用正確的資料庫方法
            group_info = self.db_manager.get_strategy_group_info(logical_group_id)
            if group_info:
                self.logger.info(f"🔍 [追價] 獲取組{logical_group_id}信息: {group_info.get('direction')} @{group_info.get('range_low')}-{group_info.get('range_high')}")
                return group_info
            else:
                self.logger.warning(f"⚠️ [追價] 組{logical_group_id}信息不存在")
                return None
        except Exception as e:
            self.logger.error(f"獲取組{group_id}信息失敗: {e}")
            return None

    def _calculate_retry_price_for_group(self, direction: str, retry_count: int) -> float:
        """計算組追價價格"""
        try:
            # 🔧 修復：從正確的地方獲取當前市價
            current_ask1 = 0
            current_bid1 = 0

            # 方法1: 從虛實單管理器獲取
            if hasattr(self, 'virtual_real_order_manager') and self.virtual_real_order_manager:
                try:
                    current_product = getattr(self.virtual_real_order_manager, 'current_product', 'TM0000')
                    if hasattr(self.virtual_real_order_manager, 'get_ask1_price'):
                        ask1_price = self.virtual_real_order_manager.get_ask1_price(current_product)
                        if ask1_price and ask1_price > 0:
                            current_ask1 = ask1_price

                    if hasattr(self.virtual_real_order_manager, 'get_bid1_price'):
                        bid1_price = self.virtual_real_order_manager.get_bid1_price(current_product)
                        if bid1_price and bid1_price > 0:
                            current_bid1 = bid1_price
                except Exception as e:
                    self.logger.debug(f"從虛實單管理器獲取市價失敗: {e}")

            # 方法2: 從主程式的best5_data獲取 (備用方案)
            if (current_ask1 == 0 or current_bid1 == 0) and hasattr(self, '_parent_ref'):
                try:
                    parent = self._parent_ref()
                    if parent and hasattr(parent, 'best5_data') and parent.best5_data:
                        if current_ask1 == 0:
                            current_ask1 = parent.best5_data.get('ask1', 0)
                        if current_bid1 == 0:
                            current_bid1 = parent.best5_data.get('bid1', 0)
                except Exception as e:
                    self.logger.debug(f"從best5_data獲取市價失敗: {e}")

            # 檢查是否成功獲取市價
            if current_ask1 > 0 and current_bid1 > 0:
                if direction == "LONG":
                    # 🔧 修復：多單使用ASK1+追價點數 (向上追價)
                    retry_price = current_ask1 + retry_count
                    self.logger.info(f"🔄 [追價] LONG追價計算: ASK1({current_ask1}) + {retry_count} = {retry_price}")
                    return retry_price
                elif direction == "SHORT":
                    # 🔧 修復：空單使用BID1-追價點數 (向下追價，更容易成交)
                    retry_price = current_bid1 - retry_count
                    self.logger.info(f"🔄 [追價] SHORT追價計算: BID1({current_bid1}) - {retry_count} = {retry_price}")
                    return retry_price
            else:
                self.logger.warning(f"無法獲取有效市價: ASK1={current_ask1}, BID1={current_bid1}")

            self.logger.warning("無法獲取當前市價，使用預設追價邏輯")
            return None

        except Exception as e:
            self.logger.error(f"計算追價價格失敗: {e}")
            return None

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
            # 根據訂單ID找到對應的部位主鍵ID
            position_pk = self._get_position_pk_by_order_id(order_info.order_id)
            if position_pk:
                # 設定原始價格（如果還沒設定）
                position_info = self.db_manager.get_position_by_id(position_pk)
                if position_info and not position_info.get('original_price'):
                    original_price = order_info.price if hasattr(order_info, 'price') else position_info.get('entry_price')
                    if original_price:
                        self.db_manager.set_original_price(position_pk, original_price)

                # 標記部位失敗
                success = self.db_manager.mark_position_failed(
                    position_id=position_pk,
                    failure_reason='FOK失敗',
                    order_status='CANCELLED'
                )

                if success:
                    self.logger.info(f"❌ 部位{position_pk}下單失敗: FOK取消")

                    # 🔧 新增: 事件驅動追價觸發（避免GIL風險）
                    self._trigger_retry_if_allowed(position_pk)

        except Exception as e:
            self.logger.error(f"處理取消回調失敗: {e}")

    def _trigger_retry_if_allowed(self, position_pk: int):
        """觸發追價重試（如果允許）- 事件驅動，避免GIL風險"""
        try:
            # 使用Timer延遲執行，避免立即重試
            # 這樣可以讓市場價格有時間更新
            retry_timer = threading.Timer(2.0, self._execute_delayed_retry, args=[position_pk])
            retry_timer.daemon = True  # 設為守護線程
            retry_timer.start()

            self.logger.info(f"⏰ 已排程部位{position_pk}的延遲追價（2秒後執行）")

        except Exception as e:
            self.logger.error(f"觸發追價重試失敗: {e}")

    def _execute_delayed_retry(self, position_pk: int):
        """延遲執行追價重試 - 在獨立線程中安全執行"""
        try:
            self.logger.info(f"🔄 開始執行部位{position_pk}的延遲追價")

            # 檢查部位是否仍然需要重試
            position_info = self.db_manager.get_position_by_id(position_pk)
            if not position_info:
                self.logger.warning(f"部位{position_pk}不存在，取消追價")
                return

            if position_info.get('status') != 'FAILED':
                self.logger.info(f"部位{position_pk}狀態已變更({position_info.get('status')})，取消追價")
                return

            # 執行追價重試
            if self.is_retry_allowed(position_info):
                success = self.retry_failed_position(position_pk)
                if success:
                    self.logger.info(f"✅ 部位{position_pk}延遲追價執行成功")
                else:
                    self.logger.warning(f"⚠️ 部位{position_pk}延遲追價執行失敗")
            else:
                self.logger.info(f"📋 部位{position_pk}不符合追價條件，跳過")

        except Exception as e:
            self.logger.error(f"延遲追價執行失敗: {e}")

    def _get_position_pk_by_order_id(self, order_id: str) -> Optional[int]:
        """根據訂單ID查詢部位主鍵ID"""
        try:
            # 從映射中查找
            for position_pk, mapped_order_id in self.position_order_mapping.items():
                if mapped_order_id == order_id:
                    return position_pk

            # 從資料庫查找
            position = self.db_manager.get_position_by_order_id(order_id)
            if position:
                return position['position_pk']

            return None

        except Exception as e:
            self.logger.error(f"根據訂單ID查詢部位主鍵ID失敗: {e}")
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
                    self.logger.info(f"🔄 觸發部位{position['position_pk']}追價重試")
                    self.retry_failed_position(position['position_pk'])

        except Exception as e:
            self.logger.error(f"監控失敗部位錯誤: {e}")

    def retry_failed_position(self, position_pk: int) -> bool:
        """執行單一部位的追價補單"""
        try:
            with self.retry_lock:
                # 1. 取得部位資訊
                position_info = self.db_manager.get_position_by_id(position_pk)
                if not position_info:
                    self.logger.error(f"找不到部位{position_pk}")
                    return False

                # 2. 檢查重試條件
                if not self.is_retry_allowed(position_info):
                    self.logger.warning(f"部位{position_pk}不符合重試條件")
                    return False

                # 3. 計算新價格
                retry_count = position_info.get('retry_count', 0) + 1
                new_price = self.calculate_retry_price(position_info, retry_count)

                if new_price is None:
                    self.logger.error(f"無法計算部位{position_pk}的重試價格")
                    return False

                # 4. 檢查滑價限制
                original_price = position_info.get('original_price') or position_info.get('entry_price')
                if original_price and not self.validate_slippage(original_price, new_price, self.max_slippage_points):
                    self.logger.warning(f"部位{position_pk}滑價超出限制: {abs(new_price - original_price)}點")
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
                        position_id=position_pk,
                        retry_count=retry_count,
                        retry_price=new_price,
                        retry_reason=retry_reason
                    )
                    self.logger.info(f"✅ 部位{position_pk}第{retry_count}次追價成功: @{new_price}")
                else:
                    self.logger.error(f"❌ 部位{position_pk}第{retry_count}次追價失敗")

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
                self.logger.info(f"部位{position_info['position_pk']}已達最大重試次數({self.max_retry_count})")
                return False

            # 檢查狀態
            if position_info.get('status') != 'FAILED':
                self.logger.info(f"部位{position_info['position_pk']}狀態不是FAILED")
                return False

            if position_info.get('order_status') != 'CANCELLED':
                self.logger.info(f"部位{position_info['position_pk']}訂單狀態不是CANCELLED")
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
                signal_source=f"retry_{retry_count}_{position_info['position_pk']}",
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
                            signal_source=f"retry_{retry_count}_{position_info['position_pk']}",
                            is_virtual=(order_result.mode == "virtual")
                        )

                        # 更新部位訂單映射
                        self.position_order_mapping[position_info['position_pk']] = order_result.order_id

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

    def execute_exit_retry(self, position_pk: int) -> bool:
        """
        執行出場追價

        Args:
            position_pk: 部位主鍵ID

        Returns:
            bool: 是否成功
        """
        try:
            # 1. 取得部位資訊
            position_info = self.db_manager.get_position_by_id(position_pk)
            if not position_info:
                self.logger.error(f"找不到部位 {position_pk}")
                return False

            # 2. 檢查重試條件
            retry_count = position_info.get('retry_count', 0) + 1
            if retry_count > self.max_retry_count:
                self.logger.warning(f"部位{position_pk}出場重試次數已達上限")
                return False

            # 3. 計算追價價格
            new_price = self.calculate_exit_retry_price(position_info, retry_count)
            if not new_price:
                self.logger.error(f"無法計算部位{position_pk}的出場追價")
                return False

            # 4. 檢查滑價限制
            original_price = position_info.get('entry_price')
            if original_price:
                max_slippage = 5  # 最大滑價5點
                actual_slippage = abs(new_price - original_price)
                if actual_slippage > max_slippage:
                    self.logger.warning(f"部位{position_pk}出場滑價超出限制: {actual_slippage}點")
                    return False

            # 5. 執行出場重試下單
            success = self._execute_exit_retry_order(position_info, new_price, retry_count)

            if success:
                # 6. 更新重試記錄
                self.db_manager.update_retry_info(
                    position_id=position_pk,
                    retry_count=retry_count,
                    retry_price=new_price,
                    retry_reason=f"出場追價第{retry_count}次"
                )
                self.logger.info(f"✅ 部位{position_pk}出場第{retry_count}次追價成功: @{new_price}")
            else:
                self.logger.error(f"❌ 部位{position_pk}出場第{retry_count}次追價失敗")

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
                signal_source=f"exit_retry_{retry_count}_{position_info['position_pk']}",
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
                            signal_source=f"exit_retry_{retry_count}_{position_info['position_pk']}",
                            is_virtual=(order_result.mode == "virtual")
                        )

                        # 更新部位訂單映射
                        self.position_order_mapping[position_info['position_pk']] = order_result.order_id

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

    # 🚀 延遲更新方案控制方法
    def enable_async_update(self, enabled: bool = True):
        """啟用/停用異步更新功能"""
        self.async_update_enabled = enabled
        status = "啟用" if enabled else "停用"
        self.logger.info(f"🔧 異步更新功能已{status}")
        if hasattr(self, 'async_updater'):
            print(f"[ASYNC_UPDATE] 🔧 異步更新功能已{status}")

    def get_async_update_stats(self) -> dict:
        """獲取異步更新性能統計"""
        if hasattr(self, 'async_updater'):
            return self.async_updater.get_stats()
        return {}

    def report_async_update_performance(self):
        """報告異步更新性能"""
        if hasattr(self, 'async_updater'):
            self.async_updater.report_performance_stats()
        else:
            print("[ASYNC_UPDATE] ⚠️ 異步更新器未初始化")

    def shutdown_async_updater(self):
        """關閉異步更新器"""
        if hasattr(self, 'async_updater'):
            self.async_updater.stop()
            self.logger.info("🛑 異步更新器已關閉")

    def check_async_updater_health(self):
        """檢查異步更新器健康狀態"""
        if not hasattr(self, 'async_updater') or not self.async_updater:
            return False

        # 檢查工作線程是否還在運行
        if not self.async_updater.running or not self.async_updater.worker_thread.is_alive():
            self.logger.warning("⚠️ 異步更新器工作線程已停止")
            return False

        # 檢查隊列是否過滿
        queue_size = self.async_updater.update_queue.qsize()
        if queue_size > 500:  # 隊列超過一半容量
            self.logger.warning(f"⚠️ 異步更新器隊列過滿: {queue_size}/1000")
            return False

        return True

    def restart_async_updater_if_needed(self):
        """如果需要，重新啟動異步更新器"""
        if not self.check_async_updater_health():
            self.logger.info("🔄 重新啟動異步更新器...")
            try:
                # 停止舊的更新器
                if hasattr(self, 'async_updater'):
                    self.async_updater.stop()

                # 創建新的更新器
                from async_db_updater import AsyncDatabaseUpdater
                self.async_updater = AsyncDatabaseUpdater(self.db_manager, console_enabled=True)
                self.async_updater.start()

                self.logger.info("✅ 異步更新器重新啟動成功")
                return True
            except Exception as e:
                self.logger.error(f"❌ 異步更新器重新啟動失敗: {e}")
                self.async_update_enabled = False  # 禁用異步更新
                return False
        return True

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
