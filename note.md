
----建倉還是遇到error, 但是後續確認部位完整且移動停利啟動,需看看會造成甚麼問題---

[STRATEGY] [17:16:00] 🔥 15分K線收盤突破上緣！收盤:22438 > 上緣:22434
[STRATEGY] [17:16:00] ⏳ 等待下一個報價進場做多...
🔥 [STRATEGY] LONG突破信號已觸發
🎯 [MULTI_GROUP] 根據突破方向創建策略組: LONG
INFO:multi_group_position_manager.MultiGroupPositionManager:今日已有組別 [1, 2, 3]，分配新組別ID: [4]
INFO:multi_group_position_manager.MultiGroupPositionManager:創建進場信號: LONG @ 17:16:00, 區間: 22425.0-22434.0
INFO:multi_group_position_manager.MultiGroupPositionManager:使用動態組別ID: [4]
INFO:multi_group_database:創建策略組: ID=25, 組別=4, 方向=LONG
INFO:multi_group_position_manager.MultiGroupPositionManager:創建策略組 4 (原:1): DB_ID=25
🎯 [STRATEGY] ℹ️ [17:16:00] 多組策略啟動: 1組 LONG, 區間22425.0-22434.0
✅ [MULTI_GROUP] 已創建 1 個LONG策略組
🎯 [MULTI_GROUP] 開始執行 1 組進場
INFO:multi_group_position_manager.MultiGroupPositionManager:🚀 執行組 4 進場: 3口 @ 22438.0
[TOTAL_TRACKER] 總量追蹤器初始化: strategy_4_1752052560
    目標: LONG TM0000 3口
    配置: 3口/組
[TOTAL_MANAGER] 📝 創建策略追蹤器: strategy_4_1752052560
    目標: LONG TM0000 3口 (3口/組)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 總量追蹤器創 建成功: strategy_4_1752052560
