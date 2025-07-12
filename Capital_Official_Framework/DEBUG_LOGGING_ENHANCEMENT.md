# 🔍 部位追蹤機制 DEBUG 日誌增強

**實施日期**: 2025-01-07  
**目的**: 為部位追蹤機制添加詳細的Console日誌，便於調試和監控  
**影響範圍**: 風險管理引擎、停損執行器、簡化追蹤器  

---

## 📋 **增強概覽**

### **核心原則**
- ✅ **不影響程式運作**: 所有日誌都是額外添加，不修改核心邏輯
- ✅ **統一控制開關**: 通過`console_enabled`參數統一控制所有debug輸出
- ✅ **頻率控制**: 對高頻事件進行輸出頻率控制，避免日誌洪水
- ✅ **重要事件優先**: 關鍵狀態變化立即輸出，常規檢查定時輸出
- ✅ **詳細錯誤追蹤**: 異常情況提供完整的錯誤堆疊信息

---

## 🎯 **增強的關鍵追蹤點**

### **1. 風險管理引擎 (risk_management_engine.py)**

#### **價格更新追蹤**
```
[RISK_ENGINE] 🔍 價格檢查: 22510 @09:30:15 (第1250次)
```
- **頻率控制**: 每5秒或每100次檢查輸出一次
- **追蹤內容**: 當前價格、時間、檢查次數

#### **部位狀態監控**
```
[RISK_ENGINE] 📊 部位狀態: 3個有效部位 (0個無效)
[RISK_ENGINE]   部位123: LONG @22500 峰值:22530 損益:+10 停損:22480 [移動停利]
[RISK_ENGINE]   部位124: LONG @22500 峰值:22520 損益:+10 停損:22480 [初始停損]
[RISK_ENGINE]   部位125: LONG @22500 峰值:22510 損益:+10 停損:22480 [保護停損]
```
- **頻率控制**: 每10秒輸出一次詳細狀態
- **追蹤內容**: 部位ID、方向、進場價、峰值價格、當前損益、停損狀態

#### **移動停利啟動追蹤**
```
[RISK_ENGINE] 🎯 移動停利檢查 - 部位123(第1口):
[RISK_ENGINE]   方向:LONG 進場:22500 當前:22519
[RISK_ENGINE]   啟動條件:22520 距離:-1點
[RISK_ENGINE]   狀態:⏳等待啟動 (需要20點獲利)

[RISK_ENGINE] 🚀 移動停利啟動! 部位123(第1口)
[RISK_ENGINE]   觸發價格: 22520 (需要:22520)
[RISK_ENGINE]   獲利幅度: 20點
[RISK_ENGINE]   回撤比例: 20%
```
- **頻率控制**: 未啟動時每5秒輸出，啟動時立即輸出
- **追蹤內容**: 啟動條件、距離差距、觸發事件

#### **移動停利觸發追蹤**
```
[RISK_ENGINE] 📈 移動停利追蹤 - 部位123(第1口):
[RISK_ENGINE]   當前價格:22525 峰值:22530 停利點:22526
[RISK_ENGINE]   獲利範圍:30點 當前獲利:25點
[RISK_ENGINE]   距離觸發:+1點 回撤比例:20%

[RISK_ENGINE] 💥 移動停利觸發! 部位123(第1口)
[RISK_ENGINE]   觸發價格:22525 <= 停利點:22526
[RISK_ENGINE]   峰值價格:22530 獲利:26點
```
- **頻率控制**: 已啟動時每3秒輸出狀態，觸發時立即輸出
- **追蹤內容**: 峰值追蹤、停利計算、觸發條件

#### **峰值價格更新追蹤**
```
[RISK_ENGINE] 📈 峰值價格更新! 部位123:
[RISK_ENGINE]   方向:LONG 舊峰值:22525 → 新峰值:22530
[RISK_ENGINE]   改善幅度:5點 總獲利:30點
[RISK_ENGINE]   移動停利狀態:✅已啟動

[RISK_ENGINE] 💾 更新資料庫峰值: 部位123 → 22530
```
- **頻率控制**: 只在峰值實際更新時輸出
- **追蹤內容**: 峰值變化、獲利計算、資料庫更新

#### **保護性停損更新追蹤**
```
[RISK_ENGINE] 🛡️ 開始保護性停損更新:
[RISK_ENGINE]   觸發部位: 123 獲利: 25點
[RISK_ENGINE]   已出場: 組1 第1口
[RISK_ENGINE]   找到2個活躍部位:
[RISK_ENGINE]     部位124: 第2口
[RISK_ENGINE]     部位125: 第3口
[RISK_ENGINE]   目標部位: 124 第2口
[RISK_ENGINE]   保護性停損倍數: 0.5
[RISK_ENGINE]   累積獲利計算: 25點
[RISK_ENGINE] 🧮 保護性停損計算:
[RISK_ENGINE]   方向:LONG 進場價:22500
[RISK_ENGINE]   累積獲利:25點 × 倍數:0.5
[RISK_ENGINE]   停損金額:12點
[RISK_ENGINE]   新停損價:22488
[RISK_ENGINE] ✅ 保護性停損更新完成!
[RISK_ENGINE]   部位124 第2口 → 22488
```
- **頻率控制**: 立即輸出（重要事件）
- **追蹤內容**: 觸發條件、計算過程、更新結果

