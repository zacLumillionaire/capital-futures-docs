#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部位持久化適配器
包裝現有的LiveTradingPositionManager，新增SQLite持久化功能
使用適配器模式，確保不修改原有邏輯
"""

import logging
import json
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from decimal import Decimal

# 導入現有的部位管理器
try:
    from test_ui_improvements import LiveTradingPositionManager
    LIVE_TRADING_AVAILABLE = True
except ImportError:
    LIVE_TRADING_AVAILABLE = False
    logging.warning("LiveTradingPositionManager不可用，部分功能將受限")

# 導入資料庫管理器
try:
    from database.sqlite_manager import db_manager
    from database.position_tables_schema import (
        PositionType, PositionStatus, AdjustmentReason, ExitReason,
        generate_session_id
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logging.warning("資料庫管理模組不可用，持久化功能將不可用")

# 導入策略配置
try:
    from strategy.strategy_config import StrategyConfig
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    logging.warning("策略配置模組不可用")

logger = logging.getLogger(__name__)

class PositionPersistenceAdapter:
    """
    部位持久化適配器
    
    使用適配器模式包裝LiveTradingPositionManager，
    新增SQLite持久化功能但不修改原有邏輯
    """
    
    def __init__(self, config: 'StrategyConfig', order_api=None, 
                 range_start_time=(8, 46), enable_persistence: bool = False):
        """
        初始化適配器
        
        Args:
            config: 策略配置
            order_api: 下單API
            range_start_time: 區間開始時間
            enable_persistence: 是否啟用持久化功能
        """
        self.enable_persistence = enable_persistence and DATABASE_AVAILABLE
        self.config = config
        
        # 創建原始的LiveTradingPositionManager
        if LIVE_TRADING_AVAILABLE:
            self.original_manager = LiveTradingPositionManager(
                config, order_api, range_start_time
            )
        else:
            self.original_manager = None
            logger.error("❌ LiveTradingPositionManager不可用")
        
        # 持久化相關屬性
        self.session_id = None
        self.trading_session_created = False
        self.position_ids = {}  # lot_id -> position_id 映射
        
        # 檢查持久化功能狀態
        if self.enable_persistence:
            self._check_persistence_status()
        
        logger.info(f"🔧 部位持久化適配器初始化 - 持久化: {'✅' if self.enable_persistence else '❌'}")
    
    def _check_persistence_status(self) -> bool:
        """檢查持久化功能狀態"""
        if not DATABASE_AVAILABLE:
            logger.warning("⚠️  資料庫模組不可用，持久化功能關閉")
            self.enable_persistence = False
            return False
        
        # 檢查資料庫表格是否存在
        status = db_manager.get_position_management_status()
        if not status.get("tables_exist", False):
            logger.warning("⚠️  部位管理表格不存在，持久化功能關閉")
            self.enable_persistence = False
            return False
        
        logger.info("✅ 持久化功能檢查通過")
        return True
    
    def _create_trading_session(self) -> bool:
        """創建交易會話"""
        if not self.enable_persistence or self.trading_session_created:
            return True
        
        try:
            # 生成會話ID
            self.session_id = generate_session_id()
            today = date.today().isoformat()
            
            # 準備策略配置
            strategy_config = {
                "trade_size_in_lots": self.config.trade_size_in_lots,
                "stop_loss_type": self.config.stop_loss_type.value if hasattr(self.config.stop_loss_type, 'value') else str(self.config.stop_loss_type),
                "lot_rules": [
                    {
                        "trailing_activation": rule.trailing_activation,
                        "trailing_pullback": rule.trailing_pullback,
                        "protection_multiplier": rule.protection_multiplier,
                        "use_trailing_stop": rule.use_trailing_stop
                    }
                    for rule in self.config.lot_rules
                ]
            }
            
            # 創建交易會話
            success = db_manager.create_trading_session(
                session_id=self.session_id,
                date_str=today,
                strategy_name="開盤區間突破策略",
                total_lots=self.config.trade_size_in_lots,
                strategy_config=strategy_config
            )
            
            if success:
                self.trading_session_created = True
                logger.info(f"✅ 交易會話已創建: {self.session_id}")
            else:
                logger.error("❌ 交易會話創建失敗")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 創建交易會話時發生錯誤: {e}")
            return False
    
    def _update_session_range_info(self, range_high: float, range_low: float):
        """更新會話的區間資訊"""
        if not self.enable_persistence or not self.session_id:
            return
        
        try:
            # 更新交易會話的區間資訊
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE trading_sessions 
                    SET range_high = ?, range_low = ?, range_calculated_time = ?
                    WHERE session_id = ?
                """, (range_high, range_low, datetime.now().strftime('%H:%M:%S'), self.session_id))
                conn.commit()
            
            logger.info(f"✅ 會話區間資訊已更新: {range_low} - {range_high}")
            
        except Exception as e:
            logger.error(f"❌ 更新會話區間資訊失敗: {e}")
    
    def _persist_position_entry(self, lot_info: Dict, direction: str, entry_price: float, 
                               entry_time: datetime, range_high: float, range_low: float) -> Optional[int]:
        """持久化部位進場資訊"""
        if not self.enable_persistence:
            return None
        
        try:
            # 確保交易會話已創建
            if not self.trading_session_created:
                self._create_trading_session()
            
            # 準備口數規則配置
            rule = lot_info.get('rule')
            lot_rule_config = None
            if rule:
                lot_rule_config = {
                    "trailing_activation": getattr(rule, 'trailing_activation', None),
                    "trailing_pullback": getattr(rule, 'trailing_pullback', None),
                    "protection_multiplier": getattr(rule, 'protection_multiplier', None),
                    "use_trailing_stop": getattr(rule, 'use_trailing_stop', True)
                }
            
            # 創建部位記錄
            position_id = db_manager.create_position_with_initial_stop(
                session_id=self.session_id,
                date_str=date.today().isoformat(),
                lot_id=lot_info['id'],
                strategy_name="開盤區間突破策略",
                position_type=direction,
                entry_price=entry_price,
                entry_time=entry_time.strftime('%H:%M:%S'),
                entry_datetime=entry_time.isoformat(),
                range_high=range_high,
                range_low=range_low,
                initial_stop_loss=float(lot_info.get('stop_loss', 0)),
                lot_rule_config=lot_rule_config
            )
            
            if position_id:
                # 記錄部位ID映射
                self.position_ids[lot_info['id']] = position_id
                logger.info(f"✅ 第{lot_info['id']}口部位已持久化 (ID: {position_id})")
            
            return position_id
            
        except Exception as e:
            logger.error(f"❌ 持久化部位進場失敗: {e}")
            return None
    
    def _persist_stop_loss_adjustment(self, lot_id: int, old_stop_loss: Optional[float], 
                                    new_stop_loss: float, reason: str, trigger_price: Optional[float] = None):
        """持久化停損調整記錄"""
        if not self.enable_persistence:
            return
        
        position_id = self.position_ids.get(lot_id)
        if not position_id:
            return
        
        try:
            # 映射調整原因
            adjustment_reason = AdjustmentReason.TRAILING if reason == "trailing" else AdjustmentReason.PROTECTIVE
            
            success = db_manager.record_stop_loss_adjustment(
                position_id=position_id,
                session_id=self.session_id,
                lot_id=lot_id,
                old_stop_loss=old_stop_loss,
                new_stop_loss=new_stop_loss,
                adjustment_reason=adjustment_reason,
                trigger_price=trigger_price,
                notes=f"自動{reason}調整"
            )
            
            if success:
                logger.debug(f"✅ 第{lot_id}口停損調整已記錄: {old_stop_loss} → {new_stop_loss}")
            
        except Exception as e:
            logger.error(f"❌ 記錄停損調整失敗: {e}")
    
    def _persist_position_exit(self, lot_id: int, exit_price: float, exit_reason: str, realized_pnl: float):
        """持久化部位出場資訊"""
        if not self.enable_persistence:
            return
        
        position_id = self.position_ids.get(lot_id)
        if not position_id:
            return
        
        try:
            # 映射出場原因
            exit_reason_enum = ExitReason.TRAILING_STOP
            if exit_reason == "protective":
                exit_reason_enum = ExitReason.PROTECTIVE_STOP
            elif exit_reason == "range":
                exit_reason_enum = ExitReason.RANGE_STOP
            elif exit_reason == "eod":
                exit_reason_enum = ExitReason.EOD_CLOSE
            elif exit_reason == "manual":
                exit_reason_enum = ExitReason.MANUAL_CLOSE
            
            success = db_manager.close_position(
                position_id=position_id,
                exit_price=exit_price,
                exit_time=datetime.now().strftime('%H:%M:%S'),
                exit_datetime=datetime.now().isoformat(),
                exit_reason=exit_reason_enum,
                realized_pnl=realized_pnl
            )
            
            if success:
                logger.info(f"✅ 第{lot_id}口部位出場已記錄: {exit_reason} @{exit_price} 損益:{realized_pnl:+.0f}")
            
        except Exception as e:
            logger.error(f"❌ 記錄部位出場失敗: {e}")
    
    # =====================================================
    # 適配器方法 - 包裝原始管理器的方法
    # =====================================================
    
    def update_price(self, price, timestamp):
        """更新價格並檢查交易信號 (包裝原始方法)"""
        if not self.original_manager:
            return
        
        # 調用原始方法
        self.original_manager.update_price(price, timestamp)
        
        # 持久化相關處理
        if self.enable_persistence:
            # 檢查是否剛完成區間計算
            if (self.original_manager.range_detected and 
                not self.trading_session_created):
                self._create_trading_session()
                self._update_session_range_info(
                    float(self.original_manager.range_high),
                    float(self.original_manager.range_low)
                )
            
            # 檢查是否剛建倉
            if (self.original_manager.position and 
                self.original_manager.lots and 
                not self.position_ids):
                self._persist_all_positions()
    
    def _persist_all_positions(self):
        """持久化所有部位"""
        if not self.original_manager.lots:
            return
        
        for lot in self.original_manager.lots:
            if lot['id'] not in self.position_ids:
                self._persist_position_entry(
                    lot,
                    self.original_manager.position,
                    float(self.original_manager.entry_price),
                    self.original_manager.entry_time,
                    float(self.original_manager.range_high),
                    float(self.original_manager.range_low)
                )

    # =====================================================
    # 屬性代理 - 透明地訪問原始管理器的屬性
    # =====================================================

    @property
    def position(self):
        """當前部位方向"""
        return self.original_manager.position if self.original_manager else None

    @property
    def entry_price(self):
        """進場價格"""
        return self.original_manager.entry_price if self.original_manager else None

    @property
    def entry_time(self):
        """進場時間"""
        return self.original_manager.entry_time if self.original_manager else None

    @property
    def lots(self):
        """各口部位資訊"""
        return self.original_manager.lots if self.original_manager else []

    @property
    def range_high(self):
        """區間高點"""
        return self.original_manager.range_high if self.original_manager else None

    @property
    def range_low(self):
        """區間低點"""
        return self.original_manager.range_low if self.original_manager else None

    @property
    def range_detected(self):
        """是否已檢測到區間"""
        return self.original_manager.range_detected if self.original_manager else False

    @property
    def daily_entry_completed(self):
        """當天是否已完成進場"""
        return self.original_manager.daily_entry_completed if self.original_manager else False

    @property
    def first_breakout_detected(self):
        """是否已檢測到第一次突破"""
        return self.original_manager.first_breakout_detected if self.original_manager else False

    @property
    def breakout_direction(self):
        """突破方向"""
        return self.original_manager.breakout_direction if self.original_manager else None

    # =====================================================
    # 方法代理 - 透明地調用原始管理器的方法
    # =====================================================

    def get_position_summary(self):
        """取得部位摘要"""
        if not self.original_manager:
            return {
                'position': None,
                'entry_price': 0,
                'active_lots': 0,
                'total_pnl': 0,
                'unrealized_pnl': 0,
                'lots_detail': []
            }

        return self.original_manager.get_position_summary()

    def close_all_positions(self, current_price: float, reason: str = "manual"):
        """關閉所有部位"""
        if not self.original_manager or not self.original_manager.lots:
            return 0

        # 記錄關閉前的部位資訊
        lots_to_close = [lot for lot in self.original_manager.lots if lot['status'] == 'active']

        # 手動關閉所有活躍部位 (因為原始管理器沒有close_all_positions方法)
        closed_count = 0
        for lot in lots_to_close:
            # 計算實現損益
            if self.original_manager.position == 'LONG':
                realized_pnl = (current_price - float(self.original_manager.entry_price)) * 50
            else:
                realized_pnl = (float(self.original_manager.entry_price) - current_price) * 50

            # 更新部位狀態
            lot['pnl'] = realized_pnl / 50  # 轉換為每點損益
            lot['status'] = 'exited'

            # 執行出場下單
            self.original_manager.execute_exit_order(lot, current_price, reason)

            # 持久化出場記錄
            if self.enable_persistence:
                self._persist_position_exit(lot['id'], current_price, reason, realized_pnl)

            closed_count += 1

        return closed_count

    def reset_daily_state(self):
        """重置每日狀態"""
        if self.original_manager:
            self.original_manager.reset_daily_state()

        # 重置持久化狀態
        self.session_id = None
        self.trading_session_created = False
        self.position_ids.clear()

        logger.info("🔄 每日狀態已重置")

    def is_after_range_period(self, current_time):
        """檢查是否在區間計算期間之後"""
        if not self.original_manager:
            return False
        return self.original_manager.is_after_range_period(current_time)

    # =====================================================
    # 持久化專用方法
    # =====================================================

    def get_persistence_status(self) -> Dict[str, Any]:
        """取得持久化狀態資訊"""
        status = {
            "persistence_enabled": self.enable_persistence,
            "database_available": DATABASE_AVAILABLE,
            "session_created": self.trading_session_created,
            "session_id": self.session_id,
            "position_count": len(self.position_ids),
            "position_ids": dict(self.position_ids)
        }

        if DATABASE_AVAILABLE:
            db_status = db_manager.get_position_management_status()
            status.update({
                "tables_exist": db_status.get("tables_exist", False),
                "today_active_positions": db_status.get("today_active_positions", 0)
            })

        return status

    def get_active_positions_from_db(self) -> List[Dict]:
        """從資料庫取得活躍部位"""
        if not self.enable_persistence:
            return []

        try:
            return db_manager.get_active_positions()
        except Exception as e:
            logger.error(f"❌ 從資料庫查詢活躍部位失敗: {e}")
            return []

    def get_stop_loss_history(self, lot_id: int) -> List[Dict]:
        """取得指定口數的停損調整歷史"""
        if not self.enable_persistence:
            return []

        position_id = self.position_ids.get(lot_id)
        if not position_id:
            return []

        try:
            return db_manager.get_stop_loss_history(position_id)
        except Exception as e:
            logger.error(f"❌ 查詢停損歷史失敗: {e}")
            return []

    def create_position_snapshot(self, current_price: float):
        """創建當前部位快照"""
        if not self.enable_persistence or not self.original_manager or not self.session_id:
            return

        try:
            for lot in self.original_manager.lots:
                if lot['status'] == 'active':
                    position_id = self.position_ids.get(lot['id'])
                    if position_id:
                        # 計算未實現損益
                        if self.original_manager.position == 'LONG':
                            unrealized_pnl = (current_price - float(self.original_manager.entry_price)) * 50
                        else:
                            unrealized_pnl = (float(self.original_manager.entry_price) - current_price) * 50

                        db_manager.create_position_snapshot(
                            position_id=position_id,
                            session_id=self.session_id,
                            lot_id=lot['id'],
                            current_price=current_price,
                            peak_price=float(lot.get('peak_price', current_price)),
                            stop_loss_price=float(lot.get('stop_loss', 0)),
                            status='ACTIVE',
                            trailing_activated=lot.get('trailing_on', False),
                            unrealized_pnl=unrealized_pnl
                        )

            logger.debug(f"✅ 部位快照已創建 @{current_price}")

        except Exception as e:
            logger.error(f"❌ 創建部位快照失敗: {e}")

    def enable_persistence_mode(self) -> bool:
        """啟用持久化模式"""
        if not DATABASE_AVAILABLE:
            logger.warning("⚠️  資料庫不可用，無法啟用持久化")
            return False

        self.enable_persistence = True
        return self._check_persistence_status()

    def disable_persistence_mode(self):
        """關閉持久化模式"""
        self.enable_persistence = False
        logger.info("🔒 持久化模式已關閉")

    # =====================================================
    # 特殊方法 - 支援上下文管理和字串表示
    # =====================================================

    def __str__(self):
        """字串表示"""
        status = "有部位" if self.position else "無部位"
        persistence = "持久化✅" if self.enable_persistence else "持久化❌"
        return f"PositionPersistenceAdapter({status}, {persistence})"

    def __repr__(self):
        """詳細表示"""
        return (f"PositionPersistenceAdapter("
                f"position={self.position}, "
                f"lots={len(self.lots)}, "
                f"persistence={self.enable_persistence}, "
                f"session_id={self.session_id})")

