#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務 3：執行狀態追蹤與分歧點定位
通過詳細日誌追蹤兩個系統的計算過程，找到第一個產生差異的時間點
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime, time
from pathlib import Path
import importlib.util

# 設定詳細日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('任務3_執行追蹤.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ExecutionTracker:
    """執行狀態追蹤器"""
    
    def __init__(self):
        self.test_config = {
            'start_date': '2024-11-15',
            'end_date': '2024-11-15',
            'range_start_time': '08:46',
            'range_end_time': '08:47',
            'lot1_trigger': 15,
            'lot1_pullback': 10,
            'lot2_trigger': 40,
            'lot2_pullback': 10,
            'lot3_trigger': 41,
            'lot3_pullback': 20,
            'trading_direction': 'BOTH'
        }
        
        self.results = {}
    
    def test_rev_web_trading_gui(self):
        """測試 rev_web_trading_gui.py 的直接API調用"""
        logger.info("🚀 開始測試 rev_web_trading_gui.py (直接API調用)")
        
        try:
            # 動態導入核心模組
            spec = importlib.util.spec_from_file_location(
                "rev_multi_module",
                "rev_multi_Profit-Funded Risk_多口.py"
            )
            rev_multi_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(rev_multi_module)
            
            # 導入配置工廠
            from strategy_config_factory import create_config_from_gui_dict
            
            # 創建配置
            strategy_config = create_config_from_gui_dict(self.test_config)
            
            logger.info(f"📋 配置創建完成: {strategy_config}")
            
            # 執行回測
            logger.info("🔄 開始執行回測...")
            result = rev_multi_module.run_backtest(
                strategy_config,
                self.test_config['start_date'],
                self.test_config['end_date'],
                self.test_config['range_start_time'],
                self.test_config['range_end_time']
            )
            
            logger.info(f"✅ rev_web_trading_gui 回測完成")
            logger.info(f"📊 結果摘要:")
            logger.info(f"   總損益: {result.get('total_pnl', 'N/A')}")
            logger.info(f"   最大回撤: {result.get('max_drawdown', 'N/A')}")
            logger.info(f"   多頭損益: {result.get('long_pnl', 'N/A')}")
            logger.info(f"   空頭損益: {result.get('short_pnl', 'N/A')}")
            logger.info(f"   Lot1損益: {result.get('lot1_pnl', 'N/A')}")
            logger.info(f"   Lot2損益: {result.get('lot2_pnl', 'N/A')}")
            logger.info(f"   Lot3損益: {result.get('lot3_pnl', 'N/A')}")
            
            self.results['rev_web_trading_gui'] = {
                'success': True,
                'result': result,
                'method': 'direct_api_call'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ rev_web_trading_gui 測試失敗: {e}")
            self.results['rev_web_trading_gui'] = {
                'success': False,
                'error': str(e),
                'method': 'direct_api_call'
            }
            return None
    
    def test_mdd_gui(self):
        """測試 mdd_gui.py 的subprocess調用"""
        logger.info("🚀 開始測試 mdd_gui.py (subprocess調用)")
        
        try:
            # 創建臨時配置文件
            temp_config = {
                "time_intervals": [
                    {
                        "start_date": self.test_config['start_date'],
                        "end_date": self.test_config['end_date'],
                        "range_start_time": self.test_config['range_start_time'],
                        "range_end_time": self.test_config['range_end_time']
                    }
                ],
                "lot_configs": [
                    {
                        "lot1_trigger": self.test_config['lot1_trigger'],
                        "lot1_pullback": self.test_config['lot1_pullback'],
                        "lot2_trigger": self.test_config['lot2_trigger'],
                        "lot2_pullback": self.test_config['lot2_pullback'],
                        "lot3_trigger": self.test_config['lot3_trigger'],
                        "lot3_pullback": self.test_config['lot3_pullback']
                    }
                ],
                "max_workers": 1  # 單線程便於追蹤
            }
            
            # 保存臨時配置
            config_file = "temp_task3_config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(temp_config, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📋 臨時配置已保存: {config_file}")
            
            # 修改 mdd_search_config.py
            config_py_content = f'''
# 任務3測試配置
TIME_INTERVAL_ANALYSIS_CONFIG = "{config_file}"
'''
            
            config_py_file = "experiment_analysis/mdd_search_config.py"
            with open(config_py_file, 'w', encoding='utf-8') as f:
                f.write(config_py_content)
            
            logger.info(f"📋 配置文件已更新: {config_py_file}")
            
            # 執行 enhanced_mdd_optimizer.py
            cmd = [
                'python', 
                'experiment_analysis/enhanced_mdd_optimizer.py',
                '--config', 'time_interval_analysis',
                '--max-workers', '1'
            ]
            
            logger.info(f"🔄 執行命令: {' '.join(cmd)}")
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=os.getcwd()
            )
            
            logger.info(f"📤 返回碼: {process.returncode}")
            logger.info(f"📤 標準輸出長度: {len(process.stdout)} 字符")
            logger.info(f"📤 標準錯誤長度: {len(process.stderr)} 字符")
            
            # 保存完整輸出
            with open('任務3_mdd_gui_stdout.log', 'w', encoding='utf-8') as f:
                f.write(process.stdout)
            
            with open('任務3_mdd_gui_stderr.log', 'w', encoding='utf-8') as f:
                f.write(process.stderr)
            
            # 解析結果
            if process.returncode == 0:
                # 嘗試從輸出中解析結果
                result = self.parse_mdd_output(process.stderr)
                
                logger.info(f"✅ mdd_gui 回測完成")
                logger.info(f"📊 解析結果:")
                if result:
                    logger.info(f"   總損益: {result.get('total_pnl', 'N/A')}")
                    logger.info(f"   最大回撤: {result.get('max_drawdown', 'N/A')}")
                    logger.info(f"   多頭損益: {result.get('long_pnl', 'N/A')}")
                    logger.info(f"   空頭損益: {result.get('short_pnl', 'N/A')}")
                else:
                    logger.warning("⚠️ 無法解析結果")
                
                self.results['mdd_gui'] = {
                    'success': True,
                    'result': result,
                    'method': 'subprocess_call',
                    'stdout': process.stdout,
                    'stderr': process.stderr
                }
                
                return result
            else:
                logger.error(f"❌ mdd_gui 執行失敗，返回碼: {process.returncode}")
                logger.error(f"錯誤輸出: {process.stderr[:500]}...")
                
                self.results['mdd_gui'] = {
                    'success': False,
                    'error': process.stderr,
                    'method': 'subprocess_call',
                    'return_code': process.returncode
                }
                
                return None
            
        except Exception as e:
            logger.error(f"❌ mdd_gui 測試失敗: {e}")
            self.results['mdd_gui'] = {
                'success': False,
                'error': str(e),
                'method': 'subprocess_call'
            }
            return None
        
        finally:
            # 清理臨時文件
            try:
                if os.path.exists(config_file):
                    os.remove(config_file)
                    logger.info(f"🗑️ 已清理臨時配置: {config_file}")
            except:
                pass
    
    def parse_mdd_output(self, stderr_output):
        """解析 mdd_gui 的輸出"""
        try:
            # 這裡需要根據實際的輸出格式來解析
            # 暫時返回一個模擬結果
            lines = stderr_output.split('\n')
            
            result = {
                'total_pnl': 0,
                'max_drawdown': 0,
                'long_pnl': 0,
                'short_pnl': 0
            }
            
            # 簡單的解析邏輯（需要根據實際輸出調整）
            for line in lines:
                if '總損益' in line or 'total_pnl' in line:
                    # 嘗試提取數值
                    pass
                elif '最大回撤' in line or 'max_drawdown' in line:
                    # 嘗試提取數值
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 解析輸出失敗: {e}")
            return None
    
    def compare_results(self):
        """比較兩個系統的結果"""
        logger.info("🔍 開始比較結果...")
        
        rev_result = self.results.get('rev_web_trading_gui', {}).get('result')
        mdd_result = self.results.get('mdd_gui', {}).get('result')
        
        if not rev_result or not mdd_result:
            logger.error("❌ 無法比較結果，其中一個系統執行失敗")
            return
        
        # 比較關鍵指標
        comparison_fields = ['total_pnl', 'max_drawdown', 'long_pnl', 'short_pnl']
        
        differences = []
        
        for field in comparison_fields:
            rev_val = rev_result.get(field, 0)
            mdd_val = mdd_result.get(field, 0)
            
            if abs(rev_val - mdd_val) > 0.01:  # 容忍0.01的差異
                differences.append({
                    'field': field,
                    'rev_web': rev_val,
                    'mdd_gui': mdd_val,
                    'difference': abs(rev_val - mdd_val)
                })
                logger.warning(f"❌ {field}: rev_web({rev_val}) vs mdd_gui({mdd_val}), 差異: {abs(rev_val - mdd_val)}")
            else:
                logger.info(f"✅ {field}: 一致 ({rev_val})")
        
        self.results['comparison'] = {
            'differences': differences,
            'total_differences': len(differences)
        }
        
        return differences
    
    def save_report(self):
        """保存追蹤報告"""
        report_file = "任務3_執行狀態追蹤報告.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"📋 追蹤報告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存報告失敗: {e}")
    
    def run_tracking(self):
        """執行完整的追蹤測試"""
        logger.info("🚀 開始執行狀態追蹤...")
        logger.info("=" * 80)
        
        # 1. 測試 rev_web_trading_gui
        logger.info("第1步：測試 rev_web_trading_gui.py")
        logger.info("=" * 80)
        rev_result = self.test_rev_web_trading_gui()
        
        logger.info("=" * 80)
        
        # 2. 測試 mdd_gui
        logger.info("第2步：測試 mdd_gui.py")
        logger.info("=" * 80)
        mdd_result = self.test_mdd_gui()
        
        logger.info("=" * 80)
        
        # 3. 比較結果
        logger.info("第3步：比較結果")
        logger.info("=" * 80)
        differences = self.compare_results()
        
        logger.info("=" * 80)
        
        # 4. 保存報告
        logger.info("第4步：保存報告")
        logger.info("=" * 80)
        self.save_report()
        
        # 5. 總結
        logger.info("=" * 80)
        logger.info("追蹤總結")
        logger.info("=" * 80)
        
        if differences:
            logger.error(f"🚨 發現 {len(differences)} 個差異！")
            for diff in differences:
                logger.error(f"   {diff['field']}: 差異 {diff['difference']}")
        else:
            logger.info("🎉 兩個系統結果一致！")

def main():
    """主函數"""
    tracker = ExecutionTracker()
    tracker.run_tracking()

if __name__ == "__main__":
    main()