[SIMPLIFIED_TRACKER] 📝 註冊策略組: 4 LONG TM0000 3口 @22438
INFO:multi_group_database:創建部位記錄: ID=65, 組=25, 口=1, 狀態=PENDING, 訂單ID=None
[ORDER_MGR] ⚡ 實際下單: BUY TM0000 1口 @22438 API結果:('5136', 0)
[ORDER_MGR] 🚀 BUY 實單下單成功 - TM0000 1口 @22438
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 API序號提取: ('5136', 0) -> 5136
[FIFO_MATCHER] 📝 註冊訂單: TM0000 LONG 1口 @22438.0
[ORDER_TRACKER] 📝 註冊實際訂單: 11767f79 LONG TM0000 1口 @22438
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 已註冊訂單到 追蹤器: 11767f79 (API序號: 5136)
INFO:multi_group_position_manager.MultiGroupPositionManager:📤 [簡化追蹤] 下單成功，需要更新已送出口數
INFO:multi_group_database:更新部位65訂單資訊: order_id=11767f79, api_seq_no=('5136', 0)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 第1口下單成功: ID=65, 訂單=11767f79
INFO:multi_group_database:創建部位記錄: ID=66, 組=25, 口=2, 狀態=PENDING, 訂單ID=None
[ORDER_MGR] ⚡ 實際下單: BUY TM0000 1口 @22438 API結果:('10192', 0)
[ORDER_MGR] 🚀 BUY 實單下單成功 - TM0000 1口 @22438
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 API序號提取: ('10192', 0) -> 10192
[FIFO_MATCHER] 📝 註冊訂單: TM0000 LONG 1口 @22438.0
[ORDER_TRACKER] 📝 註冊實際訂單: 58f61c14 LONG TM0000 1口 @22438
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 已註冊訂單到 追蹤器: 58f61c14 (API序號: 10192)
INFO:multi_group_position_manager.MultiGroupPositionManager:📤 [簡化追蹤] 下單成功，需要更新已送出口數
INFO:multi_group_database:更新部位66訂單資訊: order_id=58f61c14, api_seq_no=('10192', 0)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 第2口下單成功: ID=66, 訂單=58f61c14
INFO:multi_group_database:創建部位記錄: ID=67, 組=25, 口=3, 狀態=PENDING, 訂單ID=None
[ORDER_MGR] ⚡ 實際下單: BUY TM0000 1口 @22438 API結果:('1804', 0)
[ORDER_MGR] 🚀 BUY 實單下單成功 - TM0000 1口 @22438
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 API序號提取: ('1804', 0) -> 1804
[FIFO_MATCHER] 📝 註冊訂單: TM0000 LONG 1口 @22438.0
[ORDER_TRACKER] 📝 註冊實際訂單: cb28e043 LONG TM0000 1口 @22438
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 已註冊訂單到 追蹤器: cb28e043 (API序號: 1804)
INFO:multi_group_position_manager.MultiGroupPositionManager:📤 [簡化追蹤] 下單成功，需要更新已送出口數
INFO:multi_group_database:更新部位67訂單資訊: order_id=cb28e043, api_seq_no=('1804', 0)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 第3口下單成功: ID=67, 訂單=cb28e043
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 組 4 進場完成: 3/3口成功
[TOTAL_TRACKER] 📤 strategy_4_1752052560送出: 3口, 總計: 3/3
[SIMPLIFIED_TRACKER] 📤 組4送出: 3口, 總計: 3/3
✅ [MULTI_GROUP] 組別 4 進場成功
ERROR:multi_group_database:資料庫操作錯誤: 'sqlite3.Row' object has no attribute 'get'
[OPTIMIZED_RISK] ⚠️ 新部位事件觸發失敗: 'sqlite3.Row' object has no attributte 'get'
[OPTIMIZED_RISK] 💡 將使用原始風險管理系統
[REPLY_FILTER] ✅ 手動啟用回報處理 - 開始接受新的訂單回報
🎯 [MULTI_GROUP] 進場完成: 1/1 組成功
🎯 [STRATEGY] ℹ️ [17:16:01] 多組進場執行: 1/1 組成功
[PERFORMANCE] ⚠️ 報價處理延遲: 1454.5ms @22438.0
📋 [REPLY] OnNewData: ['2315545279341', 'TF', 'N', 'N', 'F020000', '6363839', 'BNF20', 'TW', 'TM2507', '', 'e4895', '22438.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '17:16:01', '', '0000000', '7174', 'y', '20250710', '2110001019050', 'A', 'FITM', '202507', '', '', '', '', '', '', 'B', '20250709', '', '', '', 'N', '', '2315545279341']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545279341 (原始: 2315545279341)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22438.0000
   📦 數量: 1
   ⏰ 時間: 20250709 17:16:01
   🔄 買賣別: BNF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22438.0, Qty=1, BuySell=BNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22438.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
📋 [REPLY] OnNewData: ['', 'TF', 'D', 'N', 'F020000', '6363839', 'BNF20', 'TW', 'TM2507', '', 'e4895', '22438.000000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '17:16:01', '', '0000000', '7174', 'y', '20250710', '2120000084178', 'A', 'FITM', '202507', '', '', '', '', '0000000450', '', 'B', '20250709', '', '', '', 'N', '', '2315545279341']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545279341)
   📊 類型: D (成交 (Deal/Done))
   🏷️ 商品: TM2507
   💰 價格: 22438.000000
   📦 數量: 1
   ⏰ 時間: 20250709 17:16:01
   🔄 買賣別: BNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000000450
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=D, Product=TM2507, Price=22438.0, Qty=1, BuySell=BNF20
[SIMPLIFIED_TRACKER] 🔍 分析BuySell欄位: 'BNF20'
[SIMPLIFIED_TRACKER]   第2個子碼: 'N' -> 非平倉
[SIMPLIFIED_TRACKER] 🏗️ 識別為新倉成交，BuySell=BNF20
[SIMPLIFIED_TRACKER] ✅ 策略組4成交: 1口 @22438, 總計: 1/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組4成交統計更新: 1口 @22438.0, 總進度: 1/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組4(DB_ID:25) 找到 1 個PENDING部位
[ASYNC_DB] 📝 排程部位65成交更新 @22438.0 (耗時:0.0ms)
[ASYNC_DB] 📝 排程風險狀態65創建 峰值:22438.0 (耗時:0.0ms)
INFO:multi_group_position_manager.MultiGroupPositionManager:🚀 [異步更新] 部位65成交確認 @22438.0 (耗時:2.1ms)
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組4 成功確認 1 個部位成交 (總耗時:11.8ms)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組4成交: 1口 @22438.0, 進度: 1/3
INFO:multi_group_database:✅ 確認部位65成交: @22438.0
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組4成交統計更新: 1口 @22438.0, 總進度: 1/3
[ASYNC_DB] ✅ 完成position_fill更新 部位:65 延遲:0.0ms 處理:114.4ms
ERROR:multi_group_database:資料庫操作錯誤: CHECK constraint failed: update_reason IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化') OR update_reason IS NULL
ERROR:multi_group_database:創建風險管理狀態失敗: CHECK constraint failed: update_reason IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化') OR update_reason IS NULL
[ASYNC_DB] ❌ 完成risk_state更新 部位:65 延遲:116.4ms 處理:115.3ms
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組4(DB_ID:25) 找到 1 個PENDING部位
[ASYNC_DB] 📝 排程部位66成交更新 @22438.0 (耗時:0.7ms)
[ASYNC_DB] 📝 排程風險狀態66創建 峰值:22438.0 (耗時:0.0ms)
INFO:multi_group_position_manager.MultiGroupPositionManager:🚀 [異步更新] 部位66成交確認 @22438.0 (耗時:3.0ms)
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組4 成功確認 1 個部位成交 (總耗時:25.8ms)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組4成交: 1口 @22438.0, 進度: 1/3
INFO:multi_group_database:✅ 確認部位66成交: @22438.0
[SIMPLIFIED_TRACKER] ✅ 進場成交處理完成
[ASYNC_DB] ✅ 完成position_fill更新 部位:66 延遲:0.7ms 處理:197.0ms
✅ [REPLY] 簡化追蹤器處理成功
📋 [REPLY] OnNewData: ['2315545279342', 'TF', 'N', 'N', 'F020000', '6363839', 'BNF20', 'TW', 'TM2507', '', 'v4913', '22438.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '17:16:01', '', '0000000', '7174', 'y', '20250710', '2110001019051', 'A', 'FITM', '202507', '', '', '', '', '', '', 'B', '20250709', '', '', '', 'N', '', '2315545279342']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545279342 (原始: 2315545279342)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22438.0000
   📦 數量: 1
   ⏰ 時間: 20250709 17:16:01
   🔄 買賣別: BNF20
   📅 合約月份: 202507
ERROR:multi_group_database:資料庫操作錯誤: CHECK constraint failed: update_reason IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化') OR update_reason IS NULL
ERROR:multi_group_database:創建風險管理狀態失敗: CHECK constraint failed: update_reason IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化') OR update_reason IS NULL
[ASYNC_DB] ❌ 完成risk_state更新 部位:66 延遲:198.0ms 處理:243.5ms
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22438.0, Qty=1, BuySell=BNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22438.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
[PERFORMANCE] ⚠️ 報價處理延遲: 103.8ms @22438.0
📋 [REPLY] OnNewData: ['', 'TF', 'D', 'N', 'F020000', '6363839', 'BNF20', 'TW', 'TM2507', '', 'v4913', '22438.000000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '17:16:01', '', '0000000', '7174', 'y', '20250710', '2120000084179', 'A', 'FITM', '202507', '', '', '', '', '0000000451', '', 'B', '20250709', '', '', '', 'N', '', '2315545279342']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545279342)
   📊 類型: D (成交 (Deal/Done))
   🏷️ 商品: TM2507
   💰 價格: 22438.000000
   📦 數量: 1
   ⏰ 時間: 20250709 17:16:01
   🔄 買賣別: BNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000000451
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=D, Product=TM2507, Price=22438.0, Qty=1, BuySell=BNF20
[SIMPLIFIED_TRACKER] 🔍 分析BuySell欄位: 'BNF20'
[SIMPLIFIED_TRACKER]   第2個子碼: 'N' -> 非平倉
[SIMPLIFIED_TRACKER] 🏗️ 識別為新倉成交，BuySell=BNF20
[SIMPLIFIED_TRACKER] ✅ 策略組4成交: 1口 @22438, 總計: 2/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組4成交統計更新: 1口 @22438.0, 總進度: 2/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組4(DB_ID:25) 找到 1 個PENDING部位
[ASYNC_DB] 📝 排程部位67成交更新 @22438.0 (耗時:9.4ms)
[ASYNC_DB] 📝 排程風險狀態67創建 峰值:22438.0 (耗時:0.0ms)
INFO:multi_group_position_manager.MultiGroupPositionManager:🚀 [異步更新] 部位67成交確認 @22438.0 (耗時:24.8ms)
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組4 成功確認 1 個部位成交 (總耗時:24.8ms)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組4成交: 1口 @22438.0, 進度: 2/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組4成交統計更新: 1口 @22438.0, 總進度: 2/3
INFO:multi_group_database:✅ 確認部位67成交: @22438.0
[ASYNC_DB] ✅ 完成position_fill更新 部位:67 延遲:11.3ms 處理:198.5ms
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組4 所有部位已成交 (3/3)，跳過重複處理
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組4成交: 1口 @22438.0, 進度: 2/3
[SIMPLIFIED_TRACKER] ✅ 進場成交處理完成
ERROR:multi_group_database:資料庫操作錯誤: CHECK constraint failed: update_reason IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化') OR update_reason IS NULL
ERROR:multi_group_database:創建風險管理狀態失敗: CHECK constraint failed: update_reason IN ('價格更新', '移動停利啟動', '保護性停損更新', '初始化') OR update_reason IS NULL
✅ [REPLY] 簡化追蹤器處理成功
[ASYNC_DB] ❌ 完成risk_state更新 部位:67 延遲:187.1ms 處理:99.8ms
[PERFORMANCE] ⚠️ 報價處理延遲: 121.7ms @22438.0
📋 [REPLY] OnNewData: ['2315545279736', 'TF', 'N', 'N', 'F020000', '6363839', 'BNF20', 'TW', 'TM2507', '', 'o4889', '22438.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '17:16:01', '', '0000000', '7174', 'y', '20250710', '2110001019052', 'A', 'FITM', '202507', '', '', '', '', '', '', 'B', '20250709', '', '', '', 'N', '', '2315545279736']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545279736 (原始: 2315545279736)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22438.0000
   📦 數量: 1
   ⏰ 時間: 20250709 17:16:01
   🔄 買賣別: BNF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22438.0, Qty=1, BuySell=BNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22438.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
📋 [REPLY] OnNewData: ['', 'TF', 'D', 'N', 'F020000', '6363839', 'BNF20', 'TW', 'TM2507', '', 'o4889', '22438.000000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '17:16:01', '', '0000000', '7174', 'y', '20250710', '2120000084180', 'A', 'FITM', '202507', '', '', '', '', '0000000452', '', 'B', '20250709', '', '', '', 'N', '', '2315545279736']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545279736)
   📊 類型: D (成交 (Deal/Done))
   🏷️ 商品: TM2507
   💰 價格: 22438.000000
   📦 數量: 1
   ⏰ 時間: 20250709 17:16:01
   🔄 買賣別: BNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000000452
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=D, Product=TM2507, Price=22438.0, Qty=1, BuySell=BNF20
[SIMPLIFIED_TRACKER] 🔍 分析BuySell欄位: 'BNF20'
[SIMPLIFIED_TRACKER]   第2個子碼: 'N' -> 非平倉
[SIMPLIFIED_TRACKER] 🏗️ 識別為新倉成交，BuySell=BNF20
[SIMPLIFIED_TRACKER] ✅ 策略組4成交: 1口 @22438, 總計: 3/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組4成交統計更新: 1口 @22438.0, 總進度: 3/3
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組4 所有部位已成交 (3/3)，跳過重複處理
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組4成交: 1口 @22438.0, 進度: 3/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組4建倉完成!
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組4成交統計更新: 1口 @22438.0, 總進度: 3/3
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組4 所有部位已成交 (3/3)，跳過重複處理
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組4成交: 1口 @22438.0, 進度: 3/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組4建倉完成!
[SIMPLIFIED_TRACKER] 🎉 策略組4建倉完成!
[SIMPLIFIED_TRACKER] ✅ 進場成交處理完成
✅ [REPLY] 簡化追蹤器處理成功
[PERFORMANCE] ⚠️ 報價處理延遲: 104.9ms @22438.0
🔍 策略收到: price=22438.0, api_time=17:16:05, sys_time=17:16:05, diff=0s, count=350
------
既然已經達成這些功能,請幫我檢查現在平倉機制,應該是用新功能,每5秒更新資料庫,在這期間使用緩存計算,但從LOG看現在可以平倉(我看期貨商部位有達成平倉)但可能是還未有更新步位狀態功能或是出錯,導致重複一直送單,所以期貨商的LOG我看到大量失敗平倉訂單,所以平倉功能是可以用,一樣我希望你在不影響平倉功能可用的狀況下進行修復.

-----


[RISK_DEBUG]   部位66: LONG @22438.0 狀態:FILLED
[RISK_DEBUG]   部位67: LONG @22438.0 狀態:FILLED
[ASYNC_PERF] 📊 異步更新統計: 平均延遲:85.6ms 最大延遲:198.0ms 成功率:50.0% 
🔍 策略收到: price=22439.0, api_time=17:16:48, sys_time=17:16:48, diff=0s, count=400

[ASYNC_DB] 📊 性能統計報告 (運行時間: 424.4s)
  總任務數: 6
  完成任務: 3
  失敗任務: 3
  緩存命中: 6
  平均延遲: 85.6ms
  最大延遲: 198.0ms
  當前隊列: 0
  隊列峰值: 1
  成功率: 50.0%

🔍 策略收到: price=22443.0, api_time=17:17:02, sys_time=17:17:03, diff=1s, count=450
[RISK_DEBUG] 🔍 風險管理引擎調用: 第250次 @22446
[RISK_DEBUG] 📊 活躍部位數量: 3
[RISK_DEBUG]   部位65: LONG @22438.0 狀態:FILLED
[RISK_DEBUG]   部位66: LONG @22438.0 狀態:FILLED
[RISK_DEBUG]   部位67: LONG @22438.0 狀態:FILLED
[ASYNC_PERF] 📊 異步更新統計: 平均延遲:85.6ms 最大延遲:198.0ms 成功率:50.0% 
🔍 策略收到: price=22447.0, api_time=17:17:21, sys_time=17:17:21, diff=0s, count=500
🔍 策略收到: price=22451.0, api_time=17:17:21, sys_time=17:17:22, diff=1s, count=550
[OPTIMIZED_RISK] 🎯 LONG移動停利啟動: 65 22453.0 >= 22453.0
[OPTIMIZED_RISK] 🎯 LONG移動停利啟動: 66 22453.0 >= 22453.0
[OPTIMIZED_RISK] 🎯 LONG移動停利啟動: 67 22453.0 >= 22453.0
[OPTIMIZED_RISK] 📊 風險事件: 3 個
INFO:risk_management_engine.RiskManagementEngine:部位 65 第1口移動停利啟動  
[RISK_DEBUG] 🔍 風險管理引擎調用: 第300次 @22453
[RISK_DEBUG] 📊 活躍部位數量: 3
[RISK_DEBUG]   部位65: LONG @22438.0 狀態:FILLED
[RISK_DEBUG]   部位66: LONG @22438.0 狀態:FILLED
[RISK_DEBUG]   部位67: LONG @22438.0 狀態:FILLED
[ASYNC_PERF] 📊 異步更新統計: 平均延遲:85.6ms 最大延遲:198.0ms 成功率:50.0%
🔍 策略收到: price=22453.0, api_time=17:17:21, sys_time=17:17:22, diff=1s, count=600
[PERFORMANCE] ⚠️ 報價處理延遲: 158.7ms @22453.0
[OPTIMIZED_RISK] 📊 風險事件: 3 個
🔍 策略收到: price=22448.0, api_time=17:17:25, sys_time=17:17:25, diff=0s, count=650

[ASYNC_DB] 📊 性能統計報告 (運行時間: 454.7s)
  總任務數: 6
  完成任務: 3
  失敗任務: 3
  緩存命中: 6
  平均延遲: 85.6ms
  最大延遲: 198.0ms
  當前隊列: 0
  隊列峰值: 1
  成功率: 50.0%

[RISK_DEBUG] 🔍 風險管理引擎調用: 第350次 @22452
[RISK_DEBUG] 📊 活躍部位數量: 3
[RISK_DEBUG]   部位65: LONG @22438.0 狀態:FILLED
[RISK_DEBUG]   部位66: LONG @22438.0 狀態:FILLED
[RISK_DEBUG]   部位67: LONG @22438.0 狀態:FILLED
[ASYNC_PERF] 📊 異步更新統計: 平均延遲:85.6ms 最大延遲:198.0ms 成功率:50.0%
🔍 策略收到: price=22452.0, api_time=17:17:42, sys_time=17:17:42, diff=0s, count=700
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍部位
[OPTIMIZED_RISK] 📊 風險事件: 3 個
🔍 策略收到: price=22455.0, api_time=17:17:55, sys_time=17:17:56, diff=1s, count=750

[ASYNC_DB] 📊 性能統計報告 (運行時間: 485.0s)
  總任務數: 6
  完成任務: 3
  失敗任務: 3
  緩存命中: 6
  平均延遲: 85.6ms
  最大延遲: 198.0ms
  當前隊列: 0
  隊列峰值: 1
  成功率: 50.0%

[PERFORMANCE] ⚠️ 報價處理延遲: 154.0ms @22454.0
[RISK_DEBUG] 🔍 風險管理引擎調用: 第400次 @22454
[RISK_DEBUG] 📊 活躍部位數量: 3
[RISK_DEBUG]   部位65: LONG @22438.0 狀態:FILLED
[RISK_DEBUG]   部位66: LONG @22438.0 狀態:FILLED
[RISK_DEBUG]   部位67: LONG @22438.0 狀態:FILLED
[ASYNC_PERF] 📊 異步更新統計: 平均延遲:85.6ms 最大延遲:198.0ms 成功率:50.0% 
🔍 策略收到: price=22454.0, api_time=17:18:09, sys_time=17:18:09, diff=0s, count=800
[PERFORMANCE] ⚠️ 報價處理延遲: 122.3ms @22453.0
🔍 策略收到: price=22454.0, api_time=17:18:22, sys_time=17:18:22, diff=0s, count=850
[PERFORMANCE] ⚠️ 報價處理延遲: 175.9ms @22453.0

[ASYNC_DB] 📊 性能統計報告 (運行時間: 515.3s)
  總任務數: 6
  完成任務: 3
  失敗任務: 3
  緩存命中: 6
  平均延遲: 85.6ms
  最大延遲: 198.0ms
  當前隊列: 0
  隊列峰值: 1
  成功率: 50.0%

[QUOTE_MGR] TM0000 五檔更新 #200 ASK1:22454.0 BID1:22453.0
[RISK_DEBUG] 🔍 風險管理引擎調用: 第450次 @22453
[RISK_DEBUG] 📊 活躍部位數量: 3
[RISK_DEBUG]   部位65: LONG @22438.0 狀態:FILLED
[RISK_DEBUG]   部位66: LONG @22438.0 狀態:FILLED
[RISK_DEBUG]   部位67: LONG @22438.0 狀態:FILLED
[ASYNC_PERF] 📊 異步更新統計: 平均延遲:85.6ms 最大延遲:198.0ms 成功率:50.0%
🔍 策略收到: price=22453.0, api_time=17:18:33, sys_time=17:18:33, diff=0s, count=900
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍部位
[PERFORMANCE] ⚠️ 報價處理延遲: 118.5ms @22453.0
[PERFORMANCE] ⚠️ 報價處理延遲: 143.0ms @22453.0



-----

[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22250.0, Qty=1
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22250.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
📋 [REPLY] OnNewData: ['2315545170118', 'TF', 'N', 'Y', 'F020000', '6363839', 'SOF20', 'TW', 'TM2507', '', '00000', '22250.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250708', '23:55:32', '', '0000000', '7174', 'y', '20250708', '2990000006597', 'A', 'FITM', '202507', '0.000', '', '', '', '', '', 'A', '20250708', '', '', '勾選平倉而留倉部位不足 退單!         0 =         17        17', 'N', '', '2315545170118']

根據群益API元件使用說明文件中「12.回報」章節的OnNewData事件說明，bstrData參數中的欄位定義如下：
•
0. KeyNo
•
1. MarketType
•
2. Type
•
3. OrderErr
•
4. Broker
•
5. CustNo
•
6. BuySell
因此，根據文件 所示，BuySell欄位確實位於bstrData參數的索引6（即第7個欄位，因為索引從0開始計算）。這表示您前次詢問時，我針對BuySell欄位位置的說明（索引5）是不精確的，在此向您更正，實際應為索引6。
接下來，我們來詳細說明針對台指期（國內期貨，MarketType為TF）的BuySell欄位資料結構及其意義：
在OnNewData事件回報的bstrData字串中，索引為6的BuySell欄位，其內容本身是一個複合型的字串，包含多個子碼（Sub-codes），這些子碼用來表示委託的買賣方向、新平倉屬性、委託時效以及委託價格類型。
對於國內期貨 (TF) 市場的委託，BuySell欄位的詳細結構與意義如下：
•
BuySell 欄位 （第一個子碼）：
◦
B：代表「買進」。
◦
S：代表「賣出」。
◦
備註：若為刪單失敗單（例如預約單已被取消，又進行刪單的情況），則此子碼將顯示0，而非B或S。
•
BuySell 欄位（第二個子碼，用於表示倉位屬性）：
◦
Y：代表「當沖」。
◦
N：代表「新倉」。
◦
O：代表「平倉」。
◦
7：代表「代沖銷」。
•
BuySell 欄位（第三個子碼，用於表示委託時效）：
◦
I：代表「立即成交否則取消 (IOC)」。
◦
R：代表「當日有效 (ROD)」。
◦
F：代表「立即全部成交否則取消 (FOK)」。
◦
這個時效選項在您下單時可以透過 pOrder.sTradeType 參數設定，例如在海外期貨AB單委託中，comboBoxsTradeTypeAB 的選項就包含0:ROD、3:IOC、4:FOK。國內期貨一般委託（SendFutureOrderCLR）或智慧單（如SendFutureSTPOrderV1、SendFutureMITOrderV1、SendFutureOCOOrderV1）的FUTUREORDER物件中，sTradeType參數也可設定0:ROD、1:IOC、2:FOK或3:IOC、4:FOK。
•
BuySell 欄位（第四個子碼，用於表示委託價格類型）：
◦
1：代表「市價」。
◦
2：代表「限價」。
◦
3：代表「範圍市價」。
◦
4：代表「停損限價」。
◦
5：代表「收市」。
•
BuySell 欄位（第五個子碼）：
◦
此欄位對於期貨市場是「N/A」（不適用）。
範例情境：下平倉單成功的回報
基於上述說明，當您下達一筆台指期平倉單並成功成交時，您會透過OnNewData事件收到回報。該回報的bstrData字串中，相關欄位將會是：
•
MarketType 欄位（索引1）：會是 TF，表示國內期貨。
•
Type 欄位（索引2）：會是 D，表示「成交 (Deal)」。
•
BuySell 欄位（索引6）：會包含例如 S（賣出）或 B（買進）作為第一個子碼，O（平倉）作為第二個子碼，以及相應的委託時效（如F代表FOK）和價格類型。
例如，一個成功的平倉買單，委託條件為FOK，價格類型為限價，其BuySell欄位內容可能類似於 "B,O,F,2" (這是一個示範格式，實際API回傳的字串會將所有子碼組合在一起，且可能不帶逗號分隔符號)。
希望這次的詳細說明能幫助您更清楚地理解群益下單API在回報平倉單時的資料結構。

-----進場追價少一口,是否為同價位導致?
[RISK_DEBUG] 📊 活躍部位數量: 0
🔍 策略收到: price=22228.0, time=08:47:00, count=1500
[STRATEGY] [08:46:59] 🔥 即時空單觸發！報價:22226 < 下緣:22227
[STRATEGY] [08:46:59] ⚡ 立即進場做空（不等1分K收盤）...
🔥 [STRATEGY] SHORT突破信號已觸發（即時）
🎯 [MULTI_GROUP] 根據突破方向創建策略組: SHORT
INFO:multi_group_position_manager.MultiGroupPositionManager:今日首次執行，分配組別ID: [1]   
INFO:multi_group_position_manager.MultiGroupPositionManager:創建進場信號: SHORT @ 08:47:00, 區間: 22227.0-22255.0
INFO:multi_group_position_manager.MultiGroupPositionManager:使用動態組別ID: [1]
INFO:multi_group_database:創建策略組: ID=22, 組別=1, 方向=SHORT
INFO:multi_group_position_manager.MultiGroupPositionManager:創建策略組 1 (原:1): DB_ID=22
🎯 [STRATEGY] ℹ️ [08:47:00] 多組策略啟動: 1組 SHORT, 區間22227.0-22255.0
✅ [MULTI_GROUP] 已創建 1 個SHORT策略組
🎯 [MULTI_GROUP] 開始執行 1 組進場
INFO:multi_group_position_manager.MultiGroupPositionManager:🚀 執行組 1 進場: 3口 @ 22226.0
[TOTAL_TRACKER] 總量追蹤器初始化: strategy_1_1752022020
    目標: SHORT TM0000 3口
    配置: 3口/組
[TOTAL_MANAGER] 📝 創建策略追蹤器: strategy_1_1752022020
    目標: SHORT TM0000 3口 (3口/組)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 總量追蹤器創建成功: strategy_1_1752022020
[SIMPLIFIED_TRACKER] 📝 註冊策略組: 1 SHORT TM0000 3口 @22226
INFO:multi_group_database:創建部位記錄: ID=56, 組=22, 口=1, 狀態=PENDING, 訂單ID=None
[ORDER_MGR] ⚡ 實際下單: SELL TM0000 1口 @22226 API結果:('8404', 0)
[ORDER_MGR] 🚀 SELL 實單下單成功 - TM0000 1口 @22226
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 API序號提取: ('8404', 0) -> 8404
[FIFO_MATCHER] 📝 註冊訂單: TM0000 SHORT 1口 @22226.0
[ORDER_TRACKER] 📝 註冊實際訂單: a701d48f SHORT TM0000 1口 @22226
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 已註冊訂單到追蹤器: a701d48f (API序號: 8404)
INFO:multi_group_position_manager.MultiGroupPositionManager:📤 [簡化追蹤] 下單成功，需要更新已送出口數
INFO:multi_group_database:更新部位56訂單資訊: order_id=a701d48f, api_seq_no=('8404', 0)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 第1口下單成功: ID=56, 訂單=a701d48f
INFO:multi_group_database:創建部位記錄: ID=57, 組=22, 口=2, 狀態=PENDING, 訂單ID=None
[ORDER_MGR] ⚡ 實際下單: SELL TM0000 1口 @22226 API結果:('7344', 0)
[ORDER_MGR] 🚀 SELL 實單下單成功 - TM0000 1口 @22226
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 API序號提取: ('7344', 0) -> 7344
[FIFO_MATCHER] 📝 註冊訂單: TM0000 SHORT 1口 @22226.0
[ORDER_TRACKER] 📝 註冊實際訂單: 6148df28 SHORT TM0000 1口 @22226
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 已註冊訂單到追蹤器: 6148df28 (API序號: 7344)
INFO:multi_group_position_manager.MultiGroupPositionManager:📤 [簡化追蹤] 下單成功，需要更新已送出口數
INFO:multi_group_database:更新部位57訂單資訊: order_id=6148df28, api_seq_no=('7344', 0)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 第2口下單成功: ID=57, 訂單=6148df28
INFO:multi_group_database:創建部位記錄: ID=58, 組=22, 口=3, 狀態=PENDING, 訂單ID=None
[ORDER_MGR] ⚡ 實際下單: SELL TM0000 1口 @22226 API結果:('5640', 0)
[ORDER_MGR] 🚀 SELL 實單下單成功 - TM0000 1口 @22226
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 API序號提取: ('5640', 0) -> 5640
[FIFO_MATCHER] 📝 註冊訂單: TM0000 SHORT 1口 @22226.0
[ORDER_TRACKER] 📝 註冊實際訂單: c777bb6b SHORT TM0000 1口 @22226
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 已註冊訂單到追蹤器: c777bb6b (API序號: 5640)
INFO:multi_group_position_manager.MultiGroupPositionManager:📤 [簡化追蹤] 下單成功，需要更新已送出口數
INFO:multi_group_database:更新部位58訂單資訊: order_id=c777bb6b, api_seq_no=('5640', 0)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 第3口下單成功: ID=58, 訂單=c777bb6b
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 組 1 進場完成: 3/3口成功
[TOTAL_TRACKER] 📤 strategy_1_1752022020送出: 3口, 總計: 3/3
[SIMPLIFIED_TRACKER] 📤 組1送出: 3口, 總計: 3/3
✅ [MULTI_GROUP] 組別 1 進場成功
[REPLY_FILTER] ✅ 手動啟用回報處理 - 開始接受新的訂單回報
🎯 [MULTI_GROUP] 進場完成: 1/1 組成功
🎯 [STRATEGY] ℹ️ [08:47:03] 多組進場執行: 1/1 組成功
📋 [REPLY] OnNewData: ['2315545187504', 'TF', 'N', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'j0180', '22226.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '08:47:03', '', '0000000', '7174', 'y', '20250709', '2110000031313', 'A', 'FITM', '202507', '', '', '', '', '', '', 'A', '20250709', '', '', '', 'N', '', '2315545187504']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545187504 (原始: 2315545187504)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22226.0000
   📦 數量: 1
   ⏰ 時間: 20250709 08:47:03
   🔄 買賣別: SNF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22226.0, Qty=1, BuySell=SNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22226.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
📋 [REPLY] OnNewData: ['', 'TF', 'C', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'j0180', '0.000000', '', '', '', '', '', '', '', '', '0', '', '', '20250709', '08:47:03', '', '0000000', '7174', 'y', '20250709', '2120000023014', 'A', 'FITM', '202507', '', '', '', '', '0000000502', '', 'A', '20250709', '', '', '', 'N', '', '2315545187504']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545187504)
   📊 類型: C (取消 (Cancel))
   🏷️ 商品: TM2507
   💰 價格: 0.000000
   📦 數量: 0
   ⏰ 時間: 20250709 08:47:03
   🔄 買賣別: SNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000000502
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=C, Product=TM2507, Price=0.0, Qty=0, BuySell=SNF20
[SIMPLIFIED_TRACKER] ❌ 策略組1取消: 1口 (原回報: 0口 @0.0)
[SIMPLIFIED_TRACKER] 📊 組1狀態: 總3口, 成交0口, 取消1口
[SIMPLIFIED_TRACKER] 🔄 追價邏輯檢查:
[SIMPLIFIED_TRACKER]   總口數: 3, 已成交: 0
[SIMPLIFIED_TRACKER]   剩餘口數: 3, 追價口數: 1
[SIMPLIFIED_TRACKER] 🚀 觸發追價: 1口
INFO:multi_group_position_manager.MultiGroupPositionManager:🔄 [簡化追蹤] 組1觸發追價: 1口 @0.0, 第1次重試
INFO:multi_group_position_manager.MultiGroupPositionManager:🔄 [簡化追蹤] 組1觸發追價重試: 1口 @0.0, 第1次
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [追價] 獲取組1信息: SHORT @22333.0-22337.0
INFO:multi_group_position_manager.MultiGroupPositionManager:🔄 [追價] SHORT追價計算: BID1(22223.0) - 1 = 22222.0
INFO:multi_group_position_manager.MultiGroupPositionManager:🔄 [簡化追蹤] 組1追價參數: SHORT 1口 @22222.0 (第1次)
[ORDER_MGR] ⚡ 實際下單: SELL TM0000 1口 @22222 API結果:('10532', 0)
[ORDER_MGR] 🚀 SELL 實單下單成功 - TM0000 1口 @22222
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 組1追價下單成功: 第1口 @22222.0
[FIFO_MATCHER] 📝 註冊訂單: TM0000 SHORT 1口 @22222.0
[ORDER_TRACKER] 📝 註冊實際訂單: 50f0d190 SHORT TM0000 1口 @22222
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 組1追價訂單已註冊: 50f0d190
INFO:multi_group_position_manager.MultiGroupPositionManager:🔄 [簡化追蹤] 組1觸發追價: 1口 @0.0, 第1次重試
INFO:multi_group_position_manager.MultiGroupPositionManager:🔄 [簡化追蹤] 組1觸發追價重試: 1口 @0.0, 第1次
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [追價] 獲取組1信息: SHORT @22333.0-22337.0
INFO:multi_group_position_manager.MultiGroupPositionManager:🔄 [追價] SHORT追價計算: BID1(22223.0) - 1 = 22222.0
INFO:multi_group_position_manager.MultiGroupPositionManager:🔄 [簡化追蹤] 組1追價參數: SHORT 1口 @22222.0 (第1次)
[ORDER_MGR] ⚡ 實際下單: SELL TM0000 1口 @22222 API結果:('3264', 0)
[ORDER_MGR] 🚀 SELL 實單下單成功 - TM0000 1口 @22222
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 組1追價下單成功: 第1口 @22222.0
[FIFO_MATCHER] 📝 註冊訂單: TM0000 SHORT 1口 @22222.0
[ORDER_TRACKER] 📝 註冊實際訂單: 115b2b8e SHORT TM0000 1口 @22222
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 組1追價訂單已註冊: 115b2b8e  
[SIMPLIFIED_TRACKER] ✅ 進場取消處理完成
✅ [REPLY] 簡化追蹤器處理成功
📋 [REPLY] OnNewData: ['2315545188672', 'TF', 'N', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'm0178', '22226.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '08:47:03', '', '0000000', '7174', 'y', '20250709', '2110000031319', 'A', 'FITM', '202507', '', '', '', '', '', '', 'A', '20250709', '', '', '', 'N', '', '2315545188672']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545188672 (原始: 2315545188672)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22226.0000
   📦 數量: 1
   ⏰ 時間: 20250709 08:47:03
   🔄 買賣別: SNF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22226.0, Qty=1, BuySell=SNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22226.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
📋 [REPLY] OnNewData: ['', 'TF', 'C', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'm0178', '0.000000', '', '', '', '', '', '', '', '', '0', '', '', '20250709', '08:47:03', '', '0000000', '7174', 'y', '20250709', '2120000023016', 'A', 'FITM', '202507', '', '', '', '', '0000000703', '', 'A', '20250709', '', '', '', 'N', '', '2315545188672']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545188672)
   📊 類型: C (取消 (Cancel))
   🏷️ 商品: TM2507
   💰 價格: 0.000000
   📦 數量: 0
   ⏰ 時間: 20250709 08:47:03
   🔄 買賣別: SNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000000703
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=C, Product=TM2507, Price=0.0, Qty=0, BuySell=SNF20
[SIMPLIFIED_TRACKER] ❌ 策略組1取消: 1口 (原回報: 0口 @0.0)
[SIMPLIFIED_TRACKER] 📊 組1狀態: 總3口, 成交0口, 取消2口
[SIMPLIFIED_TRACKER] ✅ 進場取消處理完成
✅ [REPLY] 簡化追蹤器處理成功
📋 [REPLY] OnNewData: ['2315545187505', 'TF', 'N', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'u0185', '22226.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '08:47:04', '', '0000000', '7174', 'y', '20250709', '2110000031371', 'A', 'FITM', '202507', '', '', '', '', '', '', 'A', '20250709', '', '', '', 'N', '', '2315545187505']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545187505 (原始: 2315545187505)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22226.0000
   📦 數量: 1
   ⏰ 時間: 20250709 08:47:04
   🔄 買賣別: SNF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22226.0, Qty=1, BuySell=SNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22226.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
📋 [REPLY] OnNewData: ['', 'TF', 'C', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'u0185', '0.000000', '', '', '', '', '', '', '', '', '0', '', '', '20250709', '08:47:04', '', '0000000', '7174', 'y', '20250709', '2120000023034', 'A', 'FITM', '202507', '', '', '', '', '0000000705', '', 'A', '20250709', '', '', '', 'N', '', '2315545187505']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545187505)
   📊 類型: C (取消 (Cancel))
   🏷️ 商品: TM2507
   💰 價格: 0.000000
   📦 數量: 0
   ⏰ 時間: 20250709 08:47:04
   🔄 買賣別: SNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000000705
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=C, Product=TM2507, Price=0.0, Qty=0, BuySell=SNF20
[SIMPLIFIED_TRACKER] ❌ 策略組1取消: 1口 (原回報: 0口 @0.0)
[SIMPLIFIED_TRACKER] 📊 組1狀態: 總3口, 成交0口, 取消3口
[SIMPLIFIED_TRACKER] ✅ 進場取消處理完成
✅ [REPLY] 簡化追蹤器處理成功
📋 [REPLY] OnNewData: ['2315545187515', 'TF', 'N', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'k0181', '22222.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '08:47:06', '', '0000000', '7174', 'y', '20250709', '2110000031468', 'A', 'FITM', '202507', '', '', '', '', '', '', 'A', '20250709', '', '', '', 'N', '', '2315545187515']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545187515 (原始: 2315545187515)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22222.0000
   📦 數量: 1
   ⏰ 時間: 20250709 08:47:06
   🔄 買賣別: SNF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22222.0, Qty=1, BuySell=SNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22222.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
📋 [REPLY] OnNewData: ['', 'TF', 'D', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'k0181', '22224.000000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '08:47:06', '', '0000000', '7174', 'y', '20250709', '2120000023059', 'A', 'FITM', '202507', '', '', '', '', '0000000511', '', 'A', '20250709', '', '', '', 'N', '', '2315545187515']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545187515)
   📊 類型: D (成交 (Deal/Done))
   🏷️ 商品: TM2507
   💰 價格: 22224.000000
   📦 數量: 1
   ⏰ 時間: 20250709 08:47:06
   🔄 買賣別: SNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000000511
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=D, Product=TM2507, Price=22224.0, Qty=1, BuySell=SNF20
[SIMPLIFIED_TRACKER] 🔍 分析BuySell欄位: 'SNF20'
[SIMPLIFIED_TRACKER]   第2個子碼: 'N' -> 非平倉
[SIMPLIFIED_TRACKER] 🏗️ 識別為新倉成交，BuySell=SNF20
[SIMPLIFIED_TRACKER] ✅ 策略組1成交: 1口 @22224, 總計: 1/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組1成交統計更新: 1口 @22224.0, 總進度: 1/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組1(DB_ID:22) 找到 1 個PENDING部位
INFO:multi_group_database:✅ 確認部位56成交: @22224.0
INFO:multi_group_database:創建風險管理狀態: 部位=56, 峰值=22224.0
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 部位56成交確認: @22224.0
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組1 成功確認 1 個 部位成交
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組1成交: 1口 @22224.0, 進度: 1/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組1成交統計更新: 1口 @22224.0, 總進度: 1/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組1(DB_ID:22) 找到 1 個PENDING部位
INFO:multi_group_database:✅ 確認部位57成交: @22224.0
INFO:multi_group_database:創建風險管理狀態: 部位=57, 峰值=22224.0
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 部位57成交確認: @22224.0
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組1 成功確認 1 個 部位成交
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組1成交: 1口 @22224.0, 進度: 1/3
[SIMPLIFIED_TRACKER] ✅ 進場成交處理完成
✅ [REPLY] 簡化追蹤器處理成功
📋 [REPLY] OnNewData: ['2315545188681', 'TF', 'N', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'd0176', '22222.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '08:47:08', '', '0000000', '7174', 'y', '20250709', '2110000031502', 'A', 'FITM', '202507', '', '', '', '', '', '', 'A', '20250709', '', '', '', 'N', '', '2315545188681']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545188681 (原始: 2315545188681)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22222.0000
   📦 數量: 1
   ⏰ 時間: 20250709 08:47:08
   🔄 買賣別: SNF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22222.0, Qty=1, BuySell=SNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22222.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
📋 [REPLY] OnNewData: ['', 'TF', 'D', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'd0176', '22225.000000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '08:47:08', '', '0000000', '7174', 'y', '20250709', '2120000023073', 'A', 'FITM', '202507', '', '', '', '', '0000000716', '', 'A', '20250709', '', '', '', 'N', '', '2315545188681']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545188681)
   📊 類型: D (成交 (Deal/Done))
   🏷️ 商品: TM2507
   💰 價格: 22225.000000
   📦 數量: 1
   ⏰ 時間: 20250709 08:47:08
   🔄 買賣別: SNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000000716
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=D, Product=TM2507, Price=22225.0, Qty=1, BuySell=SNF20
[SIMPLIFIED_TRACKER] 🔍 分析BuySell欄位: 'SNF20'
[SIMPLIFIED_TRACKER]   第2個子碼: 'N' -> 非平倉
[SIMPLIFIED_TRACKER] 🏗️ 識別為新倉成交，BuySell=SNF20
[SIMPLIFIED_TRACKER] ✅ 策略組1成交: 1口 @22225, 總計: 2/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組1成交統計更新: 1口 @22225.0, 總進度: 2/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組1(DB_ID:22) 找到 1 個PENDING部位
INFO:multi_group_database:✅ 確認部位58成交: @22225.0
INFO:multi_group_database:創建風險管理狀態: 部位=58, 峰值=22225.0
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 部位58成交確認: @22225.0
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組1 成功確認 1 個 部位成交
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組1成交: 1口 @22225.0, 進度: 2/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組1成交統計更新: 1口 @22225.0, 總進度: 2/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組1(DB_ID:22) 找到 0 個PENDING部位
WARNING:multi_group_position_manager.MultiGroupPositionManager:⚠️ [簡化追蹤] 組1 沒有成功確  認任何部位成交
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組1成交: 1口 @22225.0, 進度: 2/3
[SIMPLIFIED_TRACKER] ✅ 進場成交處理完成
✅ [REPLY] 簡化追蹤器處理成功
🔍 策略收到: price=22226.0, time=08:47:01, count=1550
[RISK_DEBUG] 🔍 風險管理引擎調用: 第800次 @22225


-----啟動移動停利成功,但是須加上LOG讓我確認現在停利平倉點為,例如每50個報價一次
🔍 策略收到: price=22165.0, time=08:57:54, count=7050
[RISK_DEBUG] 🔍 風險管理引擎調用: 第3550次 @22166
[RISK_DEBUG] 📊 活躍部位數量: 3
[RISK_DEBUG]   部位56: SHORT @22224.0 狀態:FILLED
[RISK_DEBUG]   部位57: SHORT @22224.0 狀態:FILLED
[RISK_DEBUG]   部位58: SHORT @22225.0 狀態:FILLED
🔍 策略收到: price=22168.0, time=08:57:57, count=7100
INFO:risk_management_engine.RiskManagementEngine:部位 58 第3口移動停利啟動
🔍 策略收到: price=22160.0, time=08:57:58, count=7150
[RISK_DEBUG] 🔍 風險管理引擎調用: 第3600次 @22159

持續觀察沒觸發止損
[RISK_DEBUG]   部位57: SHORT @22224.0 狀態:FILLED
[RISK_DEBUG]   部位58: SHORT @22225.0 狀態:FILLED
🔍 策略收到: price=22224.0, time=09:04:01, count=12700
🔍 策略收到: price=22225.0, time=09:04:06, count=12750
[RISK_DEBUG] 🔍 風險管理引擎調用: 第6400次 @22225
[RISK_DEBUG] 📊 活躍部位數量: 3
[RISK_DEBUG]   部位56: SHORT @22224.0 狀態:FILLED
[RISK_DEBUG]   部位57: SHORT @22224.0 狀態:FILLED
[RISK_DEBUG]   部位58: SHORT @22225.0 狀態:FILLED
🔍 策略收到: price=22224.0, time=09:04:09, count=12800
🔍 策略收到: price=22228.0, time=09:04:12, count=12850
[RISK_DEBUG] 🔍 風險管理引擎調用: 第6450次 @22227
[RISK_DEBUG] 📊 活躍部位數量: 3
[RISK_DEBUG]   部位56: SHORT @22224.0 狀態:FILLED

NFO:risk_management_engine.RiskManagementEngine:✅ 部位56出場成功: 初始停損
[ORDER_MGR] ⚡ 實際下單: BUY TM0000 1口 @22260 API結果:('7852', 0)
[ORDER_MGR] 🚀 BUY 實單下單成功 - TM0000 1口 @22260
INFO:multi_group_database:✅ 更新部位57狀態: ACTIVE
INFO:multi_group_database:   出場原因: 初始停損
INFO:multi_group_database:   出場價格: 22260.0
[EXIT_ORDER] 🔚 空單出場實單下單成功 - TM0000 1口 @22260.0 (ASK1)
[UNIFIED_EXIT] ✅ 部位57出場觸發成功: 初始停損 @22260.0
INFO:risk_management_engine.RiskManagementEngine:✅ 部位57出場成功: 初始停損
[ORDER_MGR] ⚡ 實際下單: BUY TM0000 1口 @22260 API結果:('12472', 0)
[ORDER_MGR] 🚀 BUY 實單下單成功 - TM0000 1口 @22260
INFO:multi_group_database:✅ 更新部位58狀態: ACTIVE
INFO:multi_group_database:   出場原因: 初始停損
INFO:multi_group_database:   出場價格: 22260.0
[EXIT_ORDER] 🔚 空單出場實單下單成功 - TM0000 1口 @22260.0 (ASK1)
[UNIFIED_EXIT] ✅ 部位58出場觸發成功: 初始停損 @22260.0
INFO:risk_management_engine.RiskManagementEngine:✅ 部位58出場成功: 初始停損
[MULTI_EXIT] ✅ 成功執行 3/3 個出場動作
📋 [REPLY] OnNewData: ['2315545203454', 'TF', 'N', 'N', 'F020000', '6363839', 'BOF20', 'TW', 'TM2507', '', 'd1020', '22256.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '09:17:16', '', '0000000', '7174', 'y', '20250709', '2110000187261', 'A', 'FITM', '202507', '', '', '', '', '', '', 'A', '20250709', '', '', '', 'N', '', '2315545203454']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545203454 (原始: 2315545203454)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22256.0000
   📦 數量: 1
   ⏰ 時間: 20250709 09:17:16
   🔄 買賣別: BOF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22256.0, Qty=1, BuySell=BOF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22256.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
INFO:risk_management_engine.RiskManagementEngine:組 22 觸發初始停損，全組出場
[ORDER_MGR] ⚡ 實際下單: BUY TM0000 1口 @22260 API結果:('12724', 0)
[ORDER_MGR] 🚀 BUY 實單下單成功 - TM0000 1口 @22260
INFO:multi_group_database:✅ 更新部位56狀態: ACTIVE
INFO:multi_group_database:   出場原因: 初始停損
INFO:multi_group_database:   出場價格: 22260.0
[EXIT_ORDER] 🔚 空單出場實單下單成功 - TM0000 1口 @22260.0 (ASK1)
[UNIFIED_EXIT] ✅ 部位56出場觸發成功: 初始停損 @22260.0
INFO:risk_management_engine.RiskManagementEngine:✅ 部位56出場成功: 初始停損
[ORDER_MGR] ⚡ 實際下單: BUY TM0000 1口 @22260 API結果:('5712', 0)
[ORDER_MGR] 🚀 BUY 實單下單成功 - TM0000 1口 @22260
INFO:multi_group_database:✅ 更新部位57狀態: ACTIVE
INFO:multi_group_database:   出場原因: 初始停損
INFO:multi_group_database:   出場價格: 22260.0
[EXIT_ORDER] 🔚 空單出場實單下單成功 - TM0000 1口 @22260.0 (ASK1)
[UNIFIED_EXIT] ✅ 部位57出場觸發成功: 初始停損 @222

-----發現報價時間跟實際時間不同,發現時已差高達三分鐘,越跑差越遠
策略收到: price=22164.0, time=09:00:04, count=8700,是否這個報LOG也加上當下時間讓我看看出甚麼問題

 策略收到: price=22160.0, time=09:00:53, count=9400
🔍 策略收到: price=22153.0, time=09:00:53, count=9450
[RISK_DEBUG] 🔍 風險管理引擎調用: 第4750次 @22151
[RISK_DEBUG] 📊 活躍部位數量: 3
[RISK_DEBUG]   部位56: SHORT @22224.0 狀態:FILLED
[RISK_DEBUG]   部位57: SHORT @22224.0 狀態:FILLED
[RISK_DEBUG]   部位58: SHORT @22225.0 狀態:FILLED
🔍 策略收到: price=22151.0, time=09:00:54, count=9500
[QUOTE_MGR] TM0000 五檔更新 #600 ASK1:22278.0 BID1:22277.0
🔍 策略收到: price=22153.0, time=09:00:54, count=9550
[RISK_DEBUG] 🔍 風險管理引擎調用: 第4800次 @22153
[RISK_DEBUG] 📊 活躍部位數量: 3
[RISK_DEBUG]   部位56: SHORT @22224.0 狀態:FILLED
[RISK_DEBUG]   部位57: SHORT @22224.0 狀態:FILLED
[RISK_DEBUG]   部位58: SHORT @22225.0 狀態:FILLED
🔍 策略收到: price=22154.0, time=09:00:54, count=9600
🔍 策略收到: price=22160.0, time=09:00:56, count=9650
發現這邊時間差8秒但實際等了非常久
[RISK_DEBUG]   部位57: SHORT @22224.0 狀態:FILLED
[RISK_DEBUG]   部位58: SHORT @22225.0 狀態:FILLED
🔍 策略收到: price=22169.0, time=09:02:03, count=10400
🔍 策略收到: price=22175.0, time=09:02:04, count=10450

感覺是否在讀取以前數據慢慢消化導致不即時?持續觀察已經差距12分鐘



----修改記憶體管理方式
🔄 [STRATEGY] 多組策略設定為可重複執行
💡 [STRATEGY] 每次區間計算完成都可以執行新的策略組
🔧 [SYSTEM] ℹ️ [12:22:01] 執行頻率變更為: 可重複執行
🎯 [STRATEGY] ℹ️ [12:22:04] 策略已準備: 1組×3口, 自動啟動: 是
✅ [STRATEGY] 多組策略已準備完成！
📊 [STRATEGY] 配置: 1組×3口
📊 [STRATEGY] 總部位數: 3
📊 [STRATEGY] 自動啟動: 是
🤖 [STRATEGY] 系統將在區間計算完成後自動啟動策略
[STRATEGY] [12:22:14] ✅ 區間時間已設定: 12:24-12:26
[STRATEGY] 🎯 自動啟用多組策略單組模式 (含動態追價)
[STRATEGY] [12:22:15] 🚀 策略監控已啟動（Console模式）
[STRATEGY] [12:22:15] 📊 監控區間: 12:24-12:26
[STRATEGY] [12:22:15] 💡 策略監控已完全Console化，避免GIL問題
🔍 策略收到: price=22378.0, api_time=12:22:18, sys_time=12:22:16, diff=-2s, count=0
🔍 策略收到: price=22376.0, api_time=12:22:52, sys_time=12:22:51, diff=-1s, count=50
[RISK_DEBUG] 🔍 風險管理引擎調用: 第50次 @22371
[RISK_DEBUG] 📊 活躍部位數量: 0
🔍 策略收到: price=22372.0, api_time=12:23:21, sys_time=12:23:20, diff=-1s, count=100
🔍 策略收到: price=22375.0, api_time=12:23:37, sys_time=12:23:36, diff=-1s, count=150
[STRATEGY] [12:23:59] 📊 開始收集區間數據: 12:24:00
[RISK_DEBUG] 🔍 風險管理引擎調用: 第100次 @22380
[RISK_DEBUG] 📊 活躍部位數量: 0
🔍 策略收到: price=22381.0, api_time=12:24:05, sys_time=12:24:04, diff=-1s, count=200
🔍 策略收到: price=22385.0, api_time=12:24:27, sys_time=12:24:26, diff=-1s, count=250
[RISK_DEBUG] 🔍 風險管理引擎調用: 第150次 @22382
[RISK_DEBUG] 📊 活躍部位數量: 0
🔍 策略收到: price=22382.0, api_time=12:24:46, sys_time=12:24:45, diff=-1s, count=300
🔍 策略收到: price=22383.0, api_time=12:25:21, sys_time=12:25:19, diff=-2s, count=350
[QUOTE_MGR] TM0000 五檔更新 #100 ASK1:22383.0 BID1:22381.0
[RISK_DEBUG] 🔍 風險管理引擎調用: 第200次 @22377
[RISK_DEBUG] 📊 活躍部位數量: 0
🔍 策略收到: price=22375.0, api_time=12:25:57, sys_time=12:25:56, diff=-1s, count=400
✅ [STRATEGY] 區間計算完成: 高:22385 低:22375 大小:10
[STRATEGY] [12:26:01] ✅ 區間計算完成: 高:22385 低:22375 大小:10
[STRATEGY] [12:26:01] 📊 收集數據點數: 114 筆，開始監測突破
🔍 策略收到: price=22379.0, api_time=12:26:31, sys_time=12:26:30, diff=-1s, count=450
[STRATEGY] [12:26:56] 🔥 即時空單觸發！報價:22374 < 下緣:22375
[STRATEGY] [12:26:56] ⚡ 立即進場做空（不等1分K收盤）...
🔥 [STRATEGY] SHORT突破信號已觸發（即時）
🎯 [MULTI_GROUP] 根據突破方向創建策略組: SHORT
INFO:multi_group_position_manager.MultiGroupPositionManager:今日已有組別 [1, 2]，分配新組別ID: [3]
INFO:multi_group_position_manager.MultiGroupPositionManager:創建進場信號: SHORT @ 12:26:58, 區間: 22375.0-22385.0
INFO:multi_group_position_manager.MultiGroupPositionManager:使用動態組別ID: [3]
INFO:multi_group_database:創建策略組: ID=24, 組別=3, 方向=SHORT
INFO:multi_group_position_manager.MultiGroupPositionManager:創建策略組 3 (原:1): DB_ID=24
🎯 [STRATEGY] ℹ️ [12:26:58] 多組策略啟動: 1組 SHORT, 區間22375.0-22385.0
✅ [MULTI_GROUP] 已創建 1 個SHORT策略組
🎯 [MULTI_GROUP] 開始執行 1 組進場
INFO:multi_group_position_manager.MultiGroupPositionManager:🚀 執行組 3 進場: 3口 @ 22374.0
[TOTAL_TRACKER] 總量追蹤器初始化: strategy_3_1752035218
    目標: SHORT TM0000 3口
    配置: 3口/組
[TOTAL_MANAGER] 📝 創建策略追蹤器: strategy_3_1752035218
    目標: SHORT TM0000 3口 (3口/組)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 總量追蹤器創建成功: strategy_3_1752035218
[SIMPLIFIED_TRACKER] 📝 註冊策略組: 3 SHORT TM0000 3口 @22374
INFO:multi_group_database:創建部位記錄: ID=62, 組=24, 口=1, 狀態=PENDING, 訂單ID=None
[ORDER_MGR] ⚡ 實際下單: SELL TM0000 1口 @22374 API結果:('11360', 0)
[ORDER_MGR] 🚀 SELL 實單下單成功 - TM0000 1口 @22374
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 API序號提取: ('11360', 0) -> 11360
[FIFO_MATCHER] 📝 註冊訂單: TM0000 SHORT 1口 @22374.0
[ORDER_TRACKER] 📝 註冊實際訂單: 4a6c2ce8 SHORT TM0000 1口 @22374
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 已註冊訂單到追蹤器: 4a6c2ce8 (API序號: 11360)
INFO:multi_group_position_manager.MultiGroupPositionManager:📤 [簡化追蹤] 下單成功，需要更新已送出口數
INFO:multi_group_database:更新部位62訂單資訊: order_id=4a6c2ce8, api_seq_no=('11360', 0)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 第1口下單成功: ID=62, 訂單=4a6c2ce8
INFO:multi_group_database:創建部位記錄: ID=63, 組=24, 口=2, 狀態=PENDING, 訂單ID=None
[ORDER_MGR] ⚡ 實際下單: SELL TM0000 1口 @22374 API結果:('11956', 0)
[ORDER_MGR] 🚀 SELL 實單下單成功 - TM0000 1口 @22374
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 API序號提取: ('11956', 0) -> 11956
[FIFO_MATCHER] 📝 註冊訂單: TM0000 SHORT 1口 @22374.0
[ORDER_TRACKER] 📝 註冊實際訂單: 6ee94249 SHORT TM0000 1口 @22374
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 已註冊訂單到追蹤器: 6ee94249 (API序號: 11956)
INFO:multi_group_position_manager.MultiGroupPositionManager:📤 [簡化追蹤] 下單成功，需要更新已送出口數
INFO:multi_group_database:更新部位63訂單資訊: order_id=6ee94249, api_seq_no=('11956', 0)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 第2口下單成功: ID=63, 訂單=6ee94249
INFO:multi_group_database:創建部位記錄: ID=64, 組=24, 口=3, 狀態=PENDING, 訂單ID=None
[ORDER_MGR] ⚡ 實際下單: SELL TM0000 1口 @22374 API結果:('7572', 0)
[ORDER_MGR] 🚀 SELL 實單下單成功 - TM0000 1口 @22374
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 API序號提取: ('7572', 0) -> 7572
[FIFO_MATCHER] 📝 註冊訂單: TM0000 SHORT 1口 @22374.0
[ORDER_TRACKER] 📝 註冊實際訂單: 54346fa5 SHORT TM0000 1口 @22374
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 已註冊訂單到追蹤器: 54346fa5 (API序號: 7572)
INFO:multi_group_position_manager.MultiGroupPositionManager:📤 [簡化追蹤] 下單成功，需要更新已送出口數
INFO:multi_group_database:更新部位64訂單資訊: order_id=54346fa5, api_seq_no=('7572', 0)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 第3口下單成功: ID=64, 訂單=54346fa5
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 組 3 進場完成: 3/3口成功
[TOTAL_TRACKER] 📤 strategy_3_1752035218送出: 3口, 總計: 3/3
[SIMPLIFIED_TRACKER] 📤 組3送出: 3口, 總計: 3/3
✅ [MULTI_GROUP] 組別 3 進場成功
[OPTIMIZED_RISK] ⚠️ 新部位事件觸發失敗: 'MultiGroupDatabaseManager' object has no attribute  'get_group_positions'
[REPLY_FILTER] ✅ 手動啟用回報處理 - 開始接受新的訂單回報
🎯 [MULTI_GROUP] 進場完成: 1/1 組成功
🎯 [STRATEGY] ℹ️ [12:27:02] 多組進場執行: 1/1 組成功
📋 [REPLY] OnNewData: ['2315545248621', 'TF', 'N', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'j3615', '22374.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '12:27:02', '', '0000000', '7174', 'y', '20250709', '2110000665652', 'A', 'FITM', '202507', '', '', '', '', '', '', 'A', '20250709', '', '', '', 'N', '', '2315545248621']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545248621 (原始: 2315545248621)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22374.0000
   📦 數量: 1
   ⏰ 時間: 20250709 12:27:02
   🔄 買賣別: SNF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22374.0, Qty=1, BuySell=SNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22374.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
ERROR:optimized_risk_manager:預計算價格點位失敗: unsupported operand type(s) for -: 'NoneType' and 'int'
ERROR:optimized_risk_manager:預計算價格點位失敗: unsupported operand type(s) for -: 'NoneType' and 'int'
ERROR:optimized_risk_manager:預計算價格點位失敗: unsupported operand type(s) for -: 'NoneType' and 'int'
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍部位
📋 [REPLY] OnNewData: ['', 'TF', 'D', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'j3615', '22374.000000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '12:27:02', '', '0000000', '7174', 'y', '20250709', '2120000066741', 'A', 'FITM', '202507', '', '', '', '', '0000010316', '', 'A', '20250709', '', '', '', 'N', '', '2315545248621']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545248621)
   📊 類型: D (成交 (Deal/Done))
   🏷️ 商品: TM2507
   💰 價格: 22374.000000
   📦 數量: 1
   ⏰ 時間: 20250709 12:27:02
   🔄 買賣別: SNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000010316
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=D, Product=TM2507, Price=22374.0, Qty=1, BuySell=SNF20
[SIMPLIFIED_TRACKER] 🔍 分析BuySell欄位: 'SNF20'
[SIMPLIFIED_TRACKER]   第2個子碼: 'N' -> 非平倉
[SIMPLIFIED_TRACKER] 🏗️ 識別為新倉成交，BuySell=SNF20
[SIMPLIFIED_TRACKER] ✅ 策略組3成交: 1口 @22374, 總計: 1/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組3成交統計更新: 1口 @22374.0, 總進度: 1/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組3(DB_ID:24) 找到 1 個PENDING部位
INFO:multi_group_database:✅ 確認部位62成交: @22374.0
INFO:multi_group_database:創建風險管理狀態: 部位=62, 峰值=22374.0
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 部位62成交確認: @22374.0
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組3 成功確認 1 個 部位成交
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組3成交: 1口 @22374.0, 進度: 1/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組3成交統計更新: 1口 @22374.0, 總進度: 1/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組3(DB_ID:24) 找到 1 個PENDING部位
INFO:multi_group_database:✅ 確認部位63成交: @22374.0
INFO:multi_group_database:創建風險管理狀態: 部位=63, 峰值=22374.0
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 部位63成交確認: @22374.0
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組3 成功確認 1 個 部位成交
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組3成交: 1口 @22374.0, 進度: 1/3
[SIMPLIFIED_TRACKER] ✅ 進場成交處理完成
✅ [REPLY] 簡化追蹤器處理成功
📋 [REPLY] OnNewData: ['2315545249358', 'TF', 'N', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'y3628', '22374.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '12:27:03', '', '0000000', '7174', 'y', '20250709', '2110000665656', 'A', 'FITM', '202507', '', '', '', '', '', '', 'A', '20250709', '', '', '', 'N', '', '2315545249358']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545249358 (原始: 2315545249358)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22374.0000
   📦 數量: 1
   ⏰ 時間: 20250709 12:27:03
   🔄 買賣別: SNF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22374.0, Qty=1, BuySell=SNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22374.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
📋 [REPLY] OnNewData: ['', 'TF', 'D', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'y3628', '22374.000000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '12:27:03', '', '0000000', '7174', 'y', '20250709', '2120000066744', 'A', 'FITM', '202507', '', '', '', '', '0000013308', '', 'A', '20250709', '', '', '', 'N', '', '2315545249358']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545249358)
   📊 類型: D (成交 (Deal/Done))
   🏷️ 商品: TM2507
   💰 價格: 22374.000000
   📦 數量: 1
   ⏰ 時間: 20250709 12:27:03
   🔄 買賣別: SNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000013308
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=D, Product=TM2507, Price=22374.0, Qty=1, BuySell=SNF20
[SIMPLIFIED_TRACKER] 🔍 分析BuySell欄位: 'SNF20'
[SIMPLIFIED_TRACKER]   第2個子碼: 'N' -> 非平倉
[SIMPLIFIED_TRACKER] 🏗️ 識別為新倉成交，BuySell=SNF20
[SIMPLIFIED_TRACKER] ✅ 策略組3成交: 1口 @22374, 總計: 2/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組3成交統計更新: 1口 @22374.0, 總進度: 2/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組3(DB_ID:24) 找到 1 個PENDING部位
INFO:multi_group_database:✅ 確認部位64成交: @22374.0
INFO:multi_group_database:創建風險管理狀態: 部位=64, 峰值=22374.0
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 部位64成交確認: @22374.0
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組3 成功確認 1 個 部位成交
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組3成交: 1口 @22374.0, 進度: 2/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組3成交統計更新: 1口 @22374.0, 總進度: 2/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組3(DB_ID:24) 找到 0 個PENDING部位
WARNING:multi_group_position_manager.MultiGroupPositionManager:⚠️ [簡化追蹤] 組3 沒有成功確  認任何部位成交
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組3成交: 1口 @22374.0, 進度: 2/3
[SIMPLIFIED_TRACKER] ✅ 進場成交處理完成
✅ [REPLY] 簡化追蹤器處理成功
📋 [REPLY] OnNewData: ['2315545249359', 'TF', 'N', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'o3596', '22374.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '12:27:03', '', '0000000', '7174', 'y', '20250709', '2110000665685', 'A', 'FITM', '202507', '', '', '', '', '', '', 'A', '20250709', '', '', '', 'N', '', '2315545249359']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545249359 (原始: 2315545249359)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22374.0000
   📦 數量: 1
   ⏰ 時間: 20250709 12:27:03
   🔄 買賣別: SNF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22374.0, Qty=1, BuySell=SNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22374.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
📋 [REPLY] OnNewData: ['', 'TF', 'D', 'N', 'F020000', '6363839', 'SNF20', 'TW', 'TM2507', '', 'o3596', '22374.000000', '', '', '', '', '', '', '', '', '1', '', '', '20250709', '12:27:03', '', '0000000', '7174', 'y', '20250709', '2120000066746', 'A', 'FITM', '202507', '', '', '', '', '0000010317', '', 'A', '20250709', '', '', '', 'N', '', '2315545249359']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545249359)
   📊 類型: D (成交 (Deal/Done))
   🏷️ 商品: TM2507
   💰 價格: 22374.000000
   📦 數量: 1
   ⏰ 時間: 20250709 12:27:03
   🔄 買賣別: SNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000010317
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=D, Product=TM2507, Price=22374.0, Qty=1, BuySell=SNF20
[SIMPLIFIED_TRACKER] 🔍 分析BuySell欄位: 'SNF20'
[SIMPLIFIED_TRACKER]   第2個子碼: 'N' -> 非平倉
[SIMPLIFIED_TRACKER] 🏗️ 識別為新倉成交，BuySell=SNF20
[SIMPLIFIED_TRACKER] ✅ 策略組3成交: 1口 @22374, 總計: 3/3
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組3成交統計更新: 1口 @22374.0, 總進度: 3/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組3(DB_ID:24) 找到 0 個PENDING部位
WARNING:multi_group_position_manager.MultiGroupPositionManager:⚠️ [簡化追蹤] 組3 沒有成功確  認任何部位成交
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組3成交: 1口 @22374.0, 進度: 3/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組3建倉完成!      
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組3成交統計更新: 1口 @22374.0, 總進度: 3/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組3(DB_ID:24) 找到 0 個PENDING部位
WARNING:multi_group_position_manager.MultiGroupPositionManager:⚠️ [簡化追蹤] 組3 沒有成功確  認任何部位成交
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組3成交: 1口 @22374.0, 進度: 3/3
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組3建倉完成!      
[SIMPLIFIED_TRACKER] 🎉 策略組3建倉完成!
[SIMPLIFIED_TRACKER] ✅ 進場成交處理完成
✅ [REPLY] 簡化追蹤器處理成功
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍部位
[RISK_DEBUG] 🔍 風險管理引擎調用: 第250次 @22372
[RISK_DEBUG] 📊 活躍部位數量: 3
[RISK_DEBUG]   部位62: SHORT @22374.0 狀態:FILLED
[RISK_DEBUG]   部位63: SHORT @22374.0 狀態:FILLED
[RISK_DEBUG]   部位64: SHORT @22374.0 狀態:FILLED
🔍 策略收到: price=22372.0, api_time=12:27:00, sys_time=12:27:14, diff=14s, count=500
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍部位
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍部位
🔍 策略收到: price=22378.0, api_time=12:27:28, sys_time=12:27:26, diff=-2s, count=550
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍部位
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍部位
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍部位
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍部位
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍部位
[OPTIMIZED_RISK] 🔄 備份同步完成: 3 個活躍




-----
[ORDER_TRACKER] 📝 註冊實際訂單: dbe20c0e LONG TM0000 1口 @22630
INFO:multi_group_position_manager.MultiGroupPositionManager:📝 已註冊訂單到追蹤器: dbe20c0e (API序號: 8120)
INFO:multi_group_position_manager.MultiGroupPositionManager:📤 [簡化追蹤] 下單成功，需要更新 已送出口數
INFO:multi_group_database:更新部位90訂單資訊: order_id=dbe20c0e, api_seq_no=('8120', 0)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 第2口下單成功: ID=90, 訂單=dbe20c0e
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ 組 5 進場完成: 2/2口成功
[TOTAL_TRACKER] 📤 strategy_5_1752132298送出: 2口, 總計: 2/2
[SIMPLIFIED_TRACKER] 📤 組5送出: 2口, 總計: 2/2
✅ [MULTI_GROUP] 組別 5 進場成功
ERROR:multi_group_database:資料庫操作錯誤: 'sqlite3.Row' object has no attribute 'get'
[OPTIMIZED_RISK] ⚠️ 新部位事件觸發失敗: 'sqlite3.Row' object has no attribute 'get'
[OPTIMIZED_RISK] 💡 將使用原始風險管理系統
[REPLY_FILTER] ✅ 手動啟用回報處理 - 開始接受新的訂單回報
🎯 [MULTI_GROUP] 進場完成: 1/1 組成功
🎯 [STRATEGY] ℹ️ [15:25:00] 多組進場執行: 1/1 組成功
[PERFORMANCE] ⚠️ 報價處理延遲: 4194.9ms @22630.0
📋 [REPLY] OnNewData: ['2315545416490', 'TF', 'N', 'N', 'F020000', '6363839', 'BNF20', 'TW', 'TM2507', '', 'g3458', '22630.0000', '', '', '', '', '', '', '', '', '1', '', '', '20250710', '15:25:03', '', '0000000', '7174', 'y', '20250711', '2110000998635', 'A', 'FITM', '202507', '', '', '', '', '', '', 'B', '20250710', '', '', '', 'N', '', '2315545416490']
✅ [REPLY] 委託回報解析:
   📋 序號: 2315545416490 (原始: 2315545416490)
   📊 類型: N (新單 (New))
   🏷️ 商品: TM2507
   💰 價格: 22630.0000
   📦 數量: 1
   ⏰ 時間: 20250710 15:25:03
   🔄 買賣別: BNF20
   📅 合約月份: 202507
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22630.0, Qty=1, BuySell=BNF20
[TOTAL_MANAGER] 🔍 FIFO處理回報: Type=N, Product=TM2507, Price=22630.0, Qty=1
✅ [REPLY] 總量追蹤管理器處理成功
📋 [REPLY] OnNewData: ['', 'TF', 'D', 'N', 'F020000', '6363839', 'BNF20', 'TW', 'TM2507', '', 'g3458', '22630.000000', '', '', '', '', '', '', '', '', '1', '', '', '20250710', '15:25:03', '', '0000000', '7174', 'y', '20250711', '2120000093737', 'A', 'FITM', '202507', '', '', '', '', '0000000858', '', 'B', '20250710', '', '', '', 'N', '', '2315545416490']
✅ [REPLY] 委託回報解析:
   📋 序號:  (原始: 2315545416490)
   📊 類型: D (成交 (Deal/Done))
   🏷️ 商品: TM2507
   💰 價格: 22630.000000
   📦 數量: 1
   ⏰ 時間: 20250710 15:25:03
   🔄 買賣別: BNF20
   📅 合約月份: 202507
   🎯 成交序號: 0000000858
[SIMPLIFIED_TRACKER] 🔍 FIFO處理回報: Type=D, Product=TM2507, Price=22630.0, Qty=1, BuySell=BNF20
[SIMPLIFIED_TRACKER] 🔍 分析BuySell欄位: 'BNF20'
[SIMPLIFIED_TRACKER]   第2個子碼: 'N' -> 非平倉
[SIMPLIFIED_TRACKER] 🏗️ 識別為新倉成交，BuySell=BNF20
[SIMPLIFIED_TRACKER] ✅ 策略組5成交: 1口 @22630, 總計: 1/2
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組5成交統計更新: 1 口 @22630.0, 總進度: 1/2
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組5(DB_ID:33) 找到 1 個PENDING部位
[ASYNC_DB] 📝 排程部位89成交更新 @22630.0 (耗時:2.9ms)
[ASYNC_DB] 📝 排程風險狀態89創建 峰值:22630.0 (耗時:0.0ms)
INFO:multi_group_position_manager.MultiGroupPositionManager:🚀 [異步更新] 部位89成交確認 @22630.0 (耗時:319.9ms)
INFO:multi_group_database:✅ 確認部位89成交: @22630.0
[ASYNC_DB] ✅ 完成position_fill更新 部位:89 延遲:2.9ms 處理:457.1ms
INFO:multi_group_position_manager.MultiGroupPositionManager:🎉 [簡化追蹤] 組5 成功確認 1 個部位成交 (總耗時:640.0ms)
INFO:multi_group_position_manager.MultiGroupPositionManager:✅ [簡化追蹤] 組5成交: 1口 @22630.0, 進度: 1/2
INFO:multi_group_position_manager.MultiGroupPositionManager:📊 [簡化追蹤] 組5成交統計更新: 1 口 @22630.0, 總進度: 1/2
INFO:multi_group_database:創建風險管理狀態: 部位=89, 峰值=22630.0
[ASYNC_DB] ✅ 完成risk_state更新 部位:89 延遲:603.9ms 處理:265.2ms
INFO:multi_group_position_manager.MultiGroupPositionManager:🔍 [簡化追蹤] 組5(DB_ID:33) 找到 1 個PENDING部位
[ASYNC_DB] 📝 排程部位90成交更新 @22630.0 (耗時:297.6ms)
INFO:multi_group_database:✅ 確認部位90成交: @22630.0
[ASYNC_DB] ✅ 完成position_fill更新 部位:90 延遲:283.6ms 處理:28.1ms
[ASYNC_DB] 📝 排程風險狀態90創建 峰值:22630.0 (耗時:0.0ms)