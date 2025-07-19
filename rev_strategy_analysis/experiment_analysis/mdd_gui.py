#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MDD 優化器 GUI 介面
專門為 enhanced_mdd_optimizer.py time_interval_analysis 提供參數設定介面
完全不修改現有回測邏輯，只是提供 GUI 參數輸入
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import subprocess
import json
import os
import sys
import threading
import logging
from datetime import datetime
from pathlib import Path
import importlib.util

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🚀 【修復】直接導入統一的回測引擎
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 導入統一的回測引擎
try:
    # 獲取正確的路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    engine_path = os.path.join(parent_dir, "rev_multi_Profit-Funded Risk_多口.py")

    spec = importlib.util.spec_from_file_location(
        "unified_backtest_engine",
        engine_path
    )
    if spec and spec.loader:
        unified_backtest_engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(unified_backtest_engine)
        logger.info(f"✅ 統一回測引擎導入成功: {engine_path}")
    else:
        raise ImportError("無法載入回測引擎")
except Exception as e:
    logger.error(f"❌ 統一回測引擎導入失敗: {e}")
    unified_backtest_engine = None

# 導入統一的配置工廠
try:
    from strategy_config_factory import create_config_from_gui_dict
    logger.info("✅ 配置工廠導入成功")
except Exception as e:
    logger.error(f"❌ 配置工廠導入失敗: {e}")
    create_config_from_gui_dict = None

app = Flask(__name__)
app.secret_key = 'mdd_gui_secret_key'

