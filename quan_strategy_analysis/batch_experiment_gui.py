#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批次實驗 Web GUI 界面
基於 Flask 的 Web 界面，用於控制和監控批次實驗
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import threading
import json
import os
from datetime import datetime
import logging
from pathlib import Path

from parameter_matrix_generator import ExperimentConfig, ParameterMatrixGenerator
from batch_backtest_engine import BatchBacktestEngine, ResultDatabase
from experiment_analyzer import ExperimentAnalyzer
from long_short_separation_analyzer import LongShortSeparationAnalyzer

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'batch_experiment_secret_key'

# 全域變量
batch_engine = None
experiment_thread = None
current_config = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>批次實驗控制台</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; margin: 5px; }
        .btn-primary { background-color: #007bff; color: white; }
        .btn-success { background-color: #28a745; color: white; }
        .btn-danger { background-color: #dc3545; color: white; }
        .btn-info { background-color: #17a2b8; color: white; }
        .btn:hover { opacity: 0.8; }
        .progress-container { background: #f0f0f0; border-radius: 10px; padding: 10px; margin: 10px 0; }
        .progress-bar { background: #007bff; height: 20px; border-radius: 10px; transition: width 0.3s; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }
        .status-card { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .status-value { font-size: 24px; font-weight: bold; color: #2e7d32; }
        .status-label { font-size: 12px; color: #666; margin-top: 5px; }
        .log-container { background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 5px; height: 300px; overflow-y: auto; font-family: monospace; }
        .results-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }
        .results-table th, .results-table td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        .results-table th { background-color: #4CAF50; color: white; }
        .results-table td:nth-child(3) { font-family: monospace; color: #666; font-size: 12px; } /* 時間區間欄位 */
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 批次實驗控制台</h1>
            <p>大規模參數優化實驗系統</p>
        </div>

        <!-- 實驗配置 -->
        <div class="card">
            <h2>⚙️ 實驗配置</h2>
            <form id="configForm">
                <div class="form-row">
                    <div class="form-group">
                        <label>開始日期:</label>
                        <input type="date" id="startDate" value="2024-11-04">
                    </div>
                    <div class="form-group">
                        <label>結束日期:</label>
                        <input type="date" id="endDate" value="2025-06-28">
                    </div>
                </div>

                <!-- 動態時間區間設定 -->
                <div class="form-group">
                    <label>時間區間設定:</label>
                    <div id="timeRangeContainer">
                        <div class="time-range-item" style="display: flex; align-items: center; margin-bottom: 10px;">
                            <input type="time" class="range-start" value="08:46" style="margin-right: 10px;">
                            <span style="margin-right: 10px;">-</span>
                            <input type="time" class="range-end" value="08:47" style="margin-right: 10px;">
                            <button type="button" class="btn-remove" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">❌</button>
                        </div>
                    </div>
                    <button type="button" id="addTimeRangeBtn" class="btn btn-secondary" style="background: #6c757d; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px;">➕ 添加時間區間</button>
                </div>

                <!-- 交易方向配置 -->
                <div class="form-group">
                    <label for="tradingDirection">🎯 交易方向:</label>
                    <select id="tradingDirection" class="form-control">
                        <option value="BOTH">都跑（多空都做）</option>
                        <option value="LONG_ONLY">只做多</option>
                        <option value="SHORT_ONLY">只做空</option>
                        <option value="ALL_MODES">全模式（多空+都跑）</option>
                    </select>
                    <small style="color: #666; display: block; margin-top: 5px;">
                        選擇只做多或只做空可獲得真正的單向策略回測結果（包含準確的MDD和勝率）
                    </small>
                </div>

                <h3>📊 參數範圍設定</h3>
                <div class="form-row">
                    <div class="form-group">
                        <label>第1口觸發點範圍:</label>
                        <input type="text" id="lot1TriggerRange" value="15-25" placeholder="例: 15-25">
                    </div>
                    <div class="form-group">
                        <label>第1口回檔範圍(%):</label>
                        <input type="text" id="lot1TrailingRange" value="10" placeholder="例: 10 或 10-20">
                    </div>
                    <div class="form-group">
                        <label>第2口觸發點範圍:</label>
                        <input type="text" id="lot2TriggerRange" value="35-45" placeholder="例: 35-45">
                    </div>
                    <div class="form-group">
                        <label>第2口回檔範圍(%):</label>
                        <input type="text" id="lot2TrailingRange" value="10" placeholder="例: 10 或 10-20">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>第3口觸發點範圍:</label>
                        <input type="text" id="lot3TriggerRange" value="40-50" placeholder="例: 40-50">
                    </div>
                    <div class="form-group">
                        <label>第3口回檔範圍(%):</label>
                        <input type="text" id="lot3TrailingRange" value="20" placeholder="例: 20 或 10-30">
                    </div>
                    <div class="form-group">
                        <label>保護係數:</label>
                        <input type="text" id="protectionRange" value="2.0" placeholder="例: 2.0">
                    </div>
                    <div class="form-group">
                        <label>最大並行數 (建議: 2-6):</label>
                        <input type="number" id="maxParallel" value="4" min="1" max="8">
                        <small style="color: #666; display: block; margin-top: 5px;">
                            您的系統有 8 核心，建議設定 2-6 以平衡速度與穩定性
                        </small>
                    </div>
                </div>

                <div class="form-row">
                    <button type="button" class="btn btn-success" id="startBtn">🚀 開始實驗</button>
                    <button type="button" class="btn btn-danger" id="stopBtn" disabled>⏹️ 停止實驗</button>
                    <button type="button" class="btn btn-info" id="generateReportBtn">📊 生成報告</button>
                    <button type="button" class="btn btn-warning" id="generateCSVBtn">📋 導出CSV</button>
                </div>
                <div class="form-row" style="margin-top: 10px;">
                    <button type="button" class="btn btn-primary" id="generateLongReportBtn">📈 多方報告</button>
                    <button type="button" class="btn btn-secondary" id="generateShortReportBtn">📉 空方報告</button>
                    <button type="button" class="btn btn-dark" id="generateBothReportsBtn">📊 多空分離報告</button>
                    <button type="button" class="btn btn-success" id="generateAllReportsBtn">🎯 自動生成全套報告</button>
                    <button type="button" class="btn btn-warning" id="generateAllHTMLReportsBtn">📊 自動生成HTML報告</button>
                </div>
            </form>
        </div>

        <!-- 實驗狀態 -->
        <div class="card">
            <h2>📈 實驗狀態</h2>
            <div class="status-grid">
                <div class="status-card">
                    <div class="status-value" id="totalExperiments">0</div>
                    <div class="status-label">總實驗數</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="completedExperiments">0</div>
                    <div class="status-label">已完成</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="progressPercent">0%</div>
                    <div class="status-label">進度</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="elapsedTime">0s</div>
                    <div class="status-label">已用時間</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="eta">0s</div>
                    <div class="status-label">預計剩餘</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="bestPnl">0</div>
                    <div class="status-label">最佳損益</div>
                </div>
                <div class="status-card">
                    <div class="status-value" id="avgSpeed">0</div>
                    <div class="status-label">平均速度(秒/實驗)</div>
                </div>
            </div>
            
            <div class="progress-container">
                <div class="progress-bar" id="progressBar" style="width: 0%"></div>
            </div>
            
            <div id="currentExperiment" style="margin-top: 10px; font-weight: bold;"></div>
        </div>

        <!-- 實驗日誌 -->
        <div class="card">
            <h2>📝 實驗日誌</h2>
            <div class="log-container" id="logContainer">
                等待實驗開始...
            </div>
        </div>

        <!-- 最佳結果 -->
        <div class="card">
            <h2>🏆 實驗結果排行榜</h2>
            <div id="bestResults">
                <p>尚無結果數據</p>
            </div>
        </div>

        <!-- 各時段MDD最低前三名 -->
        <div class="card">
            <h2>⏰ 各時段 MDD 最低前三名</h2>
            <div id="timeSlotResults">
                <p>尚無時段數據</p>
            </div>
        </div>
    </div>

    <script>
        console.log('🚀 JavaScript 腳本開始載入...');

        let updateInterval;

        // 先定義 addLog 函數
        function addLog(message) {
            const logContainer = document.getElementById('logContainer');
            const timestamp = new Date().toLocaleTimeString();
            logContainer.innerHTML += `[${timestamp}] ${message}\\n`;
            logContainer.scrollTop = logContainer.scrollHeight;
        }

        // 頁面載入完成後綁定事件
        document.addEventListener('DOMContentLoaded', function() {
            console.log('✅ DOM 載入完成，開始綁定事件...');

            // 綁定開始實驗按鈕
            document.getElementById('startBtn').addEventListener('click', function() {
                console.log('🚀 開始實驗按鈕被點擊');
                startExperiments();
            });

            // 綁定停止實驗按鈕
            document.getElementById('stopBtn').addEventListener('click', function() {
                console.log('⏹️ 停止實驗按鈕被點擊');
                stopExperiments();
            });

            // 綁定生成報告按鈕
            document.getElementById('generateReportBtn').addEventListener('click', function() {
                console.log('📊 生成報告按鈕被點擊');
                generateReport();
            });

            // 綁定導出CSV按鈕
            document.getElementById('generateCSVBtn').addEventListener('click', function() {
                console.log('📋 導出CSV按鈕被點擊');
                generateAutoCSVReport();
            });

            // 綁定多方報告按鈕
            document.getElementById('generateLongReportBtn').addEventListener('click', function() {
                console.log('📈 多方報告按鈕被點擊');
                generateLongShortReports('long');
            });

            // 綁定空方報告按鈕
            document.getElementById('generateShortReportBtn').addEventListener('click', function() {
                console.log('📉 空方報告按鈕被點擊');
                generateLongShortReports('short');
            });

            // 綁定多空分離報告按鈕
            document.getElementById('generateBothReportsBtn').addEventListener('click', function() {
                console.log('📊 多空分離報告按鈕被點擊');
                generateLongShortReports('both');
            });

            // 綁定自動生成全套報告按鈕
            document.getElementById('generateAllReportsBtn').addEventListener('click', function() {
                console.log('🎯 自動生成全套報告按鈕被點擊');
                generateAllReports();
            });

            // 綁定自動生成HTML報告按鈕
            document.getElementById('generateAllHTMLReportsBtn').addEventListener('click', function() {
                console.log('📊 自動生成HTML報告按鈕被點擊');
                generateAllHTMLReports();
            });

            // 綁定添加時間區間按鈕
            document.getElementById('addTimeRangeBtn').addEventListener('click', function() {
                console.log('➕ 添加時間區間按鈕被點擊');
                addTimeRange();
            });

            // 綁定刪除時間區間按鈕（事件委託）
            document.getElementById('timeRangeContainer').addEventListener('click', function(e) {
                if (e.target.classList.contains('btn-remove')) {
                    console.log('❌ 刪除時間區間按鈕被點擊');
                    removeTimeRange(e.target);
                }
            });

            // 載入最佳結果和時段結果
            loadBestResults();
            loadTimeSlotResults();

            console.log('✅ 所有事件綁定完成');
        });

        // 時間區間相關函數
        function createTimeRangeItem() {
            const div = document.createElement('div');
            div.className = 'time-range-item';
            div.style.cssText = 'display: flex; align-items: center; margin-bottom: 10px;';

            div.innerHTML = `
                <input type="time" class="range-start" value="08:46" style="margin-right: 10px;">
                <span style="margin-right: 10px;">-</span>
                <input type="time" class="range-end" value="08:47" style="margin-right: 10px;">
                <button type="button" class="btn-remove" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">❌</button>
            `;

            return div;
        }

        function addTimeRange() {
            const container = document.getElementById('timeRangeContainer');
            const newItem = createTimeRangeItem();
            container.appendChild(newItem);
            console.log('✅ 新增時間區間');
        }

        function removeTimeRange(button) {
            const container = document.getElementById('timeRangeContainer');
            const items = container.querySelectorAll('.time-range-item');

            // 至少保留一個時間區間
            if (items.length <= 1) {
                alert('至少需要保留一個時間區間！');
                return;
            }

            button.parentElement.remove();
            console.log('✅ 刪除時間區間');
        }

        function collectTimeRanges() {
            const items = document.querySelectorAll('.time-range-item');
            const timeRanges = [];

            items.forEach((item, index) => {
                const start = item.querySelector('.range-start').value;
                const end = item.querySelector('.range-end').value;

                if (start && end) {
                    // 驗證時間格式
                    if (start >= end) {
                        throw new Error(`時間區間 ${index + 1}: 結束時間必須晚於開始時間`);
                    }
                    timeRanges.push({start, end});
                } else {
                    throw new Error(`時間區間 ${index + 1}: 請填寫完整的開始和結束時間`);
                }
            });

            return timeRanges;
        }

        function parseRange(rangeStr) {
            try {
                if (!rangeStr || rangeStr.trim() === '') {
                    console.error('❌ 空的範圍字符串:', rangeStr);
                    return [0, 0];
                }

                if (rangeStr.includes('-')) {
                    const [start, end] = rangeStr.split('-').map(x => parseFloat(x.trim()));
                    if (isNaN(start) || isNaN(end)) {
                        console.error('❌ 無效的範圍值:', rangeStr);
                        return [0, 0];
                    }
                    return [start, end];
                } else {
                    const val = parseFloat(rangeStr.trim());
                    if (isNaN(val)) {
                        console.error('❌ 無效的數值:', rangeStr);
                        return [0, 0];
                    }
                    return [val, val];
                }
            } catch (error) {
                console.error('❌ parseRange 錯誤:', error, 'input:', rangeStr);
                return [0, 0];
            }
        }



        function startExperiments() {
            console.log('🚀 開始實驗流程...');
            addLog('🔄 正在準備實驗參數...');

            try {
                // 收集時間區間數據
                const timeRanges = collectTimeRanges();
                console.log('✅ 收集到時間區間:', timeRanges);

                // 收集表單數據
                const config = {
                    start_date: document.getElementById('startDate').value,
                    end_date: document.getElementById('endDate').value,
                    time_ranges: timeRanges,
                    trading_direction: document.getElementById('tradingDirection').value,
                lot1_trigger_range: parseRange(document.getElementById('lot1TriggerRange').value),
                lot1_trailing_range: parseRange(document.getElementById('lot1TrailingRange').value),
                lot2_trigger_range: parseRange(document.getElementById('lot2TriggerRange').value),
                lot2_trailing_range: parseRange(document.getElementById('lot2TrailingRange').value),
                lot3_trigger_range: parseRange(document.getElementById('lot3TriggerRange').value),
                lot3_trailing_range: parseRange(document.getElementById('lot3TrailingRange').value),
                protection_range: parseRange(document.getElementById('protectionRange').value),
                max_parallel: parseInt(document.getElementById('maxParallel').value)
            };

            console.log('📤 發送配置:', config);
            addLog(`📊 準備測試 ${timeRanges.length} 個時間區間的參數組合`);

            // 直接啟動實驗（包含參數矩陣生成）
            fetch('/start_experiments_direct', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                    document.getElementById('totalExperiments').textContent = data.total_experiments;
                    addLog(`✅ 實驗已開始，共 ${data.total_experiments} 個實驗`);
                    startProgressUpdate();
                } else {
                    addLog(`❌ 啟動失敗: ${data.error}`);
                }
            })
            .catch(error => {
                console.error('❌ 請求錯誤:', error);
                addLog(`❌ 請求錯誤: ${error.message}`);
            });

            } catch (error) {
                console.error('❌ 時間區間驗證錯誤:', error);
                addLog(`❌ ${error.message}`);
                alert(error.message);
            }
        }
        
        function stopExperiments() {
            fetch('/stop_experiments', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                addLog('🛑 批次實驗已停止');
                stopProgressUpdate();
            });
        }
        
        function generateReport() {
            fetch('/generate_report', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog(`📊 分析報告已生成: ${data.report_file}`);
                    window.open(`/download_report?file=${data.report_file}`, '_blank');
                } else {
                    addLog(`❌ 報告生成失敗: ${data.error}`);
                }
            });
        }
        
        function startProgressUpdate() {
            updateInterval = setInterval(updateProgress, 2000);
        }
        
        function stopProgressUpdate() {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        }
        
        function updateProgress() {
            fetch('/get_progress')
            .then(response => response.json())
            .then(data => {
                document.getElementById('completedExperiments').textContent = data.completed;
                document.getElementById('progressPercent').textContent = data.progress_percent.toFixed(1) + '%';
                document.getElementById('elapsedTime').textContent = data.elapsed_time.toFixed(0) + 's';
                document.getElementById('eta').textContent = data.eta.toFixed(0) + 's';
                document.getElementById('progressBar').style.width = data.progress_percent + '%';

                // 計算平均速度
                const avgSpeed = data.completed > 0 ? (data.elapsed_time / data.completed) : 0;
                document.getElementById('avgSpeed').textContent = avgSpeed.toFixed(1);
                
                if (data.current_experiment) {
                    document.getElementById('currentExperiment').textContent =
                        `當前實驗: ${data.current_experiment.experiment_id} (${data.current_experiment.lot1_trigger}(${data.current_experiment.lot1_trailing}%)/${data.current_experiment.lot2_trigger}(${data.current_experiment.lot2_trailing}%)/${data.current_experiment.lot3_trigger}(${data.current_experiment.lot3_trailing}%))`;
                }
                
                if (data.status === 'completed') {
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                    stopProgressUpdate();
                    addLog('🏁 所有實驗已完成');
                    loadBestResults();
                    loadTimeSlotResults();  // 同時更新時段結果
                    generateAllReports();  // 🚀 修改：自動生成全套報告（包含CSV+多空分離+HTML）
                }
            });
        }
        
        function loadBestResults() {
            let html = '';

            // 載入最高總損益前10名
            fetch('/get_best_results?metric=total_pnl&ascending=false&limit=10')
            .then(response => response.json())
            .then(data => {
                if (data.success && data.results.length > 0) {
                    html += '<h3>🏆 最高總損益前10名</h3>';
                    html += '<table class="results-table"><tr><th>排名</th><th>實驗ID</th><th>交易方向</th><th>時間區間</th><th>總損益</th><th>MDD</th><th>勝率</th><th>參數</th></tr>';
                    data.results.forEach((result, index) => {
                        const params = JSON.parse(result.parameters);
                        const timeRange = `${params.range_start_time || '08:46'}-${params.range_end_time || '08:47'}`;
                        const tradingDirection = params.trading_direction || 'BOTH';
                        const directionDisplay = {
                            'LONG_ONLY': '只做多',
                            'SHORT_ONLY': '只做空',
                            'BOTH': '多空都做'
                        }[tradingDirection] || tradingDirection;
                        html += `<tr>
                            <td>${index + 1}</td>
                            <td>${result.experiment_id}</td>
                            <td style="font-weight: bold; color: ${tradingDirection === 'LONG_ONLY' ? '#2e7d32' : tradingDirection === 'SHORT_ONLY' ? '#d32f2f' : '#1976d2'};">${directionDisplay}</td>
                            <td style="font-family: monospace; color: #666;">${timeRange}</td>
                            <td style="color: ${result.total_pnl >= 0 ? 'green' : 'red'}; font-weight: bold;">${result.total_pnl.toFixed(1)}</td>
                            <td style="color: ${result.max_drawdown <= 0 ? 'green' : 'red'};">${result.max_drawdown.toFixed(1)}</td>
                            <td>${result.win_rate.toFixed(1)}%</td>
                            <td>${params.lot1_trigger}(${params.lot1_trailing}%)/${params.lot2_trigger}(${params.lot2_trailing}%)/${params.lot3_trigger}(${params.lot3_trailing}%)</td>
                        </tr>`;
                    });
                    html += '</table>';

                    // 載入最高多頭損益前10名（只顯示多頭進場的實驗）
                    return fetch('/get_best_results?metric=long_pnl&ascending=false&limit=10&trading_direction=LONG_ONLY');
                }
            })
            .then(response => response.json())
            .then(longData => {
                if (longData.success && longData.results.length > 0) {
                    html += '<h3 style="margin-top: 30px;">📈 最高多頭損益前10名（只做多實驗）</h3>';
                    html += '<table class="results-table"><tr><th>排名</th><th>實驗ID</th><th>交易方向</th><th>時間區間</th><th>多頭損益</th><th>MDD</th><th>勝率</th><th>參數</th></tr>';
                    longData.results.forEach((result, index) => {
                        const params = JSON.parse(result.parameters);
                        const timeRange = `${params.range_start_time || '08:46'}-${params.range_end_time || '08:47'}`;
                        const tradingDirection = params.trading_direction || 'BOTH';
                        const directionDisplay = {
                            'LONG_ONLY': '只做多',
                            'SHORT_ONLY': '只做空',
                            'BOTH': '多空都做'
                        }[tradingDirection] || tradingDirection;
                        html += `<tr>
                            <td>${index + 1}</td>
                            <td>${result.experiment_id}</td>
                            <td style="font-weight: bold; color: #2e7d32;">${directionDisplay}</td>
                            <td style="font-family: monospace; color: #666;">${timeRange}</td>
                            <td style="color: ${result.long_pnl >= 0 ? 'green' : 'red'}; font-weight: bold;">${result.long_pnl.toFixed(1)}</td>
                            <td style="color: ${result.max_drawdown <= 0 ? 'green' : 'red'};">${result.max_drawdown.toFixed(1)}</td>
                            <td>${result.win_rate.toFixed(1)}%</td>
                            <td>${params.lot1_trigger}(${params.lot1_trailing}%)/${params.lot2_trigger}(${params.lot2_trailing}%)/${params.lot3_trigger}(${params.lot3_trailing}%)</td>
                        </tr>`;
                    });
                    html += '</table>';
                }

                // 載入最高空頭損益前10名（只顯示空頭進場的實驗）
                return fetch('/get_best_results?metric=short_pnl&ascending=false&limit=10&trading_direction=SHORT_ONLY');
            })
            .then(response => response.json())
            .then(shortData => {
                if (shortData.success && shortData.results.length > 0) {
                    html += '<h3 style="margin-top: 30px;">📉 最高空頭損益前10名（只做空實驗）</h3>';
                    html += '<table class="results-table"><tr><th>排名</th><th>實驗ID</th><th>交易方向</th><th>時間區間</th><th>空頭損益</th><th>MDD</th><th>勝率</th><th>參數</th></tr>';
                    shortData.results.forEach((result, index) => {
                        const params = JSON.parse(result.parameters);
                        const timeRange = `${params.range_start_time || '08:46'}-${params.range_end_time || '08:47'}`;
                        const tradingDirection = params.trading_direction || 'BOTH';
                        const directionDisplay = {
                            'LONG_ONLY': '只做多',
                            'SHORT_ONLY': '只做空',
                            'BOTH': '多空都做'
                        }[tradingDirection] || tradingDirection;
                        html += `<tr>
                            <td>${index + 1}</td>
                            <td>${result.experiment_id}</td>
                            <td style="font-weight: bold; color: #d32f2f;">${directionDisplay}</td>
                            <td style="font-family: monospace; color: #666;">${timeRange}</td>
                            <td style="color: ${result.short_pnl >= 0 ? 'green' : 'red'}; font-weight: bold;">${result.short_pnl.toFixed(1)}</td>
                            <td style="color: ${result.max_drawdown <= 0 ? 'green' : 'red'};">${result.max_drawdown.toFixed(1)}</td>
                            <td>${result.win_rate.toFixed(1)}%</td>
                            <td>${params.lot1_trigger}(${params.lot1_trailing}%)/${params.lot2_trigger}(${params.lot2_trailing}%)/${params.lot3_trigger}(${params.lot3_trailing}%)</td>
                        </tr>`;
                    });
                    html += '</table>';
                }

                // 載入最低MDD前10名
                return fetch('/get_best_results?metric=max_drawdown&ascending=true&limit=10');
            })
            .then(response => response.json())
            .then(mddData => {
                if (mddData.success && mddData.results.length > 0) {
                    html += '<h3 style="margin-top: 30px;">🛡️ 最低回撤前10名</h3>';
                    html += '<table class="results-table"><tr><th>排名</th><th>實驗ID</th><th>交易方向</th><th>時間區間</th><th>總損益</th><th>最大回撤</th><th>勝率</th><th>參數</th></tr>';
                    mddData.results.forEach((result, index) => {
                        const params = JSON.parse(result.parameters);
                        const timeRange = `${params.range_start_time || '08:46'}-${params.range_end_time || '08:47'}`;
                        const tradingDirection = params.trading_direction || 'BOTH';
                        const directionDisplay = {
                            'LONG_ONLY': '只做多',
                            'SHORT_ONLY': '只做空',
                            'BOTH': '多空都做'
                        }[tradingDirection] || tradingDirection;
                        html += `<tr>
                            <td>${index + 1}</td>
                            <td>${result.experiment_id}</td>
                            <td style="font-weight: bold; color: ${tradingDirection === 'LONG_ONLY' ? '#2e7d32' : tradingDirection === 'SHORT_ONLY' ? '#d32f2f' : '#1976d2'};">${directionDisplay}</td>
                            <td style="font-family: monospace; color: #666;">${timeRange}</td>
                            <td style="color: ${result.total_pnl >= 0 ? 'green' : 'red'}; font-weight: bold;">${result.total_pnl.toFixed(1)}</td>
                            <td style="color: ${result.max_drawdown <= 0 ? 'green' : 'red'};">${result.max_drawdown.toFixed(1)}</td>
                            <td>${result.win_rate.toFixed(1)}%</td>
                            <td>${params.lot1_trigger}(${params.lot1_trailing}%)/${params.lot2_trigger}(${params.lot2_trailing}%)/${params.lot3_trigger}(${params.lot3_trailing}%)</td>
                        </tr>`;
                    });
                    html += '</table>';
                }

                document.getElementById('bestResults').innerHTML = html;

                // 更新最佳損益顯示（使用第一個表格的第一名）
                fetch('/get_best_results?metric=total_pnl&ascending=false&limit=1')
                .then(response => response.json())
                .then(bestData => {
                    if (bestData.success && bestData.results.length > 0) {
                        document.getElementById('bestPnl').textContent = bestData.results[0].total_pnl.toFixed(1);
                    }
                });
            })
            .catch(error => {
                console.error('載入結果時發生錯誤:', error);
                document.getElementById('bestResults').innerHTML = '<p style="color: red;">載入結果時發生錯誤</p>';
            });
        }

        function loadTimeSlotResults() {
            fetch('/get_time_slot_results')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    let html = '';
                    const timeSlots = data.time_slots;

                    if (Object.keys(timeSlots).length === 0) {
                        html = '<p>尚無時段數據</p>';
                    } else {
                        // 為每個時段生成表格
                        Object.keys(timeSlots).sort().forEach(timeSlot => {
                            const results = timeSlots[timeSlot];
                            if (results.length > 0) {
                                html += `<h3 style="margin-top: 25px; color: #2e7d32;">⏰ ${timeSlot} MDD 最低前三名</h3>`;
                                html += '<table class="results-table"><tr><th>排名</th><th>實驗ID</th><th>交易方向</th><th>MDD</th><th>總損益</th><th>勝率</th><th>參數</th></tr>';

                                results.forEach((result, index) => {
                                    const params = JSON.parse(result.parameters);
                                    const tradingDirection = params.trading_direction || 'BOTH';
                                    const directionDisplay = {
                                        'LONG_ONLY': '只做多',
                                        'SHORT_ONLY': '只做空',
                                        'BOTH': '多空都做'
                                    }[tradingDirection] || tradingDirection;
                                    html += `<tr>
                                        <td>${index + 1}</td>
                                        <td>${result.experiment_id}</td>
                                        <td style="font-weight: bold; color: ${tradingDirection === 'LONG_ONLY' ? '#2e7d32' : tradingDirection === 'SHORT_ONLY' ? '#d32f2f' : '#1976d2'};">${directionDisplay}</td>
                                        <td style="color: ${result.max_drawdown <= 0 ? 'green' : 'red'}; font-weight: bold;">${result.max_drawdown.toFixed(1)}</td>
                                        <td style="color: ${result.total_pnl >= 0 ? 'green' : 'red'};">${result.total_pnl.toFixed(1)}</td>
                                        <td>${result.win_rate.toFixed(1)}%</td>
                                        <td>${params.lot1_trigger}(${params.lot1_trailing}%)/${params.lot2_trigger}(${params.lot2_trailing}%)/${params.lot3_trigger}(${params.lot3_trailing}%)</td>
                                    </tr>`;
                                });
                                html += '</table>';
                            }
                        });
                    }

                    document.getElementById('timeSlotResults').innerHTML = html;
                } else {
                    document.getElementById('timeSlotResults').innerHTML = '<p style="color: red;">載入時段結果時發生錯誤</p>';
                }
            })
            .catch(error => {
                console.error('載入時段結果時發生錯誤:', error);
                document.getElementById('timeSlotResults').innerHTML = '<p style="color: red;">載入時段結果時發生錯誤</p>';
            });
        }

        function generateAutoCSVReport() {
            console.log('📊 自動生成CSV報告...');
            addLog('📊 正在生成CSV報告...');

            fetch('/generate_csv_report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog(`✅ CSV報告已生成: ${data.filename}`);
                    addLog(`📁 文件位置: batch_result/${data.filename}`);
                    addLog(`📊 導出了 ${data.record_count} 筆實驗結果`);
                    console.log('✅ CSV報告生成成功:', data);
                } else {
                    addLog(`❌ CSV報告生成失敗: ${data.error}`);
                    console.error('❌ CSV報告生成失敗:', data.error);
                }
            })
            .catch(error => {
                addLog(`❌ CSV報告生成時發生錯誤: ${error.message}`);
                console.error('❌ CSV報告生成錯誤:', error);
            });
        }

        function generateLongShortReports(type) {
            let message = '';
            if (type === 'long') {
                message = '📈 開始生成多方專用報告...';
            } else if (type === 'short') {
                message = '📉 開始生成空方專用報告...';
            } else {
                message = '📊 開始生成多空分離報告...';
            }

            console.log(message);
            addLog(message);

            fetch('/generate_long_short_reports', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({type: type})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog(`✅ 多空分離報告生成成功`);
                    addLog(`📊 處理了 ${data.record_count} 個實驗`);

                    if (data.long_report) {
                        addLog(`📈 多方報告: ${data.long_report}`);
                    }
                    if (data.short_report) {
                        addLog(`📉 空方報告: ${data.short_report}`);
                    }
                    console.log('✅ 多空分離報告生成成功:', data);
                } else {
                    addLog(`❌ 多空分離報告生成失敗: ${data.error}`);
                    console.error('❌ 多空分離報告生成失敗:', data.error);
                }
            })
            .catch(error => {
                addLog(`❌ 生成多空分離報告時發生錯誤: ${error.message}`);
                console.error('❌ 生成多空分離報告時發生錯誤:', error);
            });
        }

        function generateAllReports() {
            console.log('🎯 開始自動生成全套報告...');
            addLog('🎯 開始自動生成全套報告（CSV + 多空分離 + HTML）...');

            fetch('/generate_complete_reports', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog(`✅ 全套報告生成成功`);
                    addLog(`📊 處理了 ${data.record_count} 個實驗`);
                    addLog(`📁 報告資料夾: ${data.output_folder}`);

                    // 顯示生成的報告列表
                    if (data.reports && data.reports.length > 0) {
                        addLog(`📋 生成的報告:`);
                        data.reports.forEach(report => {
                            addLog(`   ${report.type}: ${report.filename}`);
                        });
                    }

                    console.log('✅ 全套報告生成成功:', data);
                } else {
                    addLog(`❌ 全套報告生成失敗: ${data.error}`);
                    console.error('❌ 全套報告生成失敗:', data.error);
                }
            })
            .catch(error => {
                addLog(`❌ 生成全套報告時發生錯誤: ${error.message}`);
                console.error('❌ 生成全套報告時發生錯誤:', error);
            });
        }

        function generateAllHTMLReports() {
            console.log('📊 開始自動生成HTML報告...');
            addLog('📊 開始自動生成HTML報告...');

            fetch('/generate_all_html_reports', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    addLog(`✅ HTML報告生成成功`);
                    addLog(`📊 處理了 ${data.record_count} 個實驗`);
                    addLog(`📁 報告資料夾: ${data.output_folder}`);

                    // 顯示生成的報告列表
                    if (data.reports && data.reports.length > 0) {
                        addLog(`📋 生成的HTML報告:`);
                        data.reports.forEach(report => {
                            addLog(`   ${report.type}: ${report.filename}`);
                        });
                    }

                    console.log('✅ HTML報告生成成功:', data);
                } else {
                    addLog(`❌ HTML報告生成失敗: ${data.error}`);
                    console.error('❌ HTML報告生成失敗:', data.error);
                }
            })
            .catch(error => {
                addLog(`❌ 生成HTML報告時發生錯誤: ${error.message}`);
                console.error('❌ 生成HTML報告時發生錯誤:', error);
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/favicon.ico')
def favicon():
    return '', 204



@app.route('/start_experiments_direct', methods=['POST'])
def start_experiments_direct():
    """直接開始實驗（包含參數矩陣生成）"""
    try:
        global batch_engine, experiment_thread, current_config

        if batch_engine and batch_engine.running:
            return jsonify({"success": False, "error": "實驗正在進行中"})

        config_data = request.json
        logger.info(f"收到實驗配置: {config_data}")

        # 清理舊的實驗數據
        db = ResultDatabase()
        db.clear_all_results()
        logger.info("🗑️ 已清理舊的實驗數據")

        # 導入必要的類
        from parameter_matrix_generator import ParameterRange, TimeRange, LotParameterConfig

        # 處理時間區間數據
        time_ranges_data = config_data.get('time_ranges', [])
        if not time_ranges_data:
            # 向後兼容：如果沒有 time_ranges，使用舊的格式
            time_ranges_data = [{
                'start': config_data.get('range_start_time', '08:46'),
                'end': config_data.get('range_end_time', '08:47')
            }]

        start_times = [tr['start'] for tr in time_ranges_data]
        end_times = [tr['end'] for tr in time_ranges_data]

        logger.info(f"📊 時間區間配置: {len(time_ranges_data)} 個區間")
        for i, tr in enumerate(time_ranges_data):
            logger.info(f"  區間 {i+1}: {tr['start']} - {tr['end']}")

        # 創建實驗配置
        config = ExperimentConfig(
            trade_lots=3,
            date_ranges=[(config_data['start_date'], config_data['end_date'])],
            time_ranges=TimeRange(
                start_times=start_times,
                end_times=end_times
            ),
            lot1_config=LotParameterConfig(
                trigger_range=ParameterRange(
                    config_data['lot1_trigger_range'][0],
                    config_data['lot1_trigger_range'][1],
                    5
                ),
                trailing_range=ParameterRange(
                    config_data['lot1_trailing_range'][0],
                    config_data['lot1_trailing_range'][1],
                    5
                )
            ),
            lot2_config=LotParameterConfig(
                trigger_range=ParameterRange(
                    config_data['lot2_trigger_range'][0],
                    config_data['lot2_trigger_range'][1],
                    5
                ),
                trailing_range=ParameterRange(
                    config_data['lot2_trailing_range'][0],
                    config_data['lot2_trailing_range'][1],
                    5
                ),
                protection_range=ParameterRange(
                    config_data['protection_range'][0],
                    config_data['protection_range'][1],
                    5
                )
            ),
            lot3_config=LotParameterConfig(
                trigger_range=ParameterRange(
                    config_data['lot3_trigger_range'][0],
                    config_data['lot3_trigger_range'][1],
                    5
                ),
                trailing_range=ParameterRange(
                    config_data['lot3_trailing_range'][0],
                    config_data['lot3_trailing_range'][1],
                    5
                ),
                protection_range=ParameterRange(
                    config_data['protection_range'][0],
                    config_data['protection_range'][1],
                    5
                )
            ),
            enforce_lot_progression=True
        )

        # 生成參數矩陣
        generator = ParameterMatrixGenerator(config)
        experiments = generator.generate_full_parameter_matrix()

        # 🚀 【新增】為每個實驗添加交易方向參數
        trading_direction = config_data.get('trading_direction', 'BOTH')

        if trading_direction == 'ALL_MODES':
            # 全模式：為每個參數組合生成三種交易方向的實驗
            original_experiments = experiments.copy()
            experiments = []

            # 重新分配實驗ID，避免重複
            experiment_id = 1

            for exp in original_experiments:
                # 生成三種模式的實驗
                for mode in ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']:
                    new_exp = exp.copy()
                    new_exp['trading_direction'] = mode
                    new_exp['experiment_id'] = experiment_id  # 🚀 重新分配ID
                    experiments.append(new_exp)
                    experiment_id += 1
        else:
            # 單一模式：所有實驗使用相同的交易方向
            for experiment in experiments:
                experiment['trading_direction'] = trading_direction

        # 儲存配置
        current_config = config

        if trading_direction == 'ALL_MODES':
            logger.info(f"✅ 生成了 {len(experiments)} 個實驗配置 (全模式: 多空+都跑)")
        else:
            logger.info(f"✅ 生成了 {len(experiments)} 個實驗配置 (交易方向: {trading_direction})")

        # 創建批次引擎
        batch_engine = BatchBacktestEngine(
            max_parallel=config_data.get('max_parallel', 4)
        )

        # 在新線程中執行實驗
        def run_experiments():
            batch_engine.run_batch_experiments(experiments)

        experiment_thread = threading.Thread(target=run_experiments)
        experiment_thread.daemon = True
        experiment_thread.start()

        return jsonify({
            "success": True,
            "total_experiments": len(experiments)
        })
        
    except Exception as e:
        logger.error(f"啟動實驗失敗: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/stop_experiments', methods=['POST'])
def stop_experiments():
    try:
        global batch_engine
        
        if batch_engine:
            batch_engine.stop_experiments()
        
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"停止實驗失敗: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_progress')
def get_progress():
    try:
        global batch_engine
        
        if not batch_engine:
            return jsonify({
                "status": "not_started",
                "completed": 0,
                "total": 0,
                "progress_percent": 0,
                "elapsed_time": 0,
                "eta": 0,
                "current_experiment": None
            })
        
        progress_info = batch_engine.get_progress_info()
        return jsonify(progress_info)
        
    except Exception as e:
        logger.error(f"獲取進度失敗: {e}")
        return jsonify({"error": str(e)})

@app.route('/get_best_results')
def get_best_results():
    try:
        metric = request.args.get('metric', 'total_pnl')
        ascending = request.args.get('ascending', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 10))
        trading_direction = request.args.get('trading_direction', None)  # 🚀 新增交易方向過濾

        db = ResultDatabase()

        # 🚀 修改：使用新的過濾方法
        if trading_direction:
            results = db.get_best_results_with_direction_filter(metric, limit, ascending, trading_direction)
        else:
            results = db.get_best_results(metric, limit, ascending)

        return jsonify({
            "success": True,
            "results": results
        })

    except Exception as e:
        logger.error(f"獲取最佳結果失敗: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/get_time_slot_results', methods=['GET'])
def get_time_slot_results():
    """獲取各時段的MDD最低前三名結果"""
    try:
        db = ResultDatabase()
        all_results = db.get_all_results()

        if not all_results:
            return jsonify({"success": True, "time_slots": {}})

        # 按時段分組結果
        time_slot_groups = {}

        for result in all_results:
            if result['success'] and result['parameters']:
                try:
                    params = json.loads(result['parameters'])
                    start_time = params.get('range_start_time', '08:46')
                    end_time = params.get('range_end_time', '08:47')
                    time_slot = f"{start_time}-{end_time}"

                    if time_slot not in time_slot_groups:
                        time_slot_groups[time_slot] = []

                    time_slot_groups[time_slot].append(result)
                except (json.JSONDecodeError, KeyError):
                    continue

        # 為每個時段找出MDD最低的前三名
        time_slot_results = {}
        for time_slot, results in time_slot_groups.items():
            # 按MDD排序（升序，最低的在前）
            sorted_results = sorted(results, key=lambda x: x.get('max_drawdown', float('inf')))
            time_slot_results[time_slot] = sorted_results[:3]  # 取前三名

        return jsonify({
            "success": True,
            "time_slots": time_slot_results
        })

    except Exception as e:
        logger.error(f"獲取時段結果失敗: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/generate_csv_report', methods=['POST'])
def generate_csv_report():
    """生成CSV格式的實驗結果報告"""
    try:
        import csv
        import os
        from datetime import datetime

        # 創建 batch_result 目錄
        batch_result_dir = "batch_result"
        os.makedirs(batch_result_dir, exist_ok=True)

        # 獲取所有實驗結果
        db = ResultDatabase()
        all_results = db.get_all_results()

        if not all_results:
            return jsonify({"success": False, "error": "沒有實驗結果可以導出"})

        # 分析實驗的交易方向，創建對應的資料夾結構
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        trading_directions = set()

        for result in all_results:
            if result['success'] and result['parameters']:
                try:
                    params = json.loads(result['parameters'])
                    direction = params.get('trading_direction', 'BOTH')
                    trading_directions.add(direction)
                except:
                    trading_directions.add('BOTH')

        # 根據交易方向決定資料夾名稱
        if len(trading_directions) == 1:
            direction = list(trading_directions)[0]
            if direction == 'BOTH':
                folder_name = f"mixed_strategy_{timestamp}"
            elif direction == 'LONG_ONLY':
                folder_name = f"long_only_{timestamp}"
            elif direction == 'SHORT_ONLY':
                folder_name = f"short_only_{timestamp}"
            else:
                folder_name = f"experiment_{timestamp}"
        else:
            folder_name = f"all_modes_{timestamp}"

        # 創建實驗專用資料夾
        experiment_folder = os.path.join(batch_result_dir, folder_name)
        os.makedirs(experiment_folder, exist_ok=True)

        # 生成CSV文件路徑
        csv_filename = f"batch_experiment_results_{timestamp}.csv"
        csv_filepath = os.path.join(experiment_folder, csv_filename)

        # 準備CSV數據
        csv_data = []
        for result in all_results:
            if result['success'] and result['parameters']:
                try:
                    params = json.loads(result['parameters'])

                    # 提取時間區間
                    start_time = params.get('range_start_time', '08:46')
                    end_time = params.get('range_end_time', '08:47')
                    time_range = f"{start_time}-{end_time}"

                    # 提取參數信息（包含觸發點和回檔範圍）
                    lot1_str = f"{params.get('lot1_trigger', 0)}({params.get('lot1_trailing', 0)}%)"
                    lot2_str = f"{params.get('lot2_trigger', 0)}({params.get('lot2_trailing', 0)}%)"
                    lot3_str = f"{params.get('lot3_trigger', 0)}({params.get('lot3_trailing', 0)}%)"
                    param_str = f"{lot1_str}/{lot2_str}/{lot3_str}"

                    csv_row = {
                        '實驗ID': result['experiment_id'],
                        '時間區間': time_range,
                        '多頭損益': round(result.get('long_pnl', 0), 1),
                        '空頭損益': round(result.get('short_pnl', 0), 1),
                        '總損益': round(result.get('total_pnl', 0), 1),
                        'MDD': round(result.get('max_drawdown', 0), 1),
                        '勝率': f"{round(result.get('win_rate', 0), 1)}%",
                        '參數': param_str
                    }
                    csv_data.append(csv_row)

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"解析實驗結果失敗: {e}")
                    continue

        # 寫入CSV文件
        if csv_data:
            fieldnames = ['實驗ID', '時間區間', '多頭損益', '空頭損益', '總損益', 'MDD', '勝率', '參數']

            with open(csv_filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)

            logger.info(f"✅ CSV報告已生成: {csv_filepath}")
            logger.info(f"📊 導出了 {len(csv_data)} 筆實驗結果")

            return jsonify({
                "success": True,
                "message": f"CSV報告已生成",
                "filename": csv_filename,
                "filepath": csv_filepath,
                "record_count": len(csv_data)
            })
        else:
            return jsonify({"success": False, "error": "沒有有效的實驗結果可以導出"})

    except Exception as e:
        logger.error(f"生成CSV報告失敗: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/generate_report', methods=['POST'])
def generate_report():
    try:
        # 檢查是否有實驗結果
        db = ResultDatabase()
        results = db.get_all_results()

        if not results:
            return jsonify({"success": False, "error": "沒有實驗結果可以生成報告"})

        # 在主線程中生成報告
        analyzer = ExperimentAnalyzer()
        report_file = analyzer.generate_analysis_report()

        return jsonify({
            "success": True,
            "report_file": report_file,
            "message": f"報告已生成，包含 {len(results)} 個實驗結果"
        })

    except Exception as e:
        logger.error(f"生成報告失敗: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route('/download_report')
def download_report():
    try:
        filename = request.args.get('file')
        if filename and os.path.exists(filename):
            return send_file(filename, as_attachment=True)
        else:
            return "檔案不存在", 404
            
    except Exception as e:
        logger.error(f"下載報告失敗: {e}")
        return str(e), 500

@app.route('/generate_long_short_reports', methods=['POST'])
def generate_long_short_reports():
    """生成多空分離報告"""
    try:
        request_data = request.json
        report_type = request_data.get('type', 'both')

        logger.info(f"開始生成多空分離報告，類型: {report_type}")

        # 獲取最新的實驗資料夾
        batch_result_dir = Path("batch_result")
        experiment_folders = [d for d in batch_result_dir.iterdir() if d.is_dir()]

        if experiment_folders:
            # 使用最新的實驗資料夾
            latest_folder = max(experiment_folders, key=lambda x: x.stat().st_mtime)
            output_subdir = latest_folder.name
        else:
            # 如果沒有實驗資料夾，創建一個新的
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_subdir = f"long_short_analysis_{timestamp}"

        # 創建分析器
        analyzer = LongShortSeparationAnalyzer(output_subdir=output_subdir)

        if report_type == 'both':
            # 生成完整的多空分離報告
            result = analyzer.generate_separation_reports()
        elif report_type == 'long':
            # 只生成多方報告
            experiments_data = analyzer._extract_experiments_data()
            if experiments_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                long_report_path = analyzer._generate_long_only_report(experiments_data, timestamp)
                result = {
                    "success": True,
                    "long_report": str(long_report_path),
                    "record_count": len(experiments_data)
                }
            else:
                result = {"success": False, "error": "沒有有效的實驗數據"}
        elif report_type == 'short':
            # 只生成空方報告
            experiments_data = analyzer._extract_experiments_data()
            if experiments_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                short_report_path = analyzer._generate_short_only_report(experiments_data, timestamp)
                result = {
                    "success": True,
                    "short_report": str(short_report_path),
                    "record_count": len(experiments_data)
                }
            else:
                result = {"success": False, "error": "沒有有效的實驗數據"}
        else:
            result = {"success": False, "error": "無效的報告類型"}

        return jsonify(result)

    except Exception as e:
        logger.error(f"生成多空分離報告失敗: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/generate_all_reports', methods=['POST'])
def generate_all_reports():
    """自動生成全套報告（CSV + 多空分離 + HTML）"""
    try:
        import csv
        logger.info("🎯 開始自動生成全套報告...")

        # 檢查是否有實驗結果
        db = ResultDatabase()
        all_results = db.get_all_results()

        if not all_results:
            return jsonify({"success": False, "error": "沒有實驗結果可以生成報告"})

        # 分析實驗類型
        trading_directions = set()
        for result in all_results:
            if result['success'] and result['parameters']:
                try:
                    params = json.loads(result['parameters'])
                    direction = params.get('trading_direction', 'BOTH')
                    trading_directions.add(direction)
                except:
                    trading_directions.add('BOTH')

        # 創建統一的輸出資料夾
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if len(trading_directions) > 1:
            folder_name = f"all_modes_reports_{timestamp}"
        elif len(trading_directions) == 1:
            direction = list(trading_directions)[0]
            if direction == 'BOTH':
                folder_name = f"mixed_strategy_reports_{timestamp}"
            elif direction == 'LONG_ONLY':
                folder_name = f"long_only_reports_{timestamp}"
            elif direction == 'SHORT_ONLY':
                folder_name = f"short_only_reports_{timestamp}"
            else:
                folder_name = f"experiment_reports_{timestamp}"
        else:
            folder_name = f"reports_{timestamp}"

        output_folder = os.path.join("batch_result", folder_name)
        os.makedirs(output_folder, exist_ok=True)

        generated_reports = []

        # 1. 生成CSV報告
        logger.info("📋 生成CSV報告...")
        csv_filename = f"batch_experiment_results_{timestamp}.csv"
        csv_filepath = os.path.join(output_folder, csv_filename)

        # 準備CSV數據（複用現有邏輯）
        csv_data = []
        for result in all_results:
            if result['success'] and result['parameters']:
                try:
                    params = json.loads(result['parameters'])

                    # 提取時間區間
                    start_time = params.get('range_start_time', '08:46')
                    end_time = params.get('range_end_time', '08:47')
                    time_range = f"{start_time}-{end_time}"

                    # 提取參數信息（包含觸發點和回檔範圍）
                    lot1_str = f"{params.get('lot1_trigger', 0)}({params.get('lot1_trailing', 0)}%)"
                    lot2_str = f"{params.get('lot2_trigger', 0)}({params.get('lot2_trailing', 0)}%)"
                    lot3_str = f"{params.get('lot3_trigger', 0)}({params.get('lot3_trailing', 0)}%)"
                    param_str = f"{lot1_str}/{lot2_str}/{lot3_str}"

                    # 添加交易方向信息
                    trading_direction = params.get('trading_direction', 'BOTH')

                    csv_row = {
                        '實驗ID': result['experiment_id'],
                        '交易方向': trading_direction,
                        '時間區間': time_range,
                        '多頭損益': round(result.get('long_pnl', 0), 1),
                        '空頭損益': round(result.get('short_pnl', 0), 1),
                        '總損益': round(result.get('total_pnl', 0), 1),
                        'MDD': round(result.get('max_drawdown', 0), 1),
                        '勝率': f"{round(result.get('win_rate', 0), 1)}%",
                        '參數': param_str
                    }
                    csv_data.append(csv_row)

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"解析實驗結果失敗: {e}")
                    continue

        # 寫入CSV文件
        if csv_data:
            fieldnames = ['實驗ID', '交易方向', '時間區間', '多頭損益', '空頭損益', '總損益', 'MDD', '勝率', '參數']

            with open(csv_filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)

            generated_reports.append({
                "type": "📋 CSV總表",
                "filename": csv_filename,
                "path": csv_filepath
            })
            logger.info(f"✅ CSV報告已生成: {csv_filename}")

        # 2. 根據交易方向生成對應的分離報告
        if len(trading_directions) > 1 or 'BOTH' in trading_directions:
            logger.info("📊 生成多空分離報告...")

            # 創建分析器，使用相同的輸出資料夾
            analyzer = LongShortSeparationAnalyzer(output_subdir=folder_name)

            # 生成多空分離報告
            separation_result = analyzer.generate_separation_reports()

            if separation_result.get("success"):
                if separation_result.get("long_report"):
                    long_filename = os.path.basename(separation_result["long_report"])
                    generated_reports.append({
                        "type": "📈 多方專用報告",
                        "filename": long_filename,
                        "path": separation_result["long_report"]
                    })

                if separation_result.get("short_report"):
                    short_filename = os.path.basename(separation_result["short_report"])
                    generated_reports.append({
                        "type": "📉 空方專用報告",
                        "filename": short_filename,
                        "path": separation_result["short_report"]
                    })

                logger.info("✅ 多空分離報告已生成")
            else:
                logger.warning(f"⚠️ 多空分離報告生成失敗: {separation_result.get('error', '未知錯誤')}")

        # 3. 如果是全模式，生成各方向的專用CSV
        if len(trading_directions) > 1:
            logger.info("🎯 生成各交易方向專用CSV...")

            for direction in ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']:
                if direction in trading_directions:
                    direction_data = [row for row in csv_data if row['交易方向'] == direction]

                    if direction_data:
                        direction_filename = f"{direction.lower()}_results_{timestamp}.csv"
                        direction_filepath = os.path.join(output_folder, direction_filename)

                        with open(direction_filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(direction_data)

                        direction_name = {"LONG_ONLY": "只做多", "SHORT_ONLY": "只做空", "BOTH": "多空混合"}[direction]
                        generated_reports.append({
                            "type": f"📊 {direction_name}專用CSV",
                            "filename": direction_filename,
                            "path": direction_filepath
                        })

                        logger.info(f"✅ {direction_name}專用CSV已生成: {direction_filename}")

        return jsonify({
            "success": True,
            "message": "全套報告生成成功",
            "output_folder": output_folder,
            "record_count": len(csv_data),
            "trading_directions": list(trading_directions),
            "reports": generated_reports
        })

    except Exception as e:
        logger.error(f"生成全套報告失敗: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/generate_all_html_reports', methods=['POST'])
def generate_all_html_reports():
    """自動生成所有交易方向的HTML報告"""
    try:
        logger.info("📊 開始自動生成HTML報告...")

        # 檢查是否有實驗結果
        db = ResultDatabase()
        all_results = db.get_all_results()

        if not all_results:
            return jsonify({"success": False, "error": "沒有實驗結果可以生成報告"})

        # 分析實驗類型
        trading_directions = set()
        for result in all_results:
            if result['success'] and result['parameters']:
                try:
                    params = json.loads(result['parameters'])
                    direction = params.get('trading_direction', 'BOTH')
                    trading_directions.add(direction)
                except:
                    trading_directions.add('BOTH')

        # 創建統一的輸出資料夾
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if len(trading_directions) > 1:
            folder_name = f"html_reports_all_modes_{timestamp}"
        elif len(trading_directions) == 1:
            direction = list(trading_directions)[0]
            if direction == 'BOTH':
                folder_name = f"html_reports_mixed_{timestamp}"
            elif direction == 'LONG_ONLY':
                folder_name = f"html_reports_long_{timestamp}"
            elif direction == 'SHORT_ONLY':
                folder_name = f"html_reports_short_{timestamp}"
            else:
                folder_name = f"html_reports_{timestamp}"
        else:
            folder_name = f"html_reports_{timestamp}"

        output_folder = os.path.join("batch_result", folder_name)
        os.makedirs(output_folder, exist_ok=True)

        generated_reports = []

        # 根據實驗類型生成對應的HTML報告
        if len(trading_directions) > 1:
            # 全模式：生成三種方向的報告
            directions_to_generate = ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']
        else:
            # 單一模式：只生成對應方向的報告
            directions_to_generate = list(trading_directions)

        # 為每個交易方向生成HTML報告
        for direction in directions_to_generate:
            if direction in trading_directions:
                try:
                    logger.info(f"📊 生成 {direction} 方向的HTML報告...")

                    # 創建分析器並生成報告
                    analyzer = ExperimentAnalyzer()

                    # 生成特定方向的報告文件名
                    direction_suffix = direction.lower()
                    report_filename = f"experiment_analysis_report_{direction_suffix}_{timestamp}.html"
                    report_filepath = os.path.join(output_folder, report_filename)

                    # 生成報告
                    report_file = analyzer.generate_analysis_report(
                        output_file=report_filepath,
                        trading_direction=direction
                    )

                    if report_file and os.path.exists(report_file):
                        direction_name = {
                            'LONG_ONLY': '📈 只做多',
                            'SHORT_ONLY': '📉 只做空',
                            'BOTH': '📊 多空混合'
                        }.get(direction, direction)

                        generated_reports.append({
                            "type": f"{direction_name}HTML報告",
                            "filename": report_filename,
                            "path": report_file
                        })

                        logger.info(f"✅ {direction_name}HTML報告已生成: {report_filename}")
                    else:
                        logger.warning(f"⚠️ {direction} 方向的HTML報告生成失敗")

                except Exception as e:
                    logger.error(f"❌ 生成 {direction} 方向HTML報告時發生錯誤: {e}")
                    continue

        if generated_reports:
            return jsonify({
                "success": True,
                "message": "HTML報告生成成功",
                "output_folder": output_folder,
                "record_count": len(all_results),
                "trading_directions": list(trading_directions),
                "reports": generated_reports
            })
        else:
            return jsonify({
                "success": False,
                "error": "沒有成功生成任何HTML報告"
            })

    except Exception as e:
        logger.error(f"生成HTML報告失敗: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/generate_complete_reports', methods=['POST'])
def generate_complete_reports():
    """🚀 新增：自動生成完整報告套餐（CSV + 多空分離 + HTML）"""
    try:
        logger.info("🎯 開始自動生成完整報告套餐...")

        # 檢查是否有實驗結果
        db = ResultDatabase()
        all_results = db.get_all_results()

        if not all_results:
            return jsonify({"success": False, "error": "沒有實驗結果可以生成報告"})

        # 分析實驗類型
        trading_directions = set()
        for result in all_results:
            if result['success'] and result['parameters']:
                try:
                    params = json.loads(result['parameters'])
                    direction = params.get('trading_direction', 'BOTH')
                    trading_directions.add(direction)
                except:
                    trading_directions.add('BOTH')

        # 創建統一的輸出資料夾
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if len(trading_directions) > 1:
            folder_name = f"complete_reports_all_modes_{timestamp}"
        elif len(trading_directions) == 1:
            direction = list(trading_directions)[0]
            if direction == 'BOTH':
                folder_name = f"complete_reports_mixed_{timestamp}"
            elif direction == 'LONG_ONLY':
                folder_name = f"complete_reports_long_{timestamp}"
            elif direction == 'SHORT_ONLY':
                folder_name = f"complete_reports_short_{timestamp}"
            else:
                folder_name = f"complete_reports_{timestamp}"
        else:
            folder_name = f"complete_reports_{timestamp}"

        output_folder = os.path.join("batch_result", folder_name)
        os.makedirs(output_folder, exist_ok=True)

        generated_reports = []

        # 1. 生成CSV報告
        logger.info("📋 生成CSV報告...")
        csv_filename = f"batch_experiment_results_{timestamp}.csv"
        csv_filepath = os.path.join(output_folder, csv_filename)

        # 準備CSV數據
        csv_data = []
        for result in all_results:
            if result['success'] and result['parameters']:
                try:
                    params = json.loads(result['parameters'])

                    # 提取時間區間
                    start_time = params.get('range_start_time', '08:46')
                    end_time = params.get('range_end_time', '08:47')
                    time_range = f"{start_time}-{end_time}"

                    # 提取參數信息
                    lot1_str = f"{params.get('lot1_trigger', 0)}({params.get('lot1_trailing', 0)}%)"
                    lot2_str = f"{params.get('lot2_trigger', 0)}({params.get('lot2_trailing', 0)}%)"
                    lot3_str = f"{params.get('lot3_trigger', 0)}({params.get('lot3_trailing', 0)}%)"
                    param_str = f"{lot1_str}/{lot2_str}/{lot3_str}"

                    # 添加交易方向信息
                    trading_direction = params.get('trading_direction', 'BOTH')

                    csv_row = {
                        '實驗ID': result['experiment_id'],
                        '交易方向': trading_direction,
                        '時間區間': time_range,
                        '多頭損益': round(result.get('long_pnl', 0), 1),
                        '空頭損益': round(result.get('short_pnl', 0), 1),
                        '總損益': round(result.get('total_pnl', 0), 1),
                        'MDD': round(result.get('max_drawdown', 0), 1),
                        '勝率': f"{round(result.get('win_rate', 0), 1)}%",
                        '參數': param_str
                    }
                    csv_data.append(csv_row)

                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"解析實驗結果失敗: {e}")
                    continue

        # 寫入CSV文件
        if csv_data:
            import csv
            fieldnames = ['實驗ID', '交易方向', '時間區間', '多頭損益', '空頭損益', '總損益', 'MDD', '勝率', '參數']

            with open(csv_filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)

            generated_reports.append({
                "type": "📋 CSV總表",
                "filename": csv_filename,
                "path": csv_filepath
            })
            logger.info(f"✅ CSV報告已生成: {csv_filename}")

        # 2. 根據交易方向生成對應的分離報告
        if len(trading_directions) > 1 or 'BOTH' in trading_directions:
            logger.info("📊 生成多空分離報告...")

            # 創建分析器，使用相同的輸出資料夾
            analyzer = LongShortSeparationAnalyzer(output_subdir=folder_name)

            # 生成多空分離報告
            separation_result = analyzer.generate_separation_reports()

            if separation_result.get("success"):
                if separation_result.get("long_report"):
                    long_filename = os.path.basename(separation_result["long_report"])
                    generated_reports.append({
                        "type": "📈 多方專用報告",
                        "filename": long_filename,
                        "path": separation_result["long_report"]
                    })

                if separation_result.get("short_report"):
                    short_filename = os.path.basename(separation_result["short_report"])
                    generated_reports.append({
                        "type": "📉 空方專用報告",
                        "filename": short_filename,
                        "path": separation_result["short_report"]
                    })

                logger.info("✅ 多空分離報告已生成")
            else:
                logger.warning(f"⚠️ 多空分離報告生成失敗: {separation_result.get('error', '未知錯誤')}")

        # 3. 如果是全模式，生成各方向的專用CSV
        if len(trading_directions) > 1:
            logger.info("🎯 生成各交易方向專用CSV...")

            for direction in ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']:
                if direction in trading_directions:
                    direction_data = [row for row in csv_data if row['交易方向'] == direction]

                    if direction_data:
                        direction_filename = f"{direction.lower()}_results_{timestamp}.csv"
                        direction_filepath = os.path.join(output_folder, direction_filename)

                        with open(direction_filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(direction_data)

                        direction_name = {"LONG_ONLY": "只做多", "SHORT_ONLY": "只做空", "BOTH": "多空混合"}[direction]
                        generated_reports.append({
                            "type": f"📊 {direction_name}專用CSV",
                            "filename": direction_filename,
                            "path": direction_filepath
                        })

                        logger.info(f"✅ {direction_name}專用CSV已生成: {direction_filename}")

        # 4. 生成HTML報告
        logger.info("📊 生成HTML報告...")

        # 根據實驗類型生成對應的HTML報告
        if len(trading_directions) > 1:
            # 全模式：生成三種方向的報告
            directions_to_generate = ['LONG_ONLY', 'SHORT_ONLY', 'BOTH']
        else:
            # 單一模式：只生成對應方向的報告
            directions_to_generate = list(trading_directions)

        # 為每個交易方向生成HTML報告
        for direction in directions_to_generate:
            if direction in trading_directions:
                try:
                    logger.info(f"📊 生成 {direction} 方向的HTML報告...")

                    # 創建分析器並生成報告
                    analyzer = ExperimentAnalyzer()

                    # 生成特定方向的報告文件名
                    direction_suffix = direction.lower()
                    report_filename = f"experiment_analysis_report_{direction_suffix}_{timestamp}.html"
                    report_filepath = os.path.join(output_folder, report_filename)

                    # 🚀 修復圖表路徑問題：生成報告時指定相對路徑
                    report_file = analyzer.generate_analysis_report(
                        output_file=report_filepath,
                        trading_direction=direction
                    )

                    if report_file and os.path.exists(report_file):
                        direction_name = {
                            'LONG_ONLY': '📈 只做多',
                            'SHORT_ONLY': '📉 只做空',
                            'BOTH': '📊 多空混合'
                        }.get(direction, direction)

                        generated_reports.append({
                            "type": f"{direction_name}HTML報告",
                            "filename": report_filename,
                            "path": report_file
                        })

                        logger.info(f"✅ {direction_name}HTML報告已生成: {report_filename}")
                    else:
                        logger.warning(f"⚠️ {direction} 方向的HTML報告生成失敗")

                except Exception as e:
                    logger.error(f"❌ 生成 {direction} 方向HTML報告時發生錯誤: {e}")
                    continue

        return jsonify({
            "success": True,
            "message": "完整報告套餐生成成功",
            "output_folder": output_folder,
            "record_count": len(csv_data),
            "trading_directions": list(trading_directions),
            "reports": generated_reports
        })

    except Exception as e:
        logger.error(f"生成完整報告套餐失敗: {e}")
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    print("🚀 啟動批次實驗 Web GUI...")
    print("📱 請在瀏覽器中打開: http://localhost:5002")
    app.run(host='0.0.0.0', port=5002, debug=True, threaded=True)
