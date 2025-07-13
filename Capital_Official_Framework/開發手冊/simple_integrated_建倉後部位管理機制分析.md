# simple_integrated.py 建倉後部位管理機制詳細分析

## 📋 概述

本文檔詳細分析 `simple_integrated.py` 策略下單機建倉後的部位管理機制，包括初始平損點計算、移動停利啟動點、移動停利追蹤機制、保護性停損計算、內存計算批次更新等核心技術實現。

## 🛡️ 1. 初始平損點計算

### 1.1 單一策略初始停損設定

**核心函數**: `enter_position_safe(direction, price, time_str)`

```python
def enter_position_safe(self, direction, price, time_str):
    """安全的建倉處理 - 設定初始停損"""
    
    # 記錄部位資訊（隱含停損設定）
    self.current_position = {
        'direction': direction,
        'entry_price': price,
        'entry_time': time_str,
        'quantity': 1,
        'peak_price': price,  # 峰值價格追蹤
        'trailing_activated': False,  # 移動停利是否啟動
        'trailing_activation_points': 15,  # 15點啟動移動停利
        'trailing_pullback_percent': 0.20  # 20%回撤
    }
    
    # 初始停損點隱含在區間邊界中：
    # 多單停損：self.range_low (區間下軌)
    # 空單停損：self.range_high (區間上軌)
```

**停損點計算邏輯**:
- **多單停損**: 使用開盤區間下軌 (`range_low`) 作為固定停損點
- **空單停損**: 使用開盤區間上軌 (`range_high`) 作為固定停損點
- **固定不變**: 初始停損點在建倉後不會調整，直到移動停利啟動

### 1.2 多組策略初始停損設定

**模組**: `RiskManagementEngine`

```python
def _check_initial_stop_loss(self, positions: List[Dict], current_price: float) -> List[Dict]:
    """檢查初始停損條件"""
    
    for position in positions:
        direction = position['direction']
        entry_price = position['entry_price']
        
        # 從組配置中獲取停損設定
        group_config = self._get_group_config(position['group_id'])
        range_high = group_config.get('range_high', 0)
        range_low = group_config.get('range_low', 0)
        
        # 檢查停損觸發
        if direction == 'LONG' and current_price <= range_low:
            return True  # 多單觸發停損
        elif direction == 'SHORT' and current_price >= range_high:
            return True  # 空單觸發停損
            
    return False
```

**多組策略特點**:
- **組別管理**: 每個策略組有獨立的區間設定
- **全組出場**: 初始停損觸發時，整組所有口數同時出場
- **資料庫記錄**: 停損觸發記錄到 `multi_group_strategy.db`

## 🎯 2. 移動停利啟動點計算

### 2.1 啟動條件檢查

**核心函數**: `check_trailing_stop_logic(price, time_str)`

```python
def check_trailing_stop_logic(self, price, time_str):
    """移動停利邏輯檢查"""
    
    direction = self.current_position['direction']
    entry_price = self.current_position['entry_price']
    trailing_activated = self.current_position['trailing_activated']
    activation_points = self.current_position['trailing_activation_points']  # 15點
    
    # 檢查移動停利啟動條件
    if not trailing_activated:
        activation_triggered = False
        
        if direction == "LONG":
            # 多單：價格超過進場價15點時啟動
            activation_triggered = price >= entry_price + activation_points
        else:  # SHORT
            # 空單：價格低於進場價15點時啟動
            activation_triggered = price <= entry_price - activation_points
        
        if activation_triggered:
            self.current_position['trailing_activated'] = True
            self.add_strategy_log(f"🔔 移動停利已啟動！峰值價格: {peak_price:.0f}")
            return
```

**啟動點計算邏輯**:
- **多單啟動**: 當前價格 ≥ 進場價格 + 15點
- **空單啟動**: 當前價格 ≤ 進場價格 - 15點
- **一次性啟動**: 啟動後 `trailing_activated` 設為 True，不會重複啟動
- **峰值追蹤**: 啟動同時開始追蹤峰值價格

### 2.2 多組策略啟動點配置

**配置結構**: `LotRule` 類別

