# 任務3：ID的執行——平倉信號生成與傳遞審計報告

## 🎯 審計目標
驗證當觸發平倉條件時，正確的 position_id 被用來生成信號並傳遞給執行器。

## 📋 審計範圍
1. 初始停損觸發審計
2. 移動停利觸發審計
3. 執行器接口審計

## 🔍 詳細審計結果

### 1. 初始停損觸發審計

#### 1.1 風險引擎中的初始停損觸發
**位置**: `Capital_Official_Framework/risk_management_engine.py` 第414-429行

**關鍵發現**:
✅ **初始停損觸發時正確使用 position_id**
- 當觸發初始停損時，為每個部位創建獨立的出場動作
- 每個出場動作都包含準確的 position_id 和 group_id
- 確保出場信號與特定部位的精確對應

<augment_code_snippet path="Capital_Official_Framework/risk_management_engine.py" mode="EXCERPT">
````python
# 檢查初始停損 (第二優先級)
initial_stop_exits = self._check_initial_stop_loss(positions, current_price)
if initial_stop_exits:
    # 初始停損觸發，全組出場
    for position in positions:
        pnl = self._calculate_pnl(position, current_price)
        exit_actions.append({
            'position_id': position['id'],
            'group_id': position['group_id'],
            'exit_price': current_price,
            'exit_time': current_time,
            'exit_reason': '初始停損',
            'pnl': pnl
        })
    
    self.logger.info(f"組 {positions[0]['group_id']} 觸發初始停損，全組出場")
    return exit_actions
````
</augment_code_snippet>

#### 1.2 保護性停損觸發
**位置**: `Capital_Official_Framework/risk_management_engine.py` 第434-444行

**關鍵發現**:
✅ **保護性停損觸發時精確使用 position_id**
- 針對單個部位進行保護性停損檢查
- 出場動作包含正確的 position_id 和 group_id
- 使用部位的 current_stop_loss 作為出場價格

<augment_code_snippet path="Capital_Official_Framework/risk_management_engine.py" mode="EXCERPT">
````python
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
````
</augment_code_snippet>

### 2. 移動停利觸發審計

#### 2.1 OptimizedRiskManager 中的移動停利觸發
**位置**: `Capital_Official_Framework/optimized_risk_manager.py` 第591-612行

**關鍵發現**:
✅ **移動停利觸發時正確創建 StopLossTrigger 物件**
- 從緩存中獲取 position_data 和 group_id
- 創建 StopLossTrigger 時傳入正確的 position_id 和 group_id
- 觸發原因明確標識為移動停利

<augment_code_snippet path="Capital_Official_Framework/optimized_risk_manager.py" mode="EXCERPT">
````python
# 創建移動停利觸發信息
from stop_loss_monitor import StopLossTrigger

# 🔧 修復：獲取group_id信息
position_data = self.position_cache.get(position_id, {})
group_id = position_data.get('group_id', 1)  # 預設為1

# 🔧 修復：使用正確的參數名稱
trigger_info = StopLossTrigger(
    position_id=int(position_id),
    group_id=int(group_id),
    direction=direction,
    current_price=current_price,  # 🔧 修復：trigger_price -> current_price
    stop_loss_price=current_price,  # 使用當前價格作為平倉價
    trigger_time=datetime.now().strftime("%H:%M:%S"),
    trigger_reason=f"移動停利: {direction}部位20%回撤觸發",  # ✅ 明確標識為移動停利
    breach_amount=0.0  # 移動停利不需要突破金額
)
````
</augment_code_snippet>

#### 2.2 StopLossTrigger 物件結構
**位置**: `Capital_Official_Framework/stop_loss_monitor.py` 第17-27行

**關鍵發現**:
✅ **StopLossTrigger 物件包含完整的 ID 資訊**
- position_id: int - 部位唯一標識符
- group_id: int - 組別標識符
- 包含完整的觸發上下文資訊

<augment_code_snippet path="Capital_Official_Framework/stop_loss_monitor.py" mode="EXCERPT">
````python
@dataclass
class StopLossTrigger:
    """停損觸發資訊"""
    position_id: int
    group_id: int
    direction: str
    current_price: float
    stop_loss_price: float
    trigger_time: str
    trigger_reason: str
    breach_amount: float  # 突破金額
````
</augment_code_snippet>

#### 2.3 _execute_trailing_stop 方法
**位置**: `Capital_Official_Framework/optimized_risk_manager.py` 第554-577行

**關鍵發現**:
✅ **移動停利執行時保持 position_id 一致性**
- 方法接收 position_id 作為主要參數
- 全局平倉管理器使用 position_id 進行重複檢查
- 觸發源明確標識包含 position_id

### 3. 執行器接口審計

#### 3.1 StopLossExecutor.execute_stop_loss 方法接口
**位置**: `Capital_Official_Framework/stop_loss_executor.py` 第224-234行

**關鍵發現**:
✅ **執行器接口正確接收和使用 position_id**
- 主要參數是 trigger_info，包含 position_id
- 使用 position_id 進行全局平倉管理器檢查
- 所有後續操作都基於 position_id 進行

