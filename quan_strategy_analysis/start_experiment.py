#!/usr/bin/env python3
"""
量化策略分析實驗環境啟動腳本
"""

import sys
import os

def check_environment():
    """檢查環境是否正確設置"""
    print("🔍 檢查實驗環境...")
    
    # 檢查必要文件
    required_files = [
        'batch_experiment_gui.py',
        'batch_backtest_engine.py', 
        'parameter_matrix_generator.py',
        'experiment_analyzer.py',
        'long_short_separation_analyzer.py',
        'multi_Profit-Funded Risk_多口.py',
        'sqlite_connection.py',
        'stock_data.sqlite'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ 缺少必要文件: {', '.join(missing_files)}")
        return False
    
    # 檢查目錄
    required_dirs = ['batch_result', 'charts', 'data']
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"📁 創建目錄: {dir_name}")
    
    print("✅ 環境檢查完成")
    return True

def test_imports():
    """測試關鍵模組導入"""
    print("🔍 測試模組導入...")
    
    try:
        import batch_experiment_gui
        print("✅ batch_experiment_gui 導入成功")
        
        import batch_backtest_engine
        print("✅ batch_backtest_engine 導入成功")
        
        import parameter_matrix_generator
        print("✅ parameter_matrix_generator 導入成功")
        
        import experiment_analyzer
        print("✅ experiment_analyzer 導入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模組導入失敗: {e}")
        return False

def start_gui():
    """啟動批次實驗GUI"""
    print("🚀 啟動批次實驗GUI...")
    print("📍 Web界面地址: http://localhost:5000")
    print("💡 使用 Ctrl+C 停止服務")
    
    try:
        import batch_experiment_gui
        # 這裡會啟動Flask應用
        batch_experiment_gui.app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n👋 實驗環境已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")

def main():
    """主函數"""
    print("🎯 量化策略分析實驗環境")
    print("=" * 50)
    
    # 檢查環境
    if not check_environment():
        print("❌ 環境檢查失敗，請檢查文件完整性")
        sys.exit(1)
    
    # 測試導入
    if not test_imports():
        print("❌ 模組導入失敗，請檢查依賴包")
        sys.exit(1)
    
    print("\n🎉 環境準備就緒！")
    print("\n選擇操作:")
    print("1. 啟動批次實驗GUI")
    print("2. 僅檢查環境")
    print("3. 退出")
    
    choice = input("\n請輸入選擇 (1-3): ").strip()
    
    if choice == '1':
        start_gui()
    elif choice == '2':
        print("✅ 環境檢查完成，一切正常！")
    elif choice == '3':
        print("👋 再見！")
    else:
        print("❌ 無效選擇")

if __name__ == "__main__":
    main()
