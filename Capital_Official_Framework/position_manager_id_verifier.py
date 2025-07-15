#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Position Manager ID Verifier (專門針對 multi_group_position_manager.py 的ID一致性檢測器)

此腳本專門分析 multi_group_position_manager.py 檔案中的ID一致性問題。
"""

import os
import sys
import ast
import time
from typing import List, Dict, Any, Optional

class PositionManagerIDVerifier(ast.NodeVisitor):
    """專門針對 PositionManager 的ID一致性檢測器"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.issues = []
        self.current_function = None
        self.current_class = None

        # 模糊ID名稱
        self.ambiguous_id_names = [
            "group_id", "id", "position_id", "pos_id", "group", "position"
        ]

        # 建議的ID名稱
        self.preferred_id_names = [
            "group_pk", "logical_group_id", "position_pk", "position_logical_id"
        ]

    def add_issue(self, line_number: int, issue_type: str, message: str):
        """添加問題到列表"""
        self.issues.append({
            "file_path": self.file_path,
            "line_number": line_number,
            "issue_type": issue_type,
            "message": message,
            "function": self.current_function,
            "class": self.current_class
        })

    def visit_FunctionDef(self, node):
        """訪問函數定義"""
        old_function = self.current_function
        self.current_function = node.name

        # 檢查函數參數
        for arg in node.args.args:
            if arg.arg in self.ambiguous_id_names:
                self.add_issue(
                    node.lineno,
                    "函式簽名模糊",
                    f"函式 '{node.name}' 使用了模糊參數 '{arg.arg}'。建議使用更明確的名稱，如 {', '.join(self.preferred_id_names)}"
                )

        self.generic_visit(node)
        self.current_function = old_function

    def visit_ClassDef(self, node):
        """訪問類定義"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Name(self, node):
        """訪問變數名稱"""
        if node.id in self.ambiguous_id_names:
            self.add_issue(
                node.lineno,
                "模糊變數",
                f"發現潛在的模糊變數 '{node.id}'。建議使用更明確的名稱，如 {', '.join(self.preferred_id_names)}"
            )
        self.generic_visit(node)

    def visit_Subscript(self, node):
        """訪問字典/列表下標"""
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            key = node.slice.value
            if key in self.ambiguous_id_names:
                self.add_issue(
                    node.lineno,
                    "模糊字典鍵",
                    f"字典鍵 '{key}' 使用了模糊名稱。建議使用更明確的名稱，如 {', '.join(self.preferred_id_names)}"
                )
        self.generic_visit(node)

    def visit_Constant(self, node):
        """訪問常量（包括SQL字符串）"""
        if isinstance(node.value, str):
            self._check_sql_string(node.value, node.lineno)
        self.generic_visit(node)

    def _check_sql_string(self, string_value: str, line_number: int):
        """檢查SQL字符串中的ID使用"""
        try:
            lower_string = string_value.lower()
            
            # 檢查是否為SQL語句
            sql_keywords = ['select', 'insert', 'update', 'delete', 'where', 'from']
            is_sql = any(keyword in lower_string for keyword in sql_keywords)
            
            if is_sql:
                # 檢查SELECT查詢是否使用AS別名
                if 'select' in lower_string:
                    if ('id' in lower_string or 'group_id' in lower_string or 'position_id' in lower_string) and ' as ' not in lower_string:
                        self.add_issue(
                            line_number,
                            "SQL查詢不規範",
                            f"SELECT查詢未對 'id', 'group_id', 或 'position_id' 使用 AS 進行重命名。建議使用 AS 明確指定列名"
                        )

                # 檢查WHERE子句
                if 'where' in lower_string:
                    if 'group_id =' in lower_string or 'position_id =' in lower_string:
                        self.add_issue(
                            line_number,
                            "SQL條件模糊",
                            f"WHERE子句使用了模糊的ID條件。建議使用更明確的欄位名稱"
                        )
        except Exception:
            pass

def analyze_position_manager_file(file_path: str) -> List[Dict]:
    """分析 multi_group_position_manager.py 檔案"""
    try:
        print(f"📖 讀取檔案: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"🔍 解析 AST...")
        tree = ast.parse(content, filename=file_path)

        print(f"⚙️  創建專用驗證器...")
        verifier = PositionManagerIDVerifier(file_path)

        print(f"🚀 開始分析...")
        verifier.visit(tree)

        print(f"✅ 分析完成，發現 {len(verifier.issues)} 個問題")
        return verifier.issues

    except Exception as e:
        print(f"❌ 分析錯誤: {str(e)}")
        return [{
            "file_path": file_path,
            "line_number": 0,
            "issue_type": "解析錯誤",
            "message": f"無法解析檔案: {str(e)}",
            "function": None,
            "class": None
        }]

def generate_position_manager_report(issues: List[Dict]) -> str:
    """生成 PositionManager 專屬報告"""
    report = "=== multi_group_position_manager.py ID一致性檢測報告 ===\n\n"
    
    if not issues:
        report += "🎉 恭喜！未發現任何ID一致性問題。\n"
        return report

    # 按問題類型分組
    issues_by_type = {}
    for issue in issues:
        issue_type = issue["issue_type"]
        if issue_type not in issues_by_type:
            issues_by_type[issue_type] = []
        issues_by_type[issue_type].append(issue)

    # 按優先級排序
    priority_order = ["函式簽名模糊", "模糊變數", "SQL查詢不規範", "模糊字典鍵", "SQL條件模糊"]
    
    for issue_type in priority_order:
        if issue_type in issues_by_type:
            type_issues = issues_by_type[issue_type]
            report += f"🔍 [{issue_type}] ({len(type_issues)} 個問題):\n"
            
            for issue in type_issues:
                location = f"L_{issue['line_number']}"
                if issue['function']:
                    location += f" (函式: {issue['function']})"
                if issue['class']:
                    location += f" (類: {issue['class']})"
                
                report += f"  - {location}: {issue['message']}\n"
            report += "\n"

    # 總結
    report += f"📊 總計發現 {len(issues)} 個潛在問題\n\n"

    # 建議
    report += "💡 修復建議:\n"
    report += "1. 優先處理函式簽名模糊問題，因為這會影響API設計\n"
    report += "2. 其次處理模糊變數，確保代碼可讀性\n"
    report += "3. 最後處理SQL查詢和字典鍵問題\n"
    report += "4. 建議使用: group_pk, logical_group_id, position_pk, position_logical_id\n\n"

    return report

def main():
    """主函數"""
    # 檢查檔案是否存在
    file_path = "multi_group_position_manager.py"
    if not os.path.exists(file_path):
        print(f"❌ 檔案不存在: {file_path}")
        return

    print("🎯 multi_group_position_manager.py ID一致性專項檢測")
    print("=" * 60)

    # 分析檔案
    issues = analyze_position_manager_file(file_path)

    # 生成報告
    report = generate_position_manager_report(issues)
    print(report)

    # 保存報告
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_filename = f"position_manager_id_report_{timestamp}_{len(issues)}_issues.txt"
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"📄 報告已保存至: {report_filename}")

if __name__ == "__main__":
    main()
