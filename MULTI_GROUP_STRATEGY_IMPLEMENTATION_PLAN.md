# 🎯 多組多口策略系統實施計劃

## 📋 **項目概述**

**項目名稱**: 多組多口策略系統  
**開始日期**: 2025-07-04  
**目標**: 實施靈活的多組多口交易策略，支援不同進場價格和完整風險管理

## 🎯 **核心需求分析**

### **業務需求**
1. **靈活組數配置**: 支援1-5組策略組
2. **可變口數配置**: 每組支援1-3口
3. **真實市場適應**: 每口可記錄不同實際進場價格
4. **完整風險管理**: 移植OrderTester.py的精密風險管理機制
5. **資料庫追蹤**: 使用SQLite完整記錄交易過程

### **技術需求**
1. **資料庫設計**: 策略組、部位記錄、風險管理狀態表
2. **多組管理器**: 統一管理多個策略組的生命週期
3. **風險管理引擎**: 每口獨立的停損停利機制
4. **配置界面**: 直觀的多組配置設定
5. **Console化日誌**: 避免GIL問題的日誌系統

## 🏗️ **系統架構設計**

### **1. 數據模型層**

#### **策略配置類**
```python
@dataclass
class LotRule:
    """單口風險管理規則"""
    use_trailing_stop: bool = True
    trailing_activation: Decimal = None      # 移動停利啟動點數
    trailing_pullback: Decimal = None        # 回撤比例 (0.20 = 20%)
    protective_stop_multiplier: Decimal = None  # 保護性停損倍數

@dataclass
class StrategyGroupConfig:
    """策略組配置"""
    group_id: int
    lots_per_group: int                      # 每組口數 (1-3)
    lot_rules: List[LotRule]                # 每口規則
    is_active: bool = True
    entry_price: Decimal = None              # 實際進場價格
    entry_time: str = None

@dataclass
class MultiGroupStrategyConfig:
    """多組策略總配置"""
    total_groups: int                        # 總組數 (1-5)
    lots_per_group: int                      # 每組口數 (1-3)
    groups: List[StrategyGroupConfig]
    max_daily_entries: int = 1
```

#### **資料庫表結構**
```sql
-- 策略組表
CREATE TABLE strategy_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    group_id INTEGER NOT NULL,
    direction TEXT NOT NULL,           -- LONG/SHORT
    entry_signal_time TEXT NOT NULL,   -- 信號產生時間
    range_high REAL,                   -- 區間高點
    range_low REAL,                    -- 區間低點
    status TEXT DEFAULT 'WAITING',     -- WAITING/ACTIVE/COMPLETED/CANCELLED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 部位記錄表
CREATE TABLE position_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    lot_id INTEGER NOT NULL,           -- 組內編號 (1,2,3)
    direction TEXT NOT NULL,
    entry_price REAL NOT NULL,         -- 實際進場價格
    entry_time TEXT NOT NULL,          -- 實際進場時間
    exit_price REAL,
    exit_time TEXT,
    exit_reason TEXT,                  -- 移動停利/保護性停損/初始停損
    pnl REAL,
    rule_config TEXT,                  -- JSON格式規則
    status TEXT DEFAULT 'ACTIVE',      -- ACTIVE/EXITED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES strategy_groups(id)
);

-- 風險管理狀態表
CREATE TABLE risk_management_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id INTEGER NOT NULL,
    peak_price REAL,                   -- 峰值價格追蹤
    current_stop_loss REAL,            -- 當前停損價
    trailing_activated BOOLEAN DEFAULT FALSE,
    protection_activated BOOLEAN DEFAULT FALSE,
    last_update_time TEXT,
    update_reason TEXT,                -- 更新原因
    FOREIGN KEY (position_id) REFERENCES position_records(id)
);
```

### **2. 業務邏輯層**

#### **多組部位管理器**
```python
class MultiGroupPositionManager:
    """多組部位管理器 - 核心業務邏輯"""
    
    def __init__(self, db_manager, strategy_config):
        self.db_manager = db_manager
        self.strategy_config = strategy_config
        self.active_groups = {}  # {group_id: GroupState}
        
    # 核心方法
    def create_entry_signal(self, direction, signal_time, range_high, range_low)
    def execute_group_entry(self, group_id, actual_price, actual_time)
    def check_all_exit_conditions(self, current_price, current_time)
    def update_risk_management_states(self, current_price)
```

#### **風險管理引擎**
```python
class RiskManagementEngine:
    """風險管理引擎 - 移植OrderTester.py邏輯"""
    
    def check_initial_stop_loss(self, positions, current_price)
    def check_trailing_stop_conditions(self, position, current_price)
    def update_protective_stop_loss(self, exited_position, remaining_positions)
    def calculate_position_pnl(self, position, current_price)
```

