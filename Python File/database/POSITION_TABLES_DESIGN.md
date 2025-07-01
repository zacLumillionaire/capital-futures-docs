# 📊 部位管理資料庫表格設計文檔

## 🎯 **設計目標**

### **核心原則**
1. **向後相容** - 不修改現有表格結構
2. **完整追蹤** - 記錄部位生命週期的每個階段
3. **效能優化** - 合理的索引設計
4. **資料一致性** - 觸發器自動維護統計資料

### **功能範圍**
- ✅ 每口部位的獨立管理
- ✅ 停損調整的完整記錄
- ✅ 移動停利的歷史追蹤
- ✅ 保護性停損的自動計算
- ✅ 交易會話的統計分析

## 📋 **表格結構詳解**

### **1. positions (部位主表)**

#### **用途**
記錄每口部位的完整生命週期，從建倉到出場的所有關鍵資訊。

#### **關鍵欄位說明**
```sql
session_id TEXT NOT NULL              -- 交易會話ID，格式: 20250630_084815
lot_id INTEGER NOT NULL               -- 口數編號 (1, 2, 3...)
position_type TEXT NOT NULL           -- LONG/SHORT
entry_price REAL NOT NULL             -- 進場價格
current_stop_loss REAL                -- 當前停損價格 (會動態更新)
peak_price REAL                       -- 峰值價格 (移動停利計算基準)
trailing_activated BOOLEAN            -- 移動停利是否已啟動
lot_rule_config TEXT                  -- 該口的規則配置 (JSON格式)
```

#### **狀態流轉**
```
ACTIVE → EXITED (正常出場)
ACTIVE → CANCELLED (取消部位)
```

#### **使用範例**
```python
# 建倉時插入記錄
INSERT INTO positions (
    session_id, date, lot_id, position_type, 
    entry_price, entry_time, range_high, range_low,
    current_stop_loss, peak_price, lot_rule_config
) VALUES (
    '20250630_084815', '2025-06-30', 1, 'LONG',
    22014, '08:48:15', 22010, 21998,
    21998, 22014, '{"trailing_activation": 15, "trailing_pullback": 0.20}'
);
```

### **2. stop_loss_adjustments (停損調整記錄表)**

#### **用途**
記錄每次停損點位調整的詳細資訊，包括調整原因、觸發條件等。

#### **調整原因分類**
- **INITIAL**: 初始停損設定
- **TRAILING**: 移動停利調整
- **PROTECTIVE**: 保護性停損調整
- **MANUAL**: 手動調整

#### **使用範例**
```python
# 移動停利調整記錄
INSERT INTO stop_loss_adjustments (
    position_id, session_id, lot_id,
    old_stop_loss, new_stop_loss, adjustment_reason,
    trigger_price, trigger_time, peak_price_at_adjustment,
    trailing_activation_points, trailing_pullback_ratio
) VALUES (
    1, '20250630_084815', 1,
    21998, 22005, 'TRAILING',
    22025, '08:52:30', 22025,
    15, 0.20
);
```

### **3. position_snapshots (部位快照表)**

#### **用途**
定期記錄部位狀態快照，用於：
- 系統恢復時重建部位狀態
- 歷史分析和回測驗證
- 效能監控和調試

#### **快照頻率建議**
- 價格更新時 (可選)
- 停損調整時 (必須)
- 定期快照 (每分鐘)

### **4. trading_sessions (交易會話表)**

#### **用途**
記錄每個交易會話的整體資訊，提供統計和分析基礎。

#### **會話ID格式**
```
YYYYMMDD_HHMMSS
例如: 20250630_084815 (2025年6月30日 08:48:15建立的會話)
```

## 🔧 **技術實現細節**

### **1. 資料一致性保證**

