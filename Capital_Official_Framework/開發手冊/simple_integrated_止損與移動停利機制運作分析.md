# simple_integrated.py 止損與移動停利機制運作分析

## 📋 概述

本文檔針對您提出的三個關鍵問題，詳細分析 `simple_integrated.py` 中止損平倉和移動停利平倉的運作機制，包括建倉時點位計算、平倉機制統一性，以及平倉後資料庫更新流程。

## 🎯 1. 止損平倉或移動停利啟動點位的機制

### 1.1 建倉時點位計算與存儲

**建倉時的點位設定**: `enter_position_safe(direction, price, time_str)`

```python
def enter_position_safe(self, direction, price, time_str):
    """建倉時計算並存儲所有關鍵點位"""
    
    # 記錄部位資訊，包含所有關鍵點位
    self.current_position = {
        'direction': direction,
        'entry_price': price,                    # 進場價格
        'entry_time': time_str,
        'quantity': 1,
        'peak_price': price,                     # 峰值價格追蹤（初始=進場價）
        'trailing_activated': False,             # 移動停利是否啟動
        'trailing_activation_points': 15,        # 🎯 移動停利啟動點位（15點）
        'trailing_pullback_percent': 0.20       # 🎯 移動停利回撤百分比（20%）
    }
    
    # 🛡️ 初始停損點位（隱含在區間邊界中）
    # 多單停損：self.range_low (區間下軌)
    # 空單停損：self.range_high (區間上軌)
    # 這些點位在建倉時就已經確定，存儲在類別屬性中
```

**關鍵點位存儲位置**:
1. **移動停利啟動點**: `current_position['trailing_activation_points']` = 15點
2. **移動停利回撤比例**: `current_position['trailing_pullback_percent']` = 20%
3. **初始停損點**: `self.range_low` (多單) / `self.range_high` (空單)
4. **峰值價格**: `current_position['peak_price']` (動態更新)

### 1.2 點位取用機制

**初始停損點位取用**: `check_exit_conditions_safe()`

```python
def check_exit_conditions_safe(self, price, time_str):
    """從建倉時設定的點位檢查止損條件"""
    
    direction = self.current_position['direction']
    
    # 🛡️ 取用建倉時計算的區間邊界作為停損點
    if direction == "LONG" and price <= self.range_low:
        # 多單止損：使用建倉時的區間下軌
        self.exit_position_safe(price, time_str, f"初始停損 {self.range_low:.0f}")
        return
    elif direction == "SHORT" and price >= self.range_high:
        # 空單止損：使用建倉時的區間上軌
        self.exit_position_safe(price, time_str, f"初始停損 {self.range_high:.0f}")
        return
```

**移動停利啟動點位取用**: `check_trailing_stop_logic()`

```python
def check_trailing_stop_logic(self, price, time_str):
    """從建倉時設定的參數檢查移動停利啟動"""
    
    direction = self.current_position['direction']
    entry_price = self.current_position['entry_price']
    trailing_activated = self.current_position['trailing_activated']
    
    # 🎯 取用建倉時設定的啟動點數
    activation_points = self.current_position['trailing_activation_points']  # 15點
    
    # 檢查移動停利啟動條件
    if not trailing_activated:
        if direction == "LONG":
            # 多單：價格超過進場價 + 啟動點數
            activation_triggered = price >= entry_price + activation_points
        else:  # SHORT
            # 空單：價格低於進場價 - 啟動點數
            activation_triggered = price <= entry_price - activation_points
        
        if activation_triggered:
            self.current_position['trailing_activated'] = True
            self.add_strategy_log(f"🔔 移動停利已啟動！峰值價格: {price:.0f}")
```

**移動停利觸發點位計算**:

