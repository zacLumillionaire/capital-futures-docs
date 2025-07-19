#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基於Web的交易策略回測GUI面板
使用Flask創建簡單的Web界面，避免Tkinter版本問題
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for, send_file
import subprocess
import sys
import os
import json
import threading
import glob
import shutil
from datetime import datetime
from pathlib import Path

# 🚀 【Task 2 新增】直接導入核心回測引擎（處理特殊字符檔名）
import importlib.util
spec = importlib.util.spec_from_file_location(
    "rev_multi_module",
    "rev_multi_Profit-Funded Risk_多口.py"
)
rev_multi_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rev_multi_module)

# 導入所需的函數（重命名以避免與Flask路由衝突）
core_run_backtest = rev_multi_module.run_backtest

# 🚀 【重構】導入統一的配置工廠
from strategy_config_factory import create_config_from_gui_dict

# 🔍 調試：檢查函數簽名
import inspect
print(f"🔍 DEBUG: core_run_backtest 函數簽名: {inspect.signature(core_run_backtest)}")
print(f"🔍 DEBUG: core_run_backtest 函數: {core_run_backtest}")
print(f"🔍 DEBUG: 函數所在模組: {core_run_backtest.__module__}")

app = Flask(__name__)

# 全局變數存儲回測狀態
backtest_status = {
    'running': False,
    'completed': False,
    'error': None,
    'result': None,
    'report_ready': False,
    'report_file': None
}

