# simple_integrated.py 交易生命週期分析 - 從建倉到初始風控

## 概覽
本文檔詳細分析 `simple_integrated.py` 中一筆交易從無到有的完整過程，重點關注進場觸發、下單執行、追價機制和初始風險控制。

## 1. 建倉 (Position Entry)

### 🎯 **進場的確切觸發條件**

#### **多單進場條件**
```python
def check_minute_candle_breakout_safe(self):
    """1分K線收盤價突破檢測 - 只檢測多單"""
    close_price = self.current_minute_candle['close']
    
    # 🔥 多單觸發：1分K收盤價突破區間上軌
    if close_price > self.range_high:
        self.first_breakout_detected = True
        self.breakout_direction = 'LONG'
        self.waiting_for_entry = True
        
        # 記錄突破事件
        self.add_strategy_log(f"🔥 {minute:02d}分K線收盤突破上緣！收盤:{close_price:.0f} > 上緣:{self.range_high:.0f}")
        self.add_strategy_log(f"⏳ 等待下一個報價進場做多...")
```

**特點**：
- **保守進場**：使用1分K收盤價，避免假突破
- **信號延遲**：檢測到突破後等待下一個報價進場
- **單次觸發**：`first_breakout_detected` 防止重複進場

#### **空單進場條件**
```python
def check_immediate_short_entry_safe(self, price, time_str):
    """即時空單進場檢測 - 不等1分K收盤"""
    
    # 🚀 空單觸發：任何報價跌破區間下軌立即觸發
    if price < self.range_low:
        self.first_breakout_detected = True
        self.breakout_direction = 'SHORT'
        self.waiting_for_entry = True
        
        # 記錄突破事件
        self.add_strategy_log(f"🔥 即時空單觸發！報價:{price:.0f} < 下緣:{self.range_low:.0f}")
        self.add_strategy_log(f"⚡ 立即進場做空（不等1分K收盤）...")
```

**特點**：
- **積極進場**：任何報價跌破即觸發，不等K線收盤
- **即時響應**：適合捕捉快速下跌行情
- **風險較高**：可能遇到假突破

### 🚀 **程式碼執行下單機制**

#### **下單類型：FOK (Fill or Kill)**
```python
def execute_strategy_order(self, direction: str, signal_source: str = "strategy_breakout"):
    """執行策略下單 - 統一入口"""
    
    # 建立下單參數
    order_params = OrderParams(
        account=self.default_account,
        product=product,
        direction=direction,
        quantity=1,  # 每筆固定1口
        price=price,
        order_type="FOK",  # 🎯 全部成交或全部取消
        new_close=0,  # 新倉
        day_trade="N",  # 非當沖
        signal_source=signal_source
    )
```

**FOK特點**：
- **全部成交或全部取消**：不接受部分成交
- **避免部位混亂**：確保每筆訂單要麼完全成交要麼完全失敗
- **適合快速市場**：在波動市場中確保執行品質

#### **價格選擇策略**
```python
# 多單進場 (BUY)
if direction == 'BUY':
    price = self.get_ask1_price(product)  # 使用ASK1價格
    price_type = "ASK1"

# 空單進場 (SELL) 
elif direction == 'SELL':
    price = self.get_bid1_price(product)  # 使用BID1價格
    price_type = "BID1"
```

**價格邏輯**：
- **多單進場**：使用ASK1價格，向賣方買進
- **空單進場**：使用BID1價格，向買方賣出
- **市價邏輯**：使用最佳價格確保成交機率

### 📊 **下單數量決定機制**

#### **多筆1口策略**
```python
def enter_position_safe(self, direction, price, time_str):
    """安全的建倉處理"""
    
    # 🎯 取得策略配置的總口數
    total_lots = self.virtual_real_order_manager.get_strategy_quantity()
    
    # 🔧 執行多筆1口下單（統一採用多筆1口策略）
    success_count = 0
    for lot_id in range(1, total_lots + 1):
        order_result = self.virtual_real_order_manager.execute_strategy_order(
            direction=direction,
            quantity=1,  # 🎯 強制每筆1口FOK
            signal_source=f"single_strategy_lot_{lot_id}"
        )
        
        if order_result.success:
            success_count += 1
            print(f"🚀 [STRATEGY] 第{lot_id}口下單成功")
```