# 全域變數
experiment_status = {
    'running': False,
    'completed': False,
    'error': None,
    'result': None,
    'log_content': '',
    'start_time': None,
    'parsed_results': None
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MDD 優化器 GUI</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; color: #333; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; margin: 5px; }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-success { background-color: #28a745; color: white; }
        .btn-danger { background-color: #dc3545; color: white; }
        .btn-info { background-color: #17a2b8; color: white; }
        .btn:hover { opacity: 0.8; }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .status-panel { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .status-running { background: #fff3cd; border-left: 4px solid #ffc107; }
        .status-completed { background: #d4edda; border-left: 4px solid #28a745; }
        .status-error { background: #f8d7da; border-left: 4px solid #dc3545; }
        .log-container { background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 5px; height: 300px; overflow-y: auto; font-family: monospace; font-size: 12px; }
        .time-interval-row { display: grid; grid-template-columns: 1fr 1fr auto; gap: 10px; align-items: end; margin-bottom: 10px; }
        .help-text { font-size: 12px; color: #666; margin-top: 5px; }
        .section-title { color: #495057; border-bottom: 2px solid #e9ecef; padding-bottom: 5px; margin-bottom: 15px; }
        .results-table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        .results-table th, .results-table td { padding: 10px; text-align: left; border: 1px solid #ddd; }
        .results-table th { background-color: #f8f9fa; font-weight: bold; }
        .results-table tr:nth-child(even) { background-color: #f9f9f9; }
        .best-config { background-color: #d4edda !important; }
        .recommendation-badge { background-color: #ffc107; color: #212529; padding: 2px 6px; border-radius: 3px; font-size: 12px; }
        .mdd-value { font-weight: bold; color: #dc3545; }
        .pnl-value { font-weight: bold; color: #28a745; }
        .radio-group { display: flex; gap: 15px; margin-top: 5px; }
        .radio-group label { display: flex; align-items: center; gap: 5px; cursor: pointer; }
        .radio-group input[type="radio"] { margin: 0; }
        .date-range-display { background-color: #e8f4fd; border: 1px solid #bee5eb; border-radius: 5px; padding: 10px; margin-top: 5px; }
        .date-range-display strong { color: #0c5460; font-size: 16px; }
        .date-info { color: #6c757d; font-size: 14px; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 MDD 優化器 GUI</h1>
            <p>enhanced_mdd_optimizer.py time_interval_analysis 參數設定介面</p>
        </div>

        <!-- 狀態面板 -->
        <div id="statusPanel" class="status-panel">
            <h3>📊 執行狀態</h3>
            <div id="statusContent">就緒 - 請設定參數後執行實驗</div>
        </div>

        <!-- 參數設定 -->
        <div class="card">
            <h2 class="section-title">⚙️ 參數設定</h2>
            <form id="mddForm">
                
                <!-- 停損設定 -->
                <h3>🛑 停損參數設定</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>第1口停損範圍:</label>
                        <input type="text" id="lot1StopLoss" value="15" placeholder="例: 12,15,18 或 15">
                        <div class="help-text">多個值用逗號分隔，單一值直接輸入</div>
                    </div>
                    <div class="form-group">
                        <label>第2口停損範圍:</label>
                        <input type="text" id="lot2StopLoss" value="15" placeholder="例: 20,25,30 或 25">
                        <div class="help-text">建議 >= 第1口停損值</div>
                    </div>
                    <div class="form-group">
                        <label>第3口停損範圍:</label>
                        <input type="text" id="lot3StopLoss" value="15" placeholder="例: 25,30,35 或 30">
                        <div class="help-text">建議 >= 第2口停損值</div>
                    </div>
                </div>

                <!-- 停利設定 -->
                <h3>🎯 停利參數設定</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>統一停利範圍:</label>
                        <input type="text" id="unifiedProfit" value="55" placeholder="例: 50,60,70 或 55">
                        <div class="help-text">所有口使用相同停利點數</div>
                    </div>
                    <div class="form-group">
                        <label>各口獨立停利範圍:</label>
                        <input type="text" id="individualProfit" value="30,40,50,60" placeholder="例: 30,40,50,60">
                        <div class="help-text">每口可設不同停利點數</div>
                    </div>
                </div>

                <!-- 時間區間設定 -->
                <h3>⏰ 時間區間設定</h3>
                <div id="timeIntervals">
                    <div class="time-interval-row">
                        <div class="form-group">
                            <label>區間1 開始時間:</label>
                            <input type="time" class="interval-start" value="10:30">
                        </div>
                        <div class="form-group">
                            <label>區間1 結束時間:</label>
                            <input type="time" class="interval-end" value="10:32">
                        </div>
                        <button type="button" class="btn btn-danger" onclick="removeInterval(this)">刪除</button>
                    </div>
                    <div class="time-interval-row">
                        <div class="form-group">
                            <label>區間2 開始時間:</label>
                            <input type="time" class="interval-start" value="12:00">
                        </div>
                        <div class="form-group">
                            <label>區間2 結束時間:</label>
                            <input type="time" class="interval-end" value="12:02">
                        </div>
                        <button type="button" class="btn btn-danger" onclick="removeInterval(this)">刪除</button>
                    </div>
                </div>
                <button type="button" class="btn btn-info" onclick="addInterval()">➕ 新增時間區間</button>

                <!-- 回測日期範圍 -->
                <h3>📅 回測日期範圍</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>固定日期範圍:</label>
                        <div class="date-range-display">
                            <strong>2024-11-04 至 2025-06-28</strong>
                            <span class="date-info">（約 7.8 個月，涵蓋完整交易週期）</span>
                        </div>
                        <div class="help-text">
                            此日期範圍已針對策略驗證進行最佳化，包含多種市場條件以確保回測結果的可靠性。
                        </div>
                    </div>
                </div>

                <!-- 進場方式設定 -->
                <h3>🎯 進場方式設定</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>多單進場方式:</label>
                        <div class="radio-group">
                            <label><input type="radio" name="entry_price_mode" value="range_boundary" checked> 區間下邊緣進場</label>
                            <label><input type="radio" name="entry_price_mode" value="breakout_low"> 最低點+5點進場</label>
                        </div>
                        <div class="help-text">
                            <strong>進場方式說明：</strong><br>
                            • <strong>區間下邊緣進場：</strong> 當K棒跌破區間低點時，使用區間下邊緣價格進場（保守，執行確定性高）<br>
                            • <strong>最低點+5點進場：</strong> 當K棒跌破區間低點時，使用該K棒的最低價+5點進場（避免極端價格，平衡執行風險）
                        </div>
                    </div>
                </div>

                <!-- 執行設定 -->
                <h3>⚙️ 執行設定</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>並行線程數:</label>
                        <select id="maxWorkers">
                            <option value="1">1 線程</option>
                            <option value="2">2 線程</option>
                            <option value="4">4 線程</option>
                            <option value="6" selected>6 線程 (推薦)</option>
                            <option value="8">8 線程</option>
                        </select>
                        <div class="help-text">8核心 Mac 建議使用 6 線程，保留 2 核心給系統</div>
                    </div>
                </div>

                <!-- 執行控制 -->
                <div style="margin-top: 30px; text-align: center;">
                    <button type="submit" id="runBtn" class="btn btn-primary">🚀 執行 MDD 優化</button>
                    <button type="button" id="stopBtn" class="btn btn-danger" onclick="stopExperiment()" disabled>⏹️ 停止執行</button>
                    <button type="button" class="btn btn-info" onclick="viewResults()">📊 查看結果</button>
                </div>
            </form>
        </div>

        <!-- 執行日誌 -->
        <div class="card">
            <h3>📝 執行日誌</h3>
            <div id="logContainer" class="log-container">
                等待執行...
            </div>
        </div>

        <!-- 實驗結果 -->
        <div class="card" id="resultsCard" style="display: none;">
            <h3>📊 實驗結果</h3>

            <!-- 時間區間分析結果 -->
            <div id="timeIntervalResults">
                <!-- 動態生成的結果表格會插入這裡 -->
            </div>

            <!-- 一日交易配置建議 -->
            <div id="dailyRecommendations" style="margin-top: 20px;">
                <h4>📋 一日交易配置建議</h4>
                <div id="recommendationsTable">
                    <!-- 動態生成的建議表格會插入這裡 -->
                </div>
            </div>

            <!-- MDD 最小 TOP 10 -->
            <div id="mddTop10" style="margin-top: 20px;">
                <h4>🏆 MDD 最小 TOP 10</h4>
                <div id="mddTop10Table">
                    <!-- 動態生成的 MDD TOP 10 表格會插入這裡 -->
                </div>
            </div>

            <!-- 風險調整收益 TOP 10 -->
            <div id="riskAdjustedTop10" style="margin-top: 20px;">
                <h4>💎 風險調整收益 TOP 10</h4>
                <div id="riskAdjustedTop10Table">
                    <!-- 動態生成的風險調整收益 TOP 10 表格會插入這裡 -->
                </div>
            </div>

            <!-- LONG 部位 PNL TOP 10 -->
            <div id="longPnlTop10" style="margin-top: 20px;">
                <h4>🟢 LONG 部位 PNL TOP 10</h4>
                <div id="longPnlTop10Table">
                    <!-- 動態生成的 LONG PNL TOP 10 表格會插入這裡 -->
                </div>
            </div>

            <!-- SHORT 部位 PNL TOP 10 -->
            <div id="shortPnlTop10" style="margin-top: 20px;">
                <h4>🔴 SHORT 部位 PNL TOP 10</h4>
                <div id="shortPnlTop10Table">
                    <!-- 動態生成的 SHORT PNL TOP 10 表格會插入這裡 -->
                </div>
            </div>
        </div>
    </div>

    <script>
        // 全域變數
        let statusCheckInterval = null;

        // 表單提交處理
        document.getElementById('mddForm').addEventListener('submit', function(e) {
            e.preventDefault();
            runExperiment();
        });

        // 執行實驗
        function runExperiment() {
            const formData = collectFormData();
            if (!validateFormData(formData)) {
                return;
            }

            // 更新 UI 狀態
            document.getElementById('runBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            updateStatus('running', '正在執行 MDD 優化實驗...');

            // 發送請求
            fetch('/run_experiment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'started') {
                    startStatusCheck();
                } else {
                    updateStatus('error', data.message || '啟動失敗');
                    resetButtons();
                }
            })
            .catch(error => {
                updateStatus('error', '請求失敗: ' + error.message);
                resetButtons();
            });
        }

        // 收集表單數據
        function collectFormData() {
            const timeIntervals = [];
            const intervalRows = document.querySelectorAll('.time-interval-row');
            intervalRows.forEach(row => {
                const start = row.querySelector('.interval-start').value;
                const end = row.querySelector('.interval-end').value;
                if (start && end) {
                    timeIntervals.push([start, end]);
                }
            });

            return {
                stop_loss_ranges: {
                    lot1: parseNumberList(document.getElementById('lot1StopLoss').value),
                    lot2: parseNumberList(document.getElementById('lot2StopLoss').value),
                    lot3: parseNumberList(document.getElementById('lot3StopLoss').value)
                },
                take_profit_ranges: {
                    unified: parseNumberList(document.getElementById('unifiedProfit').value),
                    individual: parseNumberList(document.getElementById('individualProfit').value)
                },
                time_intervals: timeIntervals,
                entry_price_mode: document.querySelector('input[name="entry_price_mode"]:checked').value,
                max_workers: parseInt(document.getElementById('maxWorkers').value)
            };
        }

        // 解析數字列表
        function parseNumberList(str) {
            return str.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
        }

        // 驗證表單數據
        function validateFormData(data) {
            if (data.stop_loss_ranges.lot1.length === 0 || 
                data.stop_loss_ranges.lot2.length === 0 || 
                data.stop_loss_ranges.lot3.length === 0) {
                alert('請填入所有停損參數');
                return false;
            }
            if (data.time_intervals.length === 0) {
                alert('請至少設定一個時間區間');
                return false;
            }
            return true;
        }

        // 開始狀態檢查
        function startStatusCheck() {
            statusCheckInterval = setInterval(checkStatus, 2000);
        }

        // 檢查執行狀態
        function checkStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    updateStatus(data.status, data.message);
                    updateLog(data.log_content);

                    // 如果有解析後的結果，顯示它們
                    if (data.parsed_results) {
                        displayParsedResults(data.parsed_results);
                    }

                    if (data.status === 'completed' || data.status === 'error') {
                        stopStatusCheck();
                        resetButtons();
                    }
                });
        }

        // 停止狀態檢查
        function stopStatusCheck() {
            if (statusCheckInterval) {
                clearInterval(statusCheckInterval);
                statusCheckInterval = null;
            }
        }

        // 更新狀態顯示
        function updateStatus(status, message) {
            const panel = document.getElementById('statusPanel');
            const content = document.getElementById('statusContent');
            
            panel.className = 'status-panel status-' + status;
            content.textContent = message;
        }

        // 更新日誌顯示
        function updateLog(logContent) {
            const logContainer = document.getElementById('logContainer');
            logContainer.textContent = logContent || '等待執行...';
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        // 顯示解析後的結果
        function displayParsedResults(results) {
            const resultsCard = document.getElementById('resultsCard');
            const timeIntervalResults = document.getElementById('timeIntervalResults');
            const recommendationsTable = document.getElementById('recommendationsTable');
            const mddTop10Table = document.getElementById('mddTop10Table');
            const riskAdjustedTop10Table = document.getElementById('riskAdjustedTop10Table');
            const longPnlTop10Table = document.getElementById('longPnlTop10Table');
            const shortPnlTop10Table = document.getElementById('shortPnlTop10Table');

            // 顯示結果卡片
            resultsCard.style.display = 'block';

            // 顯示時間區間結果
            displayTimeIntervalResults(results.time_intervals, timeIntervalResults);

            // 顯示一日配置建議
            displayDailyRecommendations(results.recommendations, recommendationsTable);

            // 顯示 MDD TOP 10
            displayMddTop10(results.mdd_top10, mddTop10Table);

            // 顯示風險調整收益 TOP 10
            displayRiskAdjustedTop10(results.risk_adjusted_top10, riskAdjustedTop10Table);

            // 顯示 LONG PNL TOP 10
            displayLongPnlTop10(results.long_pnl_top10, longPnlTop10Table);

            // 顯示 SHORT PNL TOP 10
            displayShortPnlTop10(results.short_pnl_top10, shortPnlTop10Table);
        }



        // 停利模式映射字典
        const takeProfitModeMap = {
            'unified_fixed': '統一停利',
            'individual_fixed': '各口獨立停利',
            'range_boundary': '區間邊緣停利'
        };

        // 獲取停利類型顯示文字的輔助函數
        function getTakeProfitDisplayText(config) {
            // 優先使用 take_profit_mode 字段
            if (config.take_profit_mode && takeProfitModeMap[config.take_profit_mode]) {
                const baseType = takeProfitModeMap[config.take_profit_mode];

                // 為統一停利和個別停利添加數值
                if (config.take_profit_mode === 'unified_fixed') {
                    // 從實驗結果中獲取實際使用的停利值
                    const takeProfitValue = config.lot1_take_profit || config.unified_take_profit;
                    return takeProfitValue ? `${baseType} ${takeProfitValue}` : baseType;
                } else if (config.take_profit_mode === 'individual_fixed') {
                    // 從實驗結果中獲取實際使用的停利值
                    const takeProfitValue = config.lot1_take_profit || config.individual_take_profit;
                    return takeProfitValue ? `${baseType} ${takeProfitValue}` : baseType;
                } else {
                    return baseType; // 區間邊緣停利不需要數值
                }
            }

            // 備用邏輯：使用舊的 type 字段
            if (config.type) {
                if (config.type.includes('統一停利')) {
                    return config.type;
                } else if (config.type.includes('個別停利')) {
                    return config.type;
                } else if (config.type.includes('區間')) {
                    return '區間邊緣停利';
                }
                return config.type;
            }

            // 最後備用：預設值
            return '統一停利';
        }

        // 顯示時間區間結果
        function displayTimeIntervalResults(timeIntervals, container) {
            if (!timeIntervals || timeIntervals.length === 0) {
                container.innerHTML = '<p>暫無時間區間分析結果</p>';
                return;
            }

            let html = '';

            timeIntervals.forEach(interval => {
                html += `
                    <h4>🕙 ${interval.time || interval.interval}</h4>
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>排名</th>
                                <th>停利類型</th>
                                <th>MDD</th>
                                <th>P&L</th>
                                <th>停損參數設定</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

                // 顯示前3名（從 top3 或 configs 中取得）
                let dataToShow = [];
                if (interval.top3 && interval.top3.length > 0) {
                    dataToShow = interval.top3.slice(0, 3);
                } else if (interval.configs && interval.configs.length > 0) {
                    dataToShow = interval.configs.slice(0, 3);
                }

                if (dataToShow.length > 0) {
                    dataToShow.forEach((config, index) => {
                        // 使用新的停利類型顯示邏輯
                        const stopProfitType = getTakeProfitDisplayText(config);

                        // 添加調試日誌
                        console.log(`[DEBUG] 時間區間結果 ${index + 1}:`, {
                            take_profit_mode: config.take_profit_mode,
                            type: config.type,
                            lot1_take_profit: config.lot1_take_profit,
                            displayText: stopProfitType,
                            rawConfig: config
                        });

                        html += `
                            <tr>
                                <td><strong>${index + 1}</strong></td>
                                <td>${stopProfitType}</td>
                                <td class="mdd-value">${config.mdd || 'N/A'}</td>
                                <td class="pnl-value">${config.pnl || 'N/A'}</td>
                                <td>${config.params || ''}</td>
                            </tr>
                        `;
                    });
                } else {
                    html += '<tr><td colspan="5">暫無配置數據</td></tr>';
                }

                html += `
                        </tbody>
                    </table>
                `;
            });

            container.innerHTML = html;
        }



        // 顯示一日配置建議
        function displayDailyRecommendations(recommendations, container) {
            if (recommendations.length === 0) {
                container.innerHTML = '<p>暫無建議資料</p>';
                return;
            }

            let html = `
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>時間區間</th>
                            <th>建議策略</th>
                            <th>參數設定</th>
                            <th>MDD</th>
                            <th>P&L</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            recommendations.forEach(rec => {
                html += `
                    <tr class="best-config">
                        <td><strong>${rec.time}</strong></td>
                        <td>${rec.type}</td>
                        <td>${rec.params}</td>
                        <td class="mdd-value">${rec.mdd}</td>
                        <td class="pnl-value">${rec.pnl}</td>
                    </tr>
                `;
            });

            html += `
                    </tbody>
                </table>
            `;

            container.innerHTML = html;
        }

        // 顯示 MDD TOP 10
        function displayMddTop10(mddTop10, container) {
            if (!mddTop10 || mddTop10.length === 0) {
                container.innerHTML = '<p>暫無 MDD TOP 10 數據</p>';
                return;
            }

            let html = `
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>MDD</th>
                            <th>總P&L</th>
                            <th>LONG PNL</th>
                            <th>SHORT PNL</th>
                            <th>停損參數設定</th>
                            <th>停利類型</th>
                            <th>時間區間</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            mddTop10.forEach(item => {
                // 使用新的停利類型顯示邏輯
                const stopProfitType = getTakeProfitDisplayText(item);

                // 添加調試日誌
                console.log(`[DEBUG] MDD TOP 10 項目:`, {
                    take_profit_mode: item.take_profit_mode,
                    strategy: item.strategy,
                    lot1_take_profit: item.lot1_take_profit,
                    displayText: stopProfitType,
                    rawItem: item
                });

                html += `
                    <tr>
                        <td><strong>${item.rank}</strong></td>
                        <td class="mdd-value">${item.mdd}</td>
                        <td class="pnl-value">${item.pnl}</td>
                        <td class="pnl-value">${item.long_pnl || 0}</td>
                        <td class="pnl-value">${item.short_pnl || 0}</td>
                        <td>${item.params || ''}</td>
                        <td>${stopProfitType}</td>
                        <td>${item.time || ''}</td>
                    </tr>
                `;
            });

            html += `
                    </tbody>
                </table>
            `;

            container.innerHTML = html;
        }

        // 顯示風險調整收益 TOP 10
        function displayRiskAdjustedTop10(riskTop10, container) {
            if (!riskTop10 || riskTop10.length === 0) {
                container.innerHTML = '<p>暫無風險調整收益 TOP 10 數據</p>';
                return;
            }

            let html = `
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>風險調整收益</th>
                            <th>MDD</th>
                            <th>總P&L</th>
                            <th>LONG PNL</th>
                            <th>SHORT PNL</th>
                            <th>停損參數設定</th>
                            <th>停利類型</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            riskTop10.forEach(item => {
                html += `
                    <tr>
                        <td><strong>${item.rank}</strong></td>
                        <td class="pnl-value"><strong>${item.ratio}</strong></td>
                        <td class="mdd-value">${item.mdd}</td>
                        <td class="pnl-value">${item.pnl}</td>
                        <td class="pnl-value">${item.long_pnl || 0}</td>
                        <td class="pnl-value">${item.short_pnl || 0}</td>
                        <td>${item.params || ''}</td>
                        <td>${item.strategy || ''}</td>
                    </tr>
                `;
            });

            html += `
                    </tbody>
                </table>
            `;

            container.innerHTML = html;
        }

        // 顯示 LONG PNL TOP 10
        function displayLongPnlTop10(longPnlTop10, container) {
            if (!longPnlTop10 || longPnlTop10.length === 0) {
                container.innerHTML = '<p>暫無 LONG PNL TOP 10 數據</p>';
                return;
            }

            let html = `
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>LONG PNL</th>
                            <th>總P&L</th>
                            <th>SHORT PNL</th>
                            <th>停損參數設定</th>
                            <th>停利類型</th>
                            <th>時間區間</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            longPnlTop10.forEach(item => {
                // 使用新的停利類型顯示邏輯
                const stopProfitType = getTakeProfitDisplayText(item);

                html += `
                    <tr>
                        <td><strong>${item.rank}</strong></td>
                        <td class="pnl-value"><strong>${item.long_pnl}</strong></td>
                        <td class="pnl-value">${item.pnl}</td>
                        <td class="pnl-value">${item.short_pnl || 0}</td>
                        <td>${item.params || ''}</td>
                        <td>${stopProfitType}</td>
                        <td>${item.time || ''}</td>
                    </tr>
                `;
            });

            html += `
                    </tbody>
                </table>
            `;

            container.innerHTML = html;
        }

        // 顯示 SHORT PNL TOP 10
        function displayShortPnlTop10(shortPnlTop10, container) {
            if (!shortPnlTop10 || shortPnlTop10.length === 0) {
                container.innerHTML = '<p>暫無 SHORT PNL TOP 10 數據</p>';
                return;
            }

            let html = `
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>排名</th>
                            <th>SHORT PNL</th>
                            <th>總P&L</th>
                            <th>LONG PNL</th>
                            <th>停損參數設定</th>
                            <th>停利類型</th>
                            <th>時間區間</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            shortPnlTop10.forEach(item => {
                // 使用新的停利類型顯示邏輯
                const stopProfitType = getTakeProfitDisplayText(item);

                html += `
                    <tr>
                        <td><strong>${item.rank}</strong></td>
                        <td class="pnl-value"><strong>${item.short_pnl}</strong></td>
                        <td class="pnl-value">${item.pnl}</td>
                        <td class="pnl-value">${item.long_pnl || 0}</td>
                        <td>${item.params || ''}</td>
                        <td>${stopProfitType}</td>
                        <td>${item.time || ''}</td>
                    </tr>
                `;
            });

            html += `
                    </tbody>
                </table>
            `;

            container.innerHTML = html;
        }

        // 重置按鈕狀態
        function resetButtons() {
            document.getElementById('runBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        }

        // 停止實驗
        function stopExperiment() {
            fetch('/stop_experiment', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    updateStatus('error', '實驗已停止');
                    stopStatusCheck();
                    resetButtons();
                });
        }

        // 新增時間區間
        function addInterval() {
            const container = document.getElementById('timeIntervals');
            const newRow = document.createElement('div');
            newRow.className = 'time-interval-row';
            newRow.innerHTML = `
                <div class="form-group">
                    <label>開始時間:</label>
                    <input type="time" class="interval-start" value="09:00">
                </div>
                <div class="form-group">
                    <label>結束時間:</label>
                    <input type="time" class="interval-end" value="09:02">
                </div>
                <button type="button" class="btn btn-danger" onclick="removeInterval(this)">刪除</button>
            `;
            container.appendChild(newRow);
        }

        // 刪除時間區間
        function removeInterval(btn) {
            btn.parentElement.remove();
        }

        // 查看結果
        function viewResults() {
            window.open('/results', '_blank');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """主頁面"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/run_experiment', methods=['POST'])
def run_experiment():
    """執行實驗"""
    global experiment_status
    
    if experiment_status['running']:
        return jsonify({'status': 'error', 'message': '實驗正在執行中'})
    
    try:
        params = request.json
        logger.info(f"收到實驗參數: {params}")
        
        # 重置狀態
        experiment_status = {
            'running': True,
            'completed': False,
            'error': None,
            'result': None,
            'log_content': '',
            'start_time': datetime.now()
        }
        
        # 在背景線程執行實驗
        thread = threading.Thread(target=run_experiment_thread, args=(params,))
        thread.daemon = True
        thread.start()
        
        return jsonify({'status': 'started', 'message': '實驗已啟動'})
        
    except Exception as e:
        logger.error(f"啟動實驗失敗: {e}")
        return jsonify({'status': 'error', 'message': f'啟動失敗: {str(e)}'})

def run_experiment_thread_unified(params):
    """使用統一回測引擎執行實驗"""
    global experiment_status

    try:
        if not unified_backtest_engine or not create_config_from_gui_dict:
            raise Exception("統一回測引擎或配置工廠未正確導入")

        experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 開始執行 MDD 優化實驗（使用統一引擎）\n"
        experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] 回測日期範圍: 2024-11-04 至 2025-06-28\n"
        experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] 進場方式: {params.get('entry_price_mode', 'range_boundary')}\n"
        experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] 參數: {params}\n"

        # 解析時間區間
        time_intervals = params.get('time_intervals', [])
        if isinstance(time_intervals, str):
            time_intervals = [interval.strip() for interval in time_intervals.split(',') if interval.strip()]
        elif isinstance(time_intervals, list):
            # 處理嵌套列表格式 [['10:30', '10:32'], ['12:00', '12:02']]
            if time_intervals and isinstance(time_intervals[0], list):
                time_intervals = [f"{interval[0]}-{interval[1]}" for interval in time_intervals]

        # 解析停損參數 - 處理新的參數格式
        stop_loss_ranges = params.get('stop_loss_ranges', {})
        lot1_stop_loss = stop_loss_ranges.get('lot1', [15])
        lot2_stop_loss = stop_loss_ranges.get('lot2', [40])
        lot3_stop_loss = stop_loss_ranges.get('lot3', [41])

        # 如果是舊格式，使用舊的解析方式
        if not stop_loss_ranges:
            lot1_stop_loss = parse_parameter_list(params.get('lot1_stop_loss', '15'))
            lot2_stop_loss = parse_parameter_list(params.get('lot2_stop_loss', '40'))
            lot3_stop_loss = parse_parameter_list(params.get('lot3_stop_loss', '41'))

        # 解析停利參數 - 需要執行所有三種停利模式
        take_profit_ranges = params.get('take_profit_ranges', {})

        # 準備所有停利模式的參數組合
        all_take_profit_combinations = []

        # 1. 統一停利模式 - 支援多個統一停利值
        if 'unified' in take_profit_ranges and take_profit_ranges['unified']:
            unified_values = take_profit_ranges['unified']
            all_take_profit_combinations.append({
                'mode': 'unified_fixed',
                'lot1': unified_values,  # 支援多個統一停利值
                'lot2': unified_values,  # 所有口使用相同值
                'lot3': unified_values   # 但會測試所有值
            })

        # 2. 個別停利模式
        if 'individual' in take_profit_ranges and take_profit_ranges['individual']:
            individual_values = take_profit_ranges['individual']
            all_take_profit_combinations.append({
                'mode': 'individual_fixed',
                'lot1': individual_values,
                'lot2': individual_values,
                'lot3': individual_values
            })

        # 3. 區間邊緣停利模式（固定添加）
        all_take_profit_combinations.append({
            'mode': 'range_boundary',
            'lot1': [0],  # 區間停利不使用固定點數
            'lot2': [0],
            'lot3': [0]
        })

        experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] 時間區間: {time_intervals}\n"
        experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] 停損參數: L1={lot1_stop_loss}, L2={lot2_stop_loss}, L3={lot3_stop_loss}\n"
        experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] 停利模式數量: {len(all_take_profit_combinations)}\n"
        for i, tp_combo in enumerate(all_take_profit_combinations):
            experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] 停利模式 {i+1}: {tp_combo['mode']} - L1={tp_combo['lot1']}, L2={tp_combo['lot2']}, L3={tp_combo['lot3']}\n"

        # 生成實驗組合 - 遍歷所有停利模式
        results = []
        experiment_id = 1

        for time_interval in time_intervals:
            for l1_sl in lot1_stop_loss:
                for l2_sl in lot2_stop_loss:
                    for l3_sl in lot3_stop_loss:
                        for tp_combination in all_take_profit_combinations:
                            for l1_tp in tp_combination['lot1']:
                                for l2_tp in tp_combination['lot2']:
                                    for l3_tp in tp_combination['lot3']:
                                        try:
                                            # 解析時間區間
                                            start_time, end_time = time_interval.split('-')

                                            # 根據停利模式設定配置
                                            if tp_combination['mode'] == 'range_boundary':
                                                # 區間邊緣停利模式
                                                individual_tp_enabled = False
                                                fixed_stop_mode = False
                                            else:
                                                # 固定停利模式（統一或個別）
                                                individual_tp_enabled = True
                                                fixed_stop_mode = True

                                            # 創建GUI配置
                                            gui_config = {
                                                "trade_lots": 3,
                                                "start_date": "2024-11-04",
                                                "end_date": "2025-06-28",
                                                "range_start_time": start_time.strip(),
                                                "range_end_time": end_time.strip(),
                                                "fixed_stop_mode": fixed_stop_mode,
                                                "individual_take_profit_enabled": individual_tp_enabled,
                                                "entry_price_mode": params.get('entry_price_mode', 'range_boundary'),
                                                "trading_direction": "BOTH",
                                                "lot_settings": {
                                                    "lot1": {
                                                        "trigger": l1_sl,
                                                        "trailing": 0,
                                                        "take_profit": l1_tp
                                                    },
                                                    "lot2": {
                                                        "trigger": l2_sl,
                                                        "trailing": 0,
                                                        "protection": 2.0,
                                                        "take_profit": l2_tp
                                                    },
                                                    "lot3": {
                                                        "trigger": l3_sl,
                                                        "trailing": 0,
                                                        "protection": 2.0,
                                                        "take_profit": l3_tp
                                                    }
                                                },
                                                "filters": {
                                                    "range_filter": {"enabled": False, "max_range_points": 50},
                                                    "risk_filter": {"enabled": False, "daily_loss_limit": 150, "profit_target": 200},
                                                    "stop_loss_filter": {"enabled": False, "stop_loss_type": "range_boundary", "fixed_stop_loss_points": 15.0}
                                                }
                                            }

                                            # 使用統一配置工廠
                                            strategy_config = create_config_from_gui_dict(gui_config)

                                            # 直接調用統一回測引擎
                                            result = unified_backtest_engine.run_backtest(
                                                strategy_config,
                                                start_date=gui_config["start_date"],
                                                end_date=gui_config["end_date"],
                                                range_start_time=gui_config["range_start_time"],
                                                range_end_time=gui_config["range_end_time"]
                                            )

                                            if result:
                                                mdd = result.get('max_drawdown', 0)
                                                total_pnl = result.get('total_pnl', 0)
                                                long_pnl = result.get('long_pnl', 0)
                                                short_pnl = result.get('short_pnl', 0)

                                                results.append({
                                                    'experiment_id': experiment_id,
                                                    'time_interval': time_interval,
                                                    'lot1_stop_loss': l1_sl,
                                                    'lot2_stop_loss': l2_sl,
                                                    'lot3_stop_loss': l3_sl,
                                                    'lot1_take_profit': l1_tp,
                                                    'lot2_take_profit': l2_tp,
                                                    'lot3_take_profit': l3_tp,
                                                    'take_profit_mode': tp_combination['mode'],
                                                    'mdd': mdd,
                                                    'total_pnl': total_pnl,
                                                    'long_pnl': long_pnl,
                                                    'short_pnl': short_pnl,
                                                    'risk_adjusted_return': abs(total_pnl / mdd) if mdd != 0 else 0
                                                })

                                                experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 實驗 {experiment_id} ({tp_combination['mode']}): MDD={mdd:.1f}, PNL={total_pnl:.1f}\n"

                                            experiment_id += 1

                                        except Exception as e:
                                            experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 實驗 {experiment_id} 失敗: {e}\n"
                                            experiment_id += 1

        # 生成報告
        if results:
            report_content = generate_unified_report(results)
            experiment_status['log_content'] += report_content
            experiment_status['completed'] = True
            experiment_status['result'] = '實驗執行成功'
            experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 統一引擎實驗執行成功！共完成 {len(results)} 個實驗\n"

            # 解析結果
            parsed_results = parse_experiment_results(experiment_status['log_content'])
            experiment_status['parsed_results'] = parsed_results

            # 調試信息
            experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] 📊 解析結果統計:\n"
            experiment_status['log_content'] += f"  - 時間區間分析: {len(parsed_results.get('time_intervals', []))}\n"
            experiment_status['log_content'] += f"  - 一日配置建議: {len(parsed_results.get('recommendations', []))}\n"
            experiment_status['log_content'] += f"  - MDD TOP 10: {len(parsed_results.get('mdd_top10', []))}\n"
            experiment_status['log_content'] += f"  - 風險調整收益 TOP 10: {len(parsed_results.get('risk_adjusted_top10', []))}\n"
            experiment_status['log_content'] += f"  - LONG PNL TOP 10: {len(parsed_results.get('long_pnl_top10', []))}\n"
            experiment_status['log_content'] += f"  - SHORT PNL TOP 10: {len(parsed_results.get('short_pnl_top10', []))}\n"
        else:
            experiment_status['error'] = '沒有成功的實驗結果'
            experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 沒有成功的實驗結果\n"

    except Exception as e:
        experiment_status['running'] = False
        experiment_status['error'] = str(e)
        experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 實驗執行失敗: {e}\n"
        logger.error(f"實驗執行失敗: {e}")

    finally:
        experiment_status['running'] = False
        experiment_status['log_content'] += f"[{datetime.now().strftime('%H:%M:%S')}] 實驗線程結束\n"

def parse_parameter_list(param_str):
    """解析參數列表"""
    if isinstance(param_str, list):
        return param_str
    if isinstance(param_str, str):
        return [float(x.strip()) for x in param_str.split(',') if x.strip()]
    return [float(param_str)]

def generate_unified_report(results):
    """生成統一格式的報告"""
    if not results:
        return "沒有實驗結果\n"

    # 按 MDD 排序（越小越好）
    sorted_by_mdd = sorted(results, key=lambda x: abs(x['mdd']))

    # 按風險調整收益排序（越大越好）
    sorted_by_risk_adj = sorted(results, key=lambda x: x.get('risk_adjusted_return', 0), reverse=True)

    # 按多頭PNL排序
    sorted_by_long_pnl = sorted(results, key=lambda x: x.get('long_pnl', 0), reverse=True)

    # 按空頭PNL排序
    sorted_by_short_pnl = sorted(results, key=lambda x: x.get('short_pnl', 0), reverse=True)

    # 按時間區間分組
    time_interval_groups = {}
    for result in results:
        interval = result['time_interval']
        if interval not in time_interval_groups:
            time_interval_groups[interval] = []
        time_interval_groups[interval].append(result)

    report = f"\n📊 實驗結果報告 (共 {len(results)} 個實驗)\n"
    report += "=" * 80 + "\n"

    # 各時間區間的最佳MDD前3名
    report += "\n📊 各時間區間 MDD 最佳前3名:\n"
    report += "-" * 60 + "\n"
    for interval, interval_results in time_interval_groups.items():
        sorted_interval = sorted(interval_results, key=lambda x: abs(x['mdd']))[:3]
        report += f"\n🕐 時間區間: {interval}\n"
        for i, result in enumerate(sorted_interval, 1):
            # 添加停利模式信息到報告中
            take_profit_mode = result.get('take_profit_mode', 'unified_fixed')
            report += f"  {i}. MDD:{result['mdd']:6.1f} | PNL:{result['total_pnl']:6.1f} | "
            report += f"參數:{result['lot1_stop_loss']}/{result['lot2_stop_loss']}/{result['lot3_stop_loss']} | "
            report += f"多頭:{result['long_pnl']:6.1f} | 空頭:{result['short_pnl']:6.1f} | "
            report += f"停利模式:{take_profit_mode}\n"

    # TOP 10 最佳 MDD
    report += "\n🏆 MDD 最小 TOP 10:\n"
    report += "-" * 60 + "\n"
    for i, result in enumerate(sorted_by_mdd[:10], 1):
        take_profit_mode = result.get('take_profit_mode', 'unified_fixed')
        report += f"{i:2d}. 實驗{result['experiment_id']:3d} | 時間:{result['time_interval']} | "
        report += f"MDD:{result['mdd']:6.1f} | PNL:{result['total_pnl']:6.1f} | "
        report += f"參數:{result['lot1_stop_loss']}/{result['lot2_stop_loss']}/{result['lot3_stop_loss']} | "
        report += f"多頭:{result['long_pnl']:6.1f} | 空頭:{result['short_pnl']:6.1f} | "
        report += f"停利模式:{take_profit_mode}\n"

    # TOP 10 風險調整收益
    report += "\n💎 風險調整收益 TOP 10:\n"
    report += "-" * 60 + "\n"
    for i, result in enumerate(sorted_by_risk_adj[:10], 1):
        risk_adj = result.get('risk_adjusted_return', 0)
        take_profit_mode = result.get('take_profit_mode', 'unified_fixed')
        report += f"{i:2d}. 實驗{result['experiment_id']:3d} | 時間:{result['time_interval']} | "
        report += f"風險調整:{risk_adj:6.2f} | PNL:{result['total_pnl']:6.1f} | MDD:{result['mdd']:6.1f} | "
        report += f"參數:{result['lot1_stop_loss']}/{result['lot2_stop_loss']}/{result['lot3_stop_loss']} | "
        report += f"停利模式:{take_profit_mode}\n"

    # TOP 10 多頭PNL
    report += "\n🟢 LONG 部位 PNL TOP 10:\n"
    report += "-" * 60 + "\n"
    for i, result in enumerate(sorted_by_long_pnl[:10], 1):
        take_profit_mode = result.get('take_profit_mode', 'unified_fixed')
        report += f"{i:2d}. 實驗{result['experiment_id']:3d} | 時間:{result['time_interval']} | "
        report += f"多頭PNL:{result['long_pnl']:6.1f} | 總PNL:{result['total_pnl']:6.1f} | MDD:{result['mdd']:6.1f} | "
        report += f"參數:{result['lot1_stop_loss']}/{result['lot2_stop_loss']}/{result['lot3_stop_loss']} | "
        report += f"停利模式:{take_profit_mode}\n"

    # TOP 10 空頭PNL
    report += "\n🔴 SHORT 部位 PNL TOP 10:\n"
    report += "-" * 60 + "\n"
    for i, result in enumerate(sorted_by_short_pnl[:10], 1):
        take_profit_mode = result.get('take_profit_mode', 'unified_fixed')
        report += f"{i:2d}. 實驗{result['experiment_id']:3d} | 時間:{result['time_interval']} | "
        report += f"空頭PNL:{result['short_pnl']:6.1f} | 總PNL:{result['total_pnl']:6.1f} | MDD:{result['mdd']:6.1f} | "
        report += f"參數:{result['lot1_stop_loss']}/{result['lot2_stop_loss']}/{result['lot3_stop_loss']} | "
        report += f"停利模式:{take_profit_mode}\n"

    return report

def run_experiment_thread(params):
    """原始實驗執行函數（保持向後兼容）"""
    return run_experiment_thread_unified(params)

def create_temp_config(params):
    """建立臨時配置"""
    # 計算組合數量
    lot1_count = len(params['stop_loss_ranges']['lot1'])
    lot2_count = len(params['stop_loss_ranges']['lot2'])
    lot3_count = len(params['stop_loss_ranges']['lot3'])
    unified_count = len(params['take_profit_ranges']['unified'])
    individual_count = len(params['take_profit_ranges']['individual'])
    time_interval_count = len(params['time_intervals'])

    # 計算總組合數（停損組合 × 停利模式 × 時間區間）
    stop_loss_combinations = lot1_count * lot2_count * lot3_count
    take_profit_combinations = unified_count + individual_count + 1  # +1 for range_boundary
    total_combinations = stop_loss_combinations * take_profit_combinations * time_interval_count

    return {
        'analysis_mode': 'per_time_interval',
        'stop_loss_ranges': params['stop_loss_ranges'],
        'take_profit_modes': ['unified_fixed', 'individual_fixed', 'range_boundary'],
        'take_profit_ranges': params['take_profit_ranges'],
        'time_intervals': [tuple(interval) for interval in params['time_intervals']],
        'entry_price_mode': params.get('entry_price_mode', 'range_boundary'),
        'estimated_combinations': {
            'per_interval_analysis': total_combinations,
            'breakdown': f'{stop_loss_combinations} 停損組合 × {take_profit_combinations} 停利模式 × {time_interval_count} 時間區間 = {total_combinations} 總組合 (進場方式: {params.get("entry_price_mode", "range_boundary")}) (GUI 自定義)'
        }
    }

# 備份原始配置
original_config_backup = None

def modify_config_temporarily(config_data):
    """暫時修改配置檔案"""
    global original_config_backup
    
    config_file = 'mdd_search_config.py'
    
    # 備份原始檔案
    with open(config_file, 'r', encoding='utf-8') as f:
        original_config_backup = f.read()
    
    # 讀取原始檔案並修改 get_time_interval_analysis_config 函數
    lines = original_config_backup.split('\n')
    modified_lines = []
    in_function = False
    brace_count = 0
    
    for line in lines:
        if 'def get_time_interval_analysis_config():' in line:
            in_function = True
            modified_lines.append(line)
            modified_lines.append('        """時間區間分析配置 - GUI 自定義配置"""')
            modified_lines.append(f'        return {repr(config_data)}')
            continue
        
        if in_function:
            if 'return {' in line:
                brace_count = line.count('{') - line.count('}')
                continue
            elif brace_count > 0:
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0:
                    in_function = False
                continue
            elif line.strip() == '' or line.strip().startswith('#'):
                continue
            elif not line.startswith('    '):
                in_function = False
        
        modified_lines.append(line)
    
    # 寫入修改後的檔案
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(modified_lines))

def restore_original_config():
    """恢復原始配置"""
    global original_config_backup

    if original_config_backup:
        with open('mdd_search_config.py', 'w', encoding='utf-8') as f:
            f.write(original_config_backup)
        original_config_backup = None

def parse_experiment_results(log_content):
    """解析實驗結果"""
    results = {
        'time_intervals': [],
        'recommendations': [],
        'mdd_top10': [],
        'risk_adjusted_top10': [],
        'long_pnl_top10': [],
        'short_pnl_top10': []
    }

    lines = log_content.split('\n')
    current_interval = None
    parsing_time_intervals = False
    parsing_mdd_top10 = False
    parsing_risk_top10 = False
    parsing_long_pnl_top10 = False
    parsing_short_pnl_top10 = False

    for line in lines:
        # 檢查是否開始解析時間區間分析
        if '📊 各時間區間 MDD 最佳前3名:' in line:
            parsing_time_intervals = True
            parsing_mdd_top10 = False
            parsing_risk_top10 = False
            parsing_long_pnl_top10 = False
            parsing_short_pnl_top10 = False
            print(f"[DEBUG] 開始解析時間區間分析")
            continue
        elif line.startswith('🕐 時間區間:') and parsing_time_intervals:
            # 解析時間區間標題
            interval = line.replace('🕐 時間區間:', '').strip()
            current_interval = {
                'time': interval,  # 前端期望的字段名
                'interval': interval,  # 保持兼容性
                'top3': [],
                'configs': []  # 前端期望的字段名
            }
            results['time_intervals'].append(current_interval)
            print(f"[DEBUG] 發現時間區間: {interval}")
            continue
        elif parsing_time_intervals and current_interval and line.strip() and (line.strip().startswith('1.') or line.strip().startswith('2.') or line.strip().startswith('3.')):
            # 解析時間區間的前3名
            try:
                if 'MDD:' in line and 'PNL:' in line:
                    # 提取數據
                    mdd_match = line.split('MDD:')[1].split('|')[0].strip() if 'MDD:' in line else '0'
                    pnl_match = line.split('PNL:')[1].split('|')[0].strip() if 'PNL:' in line else '0'
                    params_match = line.split('參數:')[1].split('|')[0].strip() if '參數:' in line else ''
                    long_pnl_match = line.split('多頭:')[1].split('|')[0].strip() if '多頭:' in line else '0'
                    short_pnl_match = line.split('空頭:')[1].split('|')[0].strip() if '空頭:' in line else '0'

                    # 提取停利模式信息
                    take_profit_mode = 'unified_fixed'  # 預設值
                    if '停利模式:' in line:
                        take_profit_mode = line.split('停利模式:')[1].strip()

                    # 添加到 top3 (保持兼容性)
                    current_interval['top3'].append({
                        'rank': len(current_interval['top3']) + 1,
                        'mdd': mdd_match,
                        'pnl': pnl_match,
                        'params': params_match,
                        'long_pnl': long_pnl_match,
                        'short_pnl': short_pnl_match,
                        'take_profit_mode': take_profit_mode,  # 添加停利模式信息
                        'raw_line': line
                    })

                    # 根據停利模式判斷停利類型顯示
                    stop_profit_type = '統一停利'  # 預設
                    if take_profit_mode == 'range_boundary':
                        stop_profit_type = '區間邊緣停利'
                    elif take_profit_mode == 'individual_fixed':
                        stop_profit_type = '各口獨立停利'
                    elif take_profit_mode == 'unified_fixed':
                        stop_profit_type = '統一停利'

                    # 添加到 configs (前端期望的格式)
                    current_interval['configs'].append({
                        'type': stop_profit_type,
                        'take_profit_mode': take_profit_mode,  # 添加停利模式信息
                        'mdd': float(mdd_match) if mdd_match else 0,
                        'pnl': float(pnl_match) if pnl_match else 0,
                        'params': params_match
                    })
                    print(f"[DEBUG] 解析時間區間數據: MDD={mdd_match}, PNL={pnl_match}")
            except Exception as e:
                print(f"[DEBUG] 時間區間解析錯誤: {e}, 行內容: {line}")
                pass
            continue
        # 檢查是否開始解析 TOP 10 結果
        elif '🏆 MDD 最小 TOP 10:' in line or '🏆 MDD最小 TOP 10:' in line:
            parsing_time_intervals = False
            parsing_mdd_top10 = True
            parsing_risk_top10 = False
            parsing_long_pnl_top10 = False
            parsing_short_pnl_top10 = False
            print(f"[DEBUG] 開始解析 MDD TOP 10")
            continue
        elif '💎 風險調整收益 TOP 10' in line:
            parsing_time_intervals = False
            parsing_mdd_top10 = False
            parsing_risk_top10 = True
            parsing_long_pnl_top10 = False
            parsing_short_pnl_top10 = False
            print(f"[DEBUG] 開始解析風險調整收益 TOP 10")
            continue
        elif '🟢 LONG 部位 PNL TOP 10:' in line:
            parsing_time_intervals = False
            parsing_mdd_top10 = False
            parsing_risk_top10 = False
            parsing_long_pnl_top10 = True
            parsing_short_pnl_top10 = False
            print(f"[DEBUG] 開始解析 LONG PNL TOP 10")
            continue
        elif '🔴 SHORT 部位 PNL TOP 10:' in line:
            parsing_time_intervals = False
            parsing_mdd_top10 = False
            parsing_risk_top10 = False
            parsing_long_pnl_top10 = False
            parsing_short_pnl_top10 = True
            print(f"[DEBUG] 開始解析 SHORT PNL TOP 10")
            continue
        elif '============================================================' in line or '================================================================================' in line:
            parsing_time_intervals = False
            parsing_mdd_top10 = False
            parsing_risk_top10 = False
            parsing_long_pnl_top10 = False
            parsing_short_pnl_top10 = False
        elif '📈 預期每日總計:' in line:
            parsing_time_intervals = False
            parsing_mdd_top10 = False
            parsing_risk_top10 = False
            parsing_long_pnl_top10 = False
            parsing_short_pnl_top10 = False

        # 解析 MDD TOP 10
        if parsing_mdd_top10 and 'MDD:' in line and ('總P&L:' in line or 'P&L:' in line or 'PNL:' in line):
            try:
                # 處理 [MDD GUI] 前綴
                line_clean = line.strip()
                if '[MDD GUI]' in line_clean:
                    line_clean = line_clean.split('[MDD GUI]')[1].strip()

                # 移除 INFO 等日誌前綴
                if 'INFO -' in line_clean:
                    line_clean = line_clean.split('INFO -')[1].strip()

                print(f"[DEBUG] 解析 MDD TOP 10 行: {line_clean}")

                if line_clean:
                    # 提取排名
                    rank_match = line_clean.split('.')[0].strip()
                    if rank_match.isdigit():
                        rank = rank_match

                        # 提取 MDD
                        mdd_match = None
                        if 'MDD:' in line:
                            mdd_part = line.split('MDD:')[1].split('|')[0].strip() if '|' in line.split('MDD:')[1] else line.split('MDD:')[1].strip()
                            try:
                                mdd_match = float(mdd_part)
                            except:
                                pass

                        # 提取 P&L
                        pnl_match = None
                        if '總P&L:' in line:
                            pnl_part = line.split('總P&L:')[1].split('|')[0].strip() if '|' in line.split('總P&L:')[1] else line.split('總P&L:')[1].strip()
                        elif '總PNL:' in line:
                            pnl_part = line.split('總PNL:')[1].split('|')[0].strip() if '|' in line.split('總PNL:')[1] else line.split('總PNL:')[1].strip()
                        elif 'P&L:' in line:
                            pnl_part = line.split('P&L:')[1].split('|')[0].strip() if '|' in line.split('P&L:')[1] else line.split('P&L:')[1].strip()
                        elif 'PNL:' in line:
                            pnl_part = line.split('PNL:')[1].split('|')[0].strip() if '|' in line.split('PNL:')[1] else line.split('PNL:')[1].strip()
                        else:
                            pnl_part = ''

                        if pnl_part:
                            try:
                                pnl_match = float(pnl_part)
                            except:
                                pass

                        # 提取 LONG PNL
                        long_pnl_match = None
                        if 'LONG:' in line:
                            long_pnl_part = line.split('LONG:')[1].split('|')[0].strip() if '|' in line.split('LONG:')[1] else line.split('LONG:')[1].strip()
                            try:
                                long_pnl_match = float(long_pnl_part)
                            except:
                                pass
                        elif '多頭:' in line:
                            long_pnl_part = line.split('多頭:')[1].split('|')[0].strip() if '|' in line.split('多頭:')[1] else line.split('多頭:')[1].strip()
                            try:
                                long_pnl_match = float(long_pnl_part)
                            except:
                                pass

                        # 提取 SHORT PNL
                        short_pnl_match = None
                        if 'SHORT:' in line:
                            short_pnl_part = line.split('SHORT:')[1].split('|')[0].strip() if '|' in line.split('SHORT:')[1] else line.split('SHORT:')[1].strip()
                            try:
                                short_pnl_match = float(short_pnl_part)
                            except:
                                pass
                        elif '空頭:' in line:
                            short_pnl_part = line.split('空頭:')[1].split('|')[0].strip() if '|' in line.split('空頭:')[1] else line.split('空頭:')[1].strip()
                            try:
                                short_pnl_match = float(short_pnl_part)
                            except:
                                pass

                        if mdd_match is not None and pnl_match is not None:
                            # 提取時間區間
                            import re
                            time_match = re.search(r'時間:([^|]+)', line)
                            time_interval = time_match.group(1).strip() if time_match else ''

                            # 提取參數
                            params_match = re.search(r'參數:([^|]+)', line)
                            params = params_match.group(1).strip() if params_match else ''

                            # 提取停利模式
                            take_profit_mode = 'unified_fixed'  # 預設值
                            if '停利模式:' in line:
                                take_profit_mode = line.split('停利模式:')[1].strip()

                            results['mdd_top10'].append({
                                'rank': rank,
                                'mdd': mdd_match,
                                'pnl': pnl_match,
                                'long_pnl': long_pnl_match if long_pnl_match is not None else 0,
                                'short_pnl': short_pnl_match if short_pnl_match is not None else 0,
                                'params': params,
                                'take_profit_mode': take_profit_mode,  # 添加停利模式信息
                                'strategy': '統一停利',  # 保持向後兼容
                                'time': time_interval
                            })
                            print(f"[DEBUG] 成功解析 MDD TOP 10: 排名={rank}, MDD={mdd_match}, PNL={pnl_match}, 時間={time_interval}")
            except Exception as e:
                print(f"[DEBUG] MDD TOP 10 解析錯誤: {e}, 行內容: {line}")
                pass

        # 解析風險調整收益 TOP 10
        elif parsing_risk_top10 and ('風險調整收益:' in line or '風險調整:' in line) and 'MDD:' in line:
            try:
                # 處理 [MDD GUI] 前綴
                line_clean = line.strip()
                if '[MDD GUI]' in line_clean:
                    line_clean = line_clean.split('[MDD GUI]')[1].strip()

                # 移除 INFO 等日誌前綴
                if 'INFO -' in line_clean:
                    line_clean = line_clean.split('INFO -')[1].strip()

                print(f"[DEBUG] 解析風險調整收益 TOP 10 行: {line_clean}")

                if line_clean:
                    # 提取排名
                    rank_match = line_clean.split('.')[0].strip()
                    if rank_match.isdigit():
                        rank = rank_match

                        # 提取風險調整收益
                        ratio_match = None
                        if '風險調整收益:' in line:
                            ratio_part = line.split('風險調整收益:')[1].split('|')[0].strip() if '|' in line.split('風險調整收益:')[1] else line.split('風險調整收益:')[1].strip()
                            try:
                                ratio_match = float(ratio_part)
                            except:
                                pass
                        elif '風險調整:' in line:
                            ratio_part = line.split('風險調整:')[1].split('|')[0].strip() if '|' in line.split('風險調整:')[1] else line.split('風險調整:')[1].strip()
                            try:
                                ratio_match = float(ratio_part)
                            except:
                                pass

                        # 提取 MDD
                        mdd_match = None
                        if 'MDD:' in line:
                            mdd_part = line.split('MDD:')[1].split('|')[0].strip() if '|' in line.split('MDD:')[1] else line.split('MDD:')[1].strip()
                            try:
                                mdd_match = float(mdd_part)
                            except:
                                pass

                        # 提取 P&L
                        pnl_match = None
                        if '總P&L:' in line:
                            pnl_part = line.split('總P&L:')[1].split('|')[0].strip() if '|' in line.split('總P&L:')[1] else line.split('總P&L:')[1].strip()
                        elif 'P&L:' in line:
                            pnl_part = line.split('P&L:')[1].split('|')[0].strip() if '|' in line.split('P&L:')[1] else line.split('P&L:')[1].strip()
                        else:
                            pnl_part = ''

                        if pnl_part:
                            try:
                                pnl_match = float(pnl_part)
                            except:
                                pass

                        # 提取 LONG PNL
                        long_pnl_match = None
                        if 'LONG:' in line:
                            long_pnl_part = line.split('LONG:')[1].split('|')[0].strip() if '|' in line.split('LONG:')[1] else line.split('LONG:')[1].strip()
                            try:
                                long_pnl_match = float(long_pnl_part)
                            except:
                                pass

                        # 提取 SHORT PNL
                        short_pnl_match = None
                        if 'SHORT:' in line:
                            short_pnl_part = line.split('SHORT:')[1].split('|')[0].strip() if '|' in line.split('SHORT:')[1] else line.split('SHORT:')[1].strip()
                            try:
                                short_pnl_match = float(short_pnl_part)
                            except:
                                pass

                        if ratio_match is not None and mdd_match is not None and pnl_match is not None:
                            # 提取其他信息 - 格式變為: 風險調整收益 | MDD | 總P&L | LONG | SHORT | 參數 | 策略
                            parts = line.split('|')
                            params_part = parts[5].strip() if len(parts) > 5 else ''
                            strategy_part = parts[6].strip() if len(parts) > 6 else ''

                            results['risk_adjusted_top10'].append({
                                'rank': rank,
                                'ratio': ratio_match,
                                'mdd': mdd_match,
                                'pnl': pnl_match,
                                'long_pnl': long_pnl_match if long_pnl_match is not None else 0,
                                'short_pnl': short_pnl_match if short_pnl_match is not None else 0,
                                'params': params_part,
                                'strategy': strategy_part
                            })
            except Exception as e:
                print(f"[DEBUG] 風險調整收益 TOP 10 解析錯誤: {e}, 行內容: {line}")
                pass

        # 解析 LONG PNL TOP 10
        elif parsing_long_pnl_top10 and ('LONG:' in line or '多頭PNL:' in line) and ('總P&L:' in line or 'P&L:' in line or 'PNL:' in line):
            try:
                # 處理 [MDD GUI] 前綴
                line_clean = line.strip()
                if '[MDD GUI]' in line_clean:
                    line_clean = line_clean.split('[MDD GUI]')[1].strip()

                # 移除 INFO 等日誌前綴
                if 'INFO -' in line_clean:
                    line_clean = line_clean.split('INFO -')[1].strip()

                print(f"[DEBUG] 解析 LONG PNL TOP 10 行: {line_clean}")

                if line_clean:
                    # 提取排名
                    rank_match = line_clean.split('.')[0].strip()
                    if rank_match.isdigit():
                        rank = rank_match

                        # 提取 LONG PNL
                        long_pnl_match = None
                        if 'LONG:' in line:
                            long_pnl_part = line.split('LONG:')[1].split('|')[0].strip() if '|' in line.split('LONG:')[1] else line.split('LONG:')[1].strip()
                            try:
                                long_pnl_match = float(long_pnl_part)
                            except:
                                pass
                        elif '多頭PNL:' in line:
                            long_pnl_part = line.split('多頭PNL:')[1].split('|')[0].strip() if '|' in line.split('多頭PNL:')[1] else line.split('多頭PNL:')[1].strip()
                            try:
                                long_pnl_match = float(long_pnl_part)
                            except:
                                pass

                        # 提取總 P&L
                        pnl_match = None
                        if '總P&L:' in line:
                            pnl_part = line.split('總P&L:')[1].split('|')[0].strip() if '|' in line.split('總P&L:')[1] else line.split('總P&L:')[1].strip()
                        elif '總PNL:' in line:
                            pnl_part = line.split('總PNL:')[1].split('|')[0].strip() if '|' in line.split('總PNL:')[1] else line.split('總PNL:')[1].strip()
                        elif 'P&L:' in line:
                            pnl_part = line.split('P&L:')[1].split('|')[0].strip() if '|' in line.split('P&L:')[1] else line.split('P&L:')[1].strip()
                        elif 'PNL:' in line:
                            pnl_part = line.split('PNL:')[1].split('|')[0].strip() if '|' in line.split('PNL:')[1] else line.split('PNL:')[1].strip()
                        else:
                            pnl_part = ''

                        if pnl_part:
                            try:
                                pnl_match = float(pnl_part)
                            except:
                                pass

                        # 提取 SHORT PNL
                        short_pnl_match = None
                        if 'SHORT:' in line:
                            short_pnl_part = line.split('SHORT:')[1].split('|')[0].strip() if '|' in line.split('SHORT:')[1] else line.split('SHORT:')[1].strip()
                            try:
                                short_pnl_match = float(short_pnl_part)
                            except:
                                pass

                        if long_pnl_match is not None and pnl_match is not None:
                            # 提取其他信息
                            parts = line.split('|')
                            params_part = parts[3].strip() if len(parts) > 3 else ''
                            strategy_part = parts[4].strip() if len(parts) > 4 else ''
                            time_part = parts[5].strip() if len(parts) > 5 else ''

                            results['long_pnl_top10'].append({
                                'rank': rank,
                                'long_pnl': long_pnl_match,
                                'pnl': pnl_match,
                                'short_pnl': short_pnl_match if short_pnl_match is not None else 0,
                                'params': params_part,
                                'strategy': strategy_part,
                                'time': time_part
                            })
            except Exception as e:
                print(f"[DEBUG] LONG PNL TOP 10 解析錯誤: {e}, 行內容: {line}")
                pass

        # 解析 SHORT PNL TOP 10
        elif parsing_short_pnl_top10 and ('SHORT:' in line or '空頭PNL:' in line) and ('總P&L:' in line or 'P&L:' in line or 'PNL:' in line):
            try:
                # 處理 [MDD GUI] 前綴
                line_clean = line.strip()
                if '[MDD GUI]' in line_clean:
                    line_clean = line_clean.split('[MDD GUI]')[1].strip()

                # 移除 INFO 等日誌前綴
                if 'INFO -' in line_clean:
                    line_clean = line_clean.split('INFO -')[1].strip()

                print(f"[DEBUG] 解析 SHORT PNL TOP 10 行: {line_clean}")

                if line_clean:
                    # 提取排名
                    rank_match = line_clean.split('.')[0].strip()
                    if rank_match.isdigit():
                        rank = rank_match

                        # 提取 SHORT PNL
                        short_pnl_match = None
                        if 'SHORT:' in line:
                            short_pnl_part = line.split('SHORT:')[1].split('|')[0].strip() if '|' in line.split('SHORT:')[1] else line.split('SHORT:')[1].strip()
                            try:
                                short_pnl_match = float(short_pnl_part)
                            except:
                                pass
                        elif '空頭PNL:' in line:
                            short_pnl_part = line.split('空頭PNL:')[1].split('|')[0].strip() if '|' in line.split('空頭PNL:')[1] else line.split('空頭PNL:')[1].strip()
                            try:
                                short_pnl_match = float(short_pnl_part)
                            except:
                                pass

                        # 提取總 P&L
                        pnl_match = None
                        if '總P&L:' in line:
                            pnl_part = line.split('總P&L:')[1].split('|')[0].strip() if '|' in line.split('總P&L:')[1] else line.split('總P&L:')[1].strip()
                        elif '總PNL:' in line:
                            pnl_part = line.split('總PNL:')[1].split('|')[0].strip() if '|' in line.split('總PNL:')[1] else line.split('總PNL:')[1].strip()
                        elif 'P&L:' in line:
                            pnl_part = line.split('P&L:')[1].split('|')[0].strip() if '|' in line.split('P&L:')[1] else line.split('P&L:')[1].strip()
                        elif 'PNL:' in line:
                            pnl_part = line.split('PNL:')[1].split('|')[0].strip() if '|' in line.split('PNL:')[1] else line.split('PNL:')[1].strip()
                        else:
                            pnl_part = ''

                        if pnl_part:
                            try:
                                pnl_match = float(pnl_part)
                            except:
                                pass

                        # 提取 LONG PNL
                        long_pnl_match = None
                        if 'LONG:' in line:
                            long_pnl_part = line.split('LONG:')[1].split('|')[0].strip() if '|' in line.split('LONG:')[1] else line.split('LONG:')[1].strip()
                            try:
                                long_pnl_match = float(long_pnl_part)
                            except:
                                pass

                        if short_pnl_match is not None and pnl_match is not None:
                            # 提取其他信息
                            parts = line.split('|')
                            params_part = parts[3].strip() if len(parts) > 3 else ''
                            strategy_part = parts[4].strip() if len(parts) > 4 else ''
                            time_part = parts[5].strip() if len(parts) > 5 else ''

                            results['short_pnl_top10'].append({
                                'rank': rank,
                                'short_pnl': short_pnl_match,
                                'pnl': pnl_match,
                                'long_pnl': long_pnl_match if long_pnl_match is not None else 0,
                                'params': params_part,
                                'strategy': strategy_part,
                                'time': time_part
                            })
            except Exception as e:
                print(f"[DEBUG] SHORT PNL TOP 10 解析錯誤: {e}, 行內容: {line}")
                pass

        # 解析時間區間結果
        elif '🕙' in line and '最佳配置:' in line:
            # 處理 [MDD GUI] 前綴
            line_clean = line.strip()
            if '[MDD GUI]' in line_clean:
                line_clean = line_clean.split('[MDD GUI]')[1].strip()
            if 'INFO -' in line_clean:
                line_clean = line_clean.split('INFO -')[1].strip()

            print(f"[DEBUG] 解析時間區間: {line_clean}")

            # 提取時間
            for part in line_clean.split():
                if ':' in part and '-' in part and len(part) == 11:  # 格式：10:30-10:32
                    current_interval = {
                        'time': part,
                        'configs': []
                    }
                    results['time_intervals'].append(current_interval)
                    print(f"[DEBUG] 找到時間區間: {part}")
                    break

        # 解析配置結果
        elif current_interval and 'MDD:' in line and 'P&L:' in line and not parsing_mdd_top10 and not parsing_risk_top10:
            # 處理 [MDD GUI] 前綴
            line_clean = line.strip()
            if '[MDD GUI]' in line_clean:
                line_clean = line_clean.split('[MDD GUI]')[1].strip()
            if 'INFO -' in line_clean:
                line_clean = line_clean.split('INFO -')[1].strip()

            print(f"[DEBUG] 解析配置結果: {line_clean}")

            parts = line_clean.split('|')
            if len(parts) >= 3:
                try:
                    # 修復：正確提取停利類型
                    first_part = parts[0].strip()
                    # 移除時間戳，只保留停利類型
                    if ':' in first_part:
                        type_parts = first_part.split(':')
                        # 找到不包含數字的部分作為類型
                        for part in type_parts:
                            if not any(char.isdigit() for char in part) and part.strip():
                                type_part = part.strip()
                                break
                        else:
                            type_part = type_parts[-1].strip()
                    else:
                        type_part = first_part

                    mdd_part = first_part.split('MDD:')[1].strip() if 'MDD:' in first_part else ''
                    pnl_part = parts[1].split('P&L:')[1].strip() if 'P&L:' in parts[1] else ''
                    params_part = '|'.join(parts[2:]).strip()

                    if mdd_part and pnl_part:
                        current_interval['configs'].append({
                            'type': type_part,
                            'mdd': float(mdd_part),
                            'pnl': float(pnl_part),
                            'params': params_part
                        })
                except:
                    pass

        # 解析推薦
        elif current_interval and '⭐ 推薦:' in line:
            rec_part = line.split('⭐ 推薦:')[1].strip()
            current_interval['recommendation'] = rec_part.split('(')[0].strip()

        # 解析一日配置建議
        elif ':' in line and 'MDD:' in line and 'P&L:' in line and not parsing_mdd_top10 and not parsing_risk_top10:
            # 處理 [MDD GUI] 前綴
            line_clean = line.strip()
            if '[MDD GUI]' in line_clean:
                line_clean = line_clean.split('[MDD GUI]')[1].strip()
            if 'INFO -' in line_clean:
                line_clean = line_clean.split('INFO -')[1].strip()

            # 排除時間戳行
            if not line_clean.startswith('2025-') and not line_clean.startswith('['):
                print(f"[DEBUG] 解析一日配置建議: {line_clean}")

                try:
                    # 提取時間
                    time_part = ''
                    for part in line_clean.split():
                        if ':' in part and '-' in part and len(part) == 11:  # 格式：10:30-10:32
                            time_part = part.rstrip(':')
                            break

                    if time_part:
                        # 提取MDD和P&L
                        mdd_match = line_clean.split('MDD:')[1].split(',')[0] if 'MDD:' in line_clean else ''
                        pnl_match = line_clean.split('P&L:')[1].split(')')[0] if 'P&L:' in line_clean else ''

                        # 提取策略和參數
                        content = line_clean.split(':')[1].split('(MDD:')[0] if ':' in line_clean else ''
                        content_parts = content.split(',')

                        if mdd_match and pnl_match:
                            results['recommendations'].append({
                                'time': time_part,
                                'type': content_parts[0].strip() if content_parts else '',
                                'params': content_parts[1].strip() if len(content_parts) > 1 else '',
                                'mdd': float(mdd_match),
                                'pnl': float(pnl_match)
                            })
                            print(f"[DEBUG] 找到一日配置建議: {time_part}")
                except Exception as e:
                    print(f"[DEBUG] 一日配置建議解析錯誤: {e}")
                    pass

    return results

@app.route('/status')
def get_status():
    """獲取執行狀態"""
    global experiment_status
    
    if experiment_status['running']:
        status = 'running'
        message = f"實驗執行中... (已執行 {(datetime.now() - experiment_status['start_time']).seconds} 秒)"
    elif experiment_status['completed']:
        status = 'completed'
        message = '實驗執行完成！'
    elif experiment_status['error']:
        status = 'error'
        message = f"執行錯誤: {experiment_status['error']}"
    else:
        status = 'ready'
        message = '就緒 - 請設定參數後執行實驗'
    
    return jsonify({
        'status': status,
        'message': message,
        'log_content': experiment_status['log_content'],
        'parsed_results': experiment_status.get('parsed_results')
    })

@app.route('/stop_experiment', methods=['POST'])
def stop_experiment():
    """停止實驗"""
    global experiment_status
    experiment_status['running'] = False
    experiment_status['error'] = '用戶手動停止'
    return jsonify({'status': 'stopped'})

@app.route('/results')
def view_results():
    """查看結果"""
    results_dir = Path('results')
    if not results_dir.exists():
        return "結果目錄不存在"
    
    # 找最新的 time_interval_analysis 結果檔案
    result_files = list(results_dir.glob('enhanced_mdd_results_time_interval_analysis_*.csv'))
    if not result_files:
        return "沒有找到結果檔案"
    
    latest_file = max(result_files, key=lambda f: f.stat().st_mtime)
    
    # 簡單的結果顯示
    html = f"""
    <html>
    <head><title>MDD 優化結果</title></head>
    <body>
        <h1>最新 MDD 優化結果</h1>
        <p>檔案: {latest_file.name}</p>
        <p>修改時間: {datetime.fromtimestamp(latest_file.stat().st_mtime)}</p>
        <p><a href="/download_result/{latest_file.name}">下載結果檔案</a></p>
        <p><a href="javascript:window.close()">關閉視窗</a></p>
    </body>
    </html>
    """
    return html

@app.route('/download_result/<filename>')
def download_result(filename):
    """下載結果檔案"""
    results_dir = Path('results')
    file_path = results_dir / filename
    if file_path.exists():
        return send_file(str(file_path), as_attachment=True)
    else:
        return "檔案不存在", 404

if __name__ == '__main__':
    print("🚀 MDD 優化器 GUI 啟動中...")
    print("請在瀏覽器中開啟: http://localhost:8081")
    print("按 Ctrl+C 停止服務")

    # 關閉 debug 模式避免檔案修改時重啟
    app.run(host='localhost', port=8081, debug=False)
