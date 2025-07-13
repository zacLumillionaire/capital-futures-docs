# simple_integrated.py 在倉風險管理與平倉分析

## 概覽
本文檔詳細分析 `simple_integrated.py` 中部位持有期間的動態風險管理機制，包括保護性止損、移動停利和其他平倉條件的完整實現。

## 1. 保護性止損 (Protective Stop-Loss)

### 🛡️ **保護性止損機制**

#### **單一策略模式**
在單一策略模式中，**沒有保護性止損機制**。系統只使用固定的區間邊界作為初始停損：

```python
def check_exit_conditions_safe(self, price, time_str):
    """單一策略出場檢查 - 無保護性止損"""
    
    # 🛡️ 檢查初始停損 (區間邊界) - 固定不變
    if direction == "LONG" and price <= self.range_low:
        self.exit_position_safe(price, time_str, f"初始停損 {self.range_low:.0f}")
        return
    elif direction == "SHORT" and price >= self.range_high:
        self.exit_position_safe(price, time_str, f"初始停損 {self.range_high:.0f}")
        return
```

**特點**：
- **無保本機制**：停損點不會移動到成本價
- **固定停損**：始終維持在區間邊界
- **簡化設計**：適合單一策略的簡單風控

#### **多組策略模式的保護性止損**
多組策略系統具備完整的保護性止損機制：

```python
def _check_protective_stop_loss(self, position: Dict, current_price: float) -> bool:
    """檢查保護性停損條件"""
    
    # 只有非初始停損的部位才檢查保護性停損
    if not position.get('current_stop_loss') or not position.get('protection_activated'):
        return False

    direction = position['direction']
    stop_loss_price = position['current_stop_loss']
    
    # 檢查觸發條件
    if direction == 'LONG':
        triggered = current_price <= stop_loss_price
    else:  # SHORT
        triggered = current_price >= stop_loss_price
    
    return triggered
```

#### **保護性止損啟動條件**
```python
def update_protective_stop_loss(self, position_id: int, group_id: int) -> bool:
    """更新保護性停損 - 基於累積獲利"""
    
    # 計算累積獲利
    total_profit = self._calculate_cumulative_profit(group_id, next_rule.lot_id)
    
    if total_profit <= 0:
        # 累積獲利不足，維持原始停損
        return False
    
    # 設定保護性停損
    direction = next_position['direction']
    entry_price = next_position['entry_price']
    stop_loss_amount = total_profit * float(next_rule.protective_stop_multiplier)
    
    if direction == 'LONG':
        new_stop_loss = entry_price - stop_loss_amount  # 向上移動停損
    else:  # SHORT
        new_stop_loss = entry_price + stop_loss_amount  # 向下移動停損
```

**觸發條件**：
- **前面口單獲利**：所有前面的口單都必須獲利
- **累積獲利大於零**：總獲利必須為正數
- **自動啟動**：滿足條件時自動更新停損點

**保護機制**：
- **向有利方向移動**：停損點只會向保護方向移動
- **基於累積獲利**：保護金額基於實際獲利計算
- **倍數調整**：可透過 `protective_stop_multiplier` 調整保護程度

## 2. 移動停利 (Trailing Stop)

### 🎯 **移動停利啟動條件**

#### **單一策略移動停利**
```python
def check_trailing_stop_logic(self, price, time_str):
    """移動停利邏輯檢查"""
    
    direction = self.current_position['direction']
    entry_price = self.current_position['entry_price']
    activation_points = self.current_position['trailing_activation_points']  # 15點
    trailing_activated = self.current_position['trailing_activated']
    
    # 檢查移動停利啟動條件
    if not trailing_activated:
        activation_triggered = False
        
        if direction == "LONG":
            activation_triggered = price >= entry_price + activation_points  # 獲利15點啟動
        else:  # SHORT
            activation_triggered = price <= entry_price - activation_points  # 獲利15點啟動
        
        if activation_triggered:
            self.current_position['trailing_activated'] = True
            self.add_strategy_log(f"🔔 移動停利已啟動！峰值價格: {peak_price:.0f}")
            return
```

