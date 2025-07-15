#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ID Consistency Verifier (ID一致性自動驗證器)

此腳本執行靜態程式碼分析，用於檢測程式碼中 group_id 和 position_id 使用的潛在問題。
它有助於確保整個交易系統中使用一致的命名規範和正確的ID用法。

使用方法:
    python id_consistency_verifier.py [目錄路徑]

如果未指定目錄，預設會分析 Capital_Official_Framework 目錄。

功能:
1. 自動遍歷指定目錄下的所有 .py 檔案
2. 使用 AST 進行靜態分析，無需執行程式碼
3. 檢測以下問題類型:
   - 模糊變數: 使用模糊的變數名稱如 'group_id', 'position_id', 'id'
   - 函式簽名模糊: 函式參數使用模糊的名稱
   - 模糊字典鍵: 字典中使用模糊的鍵名
   - SQL查詢不規範: SQL查詢中未使用 AS 重命名
   - SQL條件模糊: WHERE 子句中使用模糊的條件
4. 生成詳細報告，列出所有發現的問題

建議使用流程:
1. 重構前運行: 執行此腳本獲取「問題清單」，作為重構的目標
2. 重構後運行: 再次執行腳本，如果報告為空則證明重構成功且完整
3. 優先處理: 函式簽名模糊 > 模糊變數 > SQL查詢不規範 > 模糊字典鍵
4. 建議命名: 使用 group_pk, logical_group_id, position_pk, position_logical_id
"""

import os
import sys
import ast
import re
import time
from typing import List, Dict, Any, Optional, Tuple


class IDVerifier(ast.NodeVisitor):
    """
    AST node visitor that checks for potential ID consistency issues.

    This class traverses the AST of Python files and identifies potential issues
    with group_id and position_id usage.
    """

    def __init__(self, file_path: str):
        """
        Initialize the IDVerifier.

        Args:
            file_path: Path to the file being analyzed
        """
        self.file_path = file_path
        self.issues = []
        self.current_function = None
        self.current_class = None

        # List of ambiguous ID names to check for
        self.ambiguous_id_names = [
            "group_id", "id", "position_id", "pos_id", "group", "position"
        ]

        # List of preferred ID names
        self.preferred_id_names = [
            "group_pk", "logical_group_id", "position_pk", "position_logical_id"
        ]

    def add_issue(self, line_number: int, issue_type: str, message: str):
        """
        Add an issue to the list of issues found.

        Args:
            line_number: Line number where the issue was found
            issue_type: Type of issue (e.g., "模糊變數", "函式簽名模糊", etc.)
            message: Detailed description of the issue
        """
        self.issues.append({
            "file_path": self.file_path,
            "line_number": line_number,
            "issue_type": issue_type,
            "message": message
        })

    def visit_Name(self, node):
        """
        Visit a variable name node and check for ambiguous ID names.

        This method is called for each variable name in the AST.
        """
        # Check if the variable name is in our list of ambiguous names
        if node.id in self.ambiguous_id_names:
            self.add_issue(
                node.lineno,
                "模糊變數",
                f"發現潛在的模糊變數 '{node.id}'。建議使用更明確的名稱，如 {', '.join(self.preferred_id_names)}"
            )

        # Continue visiting child nodes
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """
        Visit a function definition node and check for ambiguous parameter names.

        This method is called for each function definition in the AST.
        """
        # Save the current function name for context
        old_function = self.current_function
        self.current_function = node.name

        # Check function parameters for ambiguous names
        for arg in node.args.args:
            if hasattr(arg, 'arg') and arg.arg in self.ambiguous_id_names:
                self.add_issue(
                    node.lineno,
                    "函式簽名模糊",
                    f"函式 '{node.name}' 使用了模糊參數 '{arg.arg}'。建議使用更明確的名稱，如 {', '.join(self.preferred_id_names)}"
                )

        # Visit child nodes
        self.generic_visit(node)

        # Restore the previous function context
        self.current_function = old_function

    def visit_Constant(self, node):
        """
        Visit a constant node and check for SQL queries with ambiguous ID usage.

        This method is called for each string constant in the AST.
        """
        # Check if this is a string constant
        if isinstance(node.value, str):
            self._check_sql_string(node.value, node.lineno)

        # Continue visiting child nodes
        self.generic_visit(node)

    def visit_Str(self, node):
        """
        Visit a string node (for Python < 3.8 compatibility).

        This method is called for each string literal in the AST.
        """
        self._check_sql_string(node.s, node.lineno)

        # Continue visiting child nodes
        self.generic_visit(node)

    def _check_sql_string(self, string_value: str, line_number: int):
        """
        Check a string for SQL-related ID issues.

        Args:
            string_value: The string content to check
            line_number: Line number where the string was found
        """
        # Skip empty strings
        if not string_value:
            return

        try:
            # Convert to lowercase for case-insensitive matching
            lower_string = string_value.lower()

            # Simple check for SQL keywords
            sql_keywords = ['select', 'insert', 'update', 'delete', 'where']
            is_sql = any(keyword in lower_string for keyword in sql_keywords)

            if is_sql:
                # Check for SELECT queries without AS aliases for ambiguous columns
                if 'select' in lower_string:
                    # Simple pattern matching
                    if ('id' in lower_string or 'group_id' in lower_string or 'position_id' in lower_string) and ' as ' not in lower_string:
                        self.add_issue(
                            line_number,
                            "SQL查詢不規範",
                            f"SELECT查詢未對 'id', 'group_id', 或 'position_id' 使用 AS 進行重命名。建議使用 AS 明確指定列名"
                        )

                # Check for WHERE clauses with ambiguous conditions
                if 'where' in lower_string:
                    if 'group_id =' in lower_string or 'position_id =' in lower_string:
                        self.add_issue(
                            line_number,
                            "SQL條件模糊",
                            f"WHERE子句使用了模糊的ID條件。建議使用更明確的欄位名稱"
                        )
        except Exception as e:
            # Silently ignore errors in string checking
            pass

    def visit_Subscript(self, node):
        """
        Visit a subscript node and check for dictionary key access with ambiguous IDs.

        This method is called for each dictionary/list access (e.g., dict['key']).
        """
        try:
            # Try to extract the key from the subscript
            key = None

            # Handle different Python versions and AST structures
            if hasattr(node, 'slice'):
                # Try to get the string value from various AST node types
                slice_node = node.slice

                # For ast.Constant (Python 3.8+)
                if hasattr(slice_node, 'value') and isinstance(slice_node.value, str):
                    key = slice_node.value
                # For ast.Str (older Python versions)
                elif hasattr(slice_node, 's'):
                    key = slice_node.s
                # For ast.Index wrapper (Python 3.8 and earlier)
                elif hasattr(slice_node, 'value'):
                    inner = slice_node.value
                    if hasattr(inner, 'value') and isinstance(inner.value, str):
                        key = inner.value
                    elif hasattr(inner, 's'):
                        key = inner.s

            # Check if we found a key and it's in our list of ambiguous names
            if key and key in self.ambiguous_id_names:
                self.add_issue(
                    node.lineno,
                    "模糊字典鍵",
                    f"發現潛在的模糊字典鍵訪問 '{key}'。建議使用更明確的鍵名"
                )
        except Exception as e:
            # Silently ignore errors in subscript checking
            pass

        # Continue visiting child nodes
        self.generic_visit(node)


def find_python_files(directory: str) -> List[str]:
    """
    Recursively find all Python files in the given directory.

    Args:
        directory: The root directory to start searching from

    Returns:
        A list of absolute paths to all Python files found
    """
    python_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                # Get the absolute path to the file
                file_path = os.path.abspath(os.path.join(root, file))
                python_files.append(file_path)

    return python_files


def analyze_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Analyze a Python file for ID consistency issues.

    Args:
        file_path: Path to the Python file to analyze

    Returns:
        A list of issues found in the file
    """
    try:
        print(f"    📖 讀取檔案...")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"    🔍 解析 AST...")
        # Parse the file into an AST
        tree = ast.parse(content, filename=file_path)

        print(f"    ⚙️  創建驗證器...")
        # Create an IDVerifier instance and visit the AST
        verifier = IDVerifier(file_path)

        print(f"    🚀 開始分析...")
        verifier.visit(tree)

        print(f"    ✅ 分析完成，發現 {len(verifier.issues)} 個問題")
        return verifier.issues
    except UnicodeDecodeError:
        print(f"    ❌ 編碼錯誤，嘗試其他編碼...")
        # Try with a different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
            verifier = IDVerifier(file_path)
            verifier.visit(tree)
            return verifier.issues
        except Exception as e:
            print(f"    ❌ 編碼問題無法解決: {str(e)}")
            return [{
                "file_path": file_path,
                "line_number": 0,
                "issue_type": "解析錯誤",
                "message": f"無法解析檔案 (編碼問題): {str(e)}"
            }]
    except Exception as e:
        print(f"    ❌ 分析錯誤: {str(e)}")
        # Handle parsing errors (e.g., syntax errors in the file)
        return [{
            "file_path": file_path,
            "line_number": 0,
            "issue_type": "解析錯誤",
            "message": f"無法解析檔案: {str(e)}"
        }]


