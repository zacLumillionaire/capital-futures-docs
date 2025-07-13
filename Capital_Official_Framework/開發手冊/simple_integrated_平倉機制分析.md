# simple_integrated.py 平倉機制詳細分析

## 📋 概述

本文檔詳細分析 `simple_integrated.py` 策略下單機的平倉機制，包括平倉觸發條件、平倉下單與回報、回報確認失敗後追價、成功確認方式和資料庫更新等核心技術實現。

## 🎯 1. 平倉觸發條件

### 1.1 單一策略平倉觸發條件

**核心函數**: `check_exit_conditions_safe(price, time_str)`

```python
def check_exit_conditions_safe(self, price, time_str):
    """安全的出場檢查 - 按優先級順序"""
    try:
        if not self.current_position:
            return

        direction = self.current_position['direction']
        entry_price = self.current_position['entry_price']

        # 優先級1: 收盤平倉 (13:30) - 最高優先級
        if hasattr(self, 'single_strategy_eod_close_var') and self.single_strategy_eod_close_var.get():
            hour, minute, second = map(int, time_str.split(':'))
            if hour >= 13 and minute >= 30:
                self.exit_position_safe(price, time_str, "收盤平倉")
                return

        # 優先級2: 初始停損 (區間邊界)
        if direction == "LONG" and price <= self.range_low:
            self.exit_position_safe(price, time_str, f"初始停損 {self.range_low:.0f}")
            return
        elif direction == "SHORT" and price >= self.range_high:
            self.exit_position_safe(price, time_str, f"初始停損 {self.range_high:.0f}")
            return

        # 優先級3: 移動停利
        self.check_trailing_stop_logic(price, time_str)

    except Exception as e:
        pass
```

**觸發條件優先級**:
1. **收盤平倉** (13:30): 最高優先級，強制平倉所有部位
2. **初始停損**: 價格觸及區間邊界 (range_low/range_high)
3. **移動停利**: 20%回撤觸發平倉
4. **手動平倉**: 使用者手動觸發

### 1.2 移動停利觸發邏輯

**回撤計算與觸發**:
```python
def check_trailing_stop_logic(self, price, time_str):
    """移動停利邏輯檢查"""
    
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

### 1.3 多組策略平倉觸發條件

**風險管理引擎**: `RiskManagementEngine.check_all_exit_conditions()`

```python
def check_all_exit_conditions(self, current_price: float, current_time: str) -> List[Dict]:
    """檢查所有出場條件"""
    
    exit_actions = []
    
    # 🕐 檢查收盤平倉 (13:30) - 最高優先級
    eod_close_exits = self._check_eod_close_conditions(positions, current_price, current_time)
    if eod_close_exits:
        exit_actions.extend(eod_close_exits)
        return exit_actions

    # 檢查初始停損 (第二優先級)
    initial_stop_exits = self._check_initial_stop_loss(positions, current_price)
    if initial_stop_exits:
        # 初始停損觸發，全組出場
        for position in positions:
            pnl = self._calculate_pnl(position, current_price)
            exit_actions.append({
                'position_id': position['id'],
                'exit_price': current_price,
                'exit_time': current_time,
                'exit_reason': '初始停損',
                'pnl': pnl
            })
        return exit_actions
    
    # 檢查各口的個別出場條件
    for position in positions:
        # 檢查保護性停損
        if self._check_protective_stop_loss(position, current_price):
            exit_actions.append({
                'position_id': position['id'],
                'exit_price': position['current_stop_loss'],
                'exit_time': current_time,
                'exit_reason': '保護性停損',
                'pnl': self._calculate_pnl(position, current_price)
            })
            continue
        
        # 檢查移動停利條件
        trailing_exit = self._check_trailing_stop_conditions(position, current_price, current_time)
        if trailing_exit:
            exit_actions.append(trailing_exit)
            continue
    
    return exit_actions
