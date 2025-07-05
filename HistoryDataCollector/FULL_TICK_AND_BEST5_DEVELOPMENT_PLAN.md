# Full Tick 和五檔報價功能開發計畫

## 現狀分析

### 已完成的基礎架構
✅ **基本收集器框架**
- `TickCollector` - 逐筆資料收集器
- `Best5Collector` - 五檔資料收集器
- `BaseCollector` - 基礎收集器類別

✅ **資料庫支援**
- SQLite 表格: `tick_data`, `best5_data`
- 批量插入方法: `batch_insert_tick_data()`, `batch_insert_best5_data()`
- 資料模型: `TickData`, `Best5Data`

✅ **API 事件處理**
- 歷史逐筆資料事件: `OnNotifyHistoryTicks`
- 即時逐筆資料事件: `OnNotifyTicks`
- 五檔資料事件: `OnNotifyBest5`

### 需要擴展的功能
🎯 **PostgreSQL 匯入功能**
- Tick 資料匯入到 PostgreSQL
- Best5 資料匯入到 PostgreSQL
- 高效能批量匯入優化

🎯 **資料轉換和除錯**
- 前10行資料對比輸出
- 資料格式驗證和清理

🎯 **GUI 整合**
- 收集進度顯示
- 資料統計展示
- 匯入功能整合

## 開發階段規劃

### 階段1: PostgreSQL 表格設計

#### 1.1 Tick 資料表 (tick_prices)
```sql
CREATE TABLE IF NOT EXISTS tick_prices (
    trade_datetime timestamp without time zone NOT NULL,
    symbol varchar(20) NOT NULL,
    bid_price numeric(10,2),
    ask_price numeric(10,2),
    close_price numeric(10,2) NOT NULL,
    volume integer NOT NULL,
    trade_time_ms integer,
    market_no integer,
    simulate_flag integer DEFAULT 0,
    CONSTRAINT pk_tick_prices PRIMARY KEY (trade_datetime, symbol)
);
```

#### 1.2 五檔資料表 (best5_prices)
```sql
CREATE TABLE IF NOT EXISTS best5_prices (
    trade_datetime timestamp without time zone NOT NULL,
    symbol varchar(20) NOT NULL,
    
    -- 五檔買價買量
    bid_price_1 numeric(10,2), bid_volume_1 integer,
    bid_price_2 numeric(10,2), bid_volume_2 integer,
    bid_price_3 numeric(10,2), bid_volume_3 integer,
    bid_price_4 numeric(10,2), bid_volume_4 integer,
    bid_price_5 numeric(10,2), bid_volume_5 integer,
    
    -- 五檔賣價賣量
    ask_price_1 numeric(10,2), ask_volume_1 integer,
    ask_price_2 numeric(10,2), ask_volume_2 integer,
    ask_price_3 numeric(10,2), ask_volume_3 integer,
    ask_price_4 numeric(10,2), ask_volume_4 integer,
    ask_price_5 numeric(10,2), ask_volume_5 integer,
    
    -- 延伸買賣
    extend_bid numeric(10,2), extend_bid_qty integer,
    extend_ask numeric(10,2), extend_ask_qty integer,
    
    CONSTRAINT pk_best5_prices PRIMARY KEY (trade_datetime, symbol)
);
```

### 階段2: PostgreSQL 匯入器擴展

#### 2.1 Tick 資料匯入器
```python
class TickPostgreSQLImporter:
    def convert_tick_to_postgres_format(self, tick_data):
        """將逐筆資料轉換為PostgreSQL格式"""
        # 解析日期時間
        date_str = tick_data['trade_date']  # "20241201"
        time_str = tick_data['trade_time']  # "090000"
        
        # 轉換為 datetime
        trade_datetime = datetime.strptime(
            f"{date_str} {time_str}", 
            '%Y%m%d %H%M%S'
        )
        
        # 處理毫秒
        if tick_data.get('trade_time_ms'):
            microseconds = tick_data['trade_time_ms'] * 1000
            trade_datetime = trade_datetime.replace(microsecond=microseconds)
        
        return {
            'trade_datetime': trade_datetime,
            'symbol': tick_data['symbol'],
            'bid_price': Decimal(str(tick_data.get('bid_price', 0))),
            'ask_price': Decimal(str(tick_data.get('ask_price', 0))),
            'close_price': Decimal(str(tick_data['close_price'])),
            'volume': tick_data['volume'],
            'trade_time_ms': tick_data.get('trade_time_ms', 0),
            'market_no': tick_data.get('market_no', 0),
            'simulate_flag': tick_data.get('simulate_flag', 0)
        }
    
    def import_tick_to_postgres(self, symbol='MTX00', batch_size=5000):
        """匯入逐筆資料到PostgreSQL"""
        # 使用優化的批量匯入方法
        pass
```

#### 2.2 Best5 資料匯入器
```python
class Best5PostgreSQLImporter:
    def convert_best5_to_postgres_format(self, best5_data):
        """將五檔資料轉換為PostgreSQL格式"""
        # 解析日期時間
        date_str = best5_data['trade_date']
        time_str = best5_data['trade_time']
        
        trade_datetime = datetime.strptime(
            f"{date_str} {time_str}", 
            '%Y%m%d %H%M%S'
        )
        
        return {
            'trade_datetime': trade_datetime,
            'symbol': best5_data['symbol'],
            'bid_price_1': Decimal(str(best5_data.get('bid_price_1', 0))),
            'bid_volume_1': best5_data.get('bid_volume_1', 0),
            # ... 其他五檔資料
        }
```