# HTML模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔄台指期貨反轉策略回測系統</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .section {
            margin-bottom: 25px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #fafafa;
        }
        .section h3 {
            margin-top: 0;
            color: #555;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 5px;
        }
        .form-row {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .form-row label {
            min-width: 120px;
            margin-right: 10px;
            font-weight: bold;
        }
        .form-row input, .form-row select {
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-right: 15px;
        }
        .radio-group {
            display: flex;
            gap: 15px;
        }
        .radio-group input[type="radio"] {
            margin-right: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        table th, table td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: center;
        }
        table th {
            background-color: #4CAF50;
            color: white;
        }
        .button-group {
            text-align: center;
            margin-top: 30px;
        }
        .btn {
            padding: 12px 25px;
            margin: 0 10px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        .btn-primary {
            background-color: #4CAF50;
            color: white;
        }
        .btn-secondary {
            background-color: #2196F3;
            color: white;
        }
        .btn-info {
            background-color: #FF9800;
            color: white;
        }
        .btn:hover {
            opacity: 0.8;
        }
        .btn:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            font-weight: bold;
        }
        .status.ready {
            background-color: #e8f5e8;
            color: #2e7d32;
        }
        .status.running {
            background-color: #fff3e0;
            color: #f57c00;
        }
        .status.completed {
            background-color: #e8f5e8;
            color: #2e7d32;
        }
        .status.error {
            background-color: #ffebee;
            color: #c62828;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .checkbox-group input[type="checkbox"] {
            margin-right: 8px;
        }

        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid transparent;
            border-radius: 4px;
        }

        .alert-info {
            color: #31708f;
            background-color: #d9edf7;
            border-color: #bce8f1;
        }

        .help-text {
            background-color: #e3f2fd;
            border: 1px solid #bbdefb;
            border-radius: 4px;
            padding: 12px;
            margin-top: 10px;
            font-size: 14px;
            color: #1565c0;
            display: none;
        }

        .help-text strong {
            color: #0d47a1;
        }

        #fixed_stop_mode:checked + label {
            color: #1976d2;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔄台指期貨反轉策略回測系統</h1>
        <div class="alert alert-info">
            <strong>反轉策略說明：</strong> 本系統將原始策略的進場邏輯完全反轉 - 突破上軌改做空，跌破下軌改做多，用於將虧損策略轉換為獲利策略。
        </div>
        
        <form id="backtestForm">
            <!-- 基本設定 -->
            <div class="section">
                <h3>基本設定</h3>
                <div class="form-row">
                    <label>交易口數:</label>
                    <div class="radio-group">
                        <label><input type="radio" name="trade_lots" value="1"> 1口</label>
                        <label><input type="radio" name="trade_lots" value="2"> 2口</label>
                        <label><input type="radio" name="trade_lots" value="3" checked> 3口</label>
                    </div>
                </div>
                <div class="form-row">
                    <label>開始日期:</label>
                    <input type="date" name="start_date" value="2024-11-01" required>
                    <label>結束日期:</label>
                    <input type="date" name="end_date" value="2024-11-30" required>
                </div>
                <div class="form-row" style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; border: 1px solid #e9ecef;">
                    <label style="color: #007bff; font-weight: bold;">🕐 開盤區間時間:</label>
                    <input type="time" name="range_start_time" value="08:46" step="60" style="margin-right: 10px; padding: 8px; border: 2px solid #007bff; border-radius: 4px;">
                    <label style="margin: 0 10px; font-weight: bold;">至</label>
                    <input type="time" name="range_end_time" value="08:47" step="60" style="margin-right: 10px; padding: 8px; border: 2px solid #007bff; border-radius: 4px;">
                    <small style="color: #6c757d; margin-left: 10px; font-style: italic;">⚙️ 預設為標準開盤區間 08:46-08:47，可自定義如 11:30-11:32</small>
                </div>
            </div>

            <!-- 停損模式設定 -->
            <div class="section">
                <h3>停損模式設定</h3>
                <div class="checkbox-group">
                    <input type="checkbox" name="fixed_stop_mode" id="fixed_stop_mode" checked>
                    <label for="fixed_stop_mode">🎯 啟用固定停損模式</label>
                    <div class="help-text">
                        啟用後：觸發點數將作為固定停損點，回檔比例設為0%，停用保護性停損
                    </div>
                </div>
            </div>

            <!-- 移動停利設定 -->
            <div class="section">
                <h3 id="lot_settings_title">移動停利設定</h3>
                <table>
                    <thead>
                        <tr>
                            <th>口數</th>
                            <th id="trigger_header">觸發點數</th>
                            <th id="trailing_header">回檔比例(%)</th>
                            <th id="protection_header">保護係數</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>第1口</td>
                            <td><input type="number" name="lot1_trigger" value="14" step="0.1" required></td>
                            <td><input type="number" name="lot1_trailing" value="0" step="0.1" required></td>
                            <td>N/A</td>
                        </tr>
                        <tr>
                            <td>第2口</td>
                            <td><input type="number" name="lot2_trigger" value="40" step="0.1" required></td>
                            <td><input type="number" name="lot2_trailing" value="0" step="0.1" required></td>
                            <td><input type="number" name="lot2_protection" value="0" step="0.1" required></td>
                        </tr>
                        <tr>
                            <td>第3口</td>
                            <td><input type="number" name="lot3_trigger" value="41" step="0.1" required></td>
                            <td><input type="number" name="lot3_trailing" value="0" step="0.1" required></td>
                            <td><input type="number" name="lot3_protection" value="0" step="0.1" required></td>
                        </tr>
                    </tbody>
                </table>
                <div class="help-text" id="lot_settings_help">
                    <strong>固定停損模式說明：</strong><br>
                    • 觸發點數 = 固定停損點數（例如：14點表示進場價±14點停損）<br>
                    • 回檔比例 = 0%（停用移動停損）<br>
                    • 保護係數 = 0（停用保護性停損）<br>
                    • 每口獨立運作，互不影響
                </div>
            </div>

            <!-- 每口停利設定 -->
            <div class="section">
                <h3>🎯 每口停利設定</h3>
                <div class="checkbox-group">
                    <input type="checkbox" name="individual_take_profit_enabled" id="individual_take_profit_enabled">
                    <label for="individual_take_profit_enabled">啟用每口獨立停利點數</label>
                    <div class="help-text">
                        啟用後：每口可設定不同的停利點數，停用時使用全局停利策略（區間邊緣/中點）
                    </div>
                </div>
                <table id="individual_take_profit_table" style="display: none;">
                    <thead>
                        <tr>
                            <th>口數</th>
                            <th>停利點數</th>
                            <th>說明</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>第1口</td>
                            <td><input type="number" name="lot1_take_profit" value="60" step="0.1" min="1"></td>
                            <td>進場價格 + 停利點數</td>
                        </tr>
                        <tr>
                            <td>第2口</td>
                            <td><input type="number" name="lot2_take_profit" value="80" step="0.1" min="1"></td>
                            <td>進場價格 + 停利點數</td>
                        </tr>
                        <tr>
                            <td>第3口</td>
                            <td><input type="number" name="lot3_take_profit" value="100" step="0.1" min="1"></td>
                            <td>進場價格 + 停利點數</td>
                        </tr>
                    </tbody>
                </table>
                <div class="help-text" id="individual_take_profit_help" style="display: none;">
                    <strong>每口停利說明：</strong><br>
                    • 每口使用固定停利點數，不受區間邊緣影響<br>
                    • 多頭：進場價 + 停利點數 = 停利價<br>
                    • 空頭：進場價 - 停利點數 = 停利價<br>
                    • 適合驗證MDD實驗結果的精確配置
                </div>
            </div>

            <!-- 進場價格模式設定 -->
            <div class="section">
                <h3>🎯 進場價格模式設定</h3>
                <div class="form-row">
                    <label>進場價格模式:</label>
                    <div class="radio-group">
                        <label><input type="radio" name="entry_price_mode" value="range_boundary" checked> 區間邊緣進場</label>
                        <label><input type="radio" name="entry_price_mode" value="breakout_low"> 最低點+5點進場</label>
                    </div>
                </div>
                <div class="help-text">
                    <strong>進場模式說明：</strong><br>
                    • <strong>區間邊緣進場：</strong> 當K棒跌破區間低點時，使用區間下邊緣價格進場（保守，執行確定性高）<br>
                    • <strong>最低點+5點進場：</strong> 當K棒跌破區間低點時，使用該K棒的最低價+5點進場（避免極端價格，平衡執行風險）
                </div>
            </div>

            <!-- 🚀 【新增】交易方向設定 -->
            <div class="section">
                <h3>📈 交易方向設定</h3>
                <div class="form-row">
                    <label>交易方向:</label>
                    <div class="radio-group">
                        <label><input type="radio" name="trading_direction" value="BOTH" checked> 多空都做</label>
                        <label><input type="radio" name="trading_direction" value="LONG_ONLY"> 只做多</label>
                        <label><input type="radio" name="trading_direction" value="SHORT_ONLY"> 只做空</label>
                    </div>
                </div>
                <div class="help-text">
                    <strong>交易方向說明：</strong><br>
                    • <strong>多空都做：</strong> 當出現多頭或空頭訊號時都會進場（預設模式，完整策略）<br>
                    • <strong>只做多：</strong> 只在多頭訊號出現時進場，忽略空頭訊號（適合多頭市場分析）<br>
                    • <strong>只做空：</strong> 只在空頭訊號出現時進場，忽略多頭訊號（適合空頭市場分析）
                </div>
            </div>

            <!-- 濾網設定 -->
            <div class="section">
                <h3>濾網設定</h3>
                <div class="checkbox-group">
                    <input type="checkbox" name="range_filter_enabled" id="range_filter">
                    <label for="range_filter">區間大小濾網</label>
                    <label style="margin-left: 20px;">最大區間點數:</label>
                    <input type="number" name="max_range_points" value="50" step="0.1">
                </div>
                <div class="checkbox-group">
                    <input type="checkbox" name="risk_filter_enabled" id="risk_filter">
                    <label for="risk_filter">風險管理濾網</label>
                    <label style="margin-left: 20px;">每日虧損限制:</label>
                    <input type="number" name="daily_loss_limit" value="150" step="0.1">
                </div>
                <div class="form-row" style="margin-left: 140px;">
                    <label>每日獲利目標:</label>
                    <input type="number" name="profit_target" value="200" step="0.1">
                </div>

            </div>

            <!-- 控制按鈕 -->
            <div class="button-group">
                <button type="submit" class="btn btn-primary" id="runBtn">執行回測</button>
                <button type="button" class="btn btn-secondary" onclick="loadConfig()">載入配置</button>
                <button type="button" class="btn btn-secondary" onclick="saveConfig()">儲存配置</button>
                <button type="button" class="btn btn-info" onclick="viewReport()" id="reportBtn" disabled>查看報告</button>
                <button type="button" class="btn btn-success" onclick="window.open('/reports', '_blank')">📊 報告管理</button>
                <button type="button" class="btn btn-info" onclick="kellyAnalysis()" id="kellyBtn" disabled>凱利分析</button>
            </div>
        </form>

        <!-- 狀態顯示 -->
        <div id="status" class="status ready">就緒</div>
    </div>

    <script>
        // 表單提交處理
        document.getElementById('backtestForm').addEventListener('submit', function(e) {
            e.preventDefault();
            runBacktest();
        });

        // 固定停損模式切換處理
        document.getElementById('fixed_stop_mode').addEventListener('change', function(e) {
            const isFixedMode = e.target.checked;
            updateStopLossMode(isFixedMode);
        });

        // 每口停利設定切換處理
        document.getElementById('individual_take_profit_enabled').addEventListener('change', function(e) {
            const isEnabled = e.target.checked;
            updateIndividualTakeProfitMode(isEnabled);
        });

        // 更新停損模式界面
        function updateStopLossMode(isFixedMode) {
            const title = document.getElementById('lot_settings_title');
            const triggerHeader = document.getElementById('trigger_header');
            const trailingHeader = document.getElementById('trailing_header');
            const protectionHeader = document.getElementById('protection_header');
            const helpText = document.getElementById('lot_settings_help');

            if (isFixedMode) {
                // 固定停損模式
                title.textContent = '🎯 固定停損設定';
                triggerHeader.textContent = '固定停損點數';
                trailingHeader.textContent = '回檔比例(%)';
                protectionHeader.textContent = '保護係數';
                helpText.style.display = 'block';

                // 自動設置建議值
                document.querySelector('input[name="lot1_trailing"]').value = '0';
                document.querySelector('input[name="lot2_trailing"]').value = '0';
                document.querySelector('input[name="lot3_trailing"]').value = '0';
                document.querySelector('input[name="lot2_protection"]').value = '0';
                document.querySelector('input[name="lot3_protection"]').value = '0';
            } else {
                // 移動停損模式
                title.textContent = '移動停利設定';
                triggerHeader.textContent = '觸發點數';
                trailingHeader.textContent = '回檔比例(%)';
                protectionHeader.textContent = '保護係數';
                helpText.style.display = 'none';

                // 恢復預設值
                document.querySelector('input[name="lot1_trailing"]').value = '20';
                document.querySelector('input[name="lot2_trailing"]').value = '20';
                document.querySelector('input[name="lot3_trailing"]').value = '20';
                document.querySelector('input[name="lot2_protection"]').value = '2.0';
                document.querySelector('input[name="lot3_protection"]').value = '2.0';
            }
        }

        // 更新每口停利模式界面
        function updateIndividualTakeProfitMode(isEnabled) {
            const table = document.getElementById('individual_take_profit_table');
            const helpText = document.getElementById('individual_take_profit_help');

            if (isEnabled) {
                table.style.display = 'table';
                helpText.style.display = 'block';
            } else {
                table.style.display = 'none';
                helpText.style.display = 'none';
            }
        }

        // 頁面載入時初始化
        document.addEventListener('DOMContentLoaded', function() {
            const fixedModeCheckbox = document.getElementById('fixed_stop_mode');
            updateStopLossMode(fixedModeCheckbox.checked);

            const individualTakeProfitCheckbox = document.getElementById('individual_take_profit_enabled');
            updateIndividualTakeProfitMode(individualTakeProfitCheckbox.checked);
        });

        // 執行回測
        function runBacktest() {
            const formData = new FormData(document.getElementById('backtestForm'));
            const config = {};
            
            // 收集表單數據
            for (let [key, value] of formData.entries()) {
                if (key === 'trade_lots') {
                    config[key] = parseInt(value);
                } else if (key.includes('_enabled')) {
                    config[key] = true;
                } else if (key.includes('trigger') || key.includes('trailing') || key.includes('protection') || 
                          key.includes('points') || key.includes('limit') || key.includes('target')) {
                    config[key] = parseFloat(value);
                } else {
                    config[key] = value;
                }
            }
            
            // 處理未勾選的checkbox
            if (!config.range_filter_enabled) config.range_filter_enabled = false;
            if (!config.risk_filter_enabled) config.risk_filter_enabled = false;
            if (!config.fixed_stop_mode) config.fixed_stop_mode = true;  // 🚀 固定停損模式預設啟用
            if (!config.individual_take_profit_enabled) config.individual_take_profit_enabled = false;

            // 更新UI狀態
            document.getElementById('runBtn').disabled = true;
            document.getElementById('status').className = 'status running';
            document.getElementById('status').textContent = '正在執行回測...';

            // 發送請求
            fetch('/run_backtest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('status').className = 'status completed';
                    document.getElementById('status').textContent = '回測完成';
                    document.getElementById('reportBtn').disabled = false;
                    document.getElementById('kellyBtn').disabled = false;
                    alert('回測執行完成！');
                } else {
                    document.getElementById('status').className = 'status error';
                    document.getElementById('status').textContent = '執行失敗: ' + data.error;
                    alert('回測執行失敗: ' + data.error);
                }
            })
            .catch(error => {
                document.getElementById('status').className = 'status error';
                document.getElementById('status').textContent = '執行失敗';
                alert('發生錯誤: ' + error);
            })
            .finally(() => {
                document.getElementById('runBtn').disabled = false;
            });
        }

        // 查看報告
        function viewReport() {
            // 在新窗口中打開報告
            window.open('/view_report', '_blank');
        }

        // 凱利分析
        function kellyAnalysis() {
            // 在新窗口中打開凱利分析結果
            window.open('/kelly_analysis', '_blank');
        }

        // 載入配置
        function loadConfig() {
            alert('載入配置功能：請手動調整參數或使用儲存的配置文件');
        }

        // 儲存配置
        function saveConfig() {
            const formData = new FormData(document.getElementById('backtestForm'));
            const config = {};
            for (let [key, value] of formData.entries()) {
                config[key] = value;
            }
            
            const dataStr = JSON.stringify(config, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'backtest_config.json';
            link.click();
            URL.revokeObjectURL(url);
        }

        // 定期檢查回測狀態
        function checkStatus() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                if (data.running) {
                    document.getElementById('status').className = 'status running';
                    document.getElementById('status').textContent = '正在執行回測...';
                    document.getElementById('runBtn').disabled = true;
                } else if (data.completed) {
                    if (data.report_ready) {
                        document.getElementById('status').className = 'status completed';
                        document.getElementById('status').textContent = '回測完成 - 報告已準備';
                        document.getElementById('reportBtn').disabled = false;
                    } else {
                        document.getElementById('status').className = 'status running';
                        document.getElementById('status').textContent = '正在生成報告...';
                        document.getElementById('reportBtn').disabled = true;
                    }
                    document.getElementById('kellyBtn').disabled = false;
                    document.getElementById('runBtn').disabled = false;
                } else if (data.error) {
                    document.getElementById('status').className = 'status error';
                    document.getElementById('status').textContent = '執行失敗: ' + data.error;
                    document.getElementById('runBtn').disabled = false;
                } else {
                    document.getElementById('status').className = 'status ready';
                    document.getElementById('status').textContent = '就緒';
                    document.getElementById('runBtn').disabled = false;
                }
            });
        }

        // 每2秒檢查一次狀態
        setInterval(checkStatus, 2000);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    return jsonify(backtest_status)

