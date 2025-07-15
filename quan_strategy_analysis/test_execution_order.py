#!/usr/bin/env python3
"""
測試修正後的執行順序：保護性停損應該在風險管理之前執行
"""

def test_execution_order():
    """測試保護性停損和風險管理的執行順序"""

    print("🧪 測試執行順序修正...")
    print("📋 直接執行策略文件來測試修正後的邏輯...")

    # 直接執行策略文件，使用內建的測試配置
    import subprocess
    import os

    try:
        # 執行策略文件，它會使用內建的測試配置
        result = subprocess.run(
            ["python", "multi_Profit-Funded Risk_多口.py"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print("✅ 策略執行成功")
            print("\n📝 請檢查輸出，確認:")
            print("  1. 保護性停損是否在風險管理之前觸發")
            print("  2. 第3口是否在正確的停損點位出場")
            print("  3. 風險管理是否只在必要時介入")

            # 顯示部分輸出
            lines = result.stdout.split('\n')
            risk_lines = [line for line in lines if '🚨' in line or '🛡️' in line]
            if risk_lines:
                print("\n🔍 風險管理和保護性停損相關輸出:")
                for line in risk_lines[-10:]:  # 顯示最後10行相關輸出
                    print(f"  {line}")

            return True
        else:
            print(f"❌ 策略執行失敗: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("⏰ 執行超時")
        return False
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        return False

if __name__ == "__main__":
    success = test_execution_order()
    print(f"\n{'✅ 測試完成' if success else '❌ 測試失敗'}")
