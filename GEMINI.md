1. 總體概述 (High-Level Overview)
此 Python 程式碼是目標是產出台指期交易策略，可回測，也可透過串接期貨商API進行下單。


2. 編碼風格與慣例 (Coding Style & Conventions)
模組化與函式職責單一化 (Modularity & Single Responsibility)

高度模組化: 程式碼拆分成各功能性函式，每個函式只負責一件具體的事務。

main 函式作為整合者: main() 函式的角色是流程的「指揮官」，它不處理具體的業務邏輯，而是按照順序調用其他模組化函式，將它們串聯成一個完整的工作流。這是該專案架構的核心優點。

日誌與偵錯 (Logging & Debugging)

使用中文進行日誌記錄: 這是本專案最顯著的風格。所有的進度提示、成功/失敗訊息都使用繁體中文的 print() 語句輸出。這使得非開發者或中文母語者也能輕易理解程式當前的運行狀態。

使用表情符號 (Emoji) 標示狀態: 大量使用 ✅、❌、⚠️ 等表情符號來快速傳達操作的成功、失敗或警告狀態，讓日誌更具可讀性。

範例：print(f"✅ 回測完成")

範例：print(f"❌ 調用 API 生成 時發生異常: {e}")

錯誤處理與健壯性 (Error Handling & Robustness)

廣泛使用 try...except: 幾乎所有涉及 I/O（網路請求、資料庫操作）的函式都被 try...except 區塊包裹，能有效捕捉並處理預期中的錯誤。

API 呼叫重試機制: 大量使用 tenacity 套件的 @retry 裝飾器，當 API 呼叫失敗（如超時、網路波動）時，會自動進行多次重試，極大提升了系統的穩定性。

範例：@retry(stop=stop_after_attempt(3), wait=wait_fixed(2), before=before_retry)



資料庫互動

連線池 (psycopg2.pool): 使用資料庫連線池來管理與 PostgreSQL 的連線，避免了頻繁建立和關閉連線的開銷，提升了效能。

上下文管理器 (with get_conn_cur_from_pool()): 自定義了一個上下文管理器來處理連線的獲取與釋放，確保連線在使用完畢後能被正確地歸還到池中，語法簡潔且不易出錯。