```

## 🚀 2. 平倉下單執行

### 2.1 單一策略平倉下單

**核心函數**: `exit_position_safe(price, time_str, reason)`

```python
def exit_position_safe(self, price, time_str, reason):
    """安全的出場處理 - 包含完整損益計算"""
    try:
        if not self.current_position:
            return

        direction = self.current_position['direction']
        entry_price = self.current_position['entry_price']
        entry_time = self.current_position['entry_time']

        # 計算損益
        pnl = (price - entry_price) if direction == "LONG" else (entry_price - price)
        pnl_money = pnl * 50  # 每點50元

        # 計算持倉時間
        try:
            entry_h, entry_m, entry_s = map(int, entry_time.split(':'))
            exit_h, exit_m, exit_s = map(int, time_str.split(':'))
            entry_seconds = entry_h * 3600 + entry_m * 60 + entry_s
            exit_seconds = exit_h * 3600 + exit_m * 60 + exit_s
            hold_seconds = exit_seconds - entry_seconds
            hold_minutes = hold_seconds // 60
        except:
            hold_minutes = 0

        # 記錄交易日誌
        self.add_strategy_log(f"🔚 {direction} 平倉 @{price:.0f} 原因:{reason} 損益:{pnl:+.0f}點 持倉:{hold_minutes}分")

        # 清除部位狀態
        self.current_position = None
        self.first_breakout_detected = False

        # Console輸出
        print(f"✅ [STRATEGY] {direction}平倉 @{price:.0f} {reason} 損益:{pnl_money:+.0f}元")

        # 🔧 實際下單邏輯（如果啟用下單系統）
        if hasattr(self, 'virtual_real_order_manager') and self.virtual_real_order_manager:
            # 確定平倉方向
            exit_direction = "SELL" if direction == "LONG" else "BUY"
            
            # 執行平倉下單
            order_result = self.virtual_real_order_manager.execute_strategy_order(
                direction=exit_direction,
                signal_source=f"exit_{reason}",
                product="TM0000",
                price=price,
                quantity=1,
                new_close=1  # 設定為平倉
            )
            
            if order_result.success:
                print(f"✅ [STRATEGY] 平倉下單成功: {order_result.order_id}")
            else:
                print(f"❌ [STRATEGY] 平倉下單失敗: {order_result.error}")

    except Exception as e:
        self.add_strategy_log(f"❌ 平倉失敗: {e}")
```

### 2.2 多組策略平倉下單

**統一出場管理器**: `UnifiedExitManager.execute_exit_order()`

```python
def execute_exit_order(self, position_info: Dict, exit_price: float, exit_reason: str) -> bool:
    """執行出場下單"""
    try:
        # 1. 確定出場方向
        original_direction = position_info['direction']
        if original_direction.upper() == "LONG":
            exit_direction = "SELL"  # 多單出場 → 賣出
        elif original_direction.upper() == "SHORT":
            exit_direction = "BUY"   # 空單出場 → 買回
        else:
            self.logger.error(f"無效的原始方向: {original_direction}")
            return False
        
        # 2. 使用與進場相同的下單方法，但設定為平倉
        order_result = self.order_manager.execute_strategy_order(
            direction=exit_direction,
            signal_source=f"exit_{exit_reason}_{position_info['id']}",
            product="TM0000",
            price=exit_price,
            quantity=1,
            new_close=1  # 🔧 設定為平倉 (1=平倉)
        )
        
        # 3. 檢查下單結果
        if order_result.success:
            if self.console_enabled:
                print(f"[UNIFIED_EXIT] ✅ 平倉下單成功: 部位{position_info['id']} "
                      f"訂單{order_result.order_id}")
            
            # 4. 註冊到平倉追蹤器
            if hasattr(self, 'exit_tracker') and self.exit_tracker:
                self.exit_tracker.register_exit_order(
                    position_id=position_info['id'],
                    order_id=order_result.order_id,
                    direction=exit_direction,
                    quantity=1,
                    price=exit_price,
                    product="TM0000"
                )
            
            return True
        else:
            if self.console_enabled:
                print(f"[UNIFIED_EXIT] ❌ 平倉下單失敗: {order_result.error}")
            return False
            
    except Exception as e:
        self.logger.error(f"執行平倉下單失敗: {e}")
        return False