<augment_code_snippet path="Capital_Official_Framework/stop_loss_executor.py" mode="EXCERPT">
````python
# 🔧 新增：全局平倉管理器檢查（第一層防護）
trigger_source = f"stop_loss_{getattr(trigger_info, 'trigger_reason', 'unknown')}"
if not self.global_exit_manager.mark_exit(str(position_id), trigger_source, "stop_loss"):
    existing_info = self.global_exit_manager.get_exit_info(str(position_id))
    if self.console_enabled:
        print(f"[STOP_EXECUTOR] 🔒 停損被全局管理器阻止: 部位{position_id}")
        print(f"[STOP_EXECUTOR]   已有平倉: {existing_info.get('trigger_source', 'unknown')} "
              f"({existing_info.get('exit_type', 'unknown')})")
    return StopLossExecutionResult(position_id, False,
                                 error_message="全局管理器防止重複平倉")
````
</augment_code_snippet>

#### 3.2 部位資訊查找機制
**位置**: `Capital_Official_Framework/stop_loss_executor.py` 第726-732行

**關鍵發現**:
✅ **執行器使用 position_id 查找部位資訊**
- `_get_position_info(position_id)` 方法使用 position_id 作為查找 key
- 檢查部位狀態時使用 position_id 進行精確定位
- 所有資料庫操作都基於 position_id

<augment_code_snippet path="Capital_Official_Framework/stop_loss_executor.py" mode="EXCERPT">
````python
def _check_execution_conditions(self, position_id: int) -> dict:
    """
    檢查平倉執行條件

    Args:
        position_id: 部位ID

    Returns:
        dict: {'can_execute': bool, 'reason': str}
    """
    try:
        # 1. 檢查資料庫部位狀態
        position_info = self._get_position_info(position_id)
        if not position_info:
            return {'can_execute': False, 'reason': '找不到部位資訊'}

        if position_info.get('status') == 'EXITED':
            return {'can_execute': False, 'reason': '部位已平倉'}
````
</augment_code_snippet>

#### 3.3 平倉參數計算
**位置**: `Capital_Official_Framework/stop_loss_executor.py` 第279-298行

**關鍵發現**:
✅ **平倉參數計算基於 position_id 獲取的部位資訊**
- 使用 position_info 獲取進場價格和方向
- 計算平倉方向和預期損益
- 所有計算都與特定 position_id 關聯

#### 3.4 移動停利平倉執行
**位置**: `Capital_Official_Framework/stop_loss_executor.py` 第1135-1183行

**關鍵發現**:
✅ **移動停利平倉執行保持 position_id 一致性**
- 從 trigger_info 中提取 position_id
- 註冊平倉組時使用 position_id
- 下單和狀態更新都基於 position_id

<augment_code_snippet path="Capital_Official_Framework/stop_loss_executor.py" mode="EXCERPT">
````python
def _execute_trailing_stop_exit(self, trigger_info: dict) -> bool:
    """
    執行移動停利平倉

    Args:
        trigger_info: 移動停利觸發信息

    Returns:
        bool: 執行是否成功
    """
    try:
        position_id = trigger_info['position_id']
        direction = trigger_info['direction']
        stop_price = trigger_info['stop_price']
        current_price = trigger_info['current_price']

        # 計算平倉方向（與止損邏輯相同）
        exit_direction = "SELL" if direction == "LONG" else "BUY"

        # 使用當前價格作為平倉價格（更準確）
        exit_price = current_price

        # 創建信號源（標識為移動停利）
        signal_source = f"trailing_stop_{position_id}_{int(time.time())}"
````
</augment_code_snippet>

## 🎯 審計結論

### ✅ 通過項目
1. **初始停損觸發** - 出場動作正確包含 position_id 和 group_id
2. **保護性停損觸發** - 針對單個部位精確觸發，ID 傳遞正確
3. **移動停利觸發** - StopLossTrigger 物件包含完整的 ID 資訊
4. **執行器接口** - 主要參數 trigger_info 包含正確的 position_id
5. **部位資訊查找** - 執行器使用 position_id 進行精確查找
6. **平倉參數計算** - 所有計算都基於 position_id 獲取的部位資訊
7. **移動停利執行** - 整個執行流程保持 position_id 一致性

### ⚠️ 需要關注的點
1. **觸發信號完整性** - 需要確保所有觸發場景都包含完整的 ID 資訊
2. **執行器錯誤處理** - 當 position_id 無效時的錯誤處理機制
3. **併發執行保護** - 多個觸發源同時操作同一 position_id 的保護機制

### 📊 整體評估
**結論**: 無論出於何種原因（初始停損、保護性停損、移動停利等），平倉信號中都包含了正確的 position_id，並且平倉執行器依賴此ID來執行精確的平倉操作。信號生成與傳遞機制設計合理，ID 一致性得到保障。

**風險等級**: 🟢 低風險
**建議**: 繼續保持現有的 position_id 為核心的信號傳遞機制，加強併發執行的保護措施。
