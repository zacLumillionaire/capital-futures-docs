# backtest_analyzer.py - 主分析程式
"""
策略分析工具主程式
整合所有分析模組，提供完整的策略分析功能
"""

import logging
import argparse
import sys
from pathlib import Path
from typing import Optional

from config import LOGGING_CONFIG, BACKTEST_FILE
from utils import setup_logging
from data_extractor import extract_trading_data, extract_from_sample_data, extract_from_live_log
from statistics_calculator import calculate_strategy_statistics
from visualization import create_all_visualizations
from report_generator import generate_strategy_report

# 設定日誌
setup_logging(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

class BacktestAnalyzer:
    """回測分析器主類別"""
    
    def __init__(self, use_sample_data: bool = False):
        self.use_sample_data = use_sample_data
        self.daily_df = None
        self.events_df = None
        self.statistics = None
        self.chart_files = None
        
    def run_complete_analysis(self) -> str:
        """執行完整的策略分析"""
        logger.info("🚀 開始執行策略分析...")
        
        try:
            # 步驟1: 提取交易資料
            logger.info("📊 步驟1: 提取交易資料...")
            self._extract_data()
            
            if self.daily_df.empty:
                logger.error("❌ 沒有找到交易資料，分析終止")
                return ""
            
            logger.info(f"✅ 成功提取 {len(self.events_df)} 個交易事件和 {len(self.daily_df)} 個交易日資料")
            
            # 步驟2: 計算統計指標
            logger.info("📈 步驟2: 計算統計指標...")
            self.statistics = calculate_strategy_statistics(self.daily_df, self.events_df)
            logger.info("✅ 統計指標計算完成")
            
            # 步驟3: 生成視覺化圖表
            logger.info("📊 步驟3: 生成視覺化圖表...")
            self.chart_files = create_all_visualizations(self.daily_df, self.events_df, self.statistics)
            logger.info(f"✅ 成功生成 {len(self.chart_files)} 個圖表")
            
            # 步驟4: 生成分析報告
            logger.info("📋 步驟4: 生成分析報告...")
            report_file = generate_strategy_report(self.daily_df, self.events_df, 
                                                 self.statistics, self.chart_files)
            logger.info(f"✅ 分析報告已生成: {report_file}")
            
            # 顯示摘要
            self._print_analysis_summary()
            
            logger.info("🎉 策略分析完成！")
            return report_file
            
        except Exception as e:
            logger.error(f"❌ 分析過程中發生錯誤: {e}", exc_info=True)
            return ""
    
    def _extract_data(self):
        """提取交易資料"""
        if self.use_sample_data:
            logger.info("使用範例資料進行分析...")
            self.events_df, self.daily_df = extract_from_sample_data()
        else:
            logger.info("即時執行回測程式並捕獲日誌...")
            self.events_df, self.daily_df = extract_from_live_log()
    
    def _print_analysis_summary(self):
        """列印分析摘要"""
        if not self.statistics:
            return
        
        basic = self.statistics.get('basic_metrics', {})
        risk = self.statistics.get('risk_metrics', {})
        
        print("\n" + "="*60)
        print("🎯 策略分析摘要報告")
        print("="*60)
        print(f"📅 分析期間: {self._get_analysis_period()}")
        print(f"📊 總交易次數: {basic.get('total_trades', 0)}")
        print(f"🏆 獲利次數: {basic.get('winning_trades', 0)}")
        print(f"📉 虧損次數: {basic.get('losing_trades', 0)}")
        print(f"🎯 勝率: {basic.get('win_rate', 0):.2f}%")
        print(f"💰 總損益: {basic.get('total_pnl', 0):.2f} 點")
        print(f"📈 平均損益: {basic.get('avg_pnl', 0):.2f} 點")
        print(f"⚡ 獲利因子: {basic.get('profit_factor', 0):.2f}")
        print(f"📉 最大回撤: {risk.get('max_drawdown', 0):.2%}")
        print(f"📊 夏普比率: {risk.get('sharpe_ratio', 0):.2f}")
        print("="*60)
        
        # 圖表檔案列表
        if self.chart_files:
            print("📊 生成的圖表檔案:")
            for chart_type, filepath in self.chart_files.items():
                if filepath:
                    print(f"   • {chart_type}: {Path(filepath).name}")
        
        print("="*60)
    
    def _get_analysis_period(self) -> str:
        """獲取分析期間"""
        if self.daily_df is None or self.daily_df.empty:
            return "無資料"
        
        try:
            start_date = self.daily_df['trade_date'].min()
            end_date = self.daily_df['trade_date'].max()
            return f"{start_date} 至 {end_date}"
        except:
            return "無法確定"

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='策略回測分析工具')
    parser.add_argument('--sample', action='store_true',
                       help='使用範例資料進行分析')
    parser.add_argument('--live', action='store_true',
                       help='即時執行回測程式並捕獲日誌（預設模式）')
    parser.add_argument('--backtest-file', type=str,
                       help='指定回測程式檔案路徑')

    args = parser.parse_args()

    # 如果沒有指定任何模式，預設使用即時模式
    if not args.sample and not args.live:
        args.live = True
    
    # 歡迎訊息
    print("\n" + "="*60)
    print("🎯 策略回測分析工具")
    print("="*60)
    print("本工具將為您的交易策略提供完整的分析報告")
    print("包含統計指標、視覺化圖表和詳細報告")
    print("="*60)
    
    # 建立分析器
    analyzer = BacktestAnalyzer(use_sample_data=args.sample)
    
    # 執行分析
    report_file = analyzer.run_complete_analysis()
    
    if report_file:
        print(f"\n🎉 分析完成！")
        print(f"📋 詳細報告: {report_file}")
        print(f"📊 圖表目錄: charts/")
        print(f"📁 資料目錄: data/processed/")
        
        # 詢問是否開啟報告
        try:
            response = input("\n是否要開啟HTML報告？(y/n): ").lower().strip()
            if response in ['y', 'yes', '是']:
                import webbrowser
                webbrowser.open(f"file://{Path(report_file).absolute()}")
                print("📖 報告已在瀏覽器中開啟")
        except KeyboardInterrupt:
            print("\n👋 再見！")
    else:
        print("\n❌ 分析失敗，請檢查日誌了解詳細錯誤訊息")
        sys.exit(1)

if __name__ == "__main__":
    main()