#### **數量配置來源**
```python
def get_strategy_quantity(self) -> int:
    """取得策略配置的數量"""
    try:
        if self.strategy_config and hasattr(self.strategy_config, 'trade_size_in_lots'):
            return self.strategy_config.trade_size_in_lots
        return 1  # 預設1口
    except:
        return 1
```

**數量特點**：
- **固定數量**：不是基於凱利公式等動態計算
- **配置驅動**：由 `strategy_config.trade_size_in_lots` 決定
- **預設保守**：預設1口，避免過度風險
- **多筆分散**：每筆1口分別下單，降低滑價風險

## 2. 追價 (Price Chasing)

### 🔄 **追價觸發機制**

#### **FOK失敗觸發追價**
```python
def process_order_reply(self, reply_data: str) -> bool:
    """處理訂單回報 - 簡化FIFO邏輯"""
    
    # 解析回報類型
    if reply_type == 'C':  # 取消
        # 🔧 FOK失敗觸發追價
        if self.needs_retry(is_partial_fill=False):
            self.retry_count += 1
            self.status = OrderStatus.RETRYING
            
            # 觸發追價回調
            if self.exit_retry_callbacks:
                for callback in self.exit_retry_callbacks:
                    callback(exit_order_dict, self.retry_count)
```

#### **追價條件檢查**
```python
def needs_retry(self, is_partial_fill: bool = False) -> bool:
    """檢查是否需要追價"""
    remaining_lots = self.total_lots - self.filled_lots
    
    # 基本條件檢查
    if remaining_lots <= 0 or self.retry_count >= self.max_retries:
        return False
    
    # 根據追價類型檢查開關
    if is_partial_fill:
        return self.enable_partial_retry  # 部分成交追價（預設關閉）
    else:
        return self.enable_cancel_retry   # 取消追價（預設開啟）
```

### 💰 **追價價格計算**

#### **平倉追價邏輯**
```python
def _calculate_exit_retry_price(self, original_direction: str, retry_count: int) -> float:
    """計算平倉追價價格"""
    
    # 獲取當前市價
    current_ask1 = self.get_current_ask1()
    current_bid1 = self.get_current_bid1()
    
    if original_direction.upper() == "LONG":
        # 🔧 多單平倉：使用BID1 - retry_count點 (向下追價)
        retry_price = current_bid1 - retry_count
        print(f"🔄 多單平倉追價計算: BID1({current_bid1}) - {retry_count} = {retry_price}")
        return retry_price
        
    elif original_direction.upper() == "SHORT":
        # 🔧 空單平倉：使用ASK1 + retry_count點 (向上追價)
        retry_price = current_ask1 + retry_count
        print(f"🔄 空單平倉追價計算: ASK1({current_ask1}) + {retry_count} = {retry_price}")
        return retry_price
```

**追價邏輯**：
- **多單平倉**：BID1 - retry_count，向下追價確保賣出
- **空單平倉**：ASK1 + retry_count，向上追價確保買進
- **遞進追價**：每次重試價格更積極
- **市價導向**：基於當前最佳價格計算

### 🛡️ **追價限制機制**

#### **重試次數限制**
```python
def on_exit_retry(exit_order: dict, retry_count: int):
    """平倉追價回調函數"""
    
    # 檢查追價限制
    max_retries = 5
    if retry_count > max_retries:
        print(f"❌ 部位{position_id}追價次數超限({retry_count}>{max_retries})")
        return
```

#### **滑價限制保護**
```python
# 檢查滑價限制
original_price = exit_order.get('original_price', 0)
max_slippage = 5
if original_price and abs(retry_price - original_price) > max_slippage:
    print(f"❌ 部位{position_id}追價滑價超限: {abs(retry_price - original_price):.0f}點")
    return
```

**限制特點**：
- **最大重試5次**：避免無限追價
- **滑價限制5點**：控制追價成本
- **智能放棄**：超限時自動停止追價

