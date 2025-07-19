#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務 3：直接比較測試
直接調用兩個系統的核心引擎進行比較
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path
import importlib.util

# 設定詳細日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('任務3_直接比較測試.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DirectComparisonTest:
    """直接比較測試器"""
    
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
    
    def test_rev_web_system(self):
        """測試 rev_web_trading_gui 系統"""
        logger.info("🚀 測試 rev_web_trading_gui 系統 (直接API調用)")
        
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
            
            logger.info(f"📋 配置創建完成")
            logger.info(f"   交易方向: {strategy_config.trading_direction}")
            logger.info(f"   停損類型: {strategy_config.stop_loss_type}")
            logger.info(f"   第1口設定: 觸發{self.test_config['lot1_trigger']}點, 回撤{self.test_config['lot1_pullback']}%")
            logger.info(f"   第2口設定: 觸發{self.test_config['lot2_trigger']}點, 回撤{self.test_config['lot2_pullback']}%")
            logger.info(f"   第3口設定: 觸發{self.test_config['lot3_trigger']}點, 回撤{self.test_config['lot3_pullback']}%")
            
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
            logger.info(f"   總交易次數: {result.get('total_trades', 'N/A')}")
            logger.info(f"   勝率: {result.get('win_rate', 'N/A')}")
            
            self.results['rev_web_system'] = {
                'success': True,
                'result': result,
                'method': 'direct_api_call'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ rev_web_trading_gui 測試失敗: {e}")
            self.results['rev_web_system'] = {
                'success': False,
                'error': str(e),
                'method': 'direct_api_call'
            }
            return None
    
    def test_mdd_system(self):
        """測試 mdd_gui 系統"""
        logger.info("🚀 測試 mdd_gui 系統 (直接API調用)")
        
        try:
            # 動態導入實驗版核心模組
            spec = importlib.util.spec_from_file_location(
                "exp_rev_multi_module",
                "experiment_analysis/exp_rev_multi_Profit-Funded Risk_多口.py"
            )
            exp_rev_multi_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(exp_rev_multi_module)
            
            # 導入配置工廠
            from strategy_config_factory import create_config_from_gui_dict
            
            # 創建配置
            strategy_config = create_config_from_gui_dict(self.test_config)
            
            logger.info(f"📋 配置創建完成")
            logger.info(f"   交易方向: {strategy_config.trading_direction}")
            logger.info(f"   停損類型: {strategy_config.stop_loss_type}")
            logger.info(f"   第1口設定: 觸發{self.test_config['lot1_trigger']}點, 回撤{self.test_config['lot1_pullback']}%")
            logger.info(f"   第2口設定: 觸發{self.test_config['lot2_trigger']}點, 回撤{self.test_config['lot2_pullback']}%")
            logger.info(f"   第3口設定: 觸發{self.test_config['lot3_trigger']}點, 回撤{self.test_config['lot3_pullback']}%")
            
            # 執行回測
            logger.info("🔄 開始執行回測...")
            result = exp_rev_multi_module.run_backtest(
                strategy_config,
                self.test_config['start_date'],
                self.test_config['end_date'],
                self.test_config['range_start_time'],
                self.test_config['range_end_time']
            )
            
            logger.info(f"✅ mdd_gui 回測完成")
            logger.info(f"📊 結果摘要:")
            logger.info(f"   總損益: {result.get('total_pnl', 'N/A')}")
            logger.info(f"   最大回撤: {result.get('max_drawdown', 'N/A')}")
            logger.info(f"   多頭損益: {result.get('long_pnl', 'N/A')}")
            logger.info(f"   空頭損益: {result.get('short_pnl', 'N/A')}")
            logger.info(f"   Lot1損益: {result.get('lot1_pnl', 'N/A')}")
            logger.info(f"   Lot2損益: {result.get('lot2_pnl', 'N/A')}")
            logger.info(f"   Lot3損益: {result.get('lot3_pnl', 'N/A')}")
            logger.info(f"   總交易次數: {result.get('total_trades', 'N/A')}")
            logger.info(f"   勝率: {result.get('win_rate', 'N/A')}")
            
            self.results['mdd_system'] = {
                'success': True,
                'result': result,
                'method': 'direct_api_call'
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ mdd_gui 測試失敗: {e}")
            self.results['mdd_system'] = {
                'success': False,
                'error': str(e),
                'method': 'direct_api_call'
            }
            return None
    
    def compare_results(self):
        """詳細比較兩個系統的結果"""
        logger.info("🔍 開始詳細比較結果...")
        
        rev_result = self.results.get('rev_web_system', {}).get('result')
        mdd_result = self.results.get('mdd_system', {}).get('result')
        
        if not rev_result or not mdd_result:
            logger.error("❌ 無法比較結果，其中一個系統執行失敗")
            return []
        
        # 比較關鍵指標
        comparison_fields = [
            'total_pnl', 'max_drawdown', 'long_pnl', 'short_pnl',
            'lot1_pnl', 'lot2_pnl', 'lot3_pnl', 'total_trades', 'win_rate'
        ]
        
        differences = []
        matches = []
        
        logger.info("=" * 80)
        logger.info("詳細比較結果")
        logger.info("=" * 80)
        
        for field in comparison_fields:
            rev_val = rev_result.get(field, 0)
            mdd_val = mdd_result.get(field, 0)
            
            # 處理不同的數據類型
            if rev_val is None:
                rev_val = 0
            if mdd_val is None:
                mdd_val = 0
            
            # 轉換為數值進行比較
            try:
                rev_num = float(rev_val)
                mdd_num = float(mdd_val)
                
                diff = abs(rev_num - mdd_num)
                
                if diff > 0.01:  # 容忍0.01的差異
                    differences.append({
                        'field': field,
                        'rev_web': rev_num,
                        'mdd_gui': mdd_num,
                        'difference': diff,
                        'percentage_diff': (diff / max(abs(rev_num), abs(mdd_num), 0.01)) * 100
                    })
                    logger.warning(f"❌ {field:15s}: rev_web({rev_num:8.2f}) vs mdd_gui({mdd_num:8.2f}), 差異: {diff:6.2f}")
                else:
                    matches.append(field)
                    logger.info(f"✅ {field:15s}: 一致 ({rev_num:8.2f})")
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ {field:15s}: 無法比較 (rev_web: {rev_val}, mdd_gui: {mdd_val}) - {e}")
        
        logger.info("=" * 80)
        logger.info("比較總結")
        logger.info("=" * 80)
        logger.info(f"✅ 一致字段: {len(matches)} 個")
        logger.info(f"❌ 不一致字段: {len(differences)} 個")
        
        if differences:
            logger.error("🚨 發現數據不一致！")
            logger.error("不一致詳情:")
            for diff in differences:
                logger.error(f"   {diff['field']}: 差異 {diff['difference']:.2f} ({diff['percentage_diff']:.1f}%)")
        else:
            logger.info("🎉 兩個系統結果完全一致！")
        
        self.results['comparison'] = {
            'differences': differences,
            'matches': matches,
            'total_differences': len(differences),
            'total_matches': len(matches)
        }
        
        return differences
    
    def save_detailed_report(self):
        """保存詳細報告"""
        report_file = "任務3_直接比較測試報告.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"📋 詳細報告已保存: {report_file}")
            
        except Exception as e:
            logger.error(f"❌ 保存報告失敗: {e}")
    
    def run_comparison(self):
        """執行完整的比較測試"""
        logger.info("🚀 開始直接比較測試...")
        logger.info("=" * 80)
        
        # 1. 測試 rev_web_system
        logger.info("第1步：測試 rev_web_trading_gui 系統")
        logger.info("=" * 80)
        rev_result = self.test_rev_web_system()
        
        logger.info("=" * 80)
        
        # 2. 測試 mdd_system
        logger.info("第2步：測試 mdd_gui 系統")
        logger.info("=" * 80)
        mdd_result = self.test_mdd_system()
        
        logger.info("=" * 80)
        
        # 3. 比較結果
        logger.info("第3步：詳細比較結果")
        logger.info("=" * 80)
        differences = self.compare_results()
        
        logger.info("=" * 80)
        
        # 4. 保存報告
        logger.info("第4步：保存詳細報告")
        logger.info("=" * 80)
        self.save_detailed_report()
        
        # 5. 總結
        logger.info("=" * 80)
        logger.info("測試總結")
        logger.info("=" * 80)
        
        if self.results.get('rev_web_system', {}).get('success') and self.results.get('mdd_system', {}).get('success'):
            if differences:
                logger.error(f"🚨 發現 {len(differences)} 個差異！")
                logger.error("這證實了兩個系統確實存在計算不一致的問題。")
                for diff in differences:
                    logger.error(f"   {diff['field']}: 差異 {diff['difference']:.2f}")
            else:
                logger.info("🎉 兩個系統結果完全一致！")
                logger.info("這表明問題可能在於其他層面，如數據處理或配置差異。")
        else:
            logger.error("❌ 測試未能完成，無法得出結論。")

def main():
    """主函數"""
    tester = DirectComparisonTest()
    tester.run_comparison()

if __name__ == "__main__":
    main()
