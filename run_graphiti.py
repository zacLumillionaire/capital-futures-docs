# run_graphiti.py (最終穩定版)

import asyncio
import json
from graphiti_core import Graphiti
from dotenv import load_dotenv
from datetime import datetime, timezone

# 載入 .env 檔案中的 OPENAI_API_KEY
load_dotenv() 

# --- 連線設定 ---
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "kkd5ys+UCC"

async def main():
    """主執行函式"""
    print("Initializing Graphiti...")
    graphiti = Graphiti(
        NEO4J_URI,
        NEO4J_USER,
        NEO4J_PASSWORD
    )
    print("✅ Graphiti initialized successfully.")

    try:
        print("Building indices and constraints...")
        await graphiti.build_indices_and_constraints()
        print("✅ Indices and constraints are set up.")

        strategy_name = "Final_Working_Strategy_V2"
        backtest_episode_content = {
            "strategy_name": strategy_name,
            "parameters": {"lookback_period": 25, "std_dev": 2.5},
            "results": {"sharpe_ratio": 2.1, "max_drawdown": -0.04}
        }
        
        print(f"Adding episode for strategy: {strategy_name}...")
        await graphiti.add_episode(
            name=f"Backtest run for {strategy_name}",
            episode_body=json.dumps(backtest_episode_content),
            source_description="Local backtest execution via graphiti-core",
            reference_time=datetime.now(timezone.utc)
        )
        print(f"✅ Episode added successfully!")

        # 搜尋我們剛剛加入的資料
        print("\nSearching for the new strategy...")
        results = await graphiti.search(f'What were the results for {strategy_name}?')
        
        print('\n--- Search Results ---')
        for result in results:
            print(f"Fact: {result.fact}")
            print('---')

    finally:
        await graphiti.close()
        print('\nConnection closed. Process finished successfully.')

if __name__ == '__main__':
    asyncio.run(main())