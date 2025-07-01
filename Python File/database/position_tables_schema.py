#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部位管理資料庫表格結構定義
提供SQL語句和資料模型定義
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)

# =====================================================
# 枚舉定義
# =====================================================

class PositionStatus(Enum):
    """部位狀態"""
    ACTIVE = "ACTIVE"
    EXITED = "EXITED"
    CANCELLED = "CANCELLED"

class PositionType(Enum):
    """部位類型"""
    LONG = "LONG"
    SHORT = "SHORT"

class ExitReason(Enum):
    """出場原因"""
    TRAILING_STOP = "TRAILING_STOP"
    PROTECTIVE_STOP = "PROTECTIVE_STOP"
    RANGE_STOP = "RANGE_STOP"
    EOD_CLOSE = "EOD_CLOSE"
    MANUAL_CLOSE = "MANUAL_CLOSE"

class AdjustmentReason(Enum):
    """停損調整原因"""
    INITIAL = "INITIAL"
    TRAILING = "TRAILING"
    PROTECTIVE = "PROTECTIVE"
    MANUAL = "MANUAL"

class SessionStatus(Enum):
    """交易會話狀態"""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

# =====================================================
# SQL語句定義
# =====================================================

class PositionTableSQL:
    """部位管理表格SQL語句"""
    
    # 創建表格
    CREATE_POSITIONS_TABLE = '''
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            date TEXT NOT NULL,
            lot_id INTEGER NOT NULL,
            strategy_name TEXT DEFAULT '開盤區間突破策略',
            position_type TEXT NOT NULL,
            entry_price REAL NOT NULL,
            entry_time TEXT NOT NULL,
            entry_datetime TEXT NOT NULL,
            range_high REAL NOT NULL,
            range_low REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            current_stop_loss REAL,
            peak_price REAL,
            trailing_activated BOOLEAN DEFAULT FALSE,
            exit_price REAL,
            exit_time TEXT,
            exit_datetime TEXT,
            exit_reason TEXT,
            realized_pnl REAL DEFAULT 0,
            unrealized_pnl REAL DEFAULT 0,
            lot_rule_config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, lot_id)
        )
    '''
    
    CREATE_STOP_LOSS_ADJUSTMENTS_TABLE = '''
        CREATE TABLE IF NOT EXISTS stop_loss_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            lot_id INTEGER NOT NULL,
            old_stop_loss REAL,
            new_stop_loss REAL NOT NULL,
            adjustment_reason TEXT NOT NULL,
            trigger_price REAL,
            trigger_time TEXT NOT NULL,
            trigger_datetime TEXT NOT NULL,
            peak_price_at_adjustment REAL,
            trailing_activation_points REAL,
            trailing_pullback_ratio REAL,
            cumulative_pnl_before REAL,
            protection_multiplier REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
        )
    '''
    
    CREATE_POSITION_SNAPSHOTS_TABLE = '''
        CREATE TABLE IF NOT EXISTS position_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            lot_id INTEGER NOT NULL,
            snapshot_time TEXT NOT NULL,
            snapshot_datetime TEXT NOT NULL,
            current_price REAL NOT NULL,
            peak_price REAL NOT NULL,
            stop_loss_price REAL,
            status TEXT NOT NULL,
            trailing_activated BOOLEAN,
            unrealized_pnl REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
        )
    '''
    
    CREATE_TRADING_SESSIONS_TABLE = '''
        CREATE TABLE IF NOT EXISTS trading_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL UNIQUE,
            date TEXT NOT NULL,
            strategy_name TEXT NOT NULL,
            strategy_config TEXT,
            total_lots INTEGER NOT NULL,
            range_high REAL,
            range_low REAL,
            range_calculated_time TEXT,
            signal_type TEXT,
            signal_price REAL,
            signal_time TEXT,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            total_realized_pnl REAL DEFAULT 0,
            total_unrealized_pnl REAL DEFAULT 0,
            active_positions INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
    
    # 創建索引
    CREATE_INDEXES = [
        'CREATE INDEX IF NOT EXISTS idx_positions_session_date ON positions(session_id, date)',
        'CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)',
        'CREATE INDEX IF NOT EXISTS idx_positions_date_status ON positions(date, status)',
        'CREATE INDEX IF NOT EXISTS idx_positions_lot_id ON positions(lot_id)',
        'CREATE INDEX IF NOT EXISTS idx_stop_loss_position_id ON stop_loss_adjustments(position_id)',
        'CREATE INDEX IF NOT EXISTS idx_stop_loss_session_lot ON stop_loss_adjustments(session_id, lot_id)',
        'CREATE INDEX IF NOT EXISTS idx_stop_loss_reason ON stop_loss_adjustments(adjustment_reason)',
        'CREATE INDEX IF NOT EXISTS idx_stop_loss_datetime ON stop_loss_adjustments(trigger_datetime)',
        'CREATE INDEX IF NOT EXISTS idx_snapshots_position_id ON position_snapshots(position_id)',
        'CREATE INDEX IF NOT EXISTS idx_snapshots_datetime ON position_snapshots(snapshot_datetime)',
        'CREATE INDEX IF NOT EXISTS idx_sessions_date ON trading_sessions(date)',
        'CREATE INDEX IF NOT EXISTS idx_sessions_status ON trading_sessions(status)'
    ]
    
    # 創建觸發器
    CREATE_TRIGGERS = [
        '''
        CREATE TRIGGER IF NOT EXISTS update_positions_timestamp 
            AFTER UPDATE ON positions
            FOR EACH ROW
        BEGIN
            UPDATE positions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        ''',
        '''
        CREATE TRIGGER IF NOT EXISTS update_sessions_timestamp 
            AFTER UPDATE ON trading_sessions
            FOR EACH ROW
        BEGIN
            UPDATE trading_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
        ''',
        '''
        CREATE TRIGGER IF NOT EXISTS update_session_stats_on_position_change
            AFTER UPDATE OF status, realized_pnl ON positions
            FOR EACH ROW
        BEGIN
            UPDATE trading_sessions 
            SET 
                total_realized_pnl = (
                    SELECT COALESCE(SUM(realized_pnl), 0) 
                    FROM positions 
                    WHERE session_id = NEW.session_id AND status = 'EXITED'
                ),
                active_positions = (
                    SELECT COUNT(*) 
                    FROM positions 
                    WHERE session_id = NEW.session_id AND status = 'ACTIVE'
                )
            WHERE session_id = NEW.session_id;
        END
        '''
    ]
    
    # 插入語句
    INSERT_POSITION = '''
        INSERT INTO positions (
            session_id, date, lot_id, strategy_name, position_type,
            entry_price, entry_time, entry_datetime, range_high, range_low,
            current_stop_loss, peak_price, lot_rule_config
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    INSERT_STOP_LOSS_ADJUSTMENT = '''
        INSERT INTO stop_loss_adjustments (
            position_id, session_id, lot_id, old_stop_loss, new_stop_loss,
            adjustment_reason, trigger_price, trigger_time, trigger_datetime,
            peak_price_at_adjustment, trailing_activation_points, trailing_pullback_ratio,
            cumulative_pnl_before, protection_multiplier, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    INSERT_POSITION_SNAPSHOT = '''
        INSERT INTO position_snapshots (
            position_id, session_id, lot_id, snapshot_time, snapshot_datetime,
            current_price, peak_price, stop_loss_price, status,
            trailing_activated, unrealized_pnl
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    INSERT_TRADING_SESSION = '''
        INSERT INTO trading_sessions (
            session_id, date, strategy_name, strategy_config, total_lots,
            range_high, range_low, range_calculated_time, signal_type,
            signal_price, signal_time
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    
    # 查詢語句
    SELECT_ACTIVE_POSITIONS = '''
        SELECT * FROM positions 
        WHERE date = ? AND status = 'ACTIVE'
        ORDER BY lot_id
    '''
    
    SELECT_POSITION_BY_SESSION_LOT = '''
        SELECT * FROM positions 
        WHERE session_id = ? AND lot_id = ?
    '''
    
    SELECT_STOP_LOSS_HISTORY = '''
        SELECT * FROM stop_loss_adjustments 
        WHERE position_id = ? 
        ORDER BY trigger_datetime
    '''
    
    SELECT_SESSION_STATS = '''
        SELECT 
            session_id, total_lots, active_positions,
            total_realized_pnl, total_unrealized_pnl,
            (total_realized_pnl / total_lots) as avg_pnl_per_lot
        FROM trading_sessions 
        WHERE date = ?
    '''
    
    # 更新語句
    UPDATE_POSITION_STATUS = '''
        UPDATE positions 
        SET status = ?, exit_price = ?, exit_time = ?, 
            exit_datetime = ?, exit_reason = ?, realized_pnl = ?
        WHERE id = ?
    '''
    
    UPDATE_POSITION_STOP_LOSS = '''
        UPDATE positions 
        SET current_stop_loss = ?, peak_price = ?, 
            trailing_activated = ?, unrealized_pnl = ?
        WHERE id = ?
    '''

# =====================================================
# 資料模型定義
# =====================================================

@dataclass
class PositionRecord:
    """部位記錄資料模型"""
    session_id: str
    date: str
    lot_id: int
    strategy_name: str
    position_type: PositionType
    entry_price: float
    entry_time: str
    entry_datetime: str
    range_high: float
    range_low: float
    status: PositionStatus = PositionStatus.ACTIVE
    current_stop_loss: Optional[float] = None
    peak_price: Optional[float] = None
    trailing_activated: bool = False
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    exit_datetime: Optional[str] = None
    exit_reason: Optional[ExitReason] = None
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    lot_rule_config: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'session_id': self.session_id,
            'date': self.date,
            'lot_id': self.lot_id,
            'strategy_name': self.strategy_name,
            'position_type': self.position_type.value,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time,
            'entry_datetime': self.entry_datetime,
            'range_high': self.range_high,
            'range_low': self.range_low,
            'status': self.status.value,
            'current_stop_loss': self.current_stop_loss,
            'peak_price': self.peak_price,
            'trailing_activated': self.trailing_activated,
            'exit_price': self.exit_price,
            'exit_time': self.exit_time,
            'exit_datetime': self.exit_datetime,
            'exit_reason': self.exit_reason.value if self.exit_reason else None,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'lot_rule_config': self.lot_rule_config
        }

@dataclass
class StopLossAdjustmentRecord:
    """停損調整記錄資料模型"""
    position_id: int
    session_id: str
    lot_id: int
    new_stop_loss: float
    adjustment_reason: AdjustmentReason
    trigger_time: str
    trigger_datetime: str
    old_stop_loss: Optional[float] = None
    trigger_price: Optional[float] = None
    peak_price_at_adjustment: Optional[float] = None
    trailing_activation_points: Optional[float] = None
    trailing_pullback_ratio: Optional[float] = None
    cumulative_pnl_before: Optional[float] = None
    protection_multiplier: Optional[float] = None
    notes: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[str] = None

def generate_session_id() -> str:
    """生成交易會話ID"""
    now = datetime.now()
    return now.strftime("%Y%m%d_%H%M%S")

def validate_position_data(position: PositionRecord) -> bool:
    """驗證部位資料的完整性"""
    try:
        # 基本欄位檢查
        if not all([
            position.session_id,
            position.date,
            position.lot_id > 0,
            position.strategy_name,
            position.position_type,
            position.entry_price > 0,
            position.entry_time,
            position.entry_datetime,
            position.range_high > 0,
            position.range_low > 0
        ]):
            return False
        
        # 邏輯檢查
        if position.range_high <= position.range_low:
            return False
        
        if position.position_type == PositionType.LONG:
            if position.current_stop_loss and position.current_stop_loss >= position.entry_price:
                return False
        else:  # SHORT
            if position.current_stop_loss and position.current_stop_loss <= position.entry_price:
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"驗證部位資料時發生錯誤: {e}")
        return False

if __name__ == "__main__":
    # 測試資料模型
    print("🧪 測試部位管理資料模型")
    
    # 創建測試部位記錄
    position = PositionRecord(
        session_id="20250630_084815",
        date="2025-06-30",
        lot_id=1,
        strategy_name="開盤區間突破策略",
        position_type=PositionType.LONG,
        entry_price=22014.0,
        entry_time="08:48:15",
        entry_datetime="2025-06-30 08:48:15",
        range_high=22010.0,
        range_low=21998.0,
        current_stop_loss=21998.0,
        peak_price=22014.0,
        lot_rule_config='{"trailing_activation": 15, "trailing_pullback": 0.20}'
    )
    
    # 驗證資料
    is_valid = validate_position_data(position)
    print(f"資料驗證結果: {is_valid}")
    
    # 轉換為字典
    position_dict = position.to_dict()
    print(f"部位資料: {position_dict}")
    
    # 生成會話ID
    session_id = generate_session_id()
    print(f"會話ID: {session_id}")
    
    print("✅ 資料模型測試完成")
