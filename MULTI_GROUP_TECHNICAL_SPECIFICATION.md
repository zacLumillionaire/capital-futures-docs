# 🔧 多組多口策略系統技術規格

## 📋 **技術架構詳細規格**

### **1. 資料庫設計規格**

#### **表結構定義**
```sql
-- 策略組主表
CREATE TABLE strategy_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,                    -- 交易日期 YYYY-MM-DD
    group_id INTEGER NOT NULL,             -- 組別編號 (1,2,3...)
    direction TEXT NOT NULL,               -- 方向 LONG/SHORT
    entry_signal_time TEXT NOT NULL,       -- 信號時間 HH:MM:SS
    range_high REAL,                       -- 區間高點
    range_low REAL,                        -- 區間低點
    total_lots INTEGER NOT NULL,           -- 該組總口數
    status TEXT DEFAULT 'WAITING',         -- 狀態: WAITING/ACTIVE/COMPLETED/CANCELLED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引和約束
    UNIQUE(date, group_id),
    CHECK(direction IN ('LONG', 'SHORT')),
    CHECK(status IN ('WAITING', 'ACTIVE', 'COMPLETED', 'CANCELLED')),
    CHECK(total_lots BETWEEN 1 AND 3)
);

-- 部位記錄詳細表
CREATE TABLE position_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    lot_id INTEGER NOT NULL,               -- 組內編號 (1,2,3)
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,             -- 實際進場價格
    entry_time TEXT NOT NULL,              -- 實際進場時間
    exit_price REAL,                       -- 出場價格
    exit_time TEXT,                        -- 出場時間
    exit_reason TEXT,                      -- 出場原因
    pnl REAL,                             -- 損益點數
    pnl_amount REAL,                      -- 損益金額 (點數×50)
    rule_config TEXT,                     -- JSON格式規則配置
    status TEXT DEFAULT 'ACTIVE',         -- ACTIVE/EXITED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外鍵和約束
    FOREIGN KEY (group_id) REFERENCES strategy_groups(id),
    CHECK(direction IN ('LONG', 'SHORT')),
    CHECK(status IN ('ACTIVE', 'EXITED')),
    CHECK(lot_id BETWEEN 1 AND 3),
    CHECK(exit_reason IN ('移動停利', '保護性停損', '初始停損', '手動出場') OR exit_reason IS NULL)
);

-- 風險管理狀態表
CREATE TABLE risk_management_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,
    peak_price REAL NOT NULL,              -- 峰值價格
    current_stop_loss REAL,                -- 當前停損價
    trailing_activated BOOLEAN DEFAULT FALSE,  -- 移動停利是否啟動
    protection_activated BOOLEAN DEFAULT FALSE, -- 保護性停損是否啟動
    last_update_time TEXT NOT NULL,        -- 最後更新時間
    update_reason TEXT,                    -- 更新原因
    previous_stop_loss REAL,               -- 前一次停損價
    
    -- 外鍵和約束
    FOREIGN KEY (position_id) REFERENCES position_records(id),
    CHECK(update_reason IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化') OR update_reason IS NULL)
);

-- 每日策略統計表
CREATE TABLE daily_strategy_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL UNIQUE,
    total_groups INTEGER DEFAULT 0,        -- 總組數
    completed_groups INTEGER DEFAULT 0,    -- 完成組數
    total_positions INTEGER DEFAULT 0,     -- 總部位數
    exited_positions INTEGER DEFAULT 0,    -- 已出場部位數
    total_pnl REAL DEFAULT 0,             -- 總損益點數
    total_pnl_amount REAL DEFAULT 0,      -- 總損益金額
    win_rate REAL DEFAULT 0,              -- 勝率
    avg_pnl REAL DEFAULT 0,               -- 平均損益
    max_profit REAL DEFAULT 0,            -- 最大獲利
    max_loss REAL DEFAULT 0,              -- 最大虧損
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **索引設計**
```sql
-- 性能優化索引
CREATE INDEX idx_strategy_groups_date_status ON strategy_groups(date, status);
CREATE INDEX idx_position_records_group_status ON position_records(group_id, status);
CREATE INDEX idx_position_records_date_direction ON position_records(
    (SELECT date FROM strategy_groups WHERE id = group_id), direction
);
CREATE INDEX idx_risk_states_position_update ON risk_management_states(position_id, last_update_time);
```

### **2. 核心類別設計**

#### **配置數據類**
```python
from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional
from enum import Enum, auto