```python
@dataclass
class LotRule:
    lot_id: int
    trigger_points: float  # 觸發點數
    pullback_percent: float  # 回撤百分比
    protective_stop_multiplier: float  # 保護性停損倍數
    use_trailing_stop: bool = True  # 是否使用移動停利
    
    def get_activation_points(self) -> float:
        """取得移動停利啟動點數"""
        return self.trigger_points  # 觸發點數即為啟動點數
```

**預設配置範例**:
```python
# 標準配置 (3口×3組)
lot_rules = [
    LotRule(lot_id=1, trigger_points=15.0, pullback_percent=0.10, protective_stop_multiplier=0.0),
    LotRule(lot_id=2, trigger_points=40.0, pullback_percent=0.10, protective_stop_multiplier=2.0),
    LotRule(lot_id=3, trigger_points=41.0, pullback_percent=0.20, protective_stop_multiplier=2.0)
]
```

## 📈 3. 移動停利追蹤機制

### 3.1 峰值價格追蹤

**即時更新邏輯**:
```python
def check_trailing_stop_logic(self, price, time_str):
    """峰值價格即時更新"""
    
    peak_price = self.current_position['peak_price']
    
    # 更新峰值價格（只進不退）
    if direction == "LONG":
        if price > peak_price:
            self.current_position['peak_price'] = price
            peak_price = price
    else:  # SHORT
        if price < peak_price:
            self.current_position['peak_price'] = price
            peak_price = price
```

**峰值追蹤特點**:
- **只進不退**: 峰值價格只會向有利方向更新
- **即時更新**: 每個報價都會檢查並更新峰值
- **方向區分**: 多單追蹤最高價，空單追蹤最低價
- **內存存儲**: 峰值價格存儲在 `current_position` 字典中

### 3.2 回撤計算與觸發

**回撤檢查邏輯**:
```python
def check_trailing_stop_logic(self, price, time_str):
    """檢查回撤觸發條件"""
    
    if trailing_activated:
        pullback_percent = self.current_position['trailing_pullback_percent']  # 20%
        
        if direction == "LONG":
            # 多單：計算從峰值的回撤幅度
            pullback_amount = (peak_price - entry_price) * pullback_percent
            trigger_price = peak_price - pullback_amount
            
            if price <= trigger_price:
                self.exit_position_safe(price, time_str, f"移動停利 {trigger_price:.0f}")
                return
                
        else:  # SHORT
            # 空單：計算從峰值的回撤幅度
            pullback_amount = (entry_price - peak_price) * pullback_percent
            trigger_price = peak_price + pullback_amount
            
            if price >= trigger_price:
                self.exit_position_safe(price, time_str, f"移動停利 {trigger_price:.0f}")
                return
```

**回撤計算公式**:
- **多單回撤**: 觸發價格 = 峰值價格 - (峰值價格 - 進場價格) × 回撤百分比
- **空單回撤**: 觸發價格 = 峰值價格 + (進場價格 - 峰值價格) × 回撤百分比
- **動態調整**: 觸發價格隨峰值價格動態調整
- **百分比控制**: 預設20%回撤，可透過配置調整

### 3.3 內存計算批次更新

**統一移動停利計算器**:
```python
# 🚀 優先模式：統一移動停利計算器（內存計算，無資料庫查詢）
if hasattr(self.parent, 'unified_trailing_enabled') and self.parent.unified_trailing_enabled:
    # 🚀 純內存計算，獲取所有活躍部位
    active_positions = self.parent.trailing_calculator.get_active_positions()
    
    # 為每個活躍部位更新價格（純內存操作）
    for position_id in active_positions:
        trigger_info = self.parent.trailing_calculator.update_price(
            position_id, corrected_price
        )
        
        # 如果觸發平倉，觸發信息會自動通過回調傳遞給止損執行器
        # 無需額外處理，回調機制已整合
```

**內存計算優勢**:
- **零資料庫查詢**: 所有計算在內存中完成
- **高性能**: 避免頻繁的 SQLite I/O 操作
- **批次處理**: 一次處理多個部位的價格更新
- **事件驅動**: 只在觸發條件時才執行資料庫寫入

### 3.4 異步峰值更新系統

