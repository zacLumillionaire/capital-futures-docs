# 平倉機制重新設計計劃

## 📋 **核心理念**

**完全參考建倉機制的成功模式**，將平倉機制改造為：
1. **異步狀態更新** - 使用與建倉相同的每5秒更新+內存緩存機制
2. **一對一回報確認** - 每個平倉訂單對應一個部位狀態更新
3. **FOK失敗追價** - 使用與建倉相同的追價邏輯，但方向相反

## 🔍 **建倉機制分析（參考模板）**

### **建倉成功機制回顧**
根據 `ASYNC_UPDATE_IMPLEMENTATION_REPORT.md`：

#### **1. 異步狀態更新機制**
```python
# 建倉：立即更新內存緩存，異步更新資料庫
if self.async_update_enabled:
    self.async_updater.schedule_position_fill_update(...)  # 非阻塞
    async_elapsed = (time.time() - start_time) * 1000
    self.logger.info(f"🚀 [異步更新] 部位{position_id}成交確認 @{price} (耗時:{async_elapsed:.1f}ms)")
```

#### **2. 一對一回報確認**
```python
# 建倉：每個成交回報對應一個部位更新
for fill_report in fill_reports:
    position_id = self._match_fill_to_position(fill_report)
    self._confirm_single_position_filled(position_id, fill_report)
```

#### **3. FOK失敗追價機制**
```python
# 建倉：FOK失敗後追價
if order_result.failed and "FOK" in order_result.error:
    retry_price = self._calculate_entry_retry_price(direction, retry_count)
    # 多單：ask1+1 追價
    # 空單：bid1-1 追價
```

## 🎯 **平倉機制重新設計**

### **設計原則**
1. **完全複製建倉邏輯** - 只改變下單方向和追價方向
2. **零風險部署** - 保留現有邏輯作為備份
3. **漸進式實施** - 可隨時開啟/關閉新機制

### **核心修改點**

#### **1. 平倉狀態更新 → 使用異步機制**

**現況問題**：
```python
# ❌ 當前平倉：同步更新，造成阻塞
def _update_position_exit_status(self, position_id, execution_result):
    with self.db_manager.get_connection() as conn:  # 阻塞操作
        cursor.execute("UPDATE position_records SET status = 'EXITED'...")
        conn.commit()  # 同步等待
```

**新設計**：
```python
# ✅ 新平倉：異步更新，參考建倉
def _update_position_exit_status_async(self, position_id, execution_result):
    if self.async_update_enabled:
        # 🚀 立即更新內存緩存（非阻塞）
        self.async_updater.schedule_position_exit_update(
            position_id=position_id,
            exit_price=execution_result.execution_price,
            exit_time=execution_result.execution_time,
            exit_reason=execution_result.exit_reason,
            order_id=execution_result.order_id,
            pnl=execution_result.pnl
        )
        
        async_elapsed = (time.time() - start_time) * 1000
        self.logger.info(f"🚀 [異步平倉] 部位{position_id}平倉確認 @{exit_price} (耗時:{async_elapsed:.1f}ms)")
    else:
        # 🛡️ 備份：同步更新（原有邏輯）
        self._update_position_exit_status_sync(position_id, execution_result)
```

#### **2. 平倉回報確認 → 一對一機制**

**現況問題**：
```python
# ❌ 當前：沒有明確的平倉回報匹配機制
# 風險管理引擎直接觸發平倉，沒有等待回報確認
```