### 階段3: 除錯功能實作

#### 3.1 Tick 收集器除錯
```python
# 在 TickCollector.on_history_tick_received 中添加
if self.printed_count < 10:
    self.printed_count += 1
    print(f"\n=== 第 {self.printed_count} 筆逐筆資料 ===")
    print(f"原始參數:")
    print(f"  市場別: {sMarketNo}")
    print(f"  日期: {nDate}")
    print(f"  時間: {nTimehms}")
    print(f"  買價: {nBid}")
    print(f"  賣價: {nAsk}")
    print(f"  成交價: {nClose}")
    print(f"  成交量: {nQty}")
    print(f"轉換後資料:")
    print(f"  商品代碼: {tick_data['symbol']}")
    print(f"  交易日期: {tick_data['trade_date']}")
    print(f"  交易時間: {tick_data['trade_time']}")
    print(f"  買價: {tick_data['bid_price']}")
    print(f"  賣價: {tick_data['ask_price']}")
    print(f"  成交價: {tick_data['close_price']}")
    print(f"  成交量: {tick_data['volume']}")
    print("=" * 50)
```

#### 3.2 Best5 收集器除錯
```python
# 在 Best5Collector.on_best5_received 中添加
if self.printed_count < 10:
    self.printed_count += 1
    print(f"\n=== 第 {self.printed_count} 筆五檔資料 ===")
    print(f"原始參數:")
    print(f"  買1價: {nBestBid1}, 量: {nBestBidQty1}")
    print(f"  買2價: {nBestBid2}, 量: {nBestBidQty2}")
    print(f"  賣1價: {nBestAsk1}, 量: {nBestAskQty1}")
    print(f"  賣2價: {nBestAsk2}, 量: {nBestAskQty2}")
    print(f"轉換後資料:")
    print(f"  商品代碼: {best5_data['symbol']}")
    print(f"  買1: {best5_data['bid_price_1']} x {best5_data['bid_volume_1']}")
    print(f"  買2: {best5_data['bid_price_2']} x {best5_data['bid_volume_2']}")
    print(f"  賣1: {best5_data['ask_price_1']} x {best5_data['ask_volume_1']}")
    print(f"  賣2: {best5_data['ask_price_2']} x {best5_data['ask_volume_2']}")
    print("=" * 50)
```

### 階段4: GUI 整合

#### 4.1 主程式修改
```python
# 在 main.py 中添加 tick 和 best5 匯入功能
def import_tick_to_postgres(self):
    """匯入逐筆資料到PostgreSQL"""
    try:
        importer = TickPostgreSQLImporter()
        success = importer.import_tick_to_postgres(
            symbol='MTX00',
            batch_size=5000,
            optimize_performance=True
        )
        if success:
            self.log_message("✅ 逐筆資料匯入完成")
        else:
            self.log_message("❌ 逐筆資料匯入失敗")
    except Exception as e:
        self.log_message(f"❌ 逐筆資料匯入錯誤: {e}")

def import_best5_to_postgres(self):
    """匯入五檔資料到PostgreSQL"""
    # 類似實作
    pass
```

#### 4.2 統計功能擴展
```python
# 在 DatabaseManager 中擴展統計功能
def get_data_statistics(self):
    """取得資料統計"""
    try:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # K線資料統計
            cursor.execute("SELECT COUNT(*) FROM kline_data")
            kline_count = cursor.fetchone()[0]
            
            # 逐筆資料統計
            cursor.execute("SELECT COUNT(*) FROM tick_data")
            tick_count = cursor.fetchone()[0]
            
            # 五檔資料統計
            cursor.execute("SELECT COUNT(*) FROM best5_data")
            best5_count = cursor.fetchone()[0]
            
            return {
                'kline_count': kline_count,
                'tick_count': tick_count,
                'best5_count': best5_count,
                'total_count': kline_count + tick_count + best5_count
            }
    except Exception as e:
        logger.error(f"取得統計資料失敗: {e}")
        return None
```

## 實作優先順序

### 高優先級 (立即實作)
1. **PostgreSQL 表格建立**
2. **Tick 資料匯入器**
3. **Best5 資料匯入器**
4. **除錯功能添加**

### 中優先級 (後續實作)
1. **GUI 匯入按鈕**
2. **統計功能擴展**
3. **性能優化測試**

### 低優先級 (未來考慮)
1. **即時資料監控**
2. **資料視覺化**
3. **自動化測試**

## 預期效果

### 功能完整性
- ✅ 完整的 Tick 資料收集和匯入
- ✅ 完整的五檔資料收集和匯入
- ✅ 高效能 PostgreSQL 匯入 (50-100倍提升)
- ✅ 詳細的除錯和驗證功能

### 使用體驗
- 🎯 一鍵收集和匯入
- 🎯 即時進度顯示
- 🎯 詳細統計資訊
- 🎯 錯誤處理和恢復

### 技術指標
- 📊 Tick 資料匯入速度: >1000 筆/秒
- 📊 Best5 資料匯入速度: >500 筆/秒
- 📊 資料完整性: >99.9%
- 📊 系統穩定性: 24/7 運行

這個開發計畫將讓 HistoryDataCollector 成為一個完整的期貨資料收集和分析平台！