```python
def check_trailing_stop_logic(self, price, time_str):
    """使用建倉時設定的回撤比例計算觸發點"""
    
    if trailing_activated:
        # 🎯 取用建倉時設定的回撤百分比
        pullback_percent = self.current_position['trailing_pullback_percent']  # 20%
        peak_price = self.current_position['peak_price']
        entry_price = self.current_position['entry_price']
        
        if direction == "LONG":
            # 多單觸發價格 = 峰值價格 - (峰值價格 - 進場價格) × 回撤百分比
            pullback_amount = (peak_price - entry_price) * pullback_percent
            trigger_price = peak_price - pullback_amount
            
            if price <= trigger_price:
                self.exit_position_safe(price, time_str, f"移動停利 {trigger_price:.0f}")
```

### 1.3 多組策略的點位管理

**多組策略點位存儲**: 在資料庫中的 `lot_rule_config` 欄位

```python
# LotRule 配置存儲在資料庫中
@dataclass
class LotRule:
    lot_id: int
    trigger_points: float           # 🎯 移動停利啟動點數
    pullback_percent: float         # 🎯 回撤百分比
    protective_stop_multiplier: float  # 保護性停損倍數
    
# 建倉時存儲到資料庫
position_id = self.db_manager.create_position_record(
    group_id=group_db_id,
    lot_id=lot_rule.lot_id,
    direction=direction,
    entry_time=actual_time,
    rule_config=lot_rule.to_json(),  # 🎯 點位配置存儲為JSON
    order_status='PENDING'
)
```

## 🔄 2. 止損平倉跟移動停利平倉是否都調用同一個平倉機制

### 2.1 統一平倉入口

**答案：是的，都調用同一個平倉機制**

所有類型的平倉都通過 `exit_position_safe()` 函數執行：

```python
# 🛡️ 初始停損平倉
if direction == "LONG" and price <= self.range_low:
    self.exit_position_safe(price, time_str, f"初始停損 {self.range_low:.0f}")

# 🎯 移動停利平倉
if price <= trigger_price:
    self.exit_position_safe(price, time_str, f"移動停利 {trigger_price:.0f}")

# 🕐 收盤平倉
if hour >= 13 and minute >= 30:
    self.exit_position_safe(price, time_str, "收盤平倉")
```

### 2.2 統一平倉函數實現

**核心平倉函數**: `exit_position_safe(price, time_str, reason)`

```python
def exit_position_safe(self, price, time_str, reason):
    """統一的平倉處理函數 - 所有平倉類型都使用此函數"""
    try:
        if not self.current_position:
            return

        direction = self.current_position['direction']
        entry_price = self.current_position['entry_price']
        entry_time = self.current_position['entry_time']

        # 🧮 統一損益計算
        pnl = (price - entry_price) if direction == "LONG" else (entry_price - price)
        pnl_money = pnl * 50  # 每點50元

        # ⏱️ 統一持倉時間計算
        try:
            entry_h, entry_m, entry_s = map(int, entry_time.split(':'))
            exit_h, exit_m, exit_s = map(int, time_str.split(':'))
            entry_seconds = entry_h * 3600 + entry_m * 60 + entry_s
            exit_seconds = exit_h * 3600 + exit_m * 60 + exit_s
            hold_seconds = exit_seconds - entry_seconds
            hold_minutes = hold_seconds // 60
        except:
            hold_minutes = 0

        # 📝 統一日誌記錄（reason 參數區分平倉類型）
        self.add_strategy_log(f"🔚 {direction} 平倉 @{price:.0f} 原因:{reason} 損益:{pnl:+.0f}點 持倉:{hold_minutes}分")

        # 🧹 統一狀態清理
        self.current_position = None
        self.first_breakout_detected = False

        # 📊 統一Console輸出
        print(f"✅ [STRATEGY] {direction}平倉 @{price:.0f} {reason} 損益:{pnl_money:+.0f}元")

        # 🚀 統一下單執行（如果啟用下單系統）
        if hasattr(self, 'virtual_real_order_manager') and self.virtual_real_order_manager:
            exit_direction = "SELL" if direction == "LONG" else "BUY"
            
            order_result = self.virtual_real_order_manager.execute_strategy_order(
                direction=exit_direction,
                signal_source=f"exit_{reason}",
                product="TM0000",
                price=price,
                quantity=1,
                new_close=1  # 設定為平倉
            )

    except Exception as e:
        self.add_strategy_log(f"❌ 平倉失敗: {e}")
```

