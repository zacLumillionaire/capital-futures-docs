#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
依賴分析器 - 分析 simple_integrated.py 和 virtual_simple_integrated.py 的所有依賴
生成完整的檔案清單用於程式碼審查資料夾
"""

import os
import ast
import sys
from pathlib import Path

class DependencyAnalyzer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.dependencies = set()
        self.analyzed_files = set()
        
    def analyze_file(self, file_path):
        """分析單個 Python 檔案的依賴"""
        if file_path in self.analyzed_files:
            return
            
        self.analyzed_files.add(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.process_import(alias.name, file_path)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        self.process_import(node.module, file_path)
                        
        except Exception as e:
            print(f"⚠️ 分析檔案失敗 {file_path}: {e}")
    
    def process_import(self, module_name, source_file):
        """處理導入的模組名稱"""
        # 跳過標準庫模組
        standard_modules = {
            'os', 'sys', 'time', 'sqlite3', 'tkinter', 'datetime', 'typing',
            'threading', 'queue', 'json', 'logging', 'pathlib', 'shutil',
            'comtypes', 'ast', 'inspect', 'traceback', 'collections'
        }
        
        if module_name.split('.')[0] in standard_modules:
            return
            
        # 查找對應的檔案
        possible_paths = [
            self.base_path / f"{module_name}.py",
            self.base_path / module_name / "__init__.py",
            self.base_path / "order_service" / f"{module_name}.py",
            self.base_path / "虛擬報價機" / f"{module_name}.py",
        ]
        
        for path in possible_paths:
            if path.exists():
                self.dependencies.add(str(path))
                # 遞歸分析依賴
                self.analyze_file(str(path))
                break
    
    def get_all_dependencies(self):
        """獲取所有依賴檔案"""
        return sorted(list(self.dependencies))

def find_diagnostic_tools():
    """找出所有診斷工具"""
    diagnostic_files = []
    
    # 在根目錄查找診斷工具
    root_patterns = [
        "*診斷*.py",
        "*verification*.py", 
        "*verifier*.py",
        "*check*.py",
        "cleanup_*.py",
        "全流程檢測工具.py"
    ]
    
    base_path = Path(".")
    for pattern in root_patterns:
        diagnostic_files.extend(base_path.glob(pattern))
    
    # 在 Capital_Official_Framework 目錄查找
    framework_path = base_path / "Capital_Official_Framework"
    if framework_path.exists():
        for pattern in root_patterns:
            diagnostic_files.extend(framework_path.glob(pattern))
    
    return [str(f) for f in diagnostic_files if f.is_file()]

def analyze_dependencies():
    """分析主程式依賴"""
    print("🔍 開始分析依賴關係...")
    
    base_path = Path("Capital_Official_Framework")
    analyzer = DependencyAnalyzer(base_path)
    
    # 分析主要檔案
    main_files = [
        base_path / "simple_integrated.py",
        base_path / "virtual_simple_integrated.py"
    ]
    
    for main_file in main_files:
        if main_file.exists():
            print(f"📋 分析 {main_file.name}...")
            analyzer.analyze_file(str(main_file))
        else:
            print(f"⚠️ 檔案不存在: {main_file}")
    
    # 獲取所有依賴
    dependencies = analyzer.get_all_dependencies()
    
    # 添加主檔案本身
    for main_file in main_files:
        if main_file.exists():
            dependencies.append(str(main_file))
    
    return dependencies

def generate_file_list():
    """生成完整的檔案清單"""
    print("🚀 生成檔案清單...")
    print("=" * 60)
    
    all_files = []
    
    # 1. 分析程式依賴
    print("📋 步驟1: 分析程式依賴")
    dependencies = analyze_dependencies()
    all_files.extend(dependencies)
    print(f"   找到 {len(dependencies)} 個依賴檔案")
    
    # 2. 添加虛擬報價機所有檔案
    print("📋 步驟2: 添加虛擬報價機檔案")
    virtual_quote_path = Path("Capital_Official_Framework/虛擬報價機")
    if virtual_quote_path.exists():
        virtual_files = []
        for file_path in virtual_quote_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                virtual_files.append(str(file_path))
        all_files.extend(virtual_files)
        print(f"   找到 {len(virtual_files)} 個虛擬報價機檔案")
    
    # 3. 添加診斷工具
    print("📋 步驟3: 添加診斷工具")
    diagnostic_files = find_diagnostic_tools()
    all_files.extend(diagnostic_files)
    print(f"   找到 {len(diagnostic_files)} 個診斷工具")
    
    # 4. 添加配置檔案
    print("📋 步驟4: 添加配置檔案")
    config_patterns = [
        "Capital_Official_Framework/user_config.py",
        "Capital_Official_Framework/*.db",
        "Capital_Official_Framework/*.json",
        "Capital_Official_Framework/order_service/user_config.py"
    ]
    
    config_files = []
    for pattern in config_patterns:
        config_files.extend(Path(".").glob(pattern))
    
    config_file_paths = [str(f) for f in config_files if f.is_file()]
    all_files.extend(config_file_paths)
    print(f"   找到 {len(config_file_paths)} 個配置檔案")
    
    # 去重並排序
    unique_files = sorted(list(set(all_files)))
    
    print(f"\n📊 總計: {len(unique_files)} 個檔案")
    print("=" * 60)
    
    return unique_files

if __name__ == "__main__":
    file_list = generate_file_list()
    
    # 輸出檔案清單
    print("\n📋 完整檔案清單:")
    print("-" * 60)
    for i, file_path in enumerate(file_list, 1):
        print(f"{i:3d}. {file_path}")
    
    # 保存到檔案
    output_file = "file_list_for_review.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        for file_path in file_list:
            f.write(f"{file_path}\n")
    
    print(f"\n✅ 檔案清單已保存到: {output_file}")
    print(f"📊 總計 {len(file_list)} 個檔案")