**啟動條件**：
- **多單**：當前價格 >= 進場價格 + 15點
- **空單**：當前價格 <= 進場價格 - 15點
- **單次啟動**：一旦啟動就不會關閉

#### **多組策略移動停利**
```python
def _check_trailing_stop_conditions(self, position: Dict, current_price: float, current_time: str):
    """檢查移動停利條件 - 多組策略版本"""
    
    rule_config = position.get('rule_config', {})
    trigger_points = rule_config.get('trigger_points', 15)
    pullback_ratio = rule_config.get('pullback_percentage', 0.20) / 100.0
    
    direction = position['direction']
    entry_price = position['entry_price']
    peak_price = position.get('peak_price', entry_price)
    
    # 檢查啟動條件
    if direction == 'LONG':
        profit = peak_price - entry_price
        if profit >= trigger_points:  # 獲利達到觸發點數
            # 計算移動停利點
            stop_price = peak_price - (peak_price - entry_price) * pullback_ratio
            
            if current_price <= stop_price:
                # 觸發移動停利
                return {
                    'position_id': position['id'],
                    'exit_price': stop_price,
                    'exit_time': current_time,
                    'exit_reason': '移動停利',
                    'pnl': stop_price - entry_price
                }
```

### 📈 **追蹤邏輯**

#### **峰值價格追蹤**
```python
def check_trailing_stop_logic(self, price, time_str):
    """峰值價格即時更新"""
    
    peak_price = self.current_position['peak_price']
    
    # 更新峰值價格
    if direction == "LONG":
        if price > peak_price:
            self.current_position['peak_price'] = price
            peak_price = price
    else:  # SHORT
        if price < peak_price:
            self.current_position['peak_price'] = price
            peak_price = price
```

#### **回撤計算邏輯**
```python
# 如果移動停利已啟動，檢查回撤出場條件
if trailing_activated:
    pullback_percent = self.current_position['trailing_pullback_percent']  # 20%
    
    if direction == "LONG":
        total_gain = peak_price - entry_price  # 總獲利
        pullback_amount = total_gain * pullback_percent  # 回撤金額
        trailing_stop_price = peak_price - pullback_amount  # 移動停利點
        
        if price <= trailing_stop_price:
            # 觸發移動停利出場
            self.exit_position_safe(trailing_stop_price, time_str,
                                  f"移動停利 (峰值:{peak_price:.0f} 回撤:{pullback_amount:.1f}點)")
```

**追蹤特點**：
- **峰值追蹤**：即時更新最高價（多單）或最低價（空單）
- **百分比回撤**：預設20%回撤觸發出場
- **動態調整**：停利點隨峰值價格動態調整
- **只進不退**：峰值價格只會向有利方向更新

### 🚪 **平倉執行流程**

#### **移動停利平倉**
```python
def exit_position_safe(self, price, time_str, reason):
    """移動停利平倉執行"""
    
    direction = self.current_position['direction']
    entry_price = self.current_position['entry_price']
    
    # 計算損益
    pnl = (price - entry_price) if direction == "LONG" else (entry_price - price)
    pnl_money = pnl * 50  # 每點50元
    
    # 記錄交易日誌
    self.add_strategy_log(f"🔚 {direction} 平倉 @{price:.0f} 原因:{reason} 損益:{pnl:+.0f}元")
    
    # 清除部位狀態
    self.current_position = None
    self.first_breakout_detected = False
    
    # Console輸出
    print(f"✅ [STRATEGY] {direction}平倉 @{price:.0f} {reason} 損益:{pnl_money:+.0f}元")
```

## 3. 其他平倉條件

### 🕐 **收盤平倉 (End-of-Day Close)**

#### **時間觸發機制**
```python
def check_exit_conditions_safe(self, price, time_str):
    """收盤平倉檢查 - 最高優先級"""
    
    # 🕐 檢查收盤平倉 (13:30) - 受控制開關影響
    if hasattr(self, 'single_strategy_eod_close_var') and self.single_strategy_eod_close_var.get():
        hour, minute, second = map(int, time_str.split(':'))
        if hour >= 13 and minute >= 30:
            self.exit_position_safe(price, time_str, "收盤平倉")
            return  # 立即返回，不檢查其他條件
```

