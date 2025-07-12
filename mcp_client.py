# mcp_client.py (最終 Tool-Calling API 修正版)
import requests
import json

class MCPClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        try:
            requests.get(f"{self.base_url}/healthcheck", timeout=2)
            print("✅ MCP Client initialized. Successfully connected to Graphiti Server.")
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to Graphiti Server at {self.base_url}.")
            print("Please ensure the MCP server is running in a separate terminal.")

    def _send_request(self, tool_name, params):
        # --- 關鍵修正：所有工具都呼叫同一個 /invoke_tool 端點 ---
        url = f"{self.base_url}/invoke_tool"
        
        # --- 關鍵修正：將 tool_name 和 params 一起打包成要發送的資料 ---
        payload = {
            "name": tool_name,
            "parameters": params
        }
        
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_details = {"error": str(e)}
            if 'response' in locals() and hasattr(response, 'text'):
                error_details['response_body'] = response.text
            return error_details

    def search_facts(self, query: str):
        """搜尋相關事實"""
        print(f"Searching facts for: '{query}'")
        return self._send_request("search_facts", {"query": query})

    def add_memory(self, content: str):
        """新增一條記憶"""
        print(f"Adding memory: '{content[:50]}...'")
        return self._send_request("add_memory", {"content": content})

# --- 用於直接執行此檔案來測試 (不變) ---
if __name__ == "__main__":
    client = MCPClient()
    if client:
        search_query = "Final_Working_Strategy"
        results = client.search_facts(search_query)
        
        print("\n--- Search Results ---")
        print(json.dumps(results, indent=2, ensure_ascii=False))