#### **初始停損檢查追蹤**
```
[RISK_ENGINE] 🚨 初始停損檢查 - 組1(LONG):
[RISK_ENGINE]   區間: 22480 - 22520
[RISK_ENGINE]   條件: 當前:22485 <= 區間低:22480
[RISK_ENGINE]   距離: +5點

[RISK_ENGINE] 💥 初始停損觸發! 組1(LONG)
[RISK_ENGINE]   觸發價格: 22479
[RISK_ENGINE]   停損邊界: 22480
[RISK_ENGINE]   影響部位: 3個
```
- **頻率控制**: 每10秒輸出檢查狀態，觸發時立即輸出
- **追蹤內容**: 區間邊界、觸發條件、影響範圍

### **2. 停損執行器 (stop_loss_executor.py)**

#### **停損執行開始追蹤**
```
[STOP_EXECUTOR] 🚨 開始執行停損平倉
[STOP_EXECUTOR]   部位ID: 123
[STOP_EXECUTOR]   觸發價格: 22479
[STOP_EXECUTOR]   方向: LONG
[STOP_EXECUTOR]   觸發原因: 初始停損
[STOP_EXECUTOR]   組別: 1
```

#### **部位資訊驗證追蹤**
```
[STOP_EXECUTOR] 📋 部位資訊驗證:
[STOP_EXECUTOR]   狀態: ACTIVE
[STOP_EXECUTOR]   進場價: 22500
[STOP_EXECUTOR]   方向: LONG
[STOP_EXECUTOR]   組別: 1
```

#### **平倉參數計算追蹤**
```
[STOP_EXECUTOR] 📋 平倉參數:
[STOP_EXECUTOR]   平倉方向: SHORT
[STOP_EXECUTOR]   平倉數量: 1 口
[STOP_EXECUTOR]   預期價格: 22479
[STOP_EXECUTOR]   進場價格: 22500
[STOP_EXECUTOR]   預期損益: -21點
```

#### **下單結果追蹤**
```
[STOP_EXECUTOR] 🚀 開始執行平倉下單...

[STOP_EXECUTOR] ✅ 平倉下單成功:
[STOP_EXECUTOR]   訂單ID: ORD_20250107_001
[STOP_EXECUTOR]   執行價格: 22479
[STOP_EXECUTOR]   執行時間: 09:30:25
[STOP_EXECUTOR]   實際損益: -21點
```

#### **保護性停損更新檢查**
```
[STOP_EXECUTOR] 🛡️ 移動停利獲利平倉，檢查保護性停損更新...
[STOP_EXECUTOR] ℹ️ 非移動停利獲利平倉，跳過保護性停損更新
```

#### **執行結果摘要**
```
[STOP_EXECUTOR] 📊 執行結果摘要:
[STOP_EXECUTOR]   ✅ 停損平倉執行成功
[STOP_EXECUTOR]   訂單ID: ORD_20250107_001
[STOP_EXECUTOR]   執行價格: 22479
[STOP_EXECUTOR]   損益: -21點
[STOP_EXECUTOR] ═══════════════════════════════════════
```

### **3. 簡化追蹤器 (simplified_order_tracker.py)**

#### **平倉成交回報處理**
```
[SIMPLIFIED_TRACKER] 📥 收到平倉成交回報:
[SIMPLIFIED_TRACKER]   價格: 22479 數量: 1 商品: TM0000
[SIMPLIFIED_TRACKER]   待匹配平倉訂單: 1個

[SIMPLIFIED_TRACKER] ✅ 找到匹配的平倉訂單:
[SIMPLIFIED_TRACKER]   訂單ID: ORD_20250107_001
[SIMPLIFIED_TRACKER]   部位ID: 123
[SIMPLIFIED_TRACKER]   方向: SHORT
[SIMPLIFIED_TRACKER]   註冊時間: 09:30:25

[SIMPLIFIED_TRACKER] ✅ 平倉成交確認: 部位123 1口 @22479
[SIMPLIFIED_TRACKER] 📞 觸發平倉成交回調...
[SIMPLIFIED_TRACKER] 🧹 清理已完成的平倉訂單...
[SIMPLIFIED_TRACKER] ✅ 平倉成交處理完成
[SIMPLIFIED_TRACKER]   部位123 已成功平倉
[SIMPLIFIED_TRACKER] ═══════════════════════════════════════
```