#### **觸發器自動維護**
```sql
-- 自動更新會話統計
CREATE TRIGGER update_session_stats_on_position_change
    AFTER UPDATE OF status, realized_pnl ON positions
    FOR EACH ROW
BEGIN
    UPDATE trading_sessions 
    SET 
        total_realized_pnl = (SELECT SUM(realized_pnl) FROM positions WHERE session_id = NEW.session_id),
        active_positions = (SELECT COUNT(*) FROM positions WHERE session_id = NEW.session_id AND status = 'ACTIVE')
    WHERE session_id = NEW.session_id;
END;
```

### **2. 查詢效能優化**

#### **關鍵索引**
```sql
-- 最常用的查詢模式
CREATE INDEX idx_positions_session_date ON positions(session_id, date);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_stop_loss_position_id ON stop_loss_adjustments(position_id);
```

#### **常用查詢範例**
```sql
-- 查詢當日活躍部位
SELECT * FROM positions 
WHERE date = '2025-06-30' AND status = 'ACTIVE'
ORDER BY lot_id;

-- 查詢特定部位的停損調整歷史
SELECT * FROM stop_loss_adjustments 
WHERE position_id = 1 
ORDER BY trigger_datetime;

-- 查詢會話統計
SELECT 
    session_id,
    total_lots,
    active_positions,
    total_realized_pnl,
    (total_realized_pnl / total_lots) as avg_pnl_per_lot
FROM trading_sessions 
WHERE date = '2025-06-30';
```

## 🛡️ **安全性考量**

### **1. 資料完整性**
- 外鍵約束確保關聯資料一致性
- 唯一約束防止重複記錄
- 觸發器自動維護統計資料

### **2. 錯誤處理**
```python
# 安全的資料插入範例
def safe_insert_position(session_id, lot_id, **kwargs):
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 檢查是否已存在
            cursor.execute(
                "SELECT id FROM positions WHERE session_id = ? AND lot_id = ?",
                (session_id, lot_id)
            )
            
            if cursor.fetchone():
                raise ValueError(f"部位已存在: {session_id}, lot {lot_id}")
            
            # 插入新記錄
            cursor.execute(INSERT_POSITION_SQL, values)
            conn.commit()
            
    except Exception as e:
        logger.error(f"插入部位記錄失敗: {e}")
        raise
```

## 📊 **與現有系統整合**

### **1. 保持現有表格不變**
```sql
-- 現有表格繼續使用，不做任何修改
-- market_data, strategy_signals, trade_records, strategy_status, realtime_quotes
```

### **2. 資料關聯設計**
```python
# 新舊系統資料關聯
class PositionDataBridge:
    def sync_to_trade_records(self, position):
        """將部位資料同步到現有的trade_records表"""
        if position.status == 'EXITED':
            self.insert_trade_record(
                date=position.date,
                strategy_name=position.strategy_name,
                lot_id=position.lot_id,
                entry_time=position.entry_time,
                entry_price=position.entry_price,
                exit_time=position.exit_time,
                exit_price=position.exit_price,
                position_type=position.position_type,
                pnl=position.realized_pnl,
                exit_reason=position.exit_reason
            )
```

## 🚀 **部署步驟**

### **1. 資料庫升級**
```python
def upgrade_database():
    """安全升級資料庫結構"""
    with db_manager.get_connection() as conn:
        # 執行SQL腳本
        with open('position_tables_design.sql', 'r') as f:
            sql_script = f.read()
        
        conn.executescript(sql_script)
        conn.commit()
        
    logger.info("✅ 資料庫升級完成")
```

### **2. 驗證步驟**
```python
def verify_new_tables():
    """驗證新表格是否正確創建"""
    required_tables = [
        'positions', 'stop_loss_adjustments', 
        'position_snapshots', 'trading_sessions'
    ]
    
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        for table in required_tables:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            
            if not cursor.fetchone():
                raise Exception(f"表格 {table} 創建失敗")
    
    logger.info("✅ 所有新表格驗證通過")
```

這個設計確保了：
- **完全向後相容** - 不影響現有功能
- **功能完整** - 支援所有部位管理需求
- **效能優化** - 合理的索引和查詢設計
- **易於維護** - 清晰的表格結構和關聯關係
