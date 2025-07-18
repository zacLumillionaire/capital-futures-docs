#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡單驗證純FIFO模式實現
"""

def verify_fifo_implementation():
    """驗證FIFO實現"""
    print("🔍 驗證純FIFO模式實現...")
    
    try:
        # 檢查文件是否存在
        import os
        fifo_file = "fifo_order_matcher.py"
        if not os.path.exists(fifo_file):
            print(f"❌ 文件不存在: {fifo_file}")
            return False
        
        # 讀取文件內容
        with open(fifo_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵功能
        checks = [
            ("pure_fifo_mode", "純FIFO模式開關"),
            ("_find_pure_fifo_match", "純FIFO匹配方法"),
            ("_find_price_match", "價格匹配方法"),
            ("set_pure_fifo_mode", "模式切換方法"),
            ("pure_fifo_matched", "純FIFO統計"),
            ("price_matched", "價格匹配統計")
        ]
        
        print(f"\n📋 功能檢查:")
        all_passed = True
        
        for keyword, description in checks:
            if keyword in content:
                print(f"  ✅ {description}: 已實現")
            else:
                print(f"  ❌ {description}: 未找到")
                all_passed = False
        
        # 檢查預設設定
        if "self.pure_fifo_mode = True" in content:
            print(f"  ✅ 預設開啟純FIFO模式: 正確")
        else:
            print(f"  ⚠️ 預設設定: 需要確認")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        return False

def check_integration_points():
    """檢查整合點"""
    print(f"\n🔗 檢查整合點...")
    
    integration_files = [
        "simple_integrated.py",
        "unified_order_tracker.py"
    ]
    
    for filename in integration_files:
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if "fifo_matcher" in content.lower():
                    print(f"  ✅ {filename}: 已整合FIFO匹配器")
                else:
                    print(f"  ⚠️ {filename}: 可能需要整合")
            else:
                print(f"  ❌ {filename}: 文件不存在")
                
        except Exception as e:
            print(f"  ❌ {filename}: 檢查失敗 - {e}")

def main():
    """主函數"""
    print("=" * 50)
    print("🚀 純FIFO模式實現驗證")
    print("=" * 50)
    
    # 驗證實現
    implementation_ok = verify_fifo_implementation()
    
    # 檢查整合
    check_integration_points()
    
    # 總結
    print("=" * 50)
    if implementation_ok:
        print("🎉 純FIFO模式實現驗證通過！")
        print("\n📋 使用說明:")
        print("1. 預設已開啟純FIFO模式（不比對價格）")
        print("2. 可使用 matcher.set_pure_fifo_mode(False) 切換到價格匹配模式")
        print("3. 可使用 matcher.print_statistics() 查看匹配統計")
        print("4. 純FIFO模式會記錄價格差異供分析")
    else:
        print("⚠️ 實現可能有問題，請檢查代碼")
    
    print("=" * 50)

if __name__ == "__main__":
    import os
    os.chdir("Capital_Official_Framework")
    main()
