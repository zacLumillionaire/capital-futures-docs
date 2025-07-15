# 任務2：ID的監控——移動停利與風險追蹤中的ID使用審計報告

## 🎯 審計目標
驗證在運行時的監控迴圈中，系統是否使用正確的ID來獲取部位資訊和更新狀態。

## 📋 審計範圍
1. 移動停利監控審計 (OptimizedRiskManager)
2. 風險引擎審計 (RiskManagementEngine)

## 🔍 詳細審計結果

### 1. 移動停利監控審計 (OptimizedRiskManager)

#### 1.1 on_new_position 方法 - position_id 作為緩存 key
**位置**: `Capital_Official_Framework/optimized_risk_manager.py` 第151-200行

**關鍵發現**:
✅ **position_id 正確用作緩存 key**
- 使用 `position_id = position_dict.get('id')` 提取 position_id
- 將 position_id 作為 `self.position_cache` 的 key
- 確保每個部位在緩存中有唯一標識

<augment_code_snippet path="Capital_Official_Framework/optimized_risk_manager.py" mode="EXCERPT">
````python
def on_new_position(self, position_data):
    """
    新部位事件觸發 - 立即加入監控

    Args:
        position_data: 部位數據（可能是字典或sqlite3.Row）
    """
    try:
        # 🔧 修復：安全轉換 sqlite3.Row 為字典
        if hasattr(position_data, 'keys'):
            # 這是 sqlite3.Row 對象
            try:
                position_dict = dict(position_data)
            except Exception:
                # 手動轉換
                position_dict = {key: position_data[key] for key in position_data.keys()}
        elif isinstance(position_data, dict):
            position_dict = position_data.copy()
        else:
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ⚠️ 部位數據類型無效: {type(position_data)}")
            return

        position_id = position_dict.get('id')
        if not position_id:
            if self.console_enabled:
                print(f"[OPTIMIZED_RISK] ⚠️ 部位ID無效或缺失")
            return

        with self.cache_lock:
            # 🎯 立即加入緩存
            self.position_cache[position_id] = position_dict
````
</augment_code_snippet>

#### 1.2 緩存結構設計 - 基於 position_id 的多層緩存
**位置**: `Capital_Official_Framework/optimized_risk_manager.py` 第61-66行

**關鍵發現**:
✅ **多層緩存均使用 position_id 作為 key**
- `self.position_cache = {}` - {position_id: position_data}
- `self.stop_loss_cache = {}` - {position_id: stop_loss_price}
- `self.activation_cache = {}` - {position_id: activation_price}
- `self.trailing_cache = {}` - {position_id: trailing_data}

#### 1.3 update_price 方法 - 基於 position_id 的狀態更新
**位置**: `Capital_Official_Framework/optimized_risk_manager.py` 第334-362行

**關鍵發現**:
✅ **所有操作都基於 position_id 進行**
- 遍歷 `self.position_cache.items()` 時使用 position_id 作為 key
- 所有檢查方法都傳入 position_id 作為參數
- 確保狀態更新精確定位到特定部位

<augment_code_snippet path="Capital_Official_Framework/optimized_risk_manager.py" mode="EXCERPT">
````python
def _process_cached_positions(self, current_price: float, timestamp: str) -> Dict:
    """處理緩存中的部位 - 純內存比較"""
    results = {
        'stop_loss_triggers': 0,
        'trailing_activations': 0,
        'peak_updates': 0,
        'drawdown_triggers': 0
    }
    
    try:
        with self.cache_lock:
            for position_id, position_data in self.position_cache.items():
                # 🛡️ 檢查初始停損
                if self._check_stop_loss_trigger(position_id, current_price):
                    results['stop_loss_triggers'] += 1
                
                # 🎯 檢查移動停利啟動
                elif self._check_activation_trigger(position_id, current_price):
                    results['trailing_activations'] += 1
                
                # 📈 更新已啟動的移動停利
                elif self._update_trailing_stop(position_id, current_price):
                    results['peak_updates'] += 1
````
</augment_code_snippet>

#### 1.4 移動停利執行 - position_id 和 group_id 的正確傳遞
**位置**: `Capital_Official_Framework/optimized_risk_manager.py` 第591-612行

**關鍵發現**:
✅ **移動停利觸發時正確使用 position_id 和 group_id**
- 從緩存中獲取 position_data：`position_data = self.position_cache.get(position_id, {})`
- 提取 group_id：`group_id = position_data.get('group_id', 1)`
- 創建 StopLossTrigger 時傳入正確的 position_id 和 group_id

### 2. 風險引擎審計 (RiskManagementEngine)

#### 2.1 check_all_exit_conditions 方法 - 主監控迴圈
**位置**: `Capital_Official_Framework/risk_management_engine.py` 第249-396行

**關鍵發現**:
✅ **正確獲取和使用 position_id 與 group_id**
- 調用 `self.db_manager.get_all_active_positions()` 獲取所有活躍部位
- 每個部位記錄包含 position_id (作為 'id' 欄位) 和 group_id
- 在出場動作中正確傳遞兩個 ID

