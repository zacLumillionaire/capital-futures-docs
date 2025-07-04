#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多組部位管理器
統一管理多個策略組的生命週期和風險控制
"""

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

from multi_group_config import (
    MultiGroupStrategyConfig, StrategyGroupConfig, LotRule,
    GroupStatus, PositionStatus, StopLossType
)
from multi_group_database import MultiGroupDatabaseManager

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiGroupPositionManager:
    """多組部位管理器 - 核心業務邏輯控制器"""
    
    def __init__(self, db_manager: MultiGroupDatabaseManager, 
                 strategy_config: MultiGroupStrategyConfig):
        self.db_manager = db_manager
        self.strategy_config = strategy_config
        self.active_groups = {}  # {group_id: GroupState}
        
        # 初始化日誌
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("多組部位管理器初始化完成")
    
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
        """執行特定組的進場"""
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
            
            self.logger.info(f"執行組 {group_info['group_id']} 進場: {group_info['total_lots']}口 @ {actual_price}")
            
            # 為該組的每口創建部位記錄
            position_ids = []
            for lot_rule in group_config.lot_rules:
                position_id = self.db_manager.create_position_record(
                    group_id=group_db_id,
                    lot_id=lot_rule.lot_id,
                    direction=group_info['direction'],
                    entry_price=actual_price,
                    entry_time=actual_time,
                    rule_config=lot_rule.to_json()
                )
                
                # 初始化風險管理狀態
                self.db_manager.create_risk_management_state(
                    position_id=position_id,
                    peak_price=actual_price,
                    current_time=actual_time,
                    update_reason="初始化"
                )
                
                position_ids.append(position_id)
                self.logger.info(f"創建第{lot_rule.lot_id}口部位: ID={position_id}")
            
            # 更新組狀態
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
            
            self.logger.info(f"組 {group_info['group_id']} 進場完成: {len(position_ids)}口")
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
