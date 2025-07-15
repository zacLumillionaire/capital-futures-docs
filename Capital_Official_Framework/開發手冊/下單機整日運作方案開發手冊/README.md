# 下單機整日運作方案開發手冊

## 📋 項目概述

本項目針對 simple_integrated.py 策略下單機進行全面優化，實現全天多時段搭配不同配置的交易系統。通過模組化設計，支援各指定時間繪製區間、每次有不同的進場、停損、停利等設定，實現多時段區間各自配置交易方式。

## 🎯 核心目標

實現以下功能範例：
- **09:30~09:32監控**：跌破區間底部做多單，下單3口個別停損都是15點，個別停利點是15,30,50
- **10:30~10:32監控**：跌破區間底部做空單，下單3口維持區間邊緣停損，個別停利點是15,30,60

## 📚 文檔結構

### Task 1: 多時段區間繪製機制分析與設計
**文檔**: `Task1_多時段區間繪製機制分析與設計.md`

**核心內容**:
- 分析現有08:45~08:47單一時段機制限制
- 設計多時段架構，支援時段隔離和狀態管理
- 重構區間計算邏輯，支援多個獨立時段
- 實現時段生命週期管理（waiting → collecting → completed → trading → finished）

**關鍵設計**:
```python
# 多時段配置結構
time_intervals = [
    {
        'id': 'morning_1',
        'start_time': '08:46',
        'end_time': '08:48',
        'direction_config': {...},
        'stop_loss_config': {...},
        'take_profit_config': {...}
    }
]
```

### Task 2: 方向配置靈活化機制設計
**文檔**: `Task2_方向配置靈活化機制設計.md`

**核心內容**:
- 分析現有固定方向邏輯（low做空、close突破做多）
- 設計靈活方向配置，支援順勢、逆勢、單向等策略
- 實現檢測方式選擇（即時檢測 vs 1分K檢測）
- 提供配置模板（標準、反向、只做多、只做空）

**關鍵設計**:
```python
direction_config = {
    'high_breakout': {
        'direction': BreakoutDirection.LONG,     # 突破上緣做多
        'detection_mode': DetectionMode.CANDLE_CLOSE,
        'enabled': True
    },
    'low_breakout': {
        'direction': BreakoutDirection.SHORT,    # 突破下緣做空
        'detection_mode': DetectionMode.IMMEDIATE,
        'enabled': True
    }
}
```

### Task 3: 停損機制優化設計
**文檔**: `Task3_停損機制優化設計.md`

**核心內容**:
- 分析現有區間邊緣停損限制
- 設計靈活停損配置，支援區間邊緣、固定點數、自定義價格
- 實現各口獨立停損設定
- 提供配置模板（區間邊緣、統一固定點數、各口獨立混合、遞增點數）

**關鍵設計**:
```python
stop_loss_config = {
    'stop_loss_type': StopLossType.INDIVIDUAL,
    'individual_configs': {
        1: {'type': 'fixed_points', 'points': 15},
        2: {'type': 'fixed_points', 'points': 25},
        3: {'type': 'range_boundary'}
    }
}
```

### Task 4: 停利機制優化設計
**文檔**: `Task4_停利機制優化設計.md`

**核心內容**:
- 分析現有移動停利機制限制
- 設計靈活停利配置，支援移動停利、固定點數、百分比獲利
- 實現各口獨立停利設定和混合策略
- 提供配置模板（移動停利、固定點數、混合策略、遞增固定）

**關鍵設計**:
```python
take_profit_config = {
    'take_profit_type': TakeProfitType.INDIVIDUAL,
    'individual_configs': {
        1: {
            'type': 'trailing_stop',
            'activation_points': 15,
            'pullback_percent': 0.10
        },
        2: {
            'type': 'fixed_points',
            'points': 30
        },
        3: {
            'type': 'trailing_stop',
            'activation_points': 50,
            'pullback_percent': 0.20
        }
    }
}
```

### Task 5: 下單回報機制影響評估
**文檔**: `Task5_下單回報機制影響評估.md`

