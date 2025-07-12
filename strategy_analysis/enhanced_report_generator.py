#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Report Generator for Web GUI
增強版報告生成器，整合完整的分析功能
"""

import os
import json
import re
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非GUI後端，避免線程問題
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime
from pathlib import Path
import base64
import io
import logging
import re
from typing import Dict, Any, List, Optional

# 導入策略摘要功能
try:
    from multi_Profit_Funded_Risk_多口 import format_config_summary, create_strategy_config_from_gui
except ImportError as e:
    logging.warning(f"導入策略摘要功能失敗: {e}")
    # 如果導入失敗，提供備用函數
    def format_config_summary(config):
        return "策略摘要功能暫不可用"
    def create_strategy_config_from_gui(gui_config):
        return None

def generate_strategy_summary_from_log(log_content: str, config_data: Dict[str, Any]) -> str:
    """從日誌內容生成策略摘要"""
    try:
        # 提取日期區間
        date_pattern = r'--- (\d{4}-\d{2}-\d{2}) \|'
        dates = re.findall(date_pattern, log_content)
        start_date = dates[0] if dates else "未知"
        end_date = dates[-1] if dates else "未知"

        # 提取策略設定摘要
        summary_pattern = r'📋======= 策略設定摘要.*?=======📋(.*?)(?=\[|===|$)'
        summary_match = re.search(summary_pattern, log_content, re.DOTALL)
        strategy_config = summary_match.group(1).strip() if summary_match else ""

        # 如果沒有找到完整的策略設定，嘗試提取部分信息
        if not strategy_config:
            # 提取濾網設定
            filter_patterns = [
                r'區間大小濾網：([^\n]+)',
                r'風險管理濾網：([^\n]+)',
                r'每日虧損限制：([^\n]+)',
                r'每日獲利目標：([^\n]+)',
                r'初始停損策略：([^\n]+)'
            ]

            config_parts = []
            for pattern in filter_patterns:
                match = re.search(pattern, log_content)
                if match:
                    config_parts.append(f"- {match.group(0)}")

            if config_parts:
                strategy_config = "\n".join(config_parts)

        # 提取交易口數
        lots_pattern = r'交易口數: (\d+)'
        lots_match = re.search(lots_pattern, log_content)
        trade_lots = lots_match.group(1) if lots_match else config_data.get('trade_lots', '未知')

        # 提取總交易次數和勝率
        trades_pattern = r'總交易次數: (\d+)'
        winrate_pattern = r'勝率: ([\d.]+)%'
        pnl_pattern = r'總損益\(.*?\): ([-+]?[\d.]+)'

        trades_match = re.search(trades_pattern, log_content)
        winrate_match = re.search(winrate_pattern, log_content)
        pnl_match = re.search(pnl_pattern, log_content)

        total_trades = trades_match.group(1) if trades_match else "未知"
        win_rate = winrate_match.group(1) if winrate_match else "未知"
        total_pnl = pnl_match.group(1) if pnl_match else "未知"

        # 生成摘要
        summary = f"""📅 回測期間: {start_date} 至 {end_date}
📊 交易口數: {trade_lots} 口
📈 總交易次數: {total_trades}
🎯 勝率: {win_rate}%
💰 總損益: {total_pnl} 點