### 2.3 多組策略統一平倉機制

**多組策略也使用統一出場管理器**: `UnifiedExitManager`

```python
# 所有平倉類型都通過統一出場管理器
class UnifiedExitManager:
    def trigger_exit(self, position_id: int, exit_reason: str, exit_price: Optional[float] = None):
        """統一出場觸發方法 - 所有出場的統一入口"""
        
        # 1. 獲取部位資訊
        position_info = self.db_manager.get_position_by_id(position_id)
        
        # 2. 確定出場價格
        if exit_price is None:
            exit_price = self.determine_exit_price(position_info)
        
        # 3. 執行出場下單（統一邏輯）
        success = self.execute_exit_order(position_info, exit_price, exit_reason)
        
        return success

# 不同平倉類型調用相同的統一出場管理器
# 初始停損
self.unified_exit_manager.trigger_exit(position_id, "初始停損", stop_loss_price)

# 移動停利
self.unified_exit_manager.trigger_exit(position_id, "移動停利", trailing_stop_price)

# 收盤平倉
self.unified_exit_manager.trigger_exit(position_id, "收盤平倉", current_price)
```

## 💾 3. 平倉後如何更新資料庫

### 3.1 單一策略資料庫更新

**單一策略目前沒有直接的資料庫更新**，主要依賴內存狀態管理：

```python
def exit_position_safe(self, price, time_str, reason):
    """單一策略平倉後的狀態更新"""
    
    # 🧹 清除內存狀態
    self.current_position = None
    self.first_breakout_detected = False
    
    # 📝 記錄到策略日誌（文字記錄）
    self.add_strategy_log(f"🔚 {direction} 平倉 @{price:.0f} 原因:{reason}")
    
    # 注意：單一策略模式沒有直接的資料庫更新
    # 交易記錄主要保存在策略日誌中
```

### 3.2 多組策略資料庫更新機制

**多組策略有完整的資料庫更新流程**:

#### 3.2.1 同步資料庫更新

**核心更新函數**: `MultiGroupDatabaseManager.update_position_exit()`

```python
def update_position_exit(self, position_id: int, exit_price: float, 
                       exit_time: str, exit_reason: str, pnl: float):
    """更新部位出場資訊"""
    try:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 計算損益金額 (小台指每點50元)
            pnl_amount = pnl * 50
            
            # 🗄️ 更新 position_records 表
            cursor.execute('''
                UPDATE position_records 
                SET exit_price = ?, exit_time = ?, exit_reason = ?, 
                    pnl = ?, pnl_amount = ?, status = 'EXITED',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (exit_price, exit_time, exit_reason, pnl, pnl_amount, position_id))
            
            conn.commit()
            logger.info(f"更新部位出場: ID={position_id}, 損益={pnl}點")
            
    except Exception as e:
        logger.error(f"更新部位出場失敗: {e}")
        raise
```

#### 3.2.2 異步資料庫更新

**異步更新機制**: `AsyncDBUpdater.schedule_position_exit_update()`

```python
def schedule_position_exit_update(self, position_id: int, exit_price: float,
                                exit_time: str, exit_reason: str = 'STOP_LOSS',
                                order_id: str = None, pnl: float = 0.0):
    """排程部位平倉更新（非阻塞）"""
    
    # 🚀 立即更新內存緩存（非阻塞）
    with self.cache_lock:
        self.memory_cache['exit_positions'][position_id] = {
            'id': position_id,
            'status': 'EXITED',
            'exit_price': exit_price,
            'exit_time': exit_time,
            'exit_reason': exit_reason,
            'order_id': order_id,
            'pnl': pnl,
            'updated_at': time.time()
        }
        self.memory_cache['last_updates'][position_id] = time.time()
    
    # 📝 排程資料庫更新（異步處理）
    task = UpdateTask(
        task_type='position_exit',
        position_id=position_id,
        data={
            'exit_price': exit_price,
            'exit_time': exit_time,
            'exit_reason': exit_reason,
            'order_id': order_id,
            'pnl': pnl
        }
    )
    
    self.update_queue.put_nowait(task)
```

