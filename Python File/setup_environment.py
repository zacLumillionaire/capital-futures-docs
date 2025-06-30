#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
群益證券API完整環境設置工具
根據官方文件進行環境配置
"""

import os
import sys
import subprocess
import platform
import ctypes
from pathlib import Path

def is_admin():
    """檢查是否有管理員權限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """以管理員權限重新執行"""
    if is_admin():
        return True
    else:
        print("⚠️ 需要管理員權限來註冊COM元件")
        print("正在嘗試以管理員權限重新執行...")
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            return False
        except:
            print("❌ 無法取得管理員權限")
            return False

def check_python_environment():
    """檢查Python環境"""
    print("=== Python環境檢查 ===")
    print(f"Python版本: {sys.version}")
    print(f"平台: {platform.platform()}")
    print(f"架構: {platform.architecture()[0]}")
    
    # 檢查是否為64位元Python
    is_64bit = sys.maxsize > 2**32
    print(f"Python架構: {'64-bit' if is_64bit else '32-bit'}")
    
    if not is_64bit:
        print("⚠️ 警告: 建議使用64位元Python以獲得最佳相容性")
    
    print()

def check_required_packages():
    """檢查必要套件"""
    print("=== 套件檢查與安裝 ===")
    required_packages = {
        'comtypes': '1.2.0',
        'pywin32': '306',
        'pywin32-ctypes': '0.2.2'
    }
    
    missing_packages = []
    
    for package, version in required_packages.items():
        try:
            __import__(package)
            print(f"✅ {package}: 已安裝")
        except ImportError:
            print(f"❌ {package}: 未安裝")
            missing_packages.append(f"{package}=={version}")
    
    if missing_packages:
        print(f"\n🔧 正在安裝缺少的套件: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages)
            print("✅ 套件安裝完成")
        except subprocess.CalledProcessError as e:
            print(f"❌ 套件安裝失敗: {e}")
            return False
    
    print()
    return True

def find_skcom_dll():
    """尋找SKCOM.dll檔案"""
    print("=== SKCOM.dll檔案檢查 ===")
    
    search_paths = [
        Path(".") / "SKCOM.dll",  # 當前目錄
        Path("C:/SKCOM/SKCOM.dll"),
        Path("C:/Program Files (x86)/Capital/API/SKCOM.dll"),
        Path("C:/Program Files/Capital/API/SKCOM.dll")
    ]
    
    for path in search_paths:
        if path.exists():
            print(f"✅ 找到SKCOM.dll: {path.absolute()}")
            return str(path.absolute())
        else:
            print(f"❌ 未找到: {path}")
    
    print("\n⚠️ 找不到SKCOM.dll檔案")
    print("請確認:")
    print("1. 已下載群益證券API")
    print("2. 將SKCOM.dll複製到當前目錄")
    print("3. 或安裝到標準路徑")
    return None

def register_com_component(dll_path):
    """註冊COM元件"""
    print("=== COM元件註冊 ===")
    
    if not is_admin():
        print("❌ 需要管理員權限來註冊COM元件")
        return False
    
    try:
        print(f"🔄 正在註冊: {dll_path}")
        result = subprocess.run([
            "regsvr32", "/s", dll_path
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ COM元件註冊成功")
            return True
        else:
            print(f"❌ COM元件註冊失敗: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ 註冊過程發生錯誤: {e}")
        return False

def test_comtypes_integration():
    """測試comtypes整合"""
    print("=== comtypes整合測試 ===")
    
    try:
        import comtypes.client
        print("✅ comtypes.client 導入成功")
        
        # 清理舊的生成檔案
        gen_dir = comtypes.client.gen_dir
        print(f"📁 comtypes生成目錄: {gen_dir}")
        
        # 嘗試生成SKCOM包裝
        dll_path = find_skcom_dll()
        if dll_path:
            print(f"🔄 正在生成SKCOM包裝...")
            comtypes.client.GetModule(dll_path)
            
            # 測試導入
            import comtypes.gen.SKCOMLib as sk
            print("✅ SKCOMLib 生成並導入成功")
            print(f"📦 模組位置: {sk.__file__}")
            return True
        else:
            print("❌ 無法找到SKCOM.dll進行測試")
            return False
            
    except Exception as e:
        print(f"❌ comtypes整合測試失敗: {e}")
        return False

def main():
    """主函式"""
    print("🚀 群益證券API環境設置工具")
    print("根據官方文件進行完整環境配置")
    print("=" * 50)
    
    # 檢查管理員權限
    if not run_as_admin():
        return
    
    # 步驟1: 檢查Python環境
    check_python_environment()
    
    # 步驟2: 檢查並安裝必要套件
    if not check_required_packages():
        print("❌ 套件安裝失敗，無法繼續")
        return
    
    # 步驟3: 尋找SKCOM.dll
    dll_path = find_skcom_dll()
    if not dll_path:
        print("❌ 找不到SKCOM.dll，請先下載並放置檔案")
        return
    
    # 步驟4: 註冊COM元件
    if not register_com_component(dll_path):
        print("❌ COM元件註冊失敗")
        return
    
    # 步驟5: 測試comtypes整合
    if test_comtypes_integration():
        print("\n🎉 環境設置完成！")
        print("現在可以使用群益證券API進行開發")
    else:
        print("\n⚠️ 環境設置部分完成，但comtypes整合有問題")
    
    print("\n" + "=" * 50)
    print("🔧 後續步驟:")
    print("1. 執行 python SKCOMTester.py 測試API")
    print("2. 參考官方文件進行API開發")
    print("3. 如有問題，請檢查SKCOM_Setup_Guide.md")

if __name__ == "__main__":
    main()
    input("\n按Enter鍵結束...")