{strategy_config}"""

        return summary

    except Exception as e:
        return f"策略摘要生成錯誤: {str(e)}"

# 設定matplotlib使用英文
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

logger = logging.getLogger(__name__)

def extract_trading_data_from_log(log_content: str) -> tuple:
    """從日誌內容提取交易資料"""
    events = []
    daily_data = []
    
    lines = log_content.split('\n')
    current_date = None
    current_direction = None
    current_entry_price = None
    current_risk_exit_price = None  # 🆕 添加風險管理平倉價格
    lot_counter = 0
    
    for line in lines:
        line = line.strip()
        
        # 提取交易日期和區間
        if '開盤區間:' in line and '---' in line:
            try:
                # 解析日期
                date_part = line.split('---')[1].split('|')[0].strip()
                current_date = date_part
                
                # 解析區間
                range_part = line.split('開盤區間:')[1].split('|')[0].strip()
                range_low, range_high = map(int, range_part.split(' - '))
                
                daily_data.append({
                    'trade_date': current_date,
                    'range_low': range_low,
                    'range_high': range_high,
                    'range_size': range_high - range_low,
                    'total_pnl': 0,
                    'direction': None
                })
            except:
                continue
        
        # 提取進場資訊
        elif ('📈 LONG' in line or '📉 SHORT' in line) and '進場' in line:
            try:
                current_direction = 'LONG' if '📈 LONG' in line else 'SHORT'
                # 更新當日方向
                if daily_data:
                    daily_data[-1]['direction'] = current_direction
                
                # 提取進場價格
                price_part = line.split('價格:')[1].split(',')[0].strip()
                current_entry_price = int(price_part)
                lot_counter = 0
            except:
                continue

        # 🆕 提取風險管理平倉總體資訊（包含平倉價格）
        elif '🚨 風險管理' in line and '平倉價:' in line:
            try:
                # 提取平倉價格
                price_match = re.search(r'平倉價:\s*(\d+)', line)
                if price_match:
                    current_risk_exit_price = int(price_match.group(1))
            except:
                continue

        # 提取出場資訊（包括風險管理平倉）
        elif ('✅' in line or '❌' in line or '🛡️' in line or '🚨' in line) and '損益:' in line:
            try:
                # 處理風險管理平倉的各口損益
                if '🚨' in line and '口風險平倉' in line:
                    # 提取口數
                    lot_match = re.search(r'第(\d+)口風險平倉', line)
                    if lot_match:
                        lot_number = int(lot_match.group(1))
                    else:
                        lot_counter += 1
                        lot_number = lot_counter

                    # 提取損益
                    pnl_part = line.split('損益:')[1].strip().replace('點', '')
                    pnl = int(pnl_part.replace('+', ''))

                    # 判斷風險管理類型
                    exit_type = 'risk_management'

                    events.append({
                        'trade_date': current_date,
                        'direction': current_direction,
                        'lot_number': lot_number,
                        'entry_price': current_entry_price,
                        'exit_price': current_risk_exit_price,  # 🆕 使用風險管理平倉價格
                        'pnl': pnl,
                        'exit_type': exit_type
                    })

                    # 累加到當日損益
                    if daily_data:
                        daily_data[-1]['total_pnl'] += pnl

                else:
                    # 處理正常出場
                    lot_counter += 1

                    # 提取損益
                    pnl_part = line.split('損益:')[1].strip()
                    pnl = int(pnl_part.replace('+', '').replace('-', ''))
                    if pnl_part.startswith('-'):
                        pnl = -pnl

                    # 提取出場價格
                    exit_price = None
                    if '價格:' in line:
                        price_part = line.split('價格:')[1].split(',')[0].strip()
                        exit_price = int(price_part)
                    elif '出場價:' in line:  # 🆕 處理保護性停損的出場價格
                        price_part = line.split('出場價:')[1].split(',')[0].strip()
                        exit_price = int(price_part)

                    # 判斷出場類型
                    exit_type = 'unknown'
                    if '✅' in line:
                        if '移動停利' in line:
                            exit_type = 'trailing_stop'
                        else:
                            exit_type = 'take_profit'
                    elif '❌' in line:
                        exit_type = 'stop_loss'
                    elif '🛡️' in line:
                        exit_type = 'protective_stop'

                    events.append({
                        'trade_date': current_date,
                        'direction': current_direction,
                        'lot_number': lot_counter,
                        'entry_price': current_entry_price,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'exit_type': exit_type
                    })

                    # 累加到當日損益
                    if daily_data:
                        daily_data[-1]['total_pnl'] += pnl
                    
            except:
                continue
    
    # 轉換為DataFrame
    events_df = pd.DataFrame(events)
    daily_df = pd.DataFrame(daily_data)
    
    return events_df, daily_df

def calculate_enhanced_statistics(daily_df: pd.DataFrame, events_df: pd.DataFrame) -> Dict[str, Any]:
    """計算增強統計指標"""
    if daily_df.empty:
        return {}
    
    # 基本統計
    total_trades = len(daily_df[daily_df['direction'].notna()])
    winning_trades = len(daily_df[daily_df['total_pnl'] > 0])
    losing_trades = len(daily_df[daily_df['total_pnl'] < 0])
    
    total_pnl = daily_df['total_pnl'].sum()
    avg_pnl = daily_df['total_pnl'].mean()
    
    wins = daily_df[daily_df['total_pnl'] > 0]['total_pnl']
    losses = daily_df[daily_df['total_pnl'] < 0]['total_pnl']
    
    avg_win = wins.mean() if len(wins) > 0 else 0
    avg_loss = losses.mean() if len(losses) > 0 else 0
    max_win = wins.max() if len(wins) > 0 else 0
    max_loss = losses.min() if len(losses) > 0 else 0
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    profit_factor = (wins.sum() / abs(losses.sum())) if losses.sum() != 0 else float('inf')
    
    # 風險指標
    equity_curve = daily_df['total_pnl'].cumsum()
    peak = equity_curve.expanding().max()
    drawdown = (equity_curve - peak)
    max_drawdown = drawdown.min()
    max_drawdown_pct = (max_drawdown / peak.max() * 100) if peak.max() != 0 else 0
    
    # 多空分析 - 基於交易日統計
    long_total_pnl = 0
    short_total_pnl = 0
    long_winning_days = 0
    short_winning_days = 0
    long_trading_days = 0
    short_trading_days = 0

    # 遍歷每個交易日，根據當日方向分類
    for _, day_row in daily_df.iterrows():
        if day_row['direction'] == 'LONG':
            long_trading_days += 1
            long_total_pnl += day_row['total_pnl']
            if day_row['total_pnl'] > 0:
                long_winning_days += 1
        elif day_row['direction'] == 'SHORT':
            short_trading_days += 1
            short_total_pnl += day_row['total_pnl']
            if day_row['total_pnl'] > 0:
                short_winning_days += 1

    # 計算勝率和平均損益
    long_win_rate = (long_winning_days / long_trading_days * 100) if long_trading_days > 0 else 0
    short_win_rate = (short_winning_days / short_trading_days * 100) if short_trading_days > 0 else 0
    long_avg_pnl = long_total_pnl / long_trading_days if long_trading_days > 0 else 0
    short_avg_pnl = short_total_pnl / short_trading_days if short_trading_days > 0 else 0

    # 統計多空交易次數（基於events_df）
    long_trades = len(events_df[events_df['direction'] == 'LONG'])
    short_trades = len(events_df[events_df['direction'] == 'SHORT'])

    # 口數分析
    lot_analysis = {}
    if not events_df.empty:
        for lot_num in events_df['lot_number'].unique():
            if pd.isna(lot_num):
                continue
            lot_data = events_df[events_df['lot_number'] == lot_num]
            lot_analysis[f'lot_{int(lot_num)}'] = {
                'total_pnl': lot_data['pnl'].sum(),
                'trades': len(lot_data),
                'win_rate': len(lot_data[lot_data['pnl'] > 0]) / len(lot_data) * 100 if len(lot_data) > 0 else 0
            }

    return {
        'basic_metrics': {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_win': max_win,
            'max_loss': max_loss,
            'profit_factor': profit_factor
        },
        'position_analysis': {
            'long_trades': long_trades,
            'short_trades': short_trades,
            'long_trading_days': long_trading_days,
            'short_trading_days': short_trading_days,
            'long_total_pnl': long_total_pnl,
            'short_total_pnl': short_total_pnl,
            'long_win_rate': long_win_rate,
            'short_win_rate': short_win_rate,
            'long_avg_pnl': long_avg_pnl,
            'short_avg_pnl': short_avg_pnl
        },
        'risk_metrics': {
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'volatility': daily_df['total_pnl'].std()
        },
        'lot_analysis': lot_analysis
    }

def create_enhanced_charts(daily_df: pd.DataFrame, events_df: pd.DataFrame, statistics: Dict[str, Any]) -> Dict[str, str]:
    """創建增強圖表"""
    chart_data = {}
    
    if daily_df.empty:
        return chart_data
    
    # 確保charts目錄存在
    os.makedirs('charts', exist_ok=True)
    
    # 1. 每日損益圖
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[2, 1])
        
        # 上圖：每日損益柱狀圖
        colors = ['green' if x > 0 else 'red' for x in daily_df['total_pnl']]
        bars = ax1.bar(range(len(daily_df)), daily_df['total_pnl'], color=colors, alpha=0.7)
        
        ax1.set_title('Daily P&L Analysis', fontsize=14, fontweight='bold')
        ax1.set_ylabel('P&L (Points)', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # 下圖：累積損益曲線
        equity_curve = daily_df['total_pnl'].cumsum()
        ax2.plot(range(len(daily_df)), equity_curve, linewidth=2, color='blue')
        ax2.fill_between(range(len(daily_df)), equity_curve, alpha=0.3, color='blue')
        ax2.set_title('Cumulative P&L Curve', fontsize=12)
        ax2.set_ylabel('Cumulative P&L', fontsize=10)
        ax2.set_xlabel('Trading Days', fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        chart_path = 'charts/daily_pnl_analysis.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        # 轉換為base64
        with open(chart_path, 'rb') as f:
            chart_data['daily_pnl'] = base64.b64encode(f.read()).decode('utf-8')
            
    except Exception as e:
        logger.error(f"Error creating daily P&L chart: {e}")
    
    # 2. 損益分布圖
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # 直方圖
        ax.hist(daily_df['total_pnl'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax.axvline(daily_df['total_pnl'].mean(), color='red', linestyle='--', 
                  label=f'Mean: {daily_df["total_pnl"].mean():.1f}')
        ax.axvline(0, color='black', linestyle='-', alpha=0.5)
        
        ax.set_title('P&L Distribution', fontsize=14, fontweight='bold')
        ax.set_xlabel('P&L (Points)', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        chart_path = 'charts/pnl_distribution.png'
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        with open(chart_path, 'rb') as f:
            chart_data['pnl_distribution'] = base64.b64encode(f.read()).decode('utf-8')
            
    except Exception as e:
        logger.error(f"Error creating P&L distribution chart: {e}")
    
    # 3. 口數貢獻分析
    if not events_df.empty:
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            lot_pnl = events_df.groupby('lot_number')['pnl'].sum()
            colors = ['green' if x > 0 else 'red' for x in lot_pnl.values]
            
            bars = ax.bar([f'Lot {int(i)}' for i in lot_pnl.index], lot_pnl.values, 
                         color=colors, alpha=0.7)
            
            # 添加數值標籤
            for bar, value in zip(bars, lot_pnl.values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + (5 if height >= 0 else -15),
                       f'{value:+.0f}', ha='center', va='bottom' if height >= 0 else 'top')
            
            ax.set_title('Lot Contribution Analysis', fontsize=14, fontweight='bold')
            ax.set_ylabel('P&L (Points)', fontsize=12)
            ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            chart_path = 'charts/lot_contribution.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            with open(chart_path, 'rb') as f:
                chart_data['lot_contribution'] = base64.b64encode(f.read()).decode('utf-8')
                
        except Exception as e:
            logger.error(f"Error creating lot contribution chart: {e}")
    
    return chart_data

def generate_enhanced_html_report(statistics: Dict[str, Any], chart_data: Dict[str, str], config_data: Dict[str, Any], events_df: pd.DataFrame, strategy_summary: str = "", log_content: str = "") -> str:
    """生成增強版HTML報告"""
    basic_metrics = statistics.get('basic_metrics', {})
    risk_metrics = statistics.get('risk_metrics', {})
    lot_analysis = statistics.get('lot_analysis', {})
    position_analysis = statistics.get('position_analysis', {})

    # 策略摘要現在通過參數傳入，如果為空則提供默認值
    if not strategy_summary:
        strategy_summary = "策略摘要生成失敗"

    # 圖表HTML
    charts_html = ""
    if chart_data.get('daily_pnl'):
        charts_html += f"""
        <div class="chart-container">
            <h3>📊 Daily P&L Analysis</h3>
            <img src="data:image/png;base64,{chart_data['daily_pnl']}" alt="Daily P&L Chart" style="max-width: 100%; height: auto;">
        </div>
        """

    if chart_data.get('pnl_distribution'):
        charts_html += f"""
        <div class="chart-container">
            <h3>📈 P&L Distribution</h3>
            <img src="data:image/png;base64,{chart_data['pnl_distribution']}" alt="P&L Distribution Chart" style="max-width: 100%; height: auto;">
        </div>
        """

    if chart_data.get('lot_contribution'):
        charts_html += f"""
        <div class="chart-container">
            <h3>🎯 Lot Contribution Analysis</h3>
            <img src="data:image/png;base64,{chart_data['lot_contribution']}" alt="Lot Contribution Chart" style="max-width: 100%; height: auto;">
        </div>
        """

    # 口數分析表格
    lot_table_html = ""
    if lot_analysis:
        lot_table_html = """
        <div class="table-container">
            <h3>📋 Lot Performance Summary</h3>
            <table class="performance-table">
                <thead>
                    <tr>
                        <th>Lot</th>
                        <th>Total P&L</th>
                        <th>Trades</th>
                        <th>Win Rate</th>
                    </tr>
                </thead>
                <tbody>
        """
        for lot_key, lot_data in lot_analysis.items():
            lot_num = lot_key.replace('lot_', '')
            pnl_class = 'positive' if lot_data['total_pnl'] > 0 else 'negative' if lot_data['total_pnl'] < 0 else 'neutral'
            lot_table_html += f"""
                    <tr>
                        <td>Lot {lot_num}</td>
                        <td class="{pnl_class}">{lot_data['total_pnl']:+.1f}</td>
                        <td>{lot_data['trades']}</td>
                        <td>{lot_data['win_rate']:.1f}%</td>
                    </tr>
            """
        lot_table_html += """
                </tbody>
            </table>
        </div>
        """



    # 添加詳細交易明細表格
    trade_details_html = ""
    if not events_df.empty:
        # 按日期分組顯示交易明細
        trade_details_html = """
        <div class="table-container">
            <h3>📋 Detailed Trade Records</h3>
            <table class="performance-table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Direction</th>
                        <th>Lot</th>
                        <th>Entry Price</th>
                        <th>Exit Price</th>
                        <th>P&L</th>
                        <th>Exit Type</th>
                    </tr>
                </thead>
                <tbody>
        """

        # 出場類型的中文對應
        exit_type_mapping = {
            'trailing_stop': '移動停利',
            'take_profit': '停利',
            'stop_loss': '停損',
            'protective_stop': '保護性停損',
            'risk_management': '風險管理平倉',
            'unknown': '未知'
        }

        for _, trade in events_df.iterrows():
            pnl_class = 'positive' if trade['pnl'] > 0 else 'negative' if trade['pnl'] < 0 else 'neutral'
            direction_icon = '📈' if trade['direction'] == 'LONG' else '📉'
            exit_type_display = exit_type_mapping.get(trade['exit_type'], trade['exit_type'])

            # 特殊處理風險管理平倉
            if trade['exit_type'] == 'risk_management':
                exit_type_display = '🚨 風險管理平倉'

            trade_details_html += f"""
                    <tr>
                        <td>{trade['trade_date']}</td>
                        <td>{direction_icon} {trade['direction']}</td>
                        <td>第{int(trade['lot_number'])}口</td>
                        <td>{trade['entry_price'] if pd.notna(trade['entry_price']) else 'N/A'}</td>
                        <td>{trade['exit_price'] if pd.notna(trade['exit_price']) else 'N/A'}</td>
                        <td class="{pnl_class}">{trade['pnl']:+.0f}</td>
                        <td>{exit_type_display}</td>
                    </tr>
            """

        trade_details_html += """
                </tbody>
            </table>
        </div>
        """

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Trading Strategy Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 25px;
            text-align: center;
            border-left: 5px solid #667eea;
            transition: transform 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2.2em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .neutral {{ color: #6c757d; }}
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            text-align: center;
        }}
        .chart-container h3 {{
            margin-top: 0;
            color: #333;
        }}
        .table-container {{
            margin: 30px 0;
        }}
        .performance-table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .performance-table th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
        }}
        .performance-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        .performance-table tr:hover {{
            background: #f8f9fa;
        }}
        .section-title {{
            font-size: 1.8em;
            color: #333;
            margin: 40px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Enhanced Trading Strategy Analysis</h1>
            <p>Profit-Funded Risk Multi-Lot Strategy Report</p>
            <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>

        <div class="content">
            <!-- 策略摘要 -->
            <h2 class="section-title">📋 Strategy Configuration Summary</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 30px; font-family: monospace; white-space: pre-line; border-left: 4px solid #667eea;">
                {strategy_summary}
            </div>

            <h2 class="section-title">📈 Key Performance Metrics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{basic_metrics.get('total_trades', 0)}</div>
                    <div class="stat-label">Total Trades</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value positive">{basic_metrics.get('winning_trades', 0)}</div>
                    <div class="stat-label">Winning Trades</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value negative">{basic_metrics.get('losing_trades', 0)}</div>
                    <div class="stat-label">Losing Trades</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{basic_metrics.get('win_rate', 0):.1f}%</div>
                    <div class="stat-label">Win Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value {'positive' if basic_metrics.get('total_pnl', 0) > 0 else 'negative' if basic_metrics.get('total_pnl', 0) < 0 else 'neutral'}">{basic_metrics.get('total_pnl', 0):+.1f}</div>
                    <div class="stat-label">Total P&L (Points)</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{basic_metrics.get('profit_factor', 0):.2f}</div>
                    <div class="stat-label">Profit Factor</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value negative">{risk_metrics.get('max_drawdown', 0):.1f}</div>
                    <div class="stat-label">Max Drawdown</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{basic_metrics.get('avg_pnl', 0):+.1f}</div>
                    <div class="stat-label">Avg P&L per Trade</div>
                </div>
            </div>

            <!-- 多空分析 -->
            <h2 class="section-title">⚖️ Long/Short Position Analysis</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{position_analysis.get('long_trades', 0)}</div>
                    <div class="stat-label">Long Entry Signals</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{position_analysis.get('short_trades', 0)}</div>
                    <div class="stat-label">Short Entry Signals</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{position_analysis.get('long_trading_days', 0)}</div>
                    <div class="stat-label">Long Trading Days</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{position_analysis.get('short_trading_days', 0)}</div>
                    <div class="stat-label">Short Trading Days</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value {'positive' if position_analysis.get('long_total_pnl', 0) >= 0 else 'negative'}">{position_analysis.get('long_total_pnl', 0):+.1f}</div>
                    <div class="stat-label">Long Total P&L</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value {'positive' if position_analysis.get('short_total_pnl', 0) >= 0 else 'negative'}">{position_analysis.get('short_total_pnl', 0):+.1f}</div>
                    <div class="stat-label">Short Total P&L</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{position_analysis.get('long_win_rate', 0):.1f}%</div>
                    <div class="stat-label">Long Win Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{position_analysis.get('short_win_rate', 0):.1f}%</div>
                    <div class="stat-label">Short Win Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value {'positive' if position_analysis.get('long_avg_pnl', 0) >= 0 else 'negative'}">{position_analysis.get('long_avg_pnl', 0):+.1f}</div>
                    <div class="stat-label">Long Avg P&L</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value {'positive' if position_analysis.get('short_avg_pnl', 0) >= 0 else 'negative'}">{position_analysis.get('short_avg_pnl', 0):+.1f}</div>
                    <div class="stat-label">Short Avg P&L</div>
                </div>
            </div>

            <h2 class="section-title">📊 Visual Analysis</h2>
            {charts_html}

            {lot_table_html}

            {trade_details_html}

            <!-- 交易日誌詳情 -->
            <h2 class="section-title">📋 Trading Log Details</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 30px; border-left: 4px solid #667eea;">
                <div style="max-height: 400px; overflow-y: auto; font-family: monospace; font-size: 12px; line-height: 1.4; white-space: pre-wrap; background: #ffffff; padding: 15px; border-radius: 5px; border: 1px solid #ddd;">
{log_content}
                </div>
                <p style="margin-top: 10px; color: #666; font-size: 14px;">
                    💡 此日誌用於研究階段數字比對，包含完整的交易執行細節
                </p>
            </div>
        </div>
    </div>
</body>
</html>
    """

    return html_content