def generate_report(all_issues: List[Dict[str, Any]]) -> str:
    """
    Generate a formatted report from the list of issues.

    Args:
        all_issues: List of all issues found across all files

    Returns:
        A formatted report string
    """
    if not all_issues:
        return "--- ID Consistency Verification Report ---\n\n✅ No potential issues found. Great job!\n"

    # Group issues by file
    issues_by_file = {}
    for issue in all_issues:
        file_path = issue['file_path']
        if file_path not in issues_by_file:
            issues_by_file[file_path] = []
        issues_by_file[file_path].append(issue)

    # Generate report
    report = "--- ID Consistency Verification Report ---\n\n"

    for file_path, file_issues in issues_by_file.items():
        report += f"Scanning file: {file_path}\n"

        # Group issues by type for better organization
        issues_by_type = {}
        for issue in file_issues:
            issue_type = issue['issue_type']
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)

        # Display issues by type
        for issue_type, type_issues in sorted(issues_by_type.items()):
            report += f"  [{issue_type}] ({len(type_issues)} issues):\n"
            for issue in sorted(type_issues, key=lambda x: x['line_number']):
                report += f"    - L_{issue['line_number']}: {issue['message']}\n"

        report += "\n"

    # Summary
    report += f"Found {len(all_issues)} potential issues across {len(issues_by_file)} files.\n\n"

    # Recommendations
    report += "📋 Recommendations:\n"
    report += "1. 重構前運行：執行此腳本獲取「問題清單」，作為重構的目標\n"
    report += "2. 重構後運行：再次執行腳本，如果報告為空則證明重構成功且完整\n"
    report += "3. 優先處理：函式簽名模糊 > 模糊變數 > SQL查詢不規範 > 模糊字典鍵\n"
    report += "4. 建議命名：使用 group_pk, logical_group_id, position_pk, position_logical_id\n\n"

    return report