@app.route('/view_report')
def view_report():
    """查看分析報告"""
    if backtest_status.get('report_ready') and backtest_status.get('report_file'):
        report_file = backtest_status['report_file']
        if os.path.exists(report_file):
            # 讀取HTML報告內容
            with open(report_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content
        else:
            return "報告文件不存在", 404
    else:
        return "報告尚未生成", 404

@app.route('/kelly_analysis')
def kelly_analysis():
    """執行凱利分析"""
    try:
        # 檢查是否有最近的回測結果
        if not backtest_status.get('completed') or not backtest_status.get('result'):
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>凱利公式分析結果</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                    .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; color: #856404; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📊 凱利公式分析結果</h1>
                    <div class="warning">
                        ⚠️ 請先執行回測，然後再查看凱利分析結果。
                    </div>
                </div>
            </body>
            </html>
            """, 200

        # 從最近的回測結果中提取交易數據
        result_obj = backtest_status['result']
        if isinstance(result_obj, dict) and 'stdout' in result_obj:
            # 新格式：result是包含stdout/stderr的字典
            full_output = result_obj['stdout'] + "\n" + (result_obj['stderr'] or "")
        elif hasattr(result_obj, 'stdout'):
            # 舊格式：result是subprocess.CompletedProcess對象
            full_output = result_obj.stdout + "\n" + (result_obj.stderr or "")
        else:
            # 最舊格式：result是字符串
            full_output = str(result_obj)

        # 解析回測結果中的統計數據
        lines = full_output.split('\n')
        total_trades = 0
        winning_trades = 0
        losing_trades = 0
        win_rate = 0.0
        total_pnl = 0.0

        for line in lines:
            original_line = line.strip()

            # 處理不同的日誌格式，更精確地提取內容
            clean_line = original_line
            if '] INFO [' in line:
                # 分割日誌格式: [時間] INFO [模組:行號] 內容
                parts = line.split('] ')
                if len(parts) >= 3:  # 確保有足夠的部分
                    clean_line = parts[2].strip()  # 取第三部分作為實際內容

            # 使用更精確的匹配模式
            if '總交易次數:' in clean_line:
                try:
                    value_str = clean_line.split('總交易次數:')[1].strip()
                    total_trades = int(value_str)
                except:
                    pass
            elif '獲利次數:' in clean_line:
                try:
                    value_str = clean_line.split('獲利次數:')[1].strip()
                    winning_trades = int(value_str)
                except:
                    pass
            elif '虧損次數:' in clean_line:
                try:
                    value_str = clean_line.split('虧損次數:')[1].strip()
                    losing_trades = int(value_str)
                except:
                    pass
            elif '勝率:' in clean_line:
                try:
                    value_str = clean_line.split('勝率:')[1].strip().replace('%', '')
                    win_rate = float(value_str)
                except:
                    pass
            elif '總損益(' in clean_line and '口):' in clean_line:
                try:
                    value_str = clean_line.split('):')[1].strip()
                    total_pnl = float(value_str)
                except:
                    pass

        # 計算凱利公式
        if total_trades > 0 and winning_trades > 0 and losing_trades > 0:
            win_rate_decimal = win_rate / 100.0
            lose_rate = 1 - win_rate_decimal

            # 估算平均獲利和虧損（簡化計算）
            avg_win = total_pnl / winning_trades if winning_trades > 0 else 0
            avg_loss = abs(total_pnl) / losing_trades if losing_trades > 0 and total_pnl < 0 else 50  # 預設值

            if avg_loss > 0:
                win_loss_ratio = avg_win / avg_loss
                kelly_fraction = win_rate_decimal - (lose_rate / win_loss_ratio)
            else:
                kelly_fraction = -0.1
                win_loss_ratio = 0
        else:
            avg_win = 0
            avg_loss = 0
            win_loss_ratio = 0
            kelly_fraction = -0.1

        # 生成凱利分析報告
        kelly_output = f"""📊 ======= 凱利公式資金管理分析報告 =======

📈 基本統計
  - 總交易次數：{total_trades}
  - 獲利次數：{winning_trades}
  - 虧損次數：{losing_trades}
  - 勝率：{win_rate:.2f}%

💰 損益分析
  - 平均獲利：{avg_win:.2f} 點
  - 平均虧損：{avg_loss:.2f} 點
  - 獲利虧損比：{win_loss_ratio:.2f}

🎯 凱利公式分析
  - 凱利係數：{kelly_fraction:.4f}
  - 建議資金比例：{kelly_fraction*100:.2f}%
  - 保守建議比例：{kelly_fraction*50:.2f}%

🔢 口數建議
  - 可用最大口數：5
  - 建議交易口數：{max(1, int(kelly_fraction * 5)) if kelly_fraction > 0 else 1}
  - 風險評估：{'低風險：建議交易' if kelly_fraction > 0.1 else '中風險：謹慎交易' if kelly_fraction > 0 else '高風險：凱利係數為負，不建議交易'}

📋 使用說明
  - 凱利公式提供理論最佳資金配置
  - 實際應用建議使用保守係數（凱利係數的50%）
  - 請結合個人風險承受能力調整
  - 建議定期重新計算以適應策略表現變化

⚠️ 風險提醒
  - 凱利公式假設未來表現與歷史一致
  - 市場環境變化可能影響策略效果
  - 建議搭配其他風險管理措施
==========================================
"""

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>凱利公式分析結果</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; }}
                h1 {{ color: #333; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 凱利公式分析結果</h1>
                <pre>{kelly_output}</pre>
            </div>
        </body>
        </html>
        """
        return html_content

    except Exception as e:
        return f"凱利分析執行錯誤: {str(e)}", 500

@app.route('/run_backtest', methods=['POST'])
def run_backtest():
    global backtest_status
    
    if backtest_status['running']:
        return jsonify({'success': False, 'error': '回測正在執行中'})
    
    try:
        config_data = request.json
        
        # 重置狀態
        backtest_status = {
            'running': True,
            'completed': False,
            'error': None,
            'result': None,
            'report_ready': False,
            'report_file': None
        }
        
        # 在背景線程執行回測
        thread = threading.Thread(target=execute_backtest_thread, args=(config_data,))
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': '回測已開始執行'})
        
    except Exception as e:
        backtest_status['running'] = False
        backtest_status['error'] = str(e)
        return jsonify({'success': False, 'error': str(e)})



def execute_backtest_thread(config_data):
    """在背景線程執行回測"""
    global backtest_status

    try:
        # 轉換配置格式
        gui_config = {
            "trade_lots": config_data.get("trade_lots", 3),
            "start_date": config_data.get("start_date", "2024-11-01"),
            "end_date": config_data.get("end_date", "2024-11-30"),
            "range_start_time": config_data.get("range_start_time", "08:46"),
            "range_end_time": config_data.get("range_end_time", "08:47"),
            "fixed_stop_mode": config_data.get("fixed_stop_mode", True),  # 🎯 固定停損模式預設啟用
            "individual_take_profit_enabled": config_data.get("individual_take_profit_enabled", False),  # 🎯 每口停利設定
            "entry_price_mode": config_data.get("entry_price_mode", "range_boundary"),  # 🎯 新增進場價格模式
            "trading_direction": config_data.get("trading_direction", "BOTH"),  # 🚀 【新增】交易方向設定
            "lot_settings": {
                "lot1": {
                    "trigger": config_data.get("lot1_trigger", 14),  # 🔧 修復：與HTML表單一致
                    "trailing": config_data.get("lot1_trailing", 20),
                    "take_profit": config_data.get("lot1_take_profit", 60)  # 🎯 每口停利點數
                },
                "lot2": {
                    "trigger": config_data.get("lot2_trigger", 40),
                    "trailing": config_data.get("lot2_trailing", 20),
                    "protection": config_data.get("lot2_protection", 2.0),
                    "take_profit": config_data.get("lot2_take_profit", 80)  # 🎯 每口停利點數
                },
                "lot3": {
                    "trigger": config_data.get("lot3_trigger", 41),  # 🔧 修復：與基準測試一致
                    "trailing": config_data.get("lot3_trailing", 20),
                    "protection": config_data.get("lot3_protection", 2.0),
                    "take_profit": config_data.get("lot3_take_profit", 100)  # 🎯 每口停利點數
                }
            },
            "filters": {
                "range_filter": {
                    "enabled": config_data.get("range_filter_enabled", False),
                    "max_range_points": config_data.get("max_range_points", 50)
                },
                "risk_filter": {
                    "enabled": config_data.get("risk_filter_enabled", False),
                    "daily_loss_limit": config_data.get("daily_loss_limit", 150),
                    "profit_target": config_data.get("profit_target", 200)
                },
                "stop_loss_filter": {
                    "enabled": False,  # 🚀 移除停利策略濾網，簡化配置
                    "stop_loss_type": "range_boundary",
                    "fixed_stop_loss_points": 15.0
                }
            }
        }

        # 🚀 【Task 2 重構】直接調用核心回測引擎，移除 subprocess
        print(f"🚀 直接調用回測引擎，配置: {gui_config}")

        # 🚀 【Task 4 修復】使用正確的配置工廠函數，確保GUI參數被正確處理
        print(f"🔍 DEBUG: 即將傳遞的 gui_config: {gui_config}")
        strategy_config = create_config_from_gui_dict(gui_config)
        print(f"🔍 DEBUG: 創建的 strategy_config: {repr(strategy_config)}")

        # 提取時間參數
        start_date = gui_config["start_date"]
        end_date = gui_config["end_date"]
        range_start_time = gui_config.get("range_start_time")
        range_end_time = gui_config.get("range_end_time")

        # 🚀 【新增】設置日誌捕獲器來收集詳細日誌
        import logging
        import io

        # 創建字符串緩衝區來捕獲日誌
        log_capture_string = io.StringIO()
        log_handler = logging.StreamHandler(log_capture_string)
        log_handler.setLevel(logging.INFO)

        # 設置日誌格式（與核心引擎一致）
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
                                    datefmt='%Y-%m-%dT%H:%M:%S%z')
        log_handler.setFormatter(formatter)

        # 獲取核心引擎的 logger 並添加我們的 handler
        core_logger = logging.getLogger('rev_multi_module')
        core_logger.addHandler(log_handler)
        core_logger.setLevel(logging.INFO)

        print(f"🔍 DEBUG: 調用前檢查 core_run_backtest 函數: {core_run_backtest}")
        print(f"🔍 DEBUG: 函數簽名: {inspect.signature(core_run_backtest)}")
        print(f"🔍 DEBUG: 參數值 - start_date: {start_date}, end_date: {end_date}")

        try:
            # 🚀 【Task 2 關鍵】直接調用 core_run_backtest 函數，啟用日誌捕獲
            backtest_results_dict = core_run_backtest(
                strategy_config,  # 第一個參數是位置參數
                start_date=start_date,
                end_date=end_date,
                range_start_time=range_start_time,
                range_end_time=range_end_time
            )

            # 獲取捕獲的日誌內容
            captured_logs = log_capture_string.getvalue()

        finally:
            # 清理：移除我們添加的 handler
            core_logger.removeHandler(log_handler)
            log_handler.close()

        print("=" * 60)
        print("📊 回測執行結果")
        print("=" * 60)
        print(f"✅ 回測完成，結果: {backtest_results_dict}")
        print("=" * 60)

        # 🚀 【Task 2 重構】直接使用回測結果，無需檢查 returncode
        if backtest_results_dict:
            backtest_status['running'] = False
            backtest_status['completed'] = True
            # 🚀 【Task 2 關鍵】直接儲存結構化的回測結果
            backtest_status['result'] = backtest_results_dict
            # 🚀 【新增】儲存捕獲的詳細日誌
            backtest_status['detailed_logs'] = captured_logs

            print("\n" + "=" * 100)
            print("🔍 【Task 2 重構】直接獲得的結構化數據")
            print("=" * 100)
            print(f"📊 回測結果字典: {backtest_results_dict}")
            print(f"📋 捕獲日誌長度: {len(captured_logs)} 字符")
            print("=" * 100)

            # 🚀 【Task 2 重構】直接生成HTML報告，移除 enhanced_report_generator
            try:
                print("📊 開始生成分析報告...")

                # 🚀 【Task 2 重構】直接使用結構化數據，移除所有日誌解析邏輯
                stats = {
                    'trading_days': backtest_results_dict.get('trade_days', 'N/A'),
                    'total_trades': backtest_results_dict.get('total_trades', 'N/A'),
                    'winning_trades': backtest_results_dict.get('winning_trades', 'N/A'),
                    'losing_trades': backtest_results_dict.get('losing_trades', 'N/A'),
                    'win_rate': f"{backtest_results_dict.get('win_rate', 0) * 100:.2f}%" if backtest_results_dict.get('win_rate') is not None else 'N/A',
                    'total_pnl': f"{backtest_results_dict.get('total_pnl', 0):.2f}",
                    'max_drawdown': f"{backtest_results_dict.get('max_drawdown', 0):.2f}",  # 🚀 【Task 2 新增】MDD
                    'long_trading_days': backtest_results_dict.get('long_trades', 'N/A'),
                    'long_pnl': f"{backtest_results_dict.get('long_pnl', 0):.2f}",
                    'long_win_rate': f"{backtest_results_dict.get('long_win_rate', 0) * 100:.2f}%" if backtest_results_dict.get('long_win_rate') is not None else 'N/A',
                    'short_trading_days': backtest_results_dict.get('short_trades', 'N/A'),
                    'short_pnl': f"{backtest_results_dict.get('short_pnl', 0):.2f}",
                    'short_win_rate': f"{backtest_results_dict.get('short_win_rate', 0) * 100:.2f}%" if backtest_results_dict.get('short_win_rate') is not None else 'N/A',
                    # 🚀 【新增】各口PnL統計
                    'lot1_pnl': f"{backtest_results_dict.get('lot1_pnl', 0):.2f}",
                    'lot2_pnl': f"{backtest_results_dict.get('lot2_pnl', 0):.2f}",
                    'lot3_pnl': f"{backtest_results_dict.get('lot3_pnl', 0):.2f}"
                }

                print(f"📊 使用結構化數據: {stats}")

                # 🚀 【新增】輔助函數：根據PnL數值決定CSS類別
                def get_pnl_class(pnl_str):
                    try:
                        pnl_value = float(pnl_str)
                        if pnl_value > 0:
                            return "positive"
                        elif pnl_value < 0:
                            return "negative"
                        else:
                            return ""
                    except (ValueError, TypeError):
                        return ""

                # 🚀 【新增】獲取詳細日誌並進行HTML轉義
                import html  # 🚀 【修復】將 html 導入移到使用之前
                detailed_logs = backtest_status.get('detailed_logs', '')
                escaped_logs = html.escape(detailed_logs) if detailed_logs else "無詳細日誌記錄"

                # 生成簡化的HTML報告
                from datetime import datetime
                report_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_filename = f"reports/backtest_report_{report_time}.html"

                os.makedirs("reports", exist_ok=True)

                # 🚀 【Task 2 重構】移除對 result.stdout/stderr 的引用

                # 生成簡單HTML報告
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>回測分析報告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #2e7d32; }}
        .stat-value.positive {{ color: #2e7d32; }}
        .stat-value.negative {{ color: #d32f2f; }}
        .stat-label {{ font-size: 14px; color: #666; margin-top: 5px; }}
        .log-section {{ margin-top: 30px; }}
        .log-content {{ background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 400px; overflow-y: auto; white-space: pre-wrap; font-family: monospace; font-size: 12px; }}
        .debug-section {{ margin-top: 20px; background: #fff3cd; padding: 15px; border-radius: 5px; }}

        /* 🚀 【新增】詳細日誌區塊樣式 */
        .log-container {{
            margin-top: 30px;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            background: #fafafa;
        }}
        .log-header {{
            background: #f0f0f0;
            padding: 12px 15px;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-weight: bold;
        }}
        #logToggleBtn {{
            background: #1976d2;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }}
        #logToggleBtn:hover {{
            background: #1565c0;
        }}

        h1, h2 {{ color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Profit-Funded Risk 多口交易策略回測報告</h1>
            <p>報告生成時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>

        <h2>📈 關鍵統計指標</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats.get('trading_days', 'N/A')}</div>
                <div class="stat-label">總交易天數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('total_trades', 'N/A')}</div>
                <div class="stat-label">總交易次數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('win_rate', 'N/A')}</div>
                <div class="stat-label">勝率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('total_pnl', 'N/A')}</div>
                <div class="stat-label">總損益 (TOTAL P&L)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value negative">{stats.get('max_drawdown', 'N/A')}</div>
                <div class="stat-label">最大回撤 (MAX DRAWDOWN)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('winning_trades', 'N/A')}</div>
                <div class="stat-label">獲利次數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('losing_trades', 'N/A')}</div>
                <div class="stat-label">虧損次數</div>
            </div>
        </div>

        <!-- 🚀 【新增】各口PnL分析 -->
        <h2>🎯 各口損益分析</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value {get_pnl_class(stats.get('lot1_pnl', '0.00'))}">{stats.get('lot1_pnl', 'N/A')}</div>
                <div class="stat-label">第一口累積損益</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {get_pnl_class(stats.get('lot2_pnl', '0.00'))}">{stats.get('lot2_pnl', 'N/A')}</div>
                <div class="stat-label">第二口累積損益</div>
            </div>
            <div class="stat-card">
                <div class="stat-value {get_pnl_class(stats.get('lot3_pnl', '0.00'))}">{stats.get('lot3_pnl', 'N/A')}</div>
                <div class="stat-label">第三口累積損益</div>
            </div>
        </div>
        <div class="help-text" style="margin-top: 10px;">
            <strong>各口損益說明：</strong><br>
            • <strong>第一口：</strong> 最先進場的部位，通常風險較低<br>
            • <strong>第二口：</strong> 第二個進場的部位，可能有保護性停損<br>
            • <strong>第三口：</strong> 最後進場的部位，通常風險較高<br>
            • 透過比較各口表現，可以判斷是否要使用三口策略還是兩口多組策略
        </div>

        <h2>📊 多空部位分析</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats.get('long_trading_days', 'N/A')}</div>
                <div class="stat-label">LONG 交易天數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('long_pnl', 'N/A')}</div>
                <div class="stat-label">LONG TOTAL P&L</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('short_trading_days', 'N/A')}</div>
                <div class="stat-label">SHORT 交易天數</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('short_pnl', 'N/A')}</div>
                <div class="stat-label">SHORT TOTAL P&L</div>
            </div>
        </div>

        <div class="debug-section">
            <h3>🔧 數據驗證資訊</h3>
            <p><strong>數據來源:</strong> 直接API調用 (無subprocess)</p>
            <hr>
            <h4>📊 交易統計驗證</h4>
            <p><strong>總交易次數:</strong> {stats.get('total_trades', 'N/A')}</p>
            <p><strong>多頭交易天數:</strong> {stats.get('long_trading_days', 'N/A')}</p>
            <p><strong>空頭交易天數:</strong> {stats.get('short_trading_days', 'N/A')}</p>
            <p><strong>最大回撤:</strong> {stats.get('max_drawdown', 'N/A')} 點</p>
        </div>
    </div>

    <!-- 🚀 【新增】詳細日誌區塊 -->
    <h2>📋 詳細執行日誌</h2>
    <div class="log-container">
        <div class="log-header">
            <span>回測執行過程詳細記錄</span>
            <button onclick="toggleLogExpand()" id="logToggleBtn">展開全部</button>
        </div>
        <div class="log-content" id="logContent">
            <pre>{escaped_logs}</pre>
        </div>
    </div>

    <script>
        function toggleLogExpand() {{
            const logContent = document.getElementById('logContent');
            const toggleBtn = document.getElementById('logToggleBtn');

            if (logContent.style.maxHeight === 'none') {{
                logContent.style.maxHeight = '400px';
                toggleBtn.textContent = '展開全部';
            }} else {{
                logContent.style.maxHeight = 'none';
                toggleBtn.textContent = '收合';
            }}
        }}
    </script>