```

## 📡 3. 平倉回報處理機制

### 3.1 SimplifiedOrderTracker 平倉回報處理

**核心函數**: `_handle_exit_fill_report(price, qty, product)`

```python
def _handle_exit_fill_report(self, price: float, qty: int, product: str) -> bool:
    """處理平倉成交回報"""
    try:
        with self.data_lock:
            # 🔍 DEBUG: 平倉成交回報處理 (重要事件，立即輸出)
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 📥 收到平倉成交回報:")
                print(f"[SIMPLIFIED_TRACKER]   價格: {price:.0f} 數量: {qty} 商品: {product}")
                print(f"[SIMPLIFIED_TRACKER]   待匹配平倉訂單: {len(self.exit_orders)}個")

            # 🔧 優先使用專門的平倉追蹤器
            if self.exit_tracker:
                # 使用新的平倉追蹤器處理
                from exit_order_tracker import ExitFillReport
                fill_report = ExitFillReport(
                    order_id="",  # 將在匹配時確定
                    position_id=0,  # 將在匹配時確定
                    fill_price=price,
                    fill_quantity=qty,
                    fill_time=datetime.now().strftime('%H:%M:%S'),
                    product=product
                )

                processed = self.exit_tracker.process_exit_fill_report(fill_report)
                if processed:
                    if self.console_enabled:
                        print(f"[SIMPLIFIED_TRACKER] ✅ 新追蹤器處理平倉成交完成")
                    return True

            # 🔧 備用：使用內建平倉訂單匹配
            exit_order = self._find_matching_exit_order_fifo(price, qty, product)
            if not exit_order:
                if self.console_enabled:
                    print(f"[SIMPLIFIED_TRACKER] ⚠️ 找不到匹配的平倉訂單")
                return False

            # 更新平倉訂單狀態
            exit_order['status'] = 'FILLED'
            position_id = exit_order['position_id']

            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] ✅ 平倉成交確認: 部位{position_id} "
                      f"{qty}口 @{price:.0f}")

            # 觸發平倉成交回調
            self._trigger_exit_fill_callbacks(exit_order, price, qty)

            # 清理已完成的平倉訂單
            self._cleanup_completed_exit_order(exit_order['order_id'])

            return True

    except Exception as e:
        if self.console_enabled:
            print(f"[SIMPLIFIED_TRACKER] ❌ 處理平倉成交失敗: {e}")
        return False
```

### 3.2 ExitOrderTracker 專門平倉追蹤

**核心函數**: `process_exit_fill_report(fill_report)`

```python
def process_exit_fill_report(self, fill_report: ExitFillReport) -> bool:
    """處理平倉成交回報"""
    try:
        with self.data_lock:
            # 🎯 一對一匹配平倉訂單（參考建倉FIFO邏輯）
            exit_order = self._find_matching_exit_order_fifo(
                fill_report.fill_price, 
                fill_report.fill_quantity, 
                fill_report.product
            )
            
            if not exit_order:
                if self.console_enabled:
                    print(f"[EXIT_TRACKER] ⚠️ 找不到匹配的平倉訂單: "
                          f"{fill_report.product} {fill_report.fill_quantity}口 @{fill_report.fill_price:.0f}")
                return False
            
            position_id = exit_order.position_id
            
            # 更新訂單狀態
            exit_order.status = ExitOrderStatus.FILLED
            
            if self.console_enabled:
                print(f"[EXIT_TRACKER] ✅ 平倉成交確認: 部位{position_id} 訂單{exit_order.order_id} "
                      f"{fill_report.fill_quantity}口 @{fill_report.fill_price:.0f}")
            
            # 🚀 異步更新部位狀態（參考建倉機制）
            if self.async_updater:
                self._update_position_exit_async(position_id, fill_report, exit_order)
            else:
                # 同步更新部位狀態
                self._update_position_exit_sync(position_id, fill_report, exit_order)
            
            # 觸發平倉成交回調
            self._trigger_fill_callbacks(exit_order, fill_report)
            
            # 清理已完成的訂單
            self._cleanup_completed_order(exit_order.order_id)
            
            return True
            
    except Exception as e:
        self.logger.error(f"處理平倉成交回報失敗: {e}")
        return False
```

## 🔄 4. 回報確認失敗後追價機制

### 4.1 追價觸發條件

**取消回報觸發追價**:
```python
def _handle_exit_cancel_report(self, price: float, qty: int, product: str) -> bool:
    """處理平倉取消回報 - 觸發追價機制"""
    try:
        with self.data_lock:
            # 找到被取消的平倉訂單
            exit_order = self._find_matching_exit_order_fifo(price, qty, product)
            if not exit_order:
                return False
            
            # 更新訂單狀態為取消
            exit_order['status'] = 'CANCELLED'
            position_id = exit_order['position_id']
            
            if self.console_enabled:
                print(f"[SIMPLIFIED_TRACKER] 📋 平倉訂單取消: 部位{position_id} "
                      f"{qty}口 @{price:.0f}")
            
            # 觸發追價回調
            self._trigger_exit_retry_callbacks(exit_order, "CANCELLED")
            
            return True
            
    except Exception as e:
        if self.console_enabled:
            print(f"[SIMPLIFIED_TRACKER] ❌ 處理平倉取消失敗: {e}")
        return False