#### **平倉取消回報處理**
```
[SIMPLIFIED_TRACKER] 📤 收到平倉取消回報:
[SIMPLIFIED_TRACKER]   價格: 0 數量: 0 商品: TM0000
[SIMPLIFIED_TRACKER]   待匹配平倉訂單: 1個

[SIMPLIFIED_TRACKER] ⚠️ 找到匹配的平倉取消訂單:
[SIMPLIFIED_TRACKER]   訂單ID: ORD_20250107_001
[SIMPLIFIED_TRACKER]   部位ID: 123
[SIMPLIFIED_TRACKER]   原始價格: 22479
[SIMPLIFIED_TRACKER]   原始數量: 1
[SIMPLIFIED_TRACKER]   方向: SHORT

[SIMPLIFIED_TRACKER] ❌ 平倉取消確認: 部位123
[SIMPLIFIED_TRACKER] 🔄 觸發平倉追價回調...
[SIMPLIFIED_TRACKER] 🧹 清理取消的平倉訂單...
[SIMPLIFIED_TRACKER] ✅ 平倉取消處理完成
[SIMPLIFIED_TRACKER]   部位123 將進行追價重試
[SIMPLIFIED_TRACKER] ═══════════════════════════════════════
```

---

## 🎛️ **控制開關設定**

### **統一Console開關**
所有debug日誌都通過`console_enabled`參數控制：

```python
# 在 simple_integrated.py 中設定
self.console_enabled = True  # 啟用debug日誌

# 自動傳遞給所有組件
self.multi_group_risk_engine.console_enabled = self.console_enabled
self.stop_loss_executor.console_enabled = self.console_enabled
self.simplified_tracker.console_enabled = self.console_enabled
```

### **頻率控制機制**
- **高頻事件**: 價格檢查、部位狀態檢查 → 定時輸出（5-15秒間隔）
- **中頻事件**: 移動停利檢查、初始停損檢查 → 定時輸出（3-10秒間隔）
- **重要事件**: 觸發事件、成交確認、錯誤 → 立即輸出

---

## 🔧 **使用方法**

### **啟用Debug模式**
```python
# 在程式啟動時設定
self.console_enabled = True
```

### **關閉Debug模式**
```python
# 在生產環境中關閉
self.console_enabled = False
```

### **查看特定類型的日誌**
- **風險管理**: 搜尋 `[RISK_ENGINE]`
- **停損執行**: 搜尋 `[STOP_EXECUTOR]`
- **FIFO追蹤**: 搜尋 `[SIMPLIFIED_TRACKER]`

---

## 📊 **日誌輸出示例**

### **完整交易流程日誌**
```
[RISK_ENGINE] 🔍 價格檢查: 22520 @09:30:15 (第100次)
[RISK_ENGINE] 🚀 移動停利啟動! 部位123(第1口)
[RISK_ENGINE] 📈 峰值價格更新! 部位123: 22520 → 22530
[RISK_ENGINE] 💥 移動停利觸發! 部位123(第1口)
[STOP_EXECUTOR] 🚨 開始執行停損平倉
[STOP_EXECUTOR] ✅ 平倉下單成功: ORD_20250107_001
[SIMPLIFIED_TRACKER] 📥 收到平倉成交回報: 22526
[SIMPLIFIED_TRACKER] ✅ 平倉成交處理完成
[RISK_ENGINE] 🛡️ 保護性停損更新完成! 部位124 → 22488
```

---

## ⚠️ **注意事項**

1. **效能影響**: Debug日誌會增加少量CPU使用，建議在生產環境中關閉
2. **日誌量**: 啟用後會產生大量日誌，建議配合日誌過濾工具使用
3. **記憶體使用**: 長時間運行時注意監控記憶體使用情況
4. **錯誤追蹤**: 所有異常都會輸出完整的錯誤堆疊，便於問題診斷

---

## 🎯 **調試建議**

### **問題排查順序**
1. **檢查價格更新**: 確認價格數據正常流入
2. **監控部位狀態**: 確認部位狀態正確更新
3. **追蹤觸發條件**: 確認停損/停利條件正確計算
4. **驗證執行流程**: 確認下單和成交流程正常
5. **檢查FIFO匹配**: 確認訂單匹配邏輯正確

### **常見問題模式**
- **峰值不更新**: 檢查價格數據和方向邏輯
- **停利不觸發**: 檢查啟動條件和回撤計算
- **訂單不匹配**: 檢查FIFO匹配條件和商品代碼
- **保護性停損不更新**: 檢查獲利條件和倍數設定

---

**📝 實施完成**: 2025-01-07  
**🔄 下次更新**: 根據實際使用情況進行優化調整