def generate_comprehensive_report(log_content: str, config_data: Dict[str, Any]) -> Optional[str]:
    """生成完整的分析報告"""
    try:
        print("📊 開始生成完整分析報告...")

        # 1. 提取交易資料
        print("🔍 提取交易資料...")
        events_df, daily_df = extract_trading_data_from_log(log_content)

        if daily_df.empty:
            print("⚠️ 未找到交易資料")
            return None

        print(f"✅ 提取到 {len(events_df)} 個交易事件和 {len(daily_df)} 個交易日")

        # 2. 計算統計指標
        print("📈 計算統計指標...")
        statistics = calculate_enhanced_statistics(daily_df, events_df)

        # 3. 生成圖表
        print("📊 生成圖表...")
        chart_data = create_enhanced_charts(daily_df, events_df, statistics)

        # 4. 生成策略摘要
        strategy_summary = ""
        try:
            # 使用新的日誌解析方法生成摘要
            strategy_summary = generate_strategy_summary_from_log(log_content, config_data)

            # 如果日誌解析失敗，嘗試原始方法
            if "策略摘要生成錯誤" in strategy_summary:
                if config_data:
                    strategy_config = create_strategy_config_from_gui(config_data)
                    if strategy_config:
                        strategy_summary = format_config_summary(strategy_config)
        except Exception as e:
            strategy_summary = f"策略摘要生成錯誤: {str(e)}"

        # 5. 生成HTML報告
        print("📋 生成HTML報告...")
        report_filename = f"reports/enhanced_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        os.makedirs("reports", exist_ok=True)

        html_content = generate_enhanced_html_report(statistics, chart_data, config_data, events_df, strategy_summary, log_content)

        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ 完整報告生成成功: {report_filename}")
        return report_filename

    except Exception as e:
        print(f"❌ 生成完整報告時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return None