### **3. 數據訪問層**

#### **資料庫管理器擴展**
```python
class MultiGroupDatabaseManager(SQLiteManager):
    """多組策略專用資料庫管理器"""
    
    def create_strategy_group(self, date, direction, signal_time, range_high, range_low)
    def create_position_record(self, group_id, lot_id, direction, entry_price, entry_time)
    def update_position_exit(self, position_id, exit_price, exit_time, exit_reason, pnl)
    def get_active_positions_by_group(self, group_id)
    def get_daily_strategy_summary(self, date)
```

### **4. 用戶界面層**

#### **多組配置面板**
```python
class MultiGroupConfigPanel:
    """多組策略配置界面"""
    
    def create_basic_config_section(self)      # 基本配置
    def create_group_details_section(self)     # 組別詳細設定
    def create_risk_rules_section(self)        # 風險管理規則
    def create_preview_section(self)           # 配置預覽
```

## 📊 **配置範例**

### **範例1: 保守配置 (1口×2組)**
```yaml
總組數: 2
每組口數: 1
總口數: 2

組1配置:
  - 第1口: 15點啟動移動停利, 20%回撤

組2配置:
  - 第1口: 15點啟動移動停利, 20%回撤

優勢: 風險分散, 兩次進場機會
```

### **範例2: 積極配置 (3口×3組)**
```yaml
總組數: 3
每組口數: 3
總口數: 9

每組配置:
  - 第1口: 15點啟動移動停利, 20%回撤
  - 第2口: 40點啟動移動停利, 20%回撤, 2倍保護
  - 第3口: 65點啟動移動停利, 20%回撤, 2倍保護

優勢: 最大獲利潛力, 三次進場機會
```

### **範例3: 平衡配置 (2口×2組)**
```yaml
總組數: 2
每組口數: 2
總口數: 4

每組配置:
  - 第1口: 15點啟動移動停利, 20%回撤
  - 第2口: 40點啟動移動停利, 20%回撤, 2倍保護

優勢: 平衡風險與獲利
```

## 🔄 **交易流程設計**

### **1. 信號產生階段**
```
08:46-08:47 → 區間計算 → 1分K突破 → 產生信號
↓
創建N個策略組 (根據配置)
↓
等待實際進場機會
```

### **2. 進場執行階段**
```
收到進場信號 → 選擇可用組別 → 記錄實際進場價格
↓
為該組的每口創建部位記錄
↓
初始化風險管理狀態
↓
開始追蹤停損停利
```

### **3. 風險管理階段**
```
每個報價 → 檢查所有活躍部位
↓
更新峰值價格 → 檢查移動停利條件
↓
檢查保護性停損 → 檢查初始停損
↓
執行出場 → 更新下一口保護
```

### **4. 記錄統計階段**
```
部位出場 → 更新資料庫記錄
↓
計算損益 → 更新統計數據
↓
生成交易報告 → Console日誌輸出
```

## 📈 **預期效果**

### **功能效果**
- ✅ 支援1-5組策略組配置
- ✅ 每組支援1-3口獨立管理
- ✅ 完整的風險管理機制
- ✅ 真實市場不同進場價格記錄
- ✅ SQLite資料庫完整追蹤

### **業務效果**
- 🎯 提高策略靈活性
- 🛡️ 分散交易風險
- 📊 完整的交易記錄
- 💰 最大化獲利機會
- 📈 提升策略成功率

## 🚀 **實施階段規劃**

### **階段1: 資料庫基礎建設** (預計1天)
- 設計並創建資料庫表結構
- 實施基礎的資料庫操作方法
- 測試資料庫功能

### **階段2: 核心業務邏輯** (預計2天)
- 實施多組部位管理器
- 移植風險管理引擎
- 實施交易流程控制

### **階段3: 用戶界面開發** (預計1天)
- 創建多組配置面板
- 實施配置預覽功能
- 整合到simple_integrated.py

### **階段4: 整合測試** (預計1天)
- 功能整合測試
- Console化日誌測試
- 完整流程驗證

### **階段5: 優化完善** (預計1天)
- 性能優化
- 錯誤處理完善
- 文檔完善

## 📝 **成功標準**

1. **功能完整性**: 所有配置組合都能正常運作
2. **數據準確性**: 交易記錄和統計數據準確無誤
3. **系統穩定性**: 長時間運行無GIL錯誤
4. **用戶友好性**: 配置界面直觀易用
5. **性能表現**: 多組管理不影響系統性能

---

**📝 文檔建立時間**: 2025-07-04  
**🎯 項目狀態**: 準備開始實施  
**📊 文檔版本**: v1.0