**新設計**：
```python
# ✅ 新設計：一對一平倉回報確認
class ExitOrderTracker:
    def __init__(self):
        self.pending_exit_orders = {}  # {order_id: exit_info}
        self.exit_position_mapping = {}  # {position_id: order_id}
    
    def register_exit_order(self, position_id, order_id, exit_params):
        """註冊平倉訂單，等待回報確認"""
        exit_info = {
            'position_id': position_id,
            'order_id': order_id,
            'direction': exit_params['direction'],
            'quantity': exit_params['quantity'],
            'price': exit_params['price'],
            'submit_time': time.time(),
            'status': 'PENDING'
        }
        
        self.pending_exit_orders[order_id] = exit_info
        self.exit_position_mapping[position_id] = order_id
    
    def confirm_exit_fill(self, fill_report):
        """確認平倉成交回報 - 一對一匹配"""
        matched_order = self._match_exit_fill_to_order(fill_report)
        if matched_order:
            position_id = matched_order['position_id']
            
            # 🚀 異步更新部位狀態
            self._update_position_exit_async(position_id, fill_report)
            
            # 清理已完成的訂單
            self._cleanup_completed_exit_order(matched_order['order_id'])
            
            return True
        return False
```

#### **3. 平倉追價機制 → 反向追價邏輯**

**建倉追價邏輯**：
```python
# 建倉追價：
# 多單建倉失敗 → ask1+1 追價（往上追）
# 空單建倉失敗 → bid1-1 追價（往下追）
```

**平倉追價邏輯**：
```python
# ✅ 平倉追價：方向相反
def _calculate_exit_retry_price(self, original_direction, retry_count):
    """計算平倉追價價格 - 與建倉方向相反"""
    
    if original_direction == 'LONG':
        # 多單平倉 = 賣出 → 使用bid1-1追價（往下追，確保成交）
        current_bid1 = self._get_current_bid1()
        retry_price = current_bid1 - retry_count
        
        if self.console_enabled:
            print(f"[EXIT_RETRY] 多單平倉追價: bid1({current_bid1}) - {retry_count} = {retry_price}")
            
    else:  # SHORT
        # 空單平倉 = 買進 → 使用ask1+1追價（往上追，確保成交）
        current_ask1 = self._get_current_ask1()
        retry_price = current_ask1 + retry_count
        
        if self.console_enabled:
            print(f"[EXIT_RETRY] 空單平倉追價: ask1({current_ask1}) + {retry_count} = {retry_price}")
    
    return retry_price

def execute_exit_retry(self, position_id, original_order, retry_count):
    """執行平倉追價 - 參考建倉追價邏輯"""
    try:
        # 1. 計算追價價格
        position_info = self.db_manager.get_position_by_id(position_id)
        retry_price = self._calculate_exit_retry_price(
            position_info['direction'], retry_count
        )
        
        # 2. 執行追價下單
        exit_direction = "SELL" if position_info['direction'] == "LONG" else "BUY"
        
        retry_result = self.virtual_real_order_manager.execute_strategy_order(
            direction=exit_direction,
            quantity=1,
            price=retry_price,
            signal_source=f"exit_retry_{position_id}_{retry_count}",
            order_type="FOK",
            new_close=1  # 平倉
        )
        
        # 3. 註冊追價訂單
        if retry_result.success:
            self.exit_tracker.register_exit_order(
                position_id=position_id,
                order_id=retry_result.order_id,
                exit_params={
                    'direction': exit_direction,
                    'quantity': 1,
                    'price': retry_price,
                    'retry_count': retry_count
                }
            )
        
        return retry_result.success
        
    except Exception as e:
        self.logger.error(f"平倉追價失敗: {e}")
        return False
```

## 🔧 **實施計劃**

### **階段1: 異步平倉狀態更新（1天）**