```

### 4.2 追價價格計算

**核心函數**: `_calculate_exit_retry_price(original_direction, retry_count)`

```python
def _calculate_exit_retry_price(self, original_direction: str, retry_count: int) -> Optional[float]:
    """計算平倉追價價格"""
    try:
        if self.console_enabled:
            print(f"[MAIN] 🔄 計算平倉追價: {original_direction} 第{retry_count}次")

        # 獲取當前市價
        current_ask1 = None
        current_bid1 = None
        
        if hasattr(self, 'virtual_real_order_manager') and self.virtual_real_order_manager:
            current_ask1 = self.virtual_real_order_manager.get_ask1_price("TM0000")
            current_bid1 = self.virtual_real_order_manager.get_bid1_price("TM0000")

        # 檢查是否成功獲取市價
        if current_ask1 > 0 and current_bid1 > 0:
            if original_direction.upper() == "LONG":
                # 🔧 多單平倉：使用BID1 - retry_count點 (向下追價)
                retry_price = current_bid1 - retry_count
                if self.console_enabled:
                    print(f"[MAIN] 🔄 多單平倉追價計算: BID1({current_bid1}) - {retry_count} = {retry_price}")
                return retry_price
            elif original_direction.upper() == "SHORT":
                # 🔧 空單平倉：使用ASK1 + retry_count點 (向上追價)
                retry_price = current_ask1 + retry_count
                if self.console_enabled:
                    print(f"[MAIN] 🔄 空單平倉追價計算: ASK1({current_ask1}) + {retry_count} = {retry_price}")
                return retry_price
        else:
            if self.console_enabled:
                print(f"[MAIN] ❌ 無法獲取有效市價: ASK1={current_ask1}, BID1={current_bid1}")

        return None

    except Exception as e:
        if self.console_enabled:
            print(f"[MAIN] ❌ 計算追價價格失敗: {e}")
        return None
```

**追價邏輯**:
- **多單平倉**: BID1 - retry_count點，向下追價確保賣出
- **空單平倉**: ASK1 + retry_count點，向上追價確保買進
- **遞進追價**: 每次重試價格更積極
- **市價導向**: 基於當前最佳價格計算

### 4.3 追價執行與限制

**追價回調函數**: `on_exit_retry(exit_order, retry_count)`

```python
def on_exit_retry(exit_order: dict, retry_count: int):
    """平倉追價回調函數 - 執行平倉FOK追價"""
    try:
        position_id = exit_order.get('position_id')
        original_direction = exit_order.get('original_direction')
        exit_reason = exit_order.get('exit_reason', '平倉追價')

        if self.console_enabled:
            print(f"[MAIN] 🔄 收到平倉追價回調: 部位{position_id} 第{retry_count}次")

        # 檢查追價限制
        max_retries = 5
        if retry_count > max_retries:
            if self.console_enabled:
                print(f"[MAIN] ❌ 部位{position_id}追價次數超限({retry_count}>{max_retries})")
            return

        # 計算平倉追價價格
        retry_price = self._calculate_exit_retry_price(original_direction, retry_count)
        if not retry_price:
            if self.console_enabled:
                print(f"[MAIN] ❌ 部位{position_id}無法計算追價價格")
            return

        # 檢查滑價限制
        original_price = exit_order.get('original_price', 0)
        max_slippage = 5
        if original_price and abs(retry_price - original_price) > max_slippage:
            if self.console_enabled:
                print(f"[MAIN] ❌ 部位{position_id}追價滑價超限: {abs(retry_price - original_price):.0f}點")
            return

        # 確定平倉方向
        exit_direction = "SELL" if original_direction.upper() == "LONG" else "BUY"

        # 使用虛實單管理器執行追價下單
        if hasattr(self, 'virtual_real_order_manager') and self.virtual_real_order_manager:
            order_result = self.virtual_real_order_manager.execute_strategy_order(
                direction=exit_direction,
                signal_source=f"exit_retry_{position_id}_{retry_count}",
                product="TM0000",
                price=retry_price,
                quantity=1,
                new_close=1  # 平倉
            )
            success = order_result.success if order_result else False

            if success:
                if self.console_enabled:
                    print(f"[MAIN] ✅ 部位{position_id}第{retry_count}次追價下單成功")
            else:
                if self.console_enabled:
                    print(f"[MAIN] ❌ 部位{position_id}第{retry_count}次追價下單失敗")

    except Exception as e:
        if self.console_enabled:
            print(f"[MAIN] ❌ 平倉追價回調異常: {e}")