**異步更新機制**:
```python
def _update_position_risk_state(self, position: Dict, current_price: float, current_time: str):
    """更新部位風險狀態 - 支援異步峰值更新"""
    
    # 更新峰值價格
    peak_updated = False
    if direction == 'LONG':
        if current_price > current_peak:
            current_peak = current_price
            peak_updated = True
    else:  # SHORT
        if current_price < current_peak:
            current_peak = current_price
            peak_updated = True

    # 如果峰值有更新，選擇更新方式
    if peak_updated:
        if self.enable_async_peak_update and self.async_updater:
            # 🚀 異步更新模式（靜默處理，避免過多日誌）
            self.async_updater.schedule_peak_update(
                position_id=position['id'],
                peak_price=current_peak,
                update_time=current_time,
                update_reason="價格更新"
            )
        else:
            # 🛡️ 同步更新模式（預設，確保零風險）
            self.db_manager.update_risk_management_state(
                position_id=position['id'],
                peak_price=current_peak,
                update_time=current_time,
                update_reason="價格更新"
            )
```

**異步更新優勢**:
- **降低延遲**: 避免同步資料庫寫入阻塞主線程
- **提高吞吐量**: 並行處理多個部位的峰值更新
- **減少 GIL 競爭**: 使用異步 I/O 避免 Python GIL 限制
- **可選啟用**: 預設同步模式，可選擇啟用異步模式

## 🛡️ 4. 保護性停損計算機制

### 4.1 保護性停損概念

**適用範圍**: 僅限多組策略模式

**計算邏輯**:
```python
def update_protective_stop_loss(self, exited_position: Dict) -> bool:
    """更新保護性停損"""
    
    # 只有獲利出場才觸發保護性停損更新
    if exited_position['pnl'] <= 0:
        return False
    
    group_id = exited_position['group_id']
    exited_lot_id = exited_position['lot_id']
    
    # 找到下一口需要更新保護性停損的部位
    next_position = self._find_next_position_for_protection(group_id, exited_lot_id)
    if not next_position:
        return False
    
    # 計算累積獲利
    total_profit = self._calculate_cumulative_profit(group_id, next_position['lot_id'])
    
    if total_profit <= 0:
        return False
    
    # 計算保護性停損價格
    direction = next_position['direction']
    entry_price = next_position['entry_price']
    protection_multiplier = self._get_protection_multiplier(group_id, next_position['lot_id'])
    
    stop_loss_amount = total_profit * protection_multiplier
    
    if direction == 'LONG':
        new_stop_loss = entry_price - stop_loss_amount
    else:  # SHORT
        new_stop_loss = entry_price + stop_loss_amount
    
    # 更新資料庫
    self.db_manager.update_position_stop_loss(
        position_id=next_position['id'],
        new_stop_loss=new_stop_loss,
        update_reason="保護性停損"
    )
```

**保護性停損特點**:
- **獲利觸發**: 只有前一口獲利出場才會觸發
- **累積計算**: 基於前面所有口數的累積獲利
- **倍數控制**: 透過 `protective_stop_multiplier` 控制保護程度
- **動態調整**: 每次有口數獲利出場時重新計算

### 4.2 累積獲利計算

**計算函數**:
```python
def _calculate_cumulative_profit(self, group_id: int, up_to_lot_id: int) -> float:
    """計算累積獲利"""
    
    # 獲取該組已出場的部位
    exited_positions = self.db_manager.get_exited_positions_by_group(group_id)
    
    total_profit = 0.0
    for position in exited_positions:
        # 只計算指定口數之前的獲利
        if position['lot_id'] < up_to_lot_id and position['pnl'] > 0:
            total_profit += position['pnl']
    
    return total_profit
```

**累積獲利邏輯**:
- **順序計算**: 按口數順序累積前面口數的獲利
- **只計獲利**: 虧損的口數不計入累積獲利
- **實時更新**: 每次有口數出場時重新計算

## 🔄 5. 批次更新機制

### 5.1 資料庫批次同步

**批次更新策略**:
```python
def schedule_batch_update(self):
    """排程批次更新"""
    
    # 收集待更新的資料
    pending_updates = self.collect_pending_updates()
    
    if pending_updates:
        # 批次執行資料庫更新
        self.execute_batch_database_update(pending_updates)
        
        # 清空待更新佇列
        self.clear_pending_updates()
    
    # 排程下次批次更新（每5秒）
    self.root.after(5000, self.schedule_batch_update)
```