#### **1.1 擴展異步更新器**
**檔案**: `async_db_updater.py`
```python
def schedule_position_exit_update(self, position_id, exit_price, exit_time, 
                                exit_reason, order_id, pnl):
    """排程部位平倉更新 - 參考建倉更新邏輯"""
    task = UpdateTask(
        task_type='position_exit',
        position_id=position_id,
        exit_price=exit_price,
        exit_time=exit_time,
        exit_reason=exit_reason,
        order_id=order_id,
        pnl=pnl,
        timestamp=time.time()
    )
    
    # 🚀 立即更新內存緩存
    self._update_exit_cache_immediately(position_id, task)
    
    # 📝 排程資料庫更新
    self.update_queue.put(task)

def _update_exit_cache_immediately(self, position_id, task):
    """立即更新平倉緩存 - 參考建倉緩存邏輯"""
    with self.cache_lock:
        if 'exit_positions' not in self.memory_cache:
            self.memory_cache['exit_positions'] = {}
        
        self.memory_cache['exit_positions'][position_id] = {
            'status': 'EXITED',
            'exit_price': task.exit_price,
            'exit_time': task.exit_time,
            'exit_reason': task.exit_reason,
            'order_id': task.order_id,
            'pnl': task.pnl,
            'cache_time': time.time()
        }

def get_cached_exit_status(self, position_id):
    """獲取緩存的平倉狀態"""
    with self.cache_lock:
        exit_cache = self.memory_cache.get('exit_positions', {})
        return exit_cache.get(position_id)
```

#### **1.2 修改停損執行器**
**檔案**: `stop_loss_executor.py`
```python
def _update_position_exit_status(self, position_id, execution_result, trigger_info):
    """更新部位平倉狀態 - 使用異步機制"""
    try:
        if hasattr(self, 'async_updater') and self.async_updater and self.async_update_enabled:
            # 🚀 異步更新（非阻塞）
            self.async_updater.schedule_position_exit_update(
                position_id=position_id,
                exit_price=execution_result.execution_price,
                exit_time=execution_result.execution_time,
                exit_reason=getattr(trigger_info, 'trigger_reason', 'STOP_LOSS'),
                order_id=execution_result.order_id,
                pnl=execution_result.pnl
            )
            
            if self.console_enabled:
                print(f"[STOP_EXECUTOR] 🚀 異步平倉更新已排程: 部位{position_id}")
        else:
            # 🛡️ 備份：同步更新（原有邏輯）
            self._update_position_exit_status_sync(position_id, execution_result, trigger_info)
            
    except Exception as e:
        self.logger.error(f"平倉狀態更新失敗: {e}")
        # 異步失敗時回退到同步
        self._update_position_exit_status_sync(position_id, execution_result, trigger_info)
```

### **階段2: 一對一平倉回報確認（1天）**

#### **2.1 創建平倉訂單追蹤器**
**檔案**: `exit_order_tracker.py`
```python
class ExitOrderTracker:
    """平倉訂單追蹤器 - 參考建倉追蹤邏輯"""
    
    def __init__(self, db_manager, console_enabled=True):
        self.db_manager = db_manager
        self.console_enabled = console_enabled
        self.data_lock = threading.RLock()
        
        # 平倉訂單追蹤 - 參考建倉結構
        self.pending_exit_orders = {}  # {order_id: exit_info}
        self.exit_position_mapping = {}  # {position_id: order_id}
        
        # 統計信息
        self.stats = {
            'total_exits': 0,
            'confirmed_exits': 0,
            'failed_exits': 0
        }
    
    def register_exit_order(self, position_id, order_id, exit_params):
        """註冊平倉訂單 - 參考建倉註冊邏輯"""
        # 實現邏輯...
    
    def process_exit_fill_report(self, fill_report):
        """處理平倉成交回報 - 參考建倉回報處理"""
        # 實現邏輯...
```

