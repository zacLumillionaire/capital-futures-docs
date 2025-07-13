# 虛擬報價機 (Virtual Quote Machine)

## 📋 概述

虛擬報價機是為simple_integrated.py策略下單機開發的測試工具，提供與群益API相同介面的模擬環境，讓開發者可以在不影響真實交易的情況下測試策略邏輯。

## 🎯 主要功能

- **完整API模擬**: 提供SKCenterLib、SKOrderLib、SKQuoteLib、SKReplyLib的完整模擬
- **穩定報價推送**: 每0.5秒推送模擬的台指期貨報價
- **下單成交模擬**: 模擬FOK單的下單和成交流程
- **事件驅動架構**: 保持與真實API相同的事件處理機制

## 🏗️ 系統架構

```
虛擬報價機/
├── Global.py              # API模擬介面 (替換order_service.Global)
├── quote_engine.py        # 報價生成引擎
├── event_dispatcher.py    # 事件分發器
├── order_simulator.py     # 下單模擬器
├── config_manager.py      # 配置管理器
├── price_generator.py     # 價格生成器
├── best5_generator.py     # 五檔生成器
├── reply_simulator.py     # 回報模擬器
├── connection_manager.py  # 連線管理器
├── config.json           # 配置文件
└── README.md             # 說明文檔
```

## 🚀 使用方式

### 1. 基本使用
```python
# 在simple_integrated.py中替換導入
# 原有: import order_service.Global as Global
# 替換: import 虛擬報價機.Global as Global
```

### 2. 配置設定
編輯 `config.json` 調整虛擬報價機參數：
```json
{
    "base_price": 21500,
    "price_range": 50,
    "spread": 5,
    "quote_interval": 0.5,
    "fill_probability": 0.95,
    "fill_delay_ms": 200
}
```

### 3. 啟動測試
1. 確保虛擬報價機模組在Python路徑中
2. 修改simple_integrated.py的Global導入
3. 正常啟動simple_integrated.py
4. 系統將自動使用虛擬報價機進行測試

## ⚙️ 配置參數

| 參數 | 說明 | 預設值 |
|------|------|--------|
| base_price | 基準價格 | 21500 |
| price_range | 波動範圍(±點) | 50 |
| spread | 買賣價差(點) | 5 |
| quote_interval | 報價間隔(秒) | 0.5 |
| fill_probability | 成交機率 | 0.95 |
| fill_delay_ms | 成交延遲(毫秒) | 200 |

## 📊 性能指標

- **報價延遲**: < 10毫秒
- **下單響應**: < 50毫秒
- **回報推送**: < 200毫秒
- **記憶體使用**: < 100MB
- **CPU使用**: < 5%

## 🔧 開發說明

### 核心模組

1. **Global.py**: 提供與群益API相同的介面
2. **quote_engine.py**: 負責價格生成和報價推送
3. **event_dispatcher.py**: 管理事件處理和分發
4. **order_simulator.py**: 處理下單請求和回報生成

### 事件流程

```
報價生成 → 事件分發 → simple_integrated.py
下單請求 → 訂單處理 → 回報生成 → 事件分發 → simple_integrated.py
```

## 🧪 測試驗證

### 功能測試
- [ ] 報價推送正常
- [ ] 下單回報正常
- [ ] 策略邏輯運作正常
- [ ] 連線狀態管理正常

### 性能測試
- [ ] 長時間運行穩定
- [ ] 記憶體無洩漏
- [ ] CPU使用率正常
- [ ] 響應時間符合要求

## 📞 技術支援

如有問題請參考：
- 📁 開發手冊: `../開發手冊/虛擬報價機開發手冊/`
- 🔧 配置文件: `config.json`
- 📊 日誌文件: 系統運行日誌

---
*虛擬報價機 v1.0*  
*最後更新: 2025-01-13*