# =====================================================
# 便利函數
# =====================================================

def create_position_manager(config: 'StrategyConfig', order_api=None,
                          range_start_time=(8, 46), enable_persistence: bool = False) -> PositionPersistenceAdapter:
    """
    創建部位管理器的便利函數

    Args:
        config: 策略配置
        order_api: 下單API
        range_start_time: 區間開始時間
        enable_persistence: 是否啟用持久化

    Returns:
        PositionPersistenceAdapter: 部位管理器適配器
    """
    return PositionPersistenceAdapter(
        config=config,
        order_api=order_api,
        range_start_time=range_start_time,
        enable_persistence=enable_persistence
    )

if __name__ == "__main__":
    # 測試適配器功能
    print("🧪 測試部位持久化適配器")

    # 檢查依賴模組
    print(f"LiveTradingPositionManager可用: {LIVE_TRADING_AVAILABLE}")
    print(f"資料庫模組可用: {DATABASE_AVAILABLE}")
    print(f"策略配置可用: {CONFIG_AVAILABLE}")

    if not all([LIVE_TRADING_AVAILABLE, DATABASE_AVAILABLE, CONFIG_AVAILABLE]):
        print("❌ 缺少必要模組，無法完整測試")
    else:
        print("✅ 所有模組可用，適配器準備就緒")

    print("✅ 適配器測試完成")