#### **2.2 整合到簡化追蹤器**
**檔案**: `simplified_order_tracker.py`
```python
def _handle_exit_fill_report(self, price: float, qty: int, product: str) -> bool:
    """處理平倉成交回報 - 一對一確認機制"""
    try:
        with self.data_lock:
            # 🎯 一對一匹配平倉訂單
            exit_order = self._find_matching_exit_order_fifo(price, qty, product)
            if not exit_order:
                return False
            
            position_id = exit_order['position_id']
            
            # 🚀 異步更新部位狀態（參考建倉）
            if hasattr(self, 'async_updater') and self.async_updater:
                self.async_updater.schedule_position_exit_update(
                    position_id=position_id,
                    exit_price=price,
                    exit_time=datetime.now().strftime('%H:%M:%S'),
                    exit_reason='MARKET_EXIT',
                    order_id=exit_order['order_id'],
                    pnl=self._calculate_exit_pnl(exit_order, price)
                )
            
            # 更新訂單狀態
            exit_order['status'] = 'FILLED'
            
            # 觸發回調
            self._trigger_exit_fill_callbacks(exit_order, price, qty)
            
            # 清理完成的訂單
            self._cleanup_completed_exit_order(exit_order['order_id'])
            
            return True
            
    except Exception as e:
        if self.console_enabled:
            print(f"[SIMPLIFIED_TRACKER] ❌ 平倉回報處理失敗: {e}")
        return False
```

### **階段3: 平倉追價機制（1天）**

#### **3.1 實現平倉追價邏輯**
**檔案**: `stop_loss_executor.py`
```python
def execute_exit_with_retry(self, position_info, exit_params, max_retries=5):
    """執行平倉含追價機制 - 參考建倉追價"""
    position_id = position_info['id']
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            if retry_count == 0:
                # 首次嘗試：使用原始價格
                exit_price = exit_params['price']
            else:
                # 追價：計算新價格
                exit_price = self._calculate_exit_retry_price(
                    position_info['direction'], retry_count
                )
            
            # 執行平倉下單
            result = self._execute_single_exit_order(
                position_info, exit_params['direction'], 
                exit_params['quantity'], exit_price
            )
            
            if result.success:
                # 成功：註冊訂單等待回報
                self.exit_tracker.register_exit_order(
                    position_id, result.order_id, exit_params
                )
                return result
            
            # 失敗：檢查是否需要追價
            if self._should_retry_exit(result.error_message):
                retry_count += 1
                if self.console_enabled:
                    print(f"[EXIT_RETRY] 平倉失敗，準備第{retry_count}次追價")
                continue
            else:
                # 不可重試的錯誤
                break
                
        except Exception as e:
            self.logger.error(f"平倉執行失敗: {e}")
            break
    
    # 所有重試都失敗
    return StopLossExecutionResult(position_id, False, 
                                 error_message=f"平倉失敗，已重試{retry_count}次")

def _should_retry_exit(self, error_message):
    """判斷是否應該重試平倉 - 參考建倉重試邏輯"""
    retry_keywords = ["FOK", "無法成交", "價格偏離", "委託失敗"]
    return any(keyword in error_message for keyword in retry_keywords)
```

## 📊 **預期效果**

### **性能改善**
| 指標 | 修復前 | 修復後 | 改善幅度 |
|------|--------|--------|----------|
| 平倉確認延遲 | 14秒 | 0.1秒 | 99.9% |
| 重複平倉訂單 | 50+次 | 0次 | 100% |
| 平倉成功率 | 50% | 95%+ | 90% |
| 系統響應性 | 中等 | 高 | 顯著提升 |

### **功能完整性**
- ✅ **異步狀態更新** - 與建倉相同的高性能機制
- ✅ **一對一回報確認** - 確保每個平倉都有對應的狀態更新
- ✅ **FOK失敗追價** - 提高平倉成功率
- ✅ **零風險部署** - 可隨時回退到原有機制

## 🎯 **總結**

這個重新設計計劃**完全基於建倉機制的成功經驗**：
1. **複製成功模式** - 異步更新、一對一確認、追價機制
2. **只改變方向** - 下單方向和追價方向相反，其他邏輯相同
3. **漸進式實施** - 分3個階段，每個階段1天，總共3天完成

**關鍵優勢**：
- 使用已驗證的成功機制，風險極低
- 性能與建倉相同，解決阻塞問題
- 完整的追價機制，提高平倉成功率
- 可隨時開啟/關閉，便於測試和部署