#### 3.2.3 資料庫更新執行

**異步任務處理**: `_process_position_exit_task()`

```python
def _process_position_exit_task(self, task: UpdateTask) -> bool:
    """處理平倉任務"""
    try:
        # 檢查是否有專用的平倉更新方法
        if hasattr(self.db_manager, 'update_position_exit_status'):
            success = self.db_manager.update_position_exit_status(
                position_id=task.position_id,
                exit_price=task.data['exit_price'],
                exit_time=task.data['exit_time'],
                exit_reason=task.data['exit_reason'],
                order_id=task.data.get('order_id'),
                pnl=task.data.get('pnl', 0.0)
            )
        else:
            # 回退到通用的資料庫更新方法
            success = self._update_position_exit_fallback(task)

        return success
        
    except Exception as e:
        logger.error(f"處理平倉任務失敗: {e}")
        return False
```

**回退更新方法**: `_update_position_exit_fallback()`

```python
def _update_position_exit_fallback(self, task: UpdateTask) -> bool:
    """平倉更新回退方法"""
    try:
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()

            # 🗄️ 更新 position_records 表
            cursor.execute('''
                UPDATE position_records
                SET status = 'EXITED',
                    exit_price = ?,
                    exit_time = ?,
                    exit_reason = ?,
                    exit_order_id = ?,
                    realized_pnl = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                task.data['exit_price'],
                task.data['exit_time'],
                task.data['exit_reason'],
                task.data.get('order_id'),
                task.data.get('pnl', 0.0),
                task.position_id
            ))

            # 檢查是否有更新到記錄
            if cursor.rowcount == 0:
                logger.warning(f"平倉更新未影響任何記錄: 部位{task.position_id}")
                return False

            conn.commit()
            return True
            
    except Exception as e:
        logger.error(f"平倉更新回退方法失敗: {e}")
        return False
```

### 3.3 資料庫更新流程總結

**完整的平倉資料庫更新流程**:

1. **觸發平倉** → `exit_position_safe()` 或 `UnifiedExitManager.trigger_exit()`
2. **立即更新內存** → 異步更新器的內存緩存
3. **排程資料庫更新** → 加入異步更新佇列
4. **執行資料庫更新** → 更新 `position_records` 表的以下欄位：
   - `status` → 'EXITED'
   - `exit_price` → 平倉價格
   - `exit_time` → 平倉時間
   - `exit_reason` → 平倉原因
   - `realized_pnl` → 實現損益（點數）
   - `pnl_amount` → 損益金額（新台幣）
   - `updated_at` → 更新時間戳

**資料庫表結構**:
```sql
-- position_records 表的平倉相關欄位
exit_price REAL,           -- 出場價格
exit_time TEXT,            -- 出場時間 (HH:MM:SS)
exit_reason TEXT,          -- 出場原因
realized_pnl REAL,         -- 已實現損益 (點數)
pnl_amount REAL,           -- 損益金額 (新台幣)
status TEXT,               -- 部位狀態: ACTIVE/EXITED
updated_at TIMESTAMP       -- 最後更新時間
```

## 📊 總結

1. **點位機制**: 建倉時就計算並存儲所有關鍵點位（停損點、移動停利啟動點、回撤比例），後續平倉檢查直接取用這些預設值。

2. **統一平倉**: 止損平倉和移動停利平倉都調用同一個 `exit_position_safe()` 函數，只是 `reason` 參數不同，確保了平倉邏輯的一致性。

3. **資料庫更新**: 多組策略有完整的同步/異步資料庫更新機制，單一策略主要依賴內存狀態和策略日誌記錄。