## 3. 初始止損 (Initial Stop-Loss)

### 🛡️ **停損點計算方式**

#### **基於區間邊界的停損**
```python
def enter_position_safe(self, direction, price, time_str):
    """建倉時設定初始停損"""
    
    # 記錄部位資訊（隱含停損設定）
    self.current_position = {
        'direction': direction,
        'entry_price': price,
        'entry_time': time_str,
        'quantity': 1,
        # 停損點隱含在區間邊界中
        # 多單停損：self.range_low
        # 空單停損：self.range_high
    }
```

#### **停損觸發檢查**
```python
def check_exit_conditions_safe(self, price, time_str):
    """出場條件檢查 - 包含初始停損"""
    
    direction = self.current_position['direction']
    entry_price = self.current_position['entry_price']
    
    # 🛡️ 初始停損檢查 (區間邊界)
    if direction == "LONG" and price <= self.range_low:
        self.exit_position_safe(price, time_str, f"初始停損 {self.range_low:.0f}")
        return
    elif direction == "SHORT" and price >= self.range_high:
        self.exit_position_safe(price, time_str, f"初始停損 {self.range_high:.0f}")
        return
```

### 📐 **停損計算邏輯**

**停損設定特點**：
- **多單停損**：區間下軌 (`range_low`)
- **空單停損**：區間上軌 (`range_high`)
- **固定停損**：不是基於固定點數，而是基於技術指標（區間邊界）
- **邏輯一致**：進場突破區間，停損回到區間內

**停損距離範例**：
```
假設區間：上軌 17,450，下軌 17,400 (區間50點)

多單進場：17,451 (突破上軌)
多單停損：17,400 (區間下軌) → 停損距離 51點

空單進場：17,399 (跌破下軌)  
空單停損：17,450 (區間上軌) → 停損距離 51點
```

### 🔍 **停損監控方式**

#### **程式內部邏輯監控**
```python
# 在每個報價更新時檢查停損
def process_strategy_logic_safe(self, price, time_str):
    """主策略邏輯處理"""
    
    # 出場條件檢查（有部位時）
    if self.current_position:
        self.check_exit_conditions_safe(price, time_str)
```

**監控特點**：
- **軟體監控**：不是掛實際停損單到券商
- **即時檢查**：每個報價都檢查停損條件
- **程式控制**：由程式邏輯決定是否觸發停損
- **靈活性高**：可以整合複雜的停損邏輯

#### **停損執行流程**
```python
def exit_position_safe(self, price, time_str, reason):
    """安全平倉處理"""
    
    # 計算損益
    direction = self.current_position['direction']
    entry_price = self.current_position['entry_price']
    
    if direction == "LONG":
        pnl = (price - entry_price) * 50  # 台指期每點50元
    else:  # SHORT
        pnl = (entry_price - price) * 50
    
    # 記錄交易日誌
    self.add_strategy_log(f"🔚 {direction} 平倉 @{price:.0f} 原因:{reason} 損益:{pnl:+.0f}元")
    
    # 清除部位狀態
    self.current_position = None
    self.first_breakout_detected = False
```

## 4. 總結

### 🎯 **交易生命週期特點**

1. **保守的多單進場**：1分K收盤價突破，避免假突破
2. **積極的空單進場**：即時報價突破，捕捉快速下跌
3. **FOK下單策略**：全部成交或全部取消，確保執行品質
4. **多筆1口分散**：降低滑價風險，提高成交機率
5. **智能追價機制**：最多5次重試，滑價限制5點
6. **區間邊界停損**：基於技術指標的固定停損點
7. **軟體監控停損**：程式內部邏輯，靈活性高

### 🔧 **風險控制設計**

- **進場風控**：突破確認 + 信號延遲
- **執行風控**：FOK下單 + 多筆分散
- **追價風控**：重試限制 + 滑價保護  
- **停損風控**：固定停損點 + 即時監控

這個系統在進場到初始風控的設計上體現了專業的量化交易思維，平衡了執行效率和風險控制。