```

**追價限制機制**:
- **最大重試次數**: 5次
- **滑價限制**: 最大5點滑價保護
- **時間限制**: 30秒內必須完成
- **智能放棄**: 超限時自動停止追價

## ✅ 5. 成功確認方式和資料庫更新

### 5.1 平倉成功確認流程

**成交確認步驟**:
1. **回報匹配**: 使用FIFO邏輯匹配平倉訂單與成交回報
2. **狀態更新**: 更新訂單狀態為 `FILLED`
3. **損益計算**: 計算實際損益和持倉時間
4. **資料庫更新**: 更新部位狀態為 `EXITED`
5. **回調觸發**: 觸發平倉成交回調函數
6. **清理訂單**: 清理已完成的平倉訂單記錄

### 5.2 資料庫更新機制

**同步更新**:
```python
def _update_position_exit_sync(self, position_id: int, fill_report: ExitFillReport, exit_order: ExitOrderInfo):
    """同步更新部位平倉狀態"""
    try:
        # 計算損益
        pnl = self._calculate_exit_pnl(exit_order, fill_report.fill_price)
        
        # 更新資料庫
        self.db_manager.update_position_exit(
            position_id=position_id,
            exit_price=fill_report.fill_price,
            exit_time=fill_report.fill_time,
            exit_reason='MARKET_EXIT',
            pnl=pnl
        )
        
        if self.console_enabled:
            print(f"[EXIT_TRACKER] 📊 同步更新部位{position_id}平倉狀態完成")
            
    except Exception as e:
        self.logger.error(f"同步更新部位平倉狀態失敗: {e}")
```

**異步更新**:
```python
def _update_position_exit_async(self, position_id: int, fill_report: ExitFillReport, exit_order: ExitOrderInfo):
    """異步更新部位平倉狀態"""
    try:
        # 計算損益
        pnl = self._calculate_exit_pnl(exit_order, fill_report.fill_price)
        
        # 異步更新部位狀態
        self.async_updater.schedule_position_exit_update(
            position_id=position_id,
            exit_price=fill_report.fill_price,
            exit_time=fill_report.fill_time,
            exit_reason='MARKET_EXIT',
            order_id=exit_order.order_id,
            pnl=pnl
        )
        
        if self.console_enabled:
            print(f"[EXIT_TRACKER] 🚀 異步平倉更新已排程: 部位{position_id} @{fill_report.fill_price:.0f}")
            
    except Exception as e:
        self.logger.error(f"異步更新部位平倉狀態失敗: {e}")
```

### 5.3 多組策略平倉執行

**批次平倉執行**: `execute_exit_actions(exit_actions)`

```python
def execute_exit_actions(self, exit_actions: List[Dict]) -> int:
    """執行批次平倉動作"""
    success_count = 0
    
    for action in exit_actions:
        try:
            position_id = action['position_id']
            exit_price = action['exit_price']
            exit_reason = action['exit_reason']
            
            # 使用統一出場管理器執行平倉
            success = self.unified_exit_manager.trigger_exit(
                position_id=position_id,
                exit_reason=exit_reason,
                exit_price=exit_price
            )
            
            if success:
                success_count += 1
                if self.console_enabled:
                    print(f"[MULTI_EXIT] ✅ 部位{position_id}平倉成功: {exit_reason}")
            else:
                if self.console_enabled:
                    print(f"[MULTI_EXIT] ❌ 部位{position_id}平倉失敗: {exit_reason}")
                    
        except Exception as e:
            self.logger.error(f"執行平倉動作失敗: {e}")
    
    return success_count
```

## 📊 總結

simple_integrated.py 的平倉機制採用了多層次的觸發和執行架構：

1. **觸發層**: 收盤平倉、初始停損、移動停利、保護性停損等多種觸發條件
2. **執行層**: 統一出場管理器和虛實單管理器提供標準化平倉下單
3. **追蹤層**: FIFO回報追蹤和專門的平倉訂單追蹤器
4. **追價層**: 智能追價機制，包含重試限制和滑價保護
5. **更新層**: 同步/異步資料庫更新，確保部位狀態一致性

整個系統通過追價機制、錯誤處理、批次執行等技術，確保了高效可靠的平倉執行能力。