</body>
</html>
                """

                with open(report_filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                print("✅ 分析報告生成成功")
                backtest_status['report_ready'] = True
                backtest_status['report_file'] = report_filename
                print(f"📋 報告文件: {report_filename}")

            except Exception as e:
                print(f"⚠️ 報告生成過程中發生錯誤: {e}")
                import traceback
                traceback.print_exc()

        else:
            # 🚀 【Task 2 重構】處理回測失敗情況
            backtest_status['running'] = False
            backtest_status['error'] = "回測執行失敗：未獲得有效結果"
            print(f"❌ 回測執行失敗：未獲得有效結果")

    except Exception as e:
        backtest_status['running'] = False
        backtest_status['error'] = str(e)
        print(f"❌ 執行過程中發生異常: {e}")
        import traceback
        traceback.print_exc()

# ============================================================================
# 報告管理功能
# ============================================================================

def get_report_metadata(report_path):
    """從報告文件中提取元數據"""
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取策略參數
        metadata = {
            'filename': os.path.basename(report_path),
            'filepath': report_path,
            'size': os.path.getsize(report_path),
            'created_time': datetime.fromtimestamp(os.path.getctime(report_path)),
            'trade_lots': 'N/A',
            'date_range': 'N/A',
            'total_trades': 'N/A',
            'win_rate': 'N/A'
        }

        # 從HTML內容中提取關鍵信息
        if '交易口數:' in content:
            try:
                trade_lots = content.split('交易口數:')[1].split('<')[0].strip()
                metadata['trade_lots'] = trade_lots
            except:
                pass

        if '總交易次數:' in content:
            try:
                total_trades = content.split('總交易次數:')[1].split('<')[0].strip()
                metadata['total_trades'] = total_trades
            except:
                pass

        if '勝率:' in content:
            try:
                win_rate = content.split('勝率:')[1].split('<')[0].strip()
                metadata['win_rate'] = win_rate
            except:
                pass

        return metadata
    except Exception as e:
        return {
            'filename': os.path.basename(report_path),
            'filepath': report_path,
            'size': 0,
            'created_time': datetime.now(),
            'trade_lots': 'Error',
            'date_range': 'Error',
            'total_trades': 'Error',
            'win_rate': 'Error'
        }



@app.route('/reports')
def list_reports():
    """顯示歷史報告列表"""
    try:
        reports_dir = 'reports'
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        # 獲取所有報告文件
        report_files = glob.glob(os.path.join(reports_dir, '*.html'))
        report_files.sort(key=os.path.getctime, reverse=True)  # 按創建時間倒序

        # 提取報告元數據
        reports_data = []
        for report_file in report_files:
            metadata = get_report_metadata(report_file)
            reports_data.append(metadata)

        html_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>歷史報告管理</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .nav-buttons { text-align: center; margin-bottom: 20px; }
        .nav-buttons a { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 0 10px; }
        .nav-buttons a:hover { background: #0056b3; }
        .reports-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .reports-table th, .reports-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .reports-table th { background: #e9ecef; font-weight: bold; }
        .reports-table tr:hover { background: #f8f9fa; }
        .action-buttons { display: flex; gap: 5px; }
        .btn { padding: 5px 10px; text-decoration: none; border-radius: 3px; font-size: 12px; border: none; cursor: pointer; }
        .btn-view { background: #28a745; color: white; }
        .btn-download { background: #17a2b8; color: white; }
        .btn-delete { background: #dc3545; color: white; }
        .btn:hover { opacity: 0.8; }
        .file-size { color: #6c757d; font-size: 12px; }
        .stats { color: #495057; font-size: 13px; }
        .delete-all { background: #dc3545; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; margin-left: 10px; }
        .delete-all:hover { background: #c82333; }
        .summary { background: #e7f3ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .report-row { border-bottom: 1px solid #eee; }
        .report-row:nth-child(even) { background-color: #f9f9f9; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 歷史報告管理</h1>

        <div class="nav-buttons">
            <a href="/">🏠 返回主頁</a>
            <button class="delete-all" onclick="deleteAllReports()">🗑️ 清空所有報告</button>
        </div>

        <div class="summary">
            <strong>📈 報告總覽：</strong> 共 {{ total_reports }} 個報告
        </div>

        {% if reports_data %}
        <table class="reports-table">
            <thead>
                <tr>
                    <th>報告名稱</th>
                    <th>創建時間</th>
                    <th>文件大小</th>
                    <th>交易口數</th>
                    <th>交易次數</th>
                    <th>勝率</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
                {% for report in reports_data %}
                <tr class="report-row">
                    <td>
                        <strong>{{ report.filename }}</strong>
                    </td>
                    <td>{{ report.created_time.strftime('%Y-%m-%d %H:%M:%S') }}</td>
                    <td class="file-size">{{ "%.1f"|format(report.size/1024) }} KB</td>
                    <td class="stats">{{ report.trade_lots }}口</td>
                    <td class="stats">{{ report.total_trades }}</td>
                    <td class="stats">{{ report.win_rate }}</td>
                    <td>
                        <div class="action-buttons">
                            <a href="/view_report/{{ report.filename }}" class="btn btn-view" target="_blank">👁️ 查看</a>
                            <a href="/download_report/{{ report.filename }}" class="btn btn-download">💾 下載</a>
                            <button class="btn btn-delete" onclick="deleteReport('{{ report.filename }}')">🗑️ 刪除</button>
                        </div>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}

        {% if not reports_data %}
        <div style="text-align: center; padding: 50px; color: #6c757d;">
            <h3>📭 暫無歷史報告</h3>
            <p>執行回測後，報告將會顯示在這裡</p>
            <a href="/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">開始回測</a>
        </div>
        {% endif %}
    </div>

    <script>
        function deleteReport(filename) {
            if (confirm('確定要刪除報告 "' + filename + '" 嗎？')) {
                fetch('/delete_report/' + filename, { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('報告已刪除');
                            location.reload();
                        } else {
                            alert('刪除失敗: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('刪除失敗: ' + error);
                    });
            }
        }



        function deleteAllReports() {
            if (confirm('確定要刪除所有歷史報告嗎？此操作無法撤銷！')) {
                fetch('/delete_all_reports', { method: 'DELETE' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('所有報告已刪除');
                            location.reload();
                        } else {
                            alert('刪除失敗: ' + data.error);
                        }
                    })
                    .catch(error => {
                        alert('刪除失敗: ' + error);
                    });
            }
        }
    </script>
</body>
</html>
        """

        from jinja2 import Template
        template = Template(html_template)
        return template.render(
            reports_data=reports_data,
            total_reports=len(reports_data)
        )

    except Exception as e:
        return jsonify({'error': f'獲取報告列表失敗: {str(e)}'})

