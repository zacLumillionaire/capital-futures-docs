# /Users/z/big/my-capital-project/strategy_memory.py
# --- 最終 zep-python 1.x 版 ---

from typing import Dict, Any, List
# 導入 Zep 和 Document 的方式不同
from zep_python import Zep, Document

# Zep 伺服器連線設定 (不變)
ZEP_API_URL = "http://localhost:8000"
ZEP_API_KEY = "zep_local_secret" # 1.x 版需要這個 Key，但我們 legacy 伺服器可能不驗證

async def log_backtest_to_memory(session_id: str, documents: List[Document]):
    """將一次回測紀錄作為文件寫入 Zep (非同步版本)"""
    # 1.x 版的 API 是非同步的 (async)
    async with Zep(base_url=ZEP_API_URL, api_key=ZEP_API_KEY) as client:
        print("✅ Successfully connected to local Zep Server.")
        
        # 1.x 版新增文件到集合的 API
        collection = await client.document.get_collection(session_id)
        await collection.add_documents(documents)
        
        print(f"✅ Logged new documents to session: {session_id}")

# 獨立執行檔案來測試連線和操作
async def main():
    """主執行函式"""
    strategy_name = "MA_Crossover_v1_API"
    backtest_docs = [
        Document(
            content=f"--- Backtest Log ---\nStrategy: {strategy_name}.\nParameters: {{'fast_ma': 25, 'slow_ma': 55}}\nResult: Sharpe Ratio was 1.6, Max Drawdown was -0.09.",
            metadata={
                "strategy_name": strategy_name,
                "sharpe_ratio": 1.6,
                "max_drawdown": -0.09
            }
        )
    ]
    
    await log_backtest_to_memory(
        session_id=f"strategy_dev_{strategy_name}",
        documents=backtest_docs
    )

if __name__ == "__main__":
    import asyncio
    # 因為是 async 函式，需要用 asyncio.run 來執行
    asyncio.run(main())