**核心內容**:
- 評估現有OnNewData回報處理在多時段下的適用性
- 分析雙追蹤器架構（SimplifiedOrderTracker + UnifiedOrderTracker）
- 設計訂單標識擴展和回報路由機制
- 評估風險等級為低到中等，建議漸進式實施

**關鍵結論**:
- 現有下單回報機制基本適用於多時段配置
- 只需小幅度擴展signal_source格式和回報路由
- 建議優先級：基礎擴展 → 狀態隔離 → 高級功能

### Task 6: 整合方案設計與實施指南
**文檔**: `Task6_整合方案設計與實施指南.md`

**核心內容**:
- 整合所有優化方案的完整架構設計
- 提供具體實施範例和配置指南
- 詳細的4週實施時程規劃
- 完整的測試策略、性能考量、風險管理和用戶指南

**關鍵架構**:
```python
class MultiIntervalTradingManager:
    """多時段交易管理器"""
    
    def __init__(self, config: MultiIntervalTradingConfig):
        self.interval_state_manager = IntervalStateManager()
        self.flexible_stop_loss_calculator = {}
        self.flexible_take_profit_calculator = {}
        self.multi_interval_order_tracker = MultiIntervalOrderTracker()
```

## 🚀 實施路線圖

### 階段1：基礎架構（第1週）
- [ ] 實施多時段配置結構
- [ ] 實施時段狀態管理器
- [ ] 整合現有報價處理邏輯

### 階段2：核心功能（第2週）
- [ ] 實施靈活方向配置
- [ ] 實施靈活停損機制
- [ ] 實施靈活停利機制

### 階段3：整合測試（第3週）
- [ ] 實施下單回報擴展
- [ ] 整合測試和調試
- [ ] 性能測試和優化

### 階段4：GUI和文檔（第4週）
- [ ] 實施配置GUI介面
- [ ] 完善文檔和用戶指南

## 📊 技術優勢

### 架構優勢
- **模組化設計**：各組件獨立，易於維護和擴展
- **配置驅動**：通過配置文件控制所有行為
- **向後相容**：保持與現有系統的完全相容
- **可擴展性**：易於添加新的時段和策略

### 交易優勢
- **多機會捕捉**：可在多個時段尋找交易機會
- **策略多樣化**：每個時段可有不同的交易邏輯
- **風險分散**：不同時段可有不同的風險配置
- **精確控制**：各口獨立的停損停利設定

### 實施優勢
- **開發效率**：基於現有架構，開發週期短
- **測試便利**：可獨立測試各個時段配置
- **維護簡單**：配置化管理，減少代碼修改
- **用戶友好**：GUI介面，易於配置和使用

## 🛡️ 風險評估

### 技術風險
- **🟢 低風險**：現有機制穩定，修改範圍小
- **🟡 中等風險**：訂單標識變更需要全面測試
- **建議**：採用漸進式實施，先實現基礎擴展

### 實施風險
- **配置複雜度**：多時段配置可能增加用戶學習成本
- **性能影響**：多時段處理可能影響報價處理性能
- **狀態管理**：多時段並發可能產生競爭條件

### 緩解措施
- 提供配置模板和GUI介面降低複雜度
- 實施性能監控和優化機制
- 使用鎖機制確保狀態一致性

## 📞 支援資源

### 開發手冊
- 所有Task文檔提供詳細的技術分析和實施指南
- 包含完整的代碼範例和配置模板
- 提供測試策略和最佳實踐建議

### Graphiti知識庫
- 所有分析結果已存儲在Graphiti知識庫中
- 可通過search_memory_facts_python查詢相關技術細節
- 支援中文查詢和技術問題解答

### 技術支援
- 基於現有simple_integrated.py架構，降低學習成本
- 保持向後相容，確保現有功能不受影響
- 提供完整的錯誤處理和恢復機制

---

**此開發手冊提供了complete的多時段交易系統優化方案，實現了全天多時段搭配不同配置的目標，為策略下單機的整日運作提供了強大的技術基礎。**