class StopLossType(Enum):
    RANGE_BOUNDARY = auto()    # 區間邊界停損
    FIXED_POINTS = auto()      # 固定點數停損

class PositionStatus(Enum):
    ACTIVE = "ACTIVE"
    EXITED = "EXITED"

class GroupStatus(Enum):
    WAITING = "WAITING"        # 等待進場
    ACTIVE = "ACTIVE"          # 有活躍部位
    COMPLETED = "COMPLETED"    # 全部出場
    CANCELLED = "CANCELLED"    # 已取消

@dataclass
class LotRule:
    """單口風險管理規則"""
    lot_id: int                                    # 口數編號
    use_trailing_stop: bool = True                 # 使用移動停利
    trailing_activation: Optional[Decimal] = None  # 啟動點數
    trailing_pullback: Optional[Decimal] = None    # 回撤比例
    protective_stop_multiplier: Optional[Decimal] = None  # 保護倍數
    fixed_tp_points: Optional[Decimal] = None      # 固定停利點數
    
    def to_json(self) -> str:
        """轉換為JSON字符串"""
        import json
        return json.dumps({
            'lot_id': self.lot_id,
            'use_trailing_stop': self.use_trailing_stop,
            'trailing_activation': float(self.trailing_activation) if self.trailing_activation else None,
            'trailing_pullback': float(self.trailing_pullback) if self.trailing_pullback else None,
            'protective_stop_multiplier': float(self.protective_stop_multiplier) if self.protective_stop_multiplier else None,
            'fixed_tp_points': float(self.fixed_tp_points) if self.fixed_tp_points else None
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LotRule':
        """從JSON字符串創建"""
        import json
        data = json.loads(json_str)
        return cls(
            lot_id=data['lot_id'],
            use_trailing_stop=data['use_trailing_stop'],
            trailing_activation=Decimal(str(data['trailing_activation'])) if data['trailing_activation'] else None,
            trailing_pullback=Decimal(str(data['trailing_pullback'])) if data['trailing_pullback'] else None,
            protective_stop_multiplier=Decimal(str(data['protective_stop_multiplier'])) if data['protective_stop_multiplier'] else None,
            fixed_tp_points=Decimal(str(data['fixed_tp_points'])) if data['fixed_tp_points'] else None
        )

@dataclass
class StrategyGroupConfig:
    """策略組配置"""
    group_id: int
    lots_per_group: int
    lot_rules: List[LotRule]
    is_active: bool = True
    entry_price: Optional[Decimal] = None
    entry_time: Optional[str] = None
    status: GroupStatus = GroupStatus.WAITING

@dataclass
class MultiGroupStrategyConfig:
    """多組策略總配置"""
    total_groups: int                              # 總組數 (1-5)
    lots_per_group: int                           # 每組口數 (1-3)
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    groups: List[StrategyGroupConfig] = field(default_factory=list)
    max_daily_entries: int = 1                    # 每日最大進場次數
    
    def __post_init__(self):
        """初始化後處理"""
        if not self.groups:
            self.groups = self._create_default_groups()
    
    def _create_default_groups(self) -> List[StrategyGroupConfig]:
        """創建預設組配置"""
        groups = []
        for group_id in range(1, self.total_groups + 1):
            lot_rules = self._create_default_lot_rules()
            groups.append(StrategyGroupConfig(
                group_id=group_id,
                lots_per_group=self.lots_per_group,
                lot_rules=lot_rules
            ))
        return groups
    
    def _create_default_lot_rules(self) -> List[LotRule]:
        """創建預設口數規則"""
        default_rules = [
            # 第1口：快速移動停利
            LotRule(
                lot_id=1,
                use_trailing_stop=True,
                trailing_activation=Decimal('15'),
                trailing_pullback=Decimal('0.20')
            ),
            # 第2口：中等移動停利 + 保護
            LotRule(
                lot_id=2,
                use_trailing_stop=True,
                trailing_activation=Decimal('40'),
                trailing_pullback=Decimal('0.20'),
                protective_stop_multiplier=Decimal('2.0')
            ),
            # 第3口：較大移動停利 + 保護
            LotRule(
                lot_id=3,
                use_trailing_stop=True,
                trailing_activation=Decimal('65'),
                trailing_pullback=Decimal('0.20'),
                protective_stop_multiplier=Decimal('2.0')
            )
        ]
        
        return default_rules[:self.lots_per_group]
```

### **3. 核心業務邏輯類**

#### **多組部位管理器**
```python
class MultiGroupPositionManager:
    """多組部位管理器 - 核心業務邏輯控制器"""
    
    def __init__(self, db_manager, strategy_config: MultiGroupStrategyConfig):
        self.db_manager = db_manager
        self.strategy_config = strategy_config
        self.active_groups = {}  # {group_id: GroupState}
        self.risk_engine = RiskManagementEngine(db_manager)
        
        # 初始化日誌
        self.logger = self._setup_logger()
    
    def create_entry_signal(self, direction: str, signal_time: str, 
                           range_high: float, range_low: float) -> List[int]:
        """創建進場信號，返回創建的組ID列表"""
        try:
            created_groups = []
            current_date = datetime.now().strftime("%Y-%m-%d")
            
            for group_config in self.strategy_config.groups:
                if group_config.is_active:
                    group_id = self.db_manager.create_strategy_group(
                        date=current_date,
                        group_id=group_config.group_id,
                        direction=direction,
                        signal_time=signal_time,
                        range_high=range_high,
                        range_low=range_low,
                        total_lots=group_config.lots_per_group
                    )
                    
                    created_groups.append(group_id)
                    group_config.status = GroupStatus.WAITING
                    
                    self.logger.info(f"創建策略組 {group_config.group_id}: {direction} 信號 @ {signal_time}")
            
            return created_groups
            
        except Exception as e:
            self.logger.error(f"創建進場信號失敗: {e}")
            return []
    
    def execute_group_entry(self, group_id: int, actual_price: float, 
                           actual_time: str) -> bool:
        """執行特定組的進場"""
        try:
            group_config = self._get_group_config(group_id)
            if not group_config or group_config.status != GroupStatus.WAITING:
                return False
            
            # 為該組的每口創建部位記錄
            position_ids = []
            for lot_rule in group_config.lot_rules:
                position_id = self.db_manager.create_position_record(
                    group_id=group_id,
                    lot_id=lot_rule.lot_id,
                    direction=self._get_group_direction(group_id),
                    entry_price=actual_price,
                    entry_time=actual_time,
                    rule_config=lot_rule.to_json()
                )
                
                # 初始化風險管理狀態
                self.risk_engine.initialize_risk_state(
                    position_id, actual_price, actual_time
                )
                
                position_ids.append(position_id)
            
            # 更新組狀態
            group_config.status = GroupStatus.ACTIVE
            group_config.entry_price = Decimal(str(actual_price))
            group_config.entry_time = actual_time
            
            self.active_groups[group_id] = {
                'config': group_config,
                'position_ids': position_ids,
                'entry_price': actual_price,
                'entry_time': actual_time
            }
            
            self.logger.info(f"組 {group_id} 進場完成: {len(position_ids)}口 @ {actual_price}")
            return True
            
        except Exception as e:
            self.logger.error(f"組 {group_id} 進場失敗: {e}")
            return False
```

### **4. 風險管理引擎規格**

#### **風險管理核心邏輯**
```python
class RiskManagementEngine:
    """風險管理引擎 - 移植OrderTester.py的精密邏輯"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.logger = self._setup_logger()
    
    def check_all_exit_conditions(self, current_price: float, current_time: str):
        """檢查所有活躍部位的出場條件"""
        try:
            active_positions = self.db_manager.get_all_active_positions()
            
            for position in active_positions:
                # 檢查初始停損 (最高優先級)
                if self._check_initial_stop_loss(position, current_price):
                    self._execute_initial_stop_loss(position, current_price, current_time)
                    continue
                
                # 檢查移動停利條件
                if self._check_trailing_stop_conditions(position, current_price, current_time):
                    continue
                
                # 檢查保護性停損
                if self._check_protective_stop_loss(position, current_price, current_time):
                    continue
                
                # 更新峰值價格
                self._update_peak_price(position, current_price, current_time)
                
        except Exception as e:
            self.logger.error(f"檢查出場條件失敗: {e}")
    
    def _check_initial_stop_loss(self, position: dict, current_price: float) -> bool:
        """檢查初始停損條件"""
        try:
            # 獲取區間邊界停損價格
            group_info = self.db_manager.get_strategy_group_info(position['group_id'])
            
            if position['direction'] == 'LONG':
                stop_loss_price = group_info['range_low']
                return current_price <= stop_loss_price
            else:  # SHORT
                stop_loss_price = group_info['range_high']
                return current_price >= stop_loss_price
                
        except Exception as e:
            self.logger.error(f"檢查初始停損失敗: {e}")
            return False
```

---

**📝 文檔建立時間**: 2025-07-04  
**🎯 文檔狀態**: 技術規格完成  
**📊 文檔版本**: v1.0