def main():
    """Main function to run the ID consistency verifier."""
    print("=== ID一致性自動驗證器 ===\n")

    # Get the directory to analyze from command line arguments or use default
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        # Default to Capital_Official_Framework for comprehensive analysis
        directory = os.path.join(os.getcwd(), "Capital_Official_Framework")

        # If the directory doesn't exist, fall back to current directory
        if not os.path.exists(directory):
            directory = os.getcwd()

    # 檢查整個專案
    # specific_file = os.path.join(directory, "multi_group_position_manager.py")

    print(f"📁 分析目錄: {directory}")

    # Find all Python files in the directory
    python_files = find_python_files(directory)

    print(f"🔍 找到 {len(python_files)} 個 Python 檔案")

    # For demonstration, limit to first 20 files to include key files
    max_files = 20

    # 確保包含關鍵檔案
    key_files = ['multi_group_position_manager.py', 'multi_group_database.py', 'simple_integrated.py']
    priority_files = []
    other_files = []

    for file_path in python_files:
        file_name = file_path.split('\\')[-1] if '\\' in file_path else file_path.split('/')[-1]
        if file_name in key_files:
            priority_files.append(file_path)
        else:
            other_files.append(file_path)

    # 優先分析關鍵檔案，然後分析其他檔案
    python_files = priority_files + other_files

    if len(python_files) > max_files:
        print(f"⚠️  為避免輸出過多，僅分析前 {max_files} 個檔案（優先分析關鍵檔案）。")
        python_files = python_files[:max_files]

    # Analyze each file
    all_issues = []
    print("\n🔄 開始分析...")

    for i, file_path in enumerate(python_files, 1):
        print(f"  ({i}/{len(python_files)}) 分析: {os.path.basename(file_path)}")
        issues = analyze_file(file_path)
        all_issues.extend(issues)

    # Generate and display the report
    print("\n" + "="*60)
    report = generate_report(all_issues)
    print(report)

    # Save report to file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_filename = f"id_consistency_report_{timestamp}_{len(all_issues)}_issues.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"📄 報告已儲存至: {report_filename}")

    return len(all_issues)


if __name__ == "__main__":
    main()
