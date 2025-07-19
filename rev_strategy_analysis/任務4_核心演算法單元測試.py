#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任務 4：核心演算法的隔離單元測試
將PNL和MDD計算邏輯完全剝離出來，排除其他因素干擾，只驗證演算法本身的一致性
"""

import unittest
import sys
import os
import logging
from decimal import Decimal
from datetime import datetime
from pathlib import Path
import importlib.util

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('任務4_核心演算法單元測試.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CoreAlgorithmTest(unittest.TestCase):
    """核心演算法一致性測試"""
    
    @classmethod
    def setUpClass(cls):
        """測試類初始化"""
        logger.info("🚀 開始核心演算法隔離單元測試...")
        
        # 導入兩個核心模組
        cls.rev_web_module = cls._import_module(
            "rev_multi_module",
            "rev_multi_Profit-Funded Risk_多口.py"
        )
        
        cls.mdd_module = cls._import_module(
            "exp_rev_multi_module", 
            "experiment_analysis/exp_rev_multi_Profit-Funded Risk_多口.py"
        )
        
        # 導入配置工廠
        from strategy_config_factory import create_config_from_gui_dict
        cls.create_config_func = create_config_from_gui_dict
        
        # 測試配置
        cls.test_config_dict = {
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
        
        logger.info("✅ 測試環境初始化完成")
    
    @staticmethod
    def _import_module(module_name, file_path):
        """動態導入模組"""
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            logger.info(f"✅ 成功導入模組: {file_path}")
            return module
        except Exception as e:
            logger.error(f"❌ 導入模組失敗 {file_path}: {e}")
            return None
    
    def test_01_module_import(self):
        """測試1：模組導入測試"""
        logger.info("=" * 60)
        logger.info("測試1：模組導入測試")
        logger.info("=" * 60)
        
        self.assertIsNotNone(self.rev_web_module, "rev_web_module 導入失敗")
        self.assertIsNotNone(self.mdd_module, "mdd_module 導入失敗")
        
        # 檢查關鍵函數是否存在
        self.assertTrue(hasattr(self.rev_web_module, 'run_backtest'), "rev_web_module 缺少 run_backtest 函數")
        self.assertTrue(hasattr(self.mdd_module, 'run_backtest'), "mdd_module 缺少 run_backtest 函數")
        
        logger.info("✅ 所有模組導入成功，關鍵函數存在")
    
    def test_02_config_creation(self):
        """測試2：配置創建一致性測試"""
        logger.info("=" * 60)
        logger.info("測試2：配置創建一致性測試")
        logger.info("=" * 60)
        
        config = self.__class__.create_config_func(self.test_config_dict)
        
        self.assertIsNotNone(config, "配置創建失敗")
        self.assertEqual(config.trading_direction, 'BOTH', "交易方向設定錯誤")
        self.assertEqual(config.trade_size_in_lots, 3, "交易口數設定錯誤")
        
        logger.info(f"✅ 配置創建成功")
        logger.info(f"   交易方向: {config.trading_direction}")
        logger.info(f"   交易口數: {config.trade_size_in_lots}")
        logger.info(f"   停損類型: {config.stop_loss_type}")
    
    def test_03_backtest_execution(self):
        """測試3：回測執行測試"""
        logger.info("=" * 60)
        logger.info("測試3：回測執行測試")
        logger.info("=" * 60)
        
        config = self.__class__.create_config_func(self.test_config_dict)
        
        # 測試 rev_web_module
        logger.info("🔄 測試 rev_web_module...")
        try:
            rev_result = self.rev_web_module.run_backtest(
                config,
                self.test_config_dict['start_date'],
                self.test_config_dict['end_date'],
                self.test_config_dict['range_start_time'],
                self.test_config_dict['range_end_time']
            )
            logger.info("✅ rev_web_module 執行成功")
        except Exception as e:
            logger.error(f"❌ rev_web_module 執行失敗: {e}")
            rev_result = None
        
        # 測試 mdd_module
        logger.info("🔄 測試 mdd_module...")
        try:
            mdd_result = self.mdd_module.run_backtest(
                config,
                self.test_config_dict['start_date'],
                self.test_config_dict['end_date'],
                self.test_config_dict['range_start_time'],
                self.test_config_dict['range_end_time']
            )
            logger.info("✅ mdd_module 執行成功")
        except Exception as e:
            logger.error(f"❌ mdd_module 執行失敗: {e}")
            mdd_result = None
        
        # 保存結果供後續測試使用
        self.rev_result = rev_result
        self.mdd_result = mdd_result
        
        self.assertIsNotNone(rev_result, "rev_web_module 回測失敗")
        self.assertIsNotNone(mdd_result, "mdd_module 回測失敗")
    
    def test_04_pnl_calculation_consistency(self):
        """測試4：PNL計算一致性測試"""
        logger.info("=" * 60)
        logger.info("測試4：PNL計算一致性測試")
        logger.info("=" * 60)
        
        # 確保前面的測試已執行
        if not hasattr(self, 'rev_result') or not hasattr(self, 'mdd_result'):
            self.test_03_backtest_execution()
        
        rev_result = self.rev_result
        mdd_result = self.mdd_result
        
        # 比較總損益
        rev_total_pnl = float(rev_result.get('total_pnl', 0))
        mdd_total_pnl = float(mdd_result.get('total_pnl', 0))
        
        logger.info(f"rev_web_module 總損益: {rev_total_pnl}")
        logger.info(f"mdd_module 總損益: {mdd_total_pnl}")
        
        self.assertAlmostEqual(
            rev_total_pnl, mdd_total_pnl, places=2,
            msg=f"總損益不一致: rev_web({rev_total_pnl}) vs mdd({mdd_total_pnl})"
        )
        
        # 比較多空損益
        rev_long_pnl = float(rev_result.get('long_pnl', 0))
        mdd_long_pnl = float(mdd_result.get('long_pnl', 0))
        
        rev_short_pnl = float(rev_result.get('short_pnl', 0))
        mdd_short_pnl = float(mdd_result.get('short_pnl', 0))
        
        logger.info(f"多頭損益: rev_web({rev_long_pnl}) vs mdd({mdd_long_pnl})")
        logger.info(f"空頭損益: rev_web({rev_short_pnl}) vs mdd({mdd_short_pnl})")
        
        self.assertAlmostEqual(
            rev_long_pnl, mdd_long_pnl, places=2,
            msg=f"多頭損益不一致: rev_web({rev_long_pnl}) vs mdd({mdd_long_pnl})"
        )
        
        self.assertAlmostEqual(
            rev_short_pnl, mdd_short_pnl, places=2,
            msg=f"空頭損益不一致: rev_web({rev_short_pnl}) vs mdd({mdd_short_pnl})"
        )
        
        logger.info("✅ PNL計算一致性測試通過")
    
    def test_05_mdd_calculation_consistency(self):
        """測試5：MDD計算一致性測試"""
        logger.info("=" * 60)
        logger.info("測試5：MDD計算一致性測試")
        logger.info("=" * 60)
        
        # 確保前面的測試已執行
        if not hasattr(self, 'rev_result') or not hasattr(self, 'mdd_result'):
            self.test_03_backtest_execution()
        
        rev_result = self.rev_result
        mdd_result = self.mdd_result
        
        # 比較最大回撤
        rev_mdd = float(rev_result.get('max_drawdown', 0))
        mdd_mdd = float(mdd_result.get('max_drawdown', 0))
        
        logger.info(f"rev_web_module 最大回撤: {rev_mdd}")
        logger.info(f"mdd_module 最大回撤: {mdd_mdd}")
        
        self.assertAlmostEqual(
            rev_mdd, mdd_mdd, places=2,
            msg=f"最大回撤不一致: rev_web({rev_mdd}) vs mdd({mdd_mdd})"
        )
        
        # 比較峰值損益
        rev_peak = float(rev_result.get('peak_pnl', 0))
        mdd_peak = float(mdd_result.get('peak_pnl', 0))
        
        logger.info(f"峰值損益: rev_web({rev_peak}) vs mdd({mdd_peak})")
        
        self.assertAlmostEqual(
            rev_peak, mdd_peak, places=2,
            msg=f"峰值損益不一致: rev_web({rev_peak}) vs mdd({mdd_peak})"
        )
        
        logger.info("✅ MDD計算一致性測試通過")
    
    def test_06_lot_pnl_consistency(self):
        """測試6：各口損益一致性測試"""
        logger.info("=" * 60)
        logger.info("測試6：各口損益一致性測試")
        logger.info("=" * 60)
        
        # 確保前面的測試已執行
        if not hasattr(self, 'rev_result') or not hasattr(self, 'mdd_result'):
            self.test_03_backtest_execution()
        
        rev_result = self.rev_result
        mdd_result = self.mdd_result
        
        # 比較各口損益
        for lot_num in [1, 2, 3]:
            lot_key = f'lot{lot_num}_pnl'
            
            rev_lot_pnl = float(rev_result.get(lot_key, 0))
            mdd_lot_pnl = float(mdd_result.get(lot_key, 0))
            
            logger.info(f"第{lot_num}口損益: rev_web({rev_lot_pnl}) vs mdd({mdd_lot_pnl})")
            
            self.assertAlmostEqual(
                rev_lot_pnl, mdd_lot_pnl, places=2,
                msg=f"第{lot_num}口損益不一致: rev_web({rev_lot_pnl}) vs mdd({mdd_lot_pnl})"
            )
        
        logger.info("✅ 各口損益一致性測試通過")
    
    def test_07_trade_statistics_consistency(self):
        """測試7：交易統計一致性測試"""
        logger.info("=" * 60)
        logger.info("測試7：交易統計一致性測試")
        logger.info("=" * 60)
        
        # 確保前面的測試已執行
        if not hasattr(self, 'rev_result') or not hasattr(self, 'mdd_result'):
            self.test_03_backtest_execution()
        
        rev_result = self.rev_result
        mdd_result = self.mdd_result
        
        # 比較交易次數
        rev_trades = int(rev_result.get('total_trades', 0))
        mdd_trades = int(mdd_result.get('total_trades', 0))
        
        logger.info(f"總交易次數: rev_web({rev_trades}) vs mdd({mdd_trades})")
        
        self.assertEqual(
            rev_trades, mdd_trades,
            msg=f"總交易次數不一致: rev_web({rev_trades}) vs mdd({mdd_trades})"
        )
        
        # 比較勝率
        rev_win_rate = float(rev_result.get('win_rate', 0))
        mdd_win_rate = float(mdd_result.get('win_rate', 0))
        
        logger.info(f"勝率: rev_web({rev_win_rate}%) vs mdd({mdd_win_rate}%)")
        
        self.assertAlmostEqual(
            rev_win_rate, mdd_win_rate, places=2,
            msg=f"勝率不一致: rev_web({rev_win_rate}) vs mdd({mdd_win_rate})"
        )
        
        logger.info("✅ 交易統計一致性測試通過")
    
    def test_08_comprehensive_validation(self):
        """測試8：綜合驗證測試"""
        logger.info("=" * 60)
        logger.info("測試8：綜合驗證測試")
        logger.info("=" * 60)
        
        # 確保前面的測試已執行
        if not hasattr(self, 'rev_result') or not hasattr(self, 'mdd_result'):
            self.test_03_backtest_execution()
        
        rev_result = self.rev_result
        mdd_result = self.mdd_result
        
        # 綜合比較所有關鍵指標
        comparison_fields = [
            'total_pnl', 'max_drawdown', 'long_pnl', 'short_pnl',
            'lot1_pnl', 'lot2_pnl', 'lot3_pnl', 'total_trades', 'win_rate'
        ]
        
        all_consistent = True
        differences = []
        
        for field in comparison_fields:
            rev_val = float(rev_result.get(field, 0))
            mdd_val = float(mdd_result.get(field, 0))
            
            diff = abs(rev_val - mdd_val)
            
            if diff > 0.01:  # 容忍0.01的差異
                all_consistent = False
                differences.append({
                    'field': field,
                    'rev_web': rev_val,
                    'mdd_gui': mdd_val,
                    'difference': diff
                })
                logger.warning(f"❌ {field}: rev_web({rev_val}) vs mdd({mdd_val}), 差異: {diff}")
            else:
                logger.info(f"✅ {field}: 一致 ({rev_val})")
        
        if all_consistent:
            logger.info("🎉 綜合驗證通過：兩個系統完全一致！")
        else:
            logger.error(f"🚨 綜合驗證失敗：發現 {len(differences)} 個不一致項目")
            for diff in differences:
                logger.error(f"   {diff['field']}: 差異 {diff['difference']}")
        
        self.assertTrue(all_consistent, f"系統不一致，發現 {len(differences)} 個差異")

def main():
    """主函數"""
    # 創建測試套件
    suite = unittest.TestLoader().loadTestsFromTestCase(CoreAlgorithmTest)
    
    # 執行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 輸出測試結果摘要
    logger.info("=" * 80)
    logger.info("測試結果摘要")
    logger.info("=" * 80)
    logger.info(f"執行測試: {result.testsRun}")
    logger.info(f"失敗測試: {len(result.failures)}")
    logger.info(f"錯誤測試: {len(result.errors)}")
    
    if result.failures:
        logger.error("失敗的測試:")
        for test, traceback in result.failures:
            logger.error(f"  - {test}: {traceback}")
    
    if result.errors:
        logger.error("錯誤的測試:")
        for test, traceback in result.errors:
            logger.error(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        logger.info("🎉 所有測試通過！兩個系統的核心演算法完全一致。")
        return True
    else:
        logger.error("❌ 測試失敗！兩個系統存在不一致問題。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