<augment_code_snippet path="Capital_Official_Framework/risk_management_engine.py" mode="EXCERPT">
````python
def check_all_exit_conditions(self, current_price: float, current_time: str) -> List[Dict]:
    """檢查所有活躍部位的出場條件"""
    exit_actions = []

    try:
        active_positions = self.db_manager.get_all_active_positions()

        # 🔧 新增：多層狀態過濾（參考建倉機制）
        filtered_positions = self._filter_active_positions(active_positions)

        # 🔧 清理快取：移除已不存在的部位ID
        active_position_ids = {pos.get('id') for pos in filtered_positions if pos.get('id')}
        self._trailing_activated_cache &= active_position_ids  # 保留交集
````
</augment_code_snippet>

#### 2.2 get_all_active_positions 查詢 - 同時提取兩個 ID
**位置**: `Capital_Official_Framework/multi_group_database.py` 第641-665行

**關鍵發現**:
✅ **SQL 查詢正確關聯並提取 position_id 和 group_id**
- 主表 position_records 包含 id (position_id) 和 group_id 欄位
- JOIN 操作正確關聯 strategy_groups 表獲取組別資訊
- 查詢結果包含完整的部位和組別資訊

<augment_code_snippet path="Capital_Official_Framework/multi_group_database.py" mode="EXCERPT">
````python
def get_all_active_positions(self) -> List[Dict]:
    """取得所有活躍部位 - 🔧 修復：正確關聯策略組"""
    try:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.*, r.peak_price, r.current_stop_loss, r.trailing_activated, r.protection_activated,
                       sg.range_high, sg.range_low
                FROM position_records p
                LEFT JOIN risk_management_states r ON p.id = r.position_id
                LEFT JOIN (
                    SELECT * FROM strategy_groups
                    WHERE date = ?
                    ORDER BY id DESC
                ) sg ON p.group_id = sg.group_id
                WHERE p.status = 'ACTIVE'
                ORDER BY p.group_id, p.lot_id
            ''', (date.today().isoformat(),))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]
````
</augment_code_snippet>

#### 2.3 出場條件檢查 - position_id 作為最小單位
**位置**: `Capital_Official_Framework/risk_management_engine.py` 第398-459行

**關鍵發現**:
✅ **所有出場檢查都以 position_id 為最小單位**
- 初始停損觸發時，為每個 position 創建獨立的出場動作
- 保護性停損檢查針對單個 position 進行
- 移動停利檢查也是基於單個 position

<augment_code_snippet path="Capital_Official_Framework/risk_management_engine.py" mode="EXCERPT">
````python
# 檢查各口的個別出場條件
for position in positions:
    # 檢查保護性停損
    if self._check_protective_stop_loss(position, current_price):
        pnl = self._calculate_pnl(position, current_price)
        exit_actions.append({
            'position_id': position['id'],
            'group_id': position['group_id'],
            'exit_price': position['current_stop_loss'],
            'exit_time': current_time,
            'exit_reason': '保護性停損',
            'pnl': pnl
        })
        continue
    
    # 檢查移動停利條件
    trailing_exit = self._check_trailing_stop_conditions(position, current_price, current_time)
    if trailing_exit:
        exit_actions.append(trailing_exit)
        continue
````
</augment_code_snippet>

#### 2.4 移動停利條件檢查 - position_id 精確定位
**位置**: `Capital_Official_Framework/risk_management_engine.py` 第620-639行

**關鍵發現**:
✅ **移動停利檢查使用 position_id 進行精確定位**
- 使用 `position['id']` 獲取 position_id
- 調用 `_get_latest_peak_price(position['id'], db_peak_price)` 獲取最新峰值
- 調用 `_get_latest_trailing_state(position['id'], db_trailing_activated)` 獲取最新狀態

## 🎯 審計結論

### ✅ 通過項目
1. **OptimizedRiskManager 緩存機制** - 所有緩存都使用 position_id 作為 key
2. **多層緩存一致性** - position_cache, stop_loss_cache, activation_cache, trailing_cache 都基於 position_id
3. **價格更新處理** - 所有狀態更新都基於 position_id 進行精確定位
4. **風險引擎查詢** - get_all_active_positions 正確提取 position_id 和 group_id
5. **出場條件檢查** - 所有檢查都以 position_id 為最小單位
6. **移動停利執行** - 觸發時正確傳遞 position_id 和 group_id

### ⚠️ 需要關注的點
1. **緩存同步機制** - 需要確保內存緩存與資料庫的 position_id 對應關係正確
2. **線程安全性** - 多線程環境下 position_id 的使用需要適當的鎖機制
3. **緩存失效處理** - 部位平倉後需要正確清理對應 position_id 的緩存

### 📊 整體評估
**結論**: 在高性能的移動停利監控和全局的風險引擎輪詢中，所有狀態的讀取、更新和計算都是基於精確的 position_id 進行的，杜絕了數據錯亂的風險。系統設計合理，ID 使用規範。

**風險等級**: 🟢 低風險
**建議**: 繼續保持現有的 position_id 為核心的設計模式，定期檢查緩存同步機制的有效性。
