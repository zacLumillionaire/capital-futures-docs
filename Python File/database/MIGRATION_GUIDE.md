# 📊 資料庫遷移指南

## 🎯 **遷移目標**

將現有的策略交易系統資料庫安全地升級，新增部位管理功能，包括：
- 部位生命週期追蹤
- 停損調整記錄
- 移動停利管理
- 交易會話統計

## 🛡️ **安全保證**

### **核心安全原則**
- ✅ **自動備份** - 遷移前自動創建完整備份
- ✅ **向後相容** - 不修改現有表格結構
- ✅ **資料完整性** - 保證現有資料不受影響
- ✅ **可回滾** - 支援一鍵回滾到遷移前狀態
- ✅ **驗證機制** - 多層驗證確保遷移成功

### **風險控制**
- 遷移失敗時自動回滾
- 完整的錯誤日誌記錄
- 分步驟執行，每步都有驗證
- 測試環境先行驗證

## 📋 **遷移內容**

### **新增表格 (4個)**
1. **positions** - 部位主表
2. **stop_loss_adjustments** - 停損調整記錄
3. **position_snapshots** - 部位快照
4. **trading_sessions** - 交易會話

### **新增索引 (12個)**
- 針對常用查詢模式優化
- 提升部位查詢和統計效能

### **新增觸發器 (3個)**
- 自動更新時間戳
- 自動維護會話統計
- 確保資料一致性

### **版本管理**
- 從 v1.0.0 升級到 v1.1.0
- 完整的版本歷史記錄

## 🚀 **執行遷移**

### **方法1: 命令行執行**

```bash
# 基本遷移
python database_migration.py

# 指定資料庫路徑
python database_migration.py --db-path "custom_path.db"

# 強制執行（即使版本已是最新）
python database_migration.py --force

# 查看遷移狀態
python database_migration.py --status

# 驗證遷移結果
python database_migration.py --verify

# 回滾到備份版本
python database_migration.py --rollback
```

### **方法2: Python程式調用**

```python
from database_migration import DatabaseMigration

# 創建遷移器
migration = DatabaseMigration("strategy_trading.db")

# 檢查遷移狀態
status = migration.get_migration_status()
print(f"需要遷移: {status['needs_migration']}")

# 執行遷移
success = migration.run_migration()
if success:
    print("✅ 遷移成功")
else:
    print("❌ 遷移失敗")
```

## 🧪 **測試遷移**

### **執行測試腳本**
```bash
# 執行完整測試
python test_migration.py
```

### **測試內容**
- ✅ 遷移流程測試
- ✅ 資料完整性驗證
- ✅ 回滾功能測試
- ✅ 新表格操作測試

## 📊 **遷移步驟詳解**

### **步驟1: 環境檢查**
- 檢查當前資料庫版本
- 驗證現有資料完整性
- 確認遷移必要性

### **步驟2: 安全備份**
```
strategy_trading.db → strategy_trading.db.backup_20250630_143022
```

### **步驟3: 版本管理**
- 創建 `database_version` 表
- 記錄版本歷史

### **步驟4: 創建新表格**
```sql
-- 按順序創建
1. trading_sessions (會話管理)
2. positions (部位主表)
3. stop_loss_adjustments (停損記錄)
4. position_snapshots (快照)
```

### **步驟5: 效能優化**
- 創建查詢索引
- 設置自動觸發器

### **步驟6: 驗證測試**
- 插入測試資料
- 驗證查詢功能
- 清理測試資料

### **步驟7: 版本更新**
- 更新版本記錄到 v1.1.0
- 記錄遷移完成時間

## 🔍 **遷移驗證**

### **自動驗證項目**
- [x] 所有新表格都已創建
- [x] 索引和觸發器正常運作
- [x] 現有資料完整無損
- [x] 基本CRUD操作正常
- [x] 版本記錄正確更新

### **手動驗證建議**
```sql
-- 檢查表格結構
.schema positions
.schema stop_loss_adjustments

-- 檢查現有資料
SELECT COUNT(*) FROM market_data;
SELECT COUNT(*) FROM strategy_signals;
SELECT COUNT(*) FROM trade_records;

-- 測試新功能
INSERT INTO trading_sessions (session_id, date, strategy_name, total_lots)
VALUES ('TEST_20250630', '2025-06-30', '測試策略', 1);

SELECT * FROM trading_sessions WHERE session_id = 'TEST_20250630';
```

## ⚠️ **注意事項**

### **遷移前準備**
1. **停止交易程式** - 確保沒有程式正在使用資料庫
2. **檢查磁碟空間** - 確保有足夠空間存放備份
3. **記錄當前狀態** - 記錄現有資料筆數和重要設定

### **遷移中監控**
- 觀察日誌輸出
- 注意錯誤訊息
- 確認每步驟完成

### **遷移後檢查**
- 驗證現有功能正常
- 測試新功能可用
- 確認效能無明顯下降

## 🔄 **回滾程序**

### **自動回滾**
遷移過程中如果發生錯誤，系統會自動嘗試回滾：
```
❌ 遷移失敗 → 🔄 自動回滾 → ✅ 恢復原狀
```

### **手動回滾**
```bash
# 使用命令行回滾
python database_migration.py --rollback

# 或手動恢復備份
cp strategy_trading.db.backup_YYYYMMDD_HHMMSS strategy_trading.db
```

## 📈 **效能影響**

### **預期改善**
- ✅ 部位查詢效能提升 (新增索引)
- ✅ 統計計算自動化 (觸發器)
- ✅ 資料一致性保證 (外鍵約束)

### **資源使用**
- 💾 資料庫大小增加約 10-20%
- 🔍 查詢效能略有提升
- ⚡ 寫入效能基本不變

## 🎉 **遷移完成後**

### **新功能啟用**
- 部位管理系統可用
- 停損追蹤功能就緒
- 會話統計功能啟用

### **下一步整合**
1. 更新 `SQLiteManager` 類別
2. 創建 `PositionPersistenceAdapter`
3. 整合到現有交易系統

### **備份管理**
- 備份檔案保留建議：至少7天
- 定期清理舊備份檔案
- 重要里程碑備份永久保存

---

## 📞 **支援資訊**

如果遷移過程中遇到問題：
1. 檢查日誌檔案 `migration_YYYYMMDD_HHMMSS.log`
2. 執行 `python database_migration.py --status` 查看狀態
3. 必要時執行回滾恢復原狀
4. 聯繫技術支援並提供日誌檔案
