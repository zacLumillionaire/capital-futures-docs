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
        .results-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .results-table th, .results-table td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        .results-table th { background-color: #4CAF50; color: white; }
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
                    <div class="form-group">
                        <label>開盤區間開始:</label>
                        <input type="time" id="rangeStart" value="08:46">
                    </div>
                    <div class="form-group">
                        <label>開盤區間結束:</label>
                        <input type="time" id="rangeEnd" value="08:47">
                    </div>
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

            // 載入最佳結果
            loadBestResults();

            console.log('✅ 所有事件綁定完成');
        });

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

            // 收集表單數據
            const config = {
                start_date: document.getElementById('startDate').value,
                end_date: document.getElementById('endDate').value,
                range_start_time: document.getElementById('rangeStart').value,
                range_end_time: document.getElementById('rangeEnd').value,
                lot1_trigger_range: parseRange(document.getElementById('lot1TriggerRange').value),
                lot1_trailing_range: parseRange(document.getElementById('lot1TrailingRange').value),
                lot2_trigger_range: parseRange(document.getElementById('lot2TriggerRange').value),
                lot2_trailing_range: parseRange(document.getElementById('lot2TrailingRange').value),
                lot3_trigger_range: parseRange(document.getElementById('lot3TriggerRange').value),
                lot3_trailing_range: parseRange(document.getElementById('lot3TrailingRange').value),
                protection_range: parseRange(document.getElementById('protectionRange').value),
                max_parallel: parseInt(document.getElementById('maxParallel').value)
            };

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
                        `當前實驗: ${data.current_experiment.experiment_id} (第${data.current_experiment.lot1_trigger}/${data.current_experiment.lot2_trigger}/${data.current_experiment.lot3_trigger}口)`;
                }
                
                if (data.status === 'completed') {
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                    stopProgressUpdate();
                    addLog('🏁 所有實驗已完成');
                    loadBestResults();
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
                    html += '<table class="results-table"><tr><th>排名</th><th>實驗ID</th><th>總損益</th><th>MDD</th><th>勝率</th><th>參數</th></tr>';
                    data.results.forEach((result, index) => {
                        const params = JSON.parse(result.parameters);
                        html += `<tr>
                            <td>${index + 1}</td>
                            <td>${result.experiment_id}</td>
                            <td style="color: ${result.total_pnl >= 0 ? 'green' : 'red'}; font-weight: bold;">${result.total_pnl.toFixed(1)}</td>
                            <td style="color: ${result.max_drawdown <= 0 ? 'green' : 'red'};">${result.max_drawdown.toFixed(1)}</td>
                            <td>${result.win_rate.toFixed(1)}%</td>
                            <td>${params.lot1_trigger}/${params.lot2_trigger}/${params.lot3_trigger}</td>
                        </tr>`;
                    });
                    html += '</table>';

                    // 載入最高多頭損益前10名
                    return fetch('/get_best_results?metric=long_pnl&ascending=false&limit=10');
                }
            })
            .then(response => response.json())
            .then(longData => {
                if (longData.success && longData.results.length > 0) {
                    html += '<h3 style="margin-top: 30px;">📈 最高多頭損益前10名</h3>';
                    html += '<table class="results-table"><tr><th>排名</th><th>實驗ID</th><th>多頭損益</th><th>MDD</th><th>勝率</th><th>參數</th></tr>';
                    longData.results.forEach((result, index) => {
                        const params = JSON.parse(result.parameters);
                        html += `<tr>
                            <td>${index + 1}</td>
                            <td>${result.experiment_id}</td>
                            <td style="color: ${result.long_pnl >= 0 ? 'green' : 'red'}; font-weight: bold;">${result.long_pnl.toFixed(1)}</td>
                            <td style="color: ${result.max_drawdown <= 0 ? 'green' : 'red'};">${result.max_drawdown.toFixed(1)}</td>
                            <td>${result.win_rate.toFixed(1)}%</td>
                            <td>${params.lot1_trigger}/${params.lot2_trigger}/${params.lot3_trigger}</td>
                        </tr>`;
                    });
                    html += '</table>';
                }

                // 載入最高空頭損益前10名
                return fetch('/get_best_results?metric=short_pnl&ascending=false&limit=10');
            })
            .then(response => response.json())
            .then(shortData => {
                if (shortData.success && shortData.results.length > 0) {
                    html += '<h3 style="margin-top: 30px;">📉 最高空頭損益前10名</h3>';
                    html += '<table class="results-table"><tr><th>排名</th><th>實驗ID</th><th>空頭損益</th><th>MDD</th><th>勝率</th><th>參數</th></tr>';
                    shortData.results.forEach((result, index) => {
                        const params = JSON.parse(result.parameters);
                        html += `<tr>
                            <td>${index + 1}</td>
                            <td>${result.experiment_id}</td>
                            <td style="color: ${result.short_pnl >= 0 ? 'green' : 'red'}; font-weight: bold;">${result.short_pnl.toFixed(1)}</td>
                            <td style="color: ${result.max_drawdown <= 0 ? 'green' : 'red'};">${result.max_drawdown.toFixed(1)}</td>
                            <td>${result.win_rate.toFixed(1)}%</td>
                            <td>${params.lot1_trigger}/${params.lot2_trigger}/${params.lot3_trigger}</td>
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
                    html += '<table class="results-table"><tr><th>排名</th><th>實驗ID</th><th>總損益</th><th>最大回撤</th><th>勝率</th><th>參數</th></tr>';
                    mddData.results.forEach((result, index) => {
                        const params = JSON.parse(result.parameters);
                        html += `<tr>
                            <td>${index + 1}</td>
                            <td>${result.experiment_id}</td>
                            <td style="color: ${result.total_pnl >= 0 ? 'green' : 'red'}; font-weight: bold;">${result.total_pnl.toFixed(1)}</td>
                            <td style="color: ${result.max_drawdown <= 0 ? 'green' : 'red'};">${result.max_drawdown.toFixed(1)}</td>
                            <td>${result.win_rate.toFixed(1)}%</td>
                            <td>${params.lot1_trigger}/${params.lot2_trigger}/${params.lot3_trigger}</td>
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

        # 創建實驗配置
        config = ExperimentConfig(
            trade_lots=3,
            date_ranges=[(config_data['start_date'], config_data['end_date'])],
            time_ranges=TimeRange(
                start_times=[config_data['range_start_time']],
                end_times=[config_data['range_end_time']]
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

        # 儲存配置
        current_config = config

        logger.info(f"✅ 生成了 {len(experiments)} 個實驗配置")

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

        db = ResultDatabase()
        results = db.get_best_results(metric, limit, ascending)

        return jsonify({
            "success": True,
            "results": results
        })

    except Exception as e:
        logger.error(f"獲取最佳結果失敗: {e}")
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

if __name__ == '__main__':
    print("🚀 啟動批次實驗 Web GUI...")
    print("📱 請在瀏覽器中打開: http://localhost:5002")
    app.run(host='0.0.0.0', port=5002, debug=True, threaded=True)