**特點**：
- **最高優先級**：優先於所有其他出場條件
- **可選功能**：透過GUI開關控制是否啟用
- **強制平倉**：13:30後強制平倉所有部位
- **當沖策略**：確保不留倉過夜

#### **多組策略收盤平倉**
多組策略系統同樣支援收盤平倉，但整合在風險管理引擎中：

```python
def check_all_exit_conditions(self, current_price: float, current_time: str):
    """多組策略出場條件檢查"""
    
    # 解析時間
    hour, minute = map(int, current_time.split(':')[:2])
    
    # 收盤平倉檢查 (13:30)
    if hour >= 13 and minute >= 30:
        # 強制平倉所有活躍部位
        active_positions = self.db_manager.get_all_active_positions()
        for position in active_positions:
            exit_actions.append({
                'position_id': position['id'],
                'exit_price': current_price,
                'exit_time': current_time,
                'exit_reason': '收盤平倉',
                'pnl': self._calculate_pnl(position, current_price)
            })
```

### 🔄 **反向交易訊號**

**目前系統設計**：
- **無反向訊號**：系統不支援反向交易訊號平倉
- **單次進場**：每日只進場一次，不會有反向訊號
- **突破策略**：基於區間突破，無反向邏輯

**設計原因**：
- **簡化邏輯**：避免複雜的信號衝突
- **風險控制**：專注於停損停利機制
- **策略純度**：保持突破策略的一致性

## 4. 出場條件優先級與互動關係

### 🏆 **優先級排序**

#### **單一策略優先級**
```python
def check_exit_conditions_safe(self, price, time_str):
    """出場條件檢查 - 按優先級順序"""
    
    # 優先級1: 收盤平倉 (13:30) - 最高優先級
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
```

#### **多組策略優先級**
```python
def _check_group_exit_conditions(self, positions: List[Dict], current_price: float, current_time: str):
    """多組策略出場條件檢查 - 按優先級順序"""
    
    for position in positions:
        # 優先級1: 初始停損 (最高優先級)
        if self._check_initial_stop_loss(position, current_price):
            exit_actions.append(initial_stop_action)
            continue
        
        # 優先級2: 保護性停損
        if self._check_protective_stop_loss(position, current_price):
            exit_actions.append(protective_stop_action)
            continue
        
        # 優先級3: 移動停利
        trailing_exit = self._check_trailing_stop_conditions(position, current_price, current_time)
        if trailing_exit:
            exit_actions.append(trailing_exit)
            continue
```

### 🔄 **互動關係**

#### **停損點演進**
```
初始狀態: 區間邊界停損
    ↓
獲利15點: 啟動移動停利 (20%回撤)
    ↓
前面口單獲利: 啟動保護性停損 (向成本價移動)
    ↓
收盤時間: 強制收盤平倉 (覆蓋所有條件)
```

#### **風險控制層次**
1. **基礎保護**：初始停損（區間邊界）
2. **獲利保護**：移動停利（20%回撤）
3. **累積保護**：保護性停損（基於累積獲利）
4. **時間保護**：收盤平倉（強制平倉）

#### **條件互斥性**
- **一次觸發**：任何條件觸發後立即平倉，不檢查其他條件
- **優先級嚴格**：高優先級條件會覆蓋低優先級條件
- **狀態清除**：平倉後清除所有部位狀態和風險管理狀態

## 5. 總結

### 🎯 **風險管理特點**

1. **分層保護**：初始停損 → 移動停利 → 保護性停損 → 收盤平倉
2. **動態調整**：停利點隨市場變化動態調整
3. **獲利保護**：多種機制保護已實現和未實現獲利
4. **時間控制**：強制收盤平倉確保當沖策略執行
5. **優先級明確**：清楚的出場條件優先級避免衝突

### 🔧 **系統設計優勢**

- **模組化風控**：單一策略和多組策略分別實現
- **漸進式保護**：從基礎到進階的多層次保護
- **靈活配置**：可透過參數調整各種風控條件
- **完整記錄**：所有出場原因都有詳細日誌記錄

這個風險管理系統體現了專業量化交易的完整思維，從基礎的停損保護到進階的動態風控，提供了全方位的風險管理解決方案。