**批次更新優勢**:
- **減少 I/O**: 將多個小更新合併為一次大更新
- **提高性能**: 減少資料庫連接和事務開銷
- **保持一致性**: 批次更新確保資料一致性
- **可配置間隔**: 可調整批次更新頻率

### 5.2 內存狀態管理

**內存優先策略**:
```python
class MemoryFirstPositionManager:
    """內存優先的部位管理器"""
    
    def __init__(self):
        self.memory_positions = {}  # 內存中的部位狀態
        self.pending_db_updates = []  # 待同步到資料庫的更新
        
    def update_position_state(self, position_id: int, **kwargs):
        """更新部位狀態（內存優先）"""
        
        # 1. 立即更新內存狀態
        if position_id not in self.memory_positions:
            self.memory_positions[position_id] = {}
        
        self.memory_positions[position_id].update(kwargs)
        
        # 2. 加入待同步佇列
        self.pending_db_updates.append({
            'position_id': position_id,
            'updates': kwargs,
            'timestamp': time.time()
        })
        
    def get_position_state(self, position_id: int) -> Dict:
        """取得部位狀態（內存優先）"""
        
        # 優先從內存讀取
        if position_id in self.memory_positions:
            return self.memory_positions[position_id]
        
        # 內存沒有則從資料庫讀取
        return self.db_manager.get_position_by_id(position_id)
```

**內存管理優勢**:
- **即時讀寫**: 內存操作延遲極低
- **資料一致性**: 內存狀態為最新狀態
- **異步同步**: 資料庫同步不阻塞主流程
- **容錯機制**: 內存失效時自動從資料庫恢復

## 📊 6. 多組策略部位管理整合

### 6.1 MultiGroupPositionManager 核心功能

**主要職責**:
```python
class MultiGroupPositionManager:
    """多組部位管理器 - 核心業務邏輯"""
    
    def __init__(self, db_manager, strategy_config):
        self.db_manager = db_manager
        self.strategy_config = strategy_config
        self.active_groups = {}  # {group_id: GroupState}
        self.simplified_tracker = None  # FIFO追蹤器
        self.risk_engine = None  # 風險管理引擎
        
    def update_current_price(self, current_price: float, current_time: str):
        """更新當前價格並觸發風險管理檢查"""
        
        # 獲取所有活躍部位
        active_positions = self.get_all_active_positions()
        if not active_positions:
            return
        
        # 更新風險管理引擎
        if self.risk_engine:
            self.risk_engine.update_current_price(current_price, current_time)
        
        # 更新統一移動停利計算器
        if hasattr(self, 'trailing_calculator') and self.trailing_calculator:
            for position in active_positions:
                self.trailing_calculator.update_price(
                    position['id'], current_price
                )
```

### 6.2 統一出場管理

**UnifiedExitManager 整合**:
```python
def trigger_exit(self, position_id: int, exit_reason: str, exit_price: Optional[float] = None) -> bool:
    """統一出場觸發方法"""
    
    # 1. 獲取部位資訊
    position_info = self.db_manager.get_position_by_id(position_id)
    if not position_info:
        return False
    
    # 2. 確定出場價格
    if exit_price is None:
        exit_price = self.determine_exit_price(position_info)
    
    # 3. 執行出場下單
    success = self.execute_exit_order(position_info, exit_price, exit_reason)
    
    # 4. 更新統計和歷史記錄
    self.update_exit_statistics(position_id, exit_reason, success)
    
    return success
```

**統一出場優勢**:
- **統一入口**: 所有出場都通過統一介面
- **標準化流程**: 統一的出場執行流程
- **完整記錄**: 詳細的出場歷史和統計
- **錯誤處理**: 統一的錯誤處理和重試機制

## 📈 總結

simple_integrated.py 的建倉後部位管理機制採用了多層次的風險控制架構：

1. **初始停損層**: 基於開盤區間邊界的固定停損保護
2. **移動停利層**: 15點啟動，20%回撤的動態獲利保護
3. **保護性停損層**: 基於累積獲利的動態風險控制（多組策略）
4. **內存計算層**: 高性能的內存優先計算和批次資料庫同步
5. **異步更新層**: 可選的異步峰值更新，降低延遲提升性能

整個系統通過內存計算、批次更新、異步處理等技術，在保證風險控制精度的同時，實現了高性能的實時部位管理能力。