@app.route('/view_report/<filename>')
def view_specific_report(filename):
    """查看特定報告"""
    try:
        report_path = os.path.join('reports', filename)
        if not os.path.exists(report_path):
            return jsonify({'error': '報告文件不存在'})

        with open(report_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return jsonify({'error': f'讀取報告失敗: {str(e)}'})

@app.route('/download_report/<filename>')
def download_report(filename):
    """下載報告文件"""
    try:
        report_path = os.path.join('reports', filename)
        if not os.path.exists(report_path):
            return jsonify({'error': '報告文件不存在'})

        return send_file(report_path, as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': f'下載失敗: {str(e)}'})

@app.route('/delete_report/<filename>', methods=['DELETE'])
def delete_report(filename):
    """刪除特定報告"""
    try:
        report_path = os.path.join('reports', filename)
        if not os.path.exists(report_path):
            return jsonify({'success': False, 'error': '報告文件不存在'})

        os.remove(report_path)
        return jsonify({'success': True, 'message': f'報告 {filename} 已刪除'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'刪除失敗: {str(e)}'})


@app.route('/delete_all_reports', methods=['DELETE'])
def delete_all_reports():
    """刪除所有報告"""
    try:
        reports_dir = 'reports'
        report_files = glob.glob(os.path.join(reports_dir, '*.html'))

        deleted_count = 0
        for report_file in report_files:
            os.remove(report_file)
            deleted_count += 1

        return jsonify({'success': True, 'message': f'已刪除 {deleted_count} 個報告'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'刪除失敗: {str(e)}'})

if __name__ == '__main__':
    print("正在啟動Web GUI...")
    print("請在瀏覽器中打開: http://localhost:8080")
    app.run(debug=True, host='localhost', port=8080)
