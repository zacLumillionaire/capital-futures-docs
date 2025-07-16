#!/usr/bin/env python3
"""
快速配置修改範例

這個文件展示如何快速修改主程式的關鍵參數，
您可以複製這些代碼片段到 rev_future_path_analyzer.py 中使用。
"""

from decimal import Decimal
from rev_strategy_core import StrategyConfig, LotRule, RangeFilter, RiskConfig, StopLossType

# ==============================================================================
# 🚀 快速修改：分析參數
# ==============================================================================

# 原始設定 (在 rev_future_path_analyzer.py 第 237-241 行)
"""
NUM_SIMULATIONS = 2000      # 模擬次數
NUM_FUTURE_DAYS = 60        # 未來預測天數
PROFIT_TARGET_PCT = 0.20    # 獲利目標 20%
RISK_LIMIT_PCT = 0.15       # 風險底線 15%
INITIAL_CAPITAL = 100000    # 起始資金 100,000 點
"""

# 修改為快速測試 (複製到主程式中)
NUM_SIMULATIONS = 1000      # 減少模擬次數，加快執行速度
NUM_FUTURE_DAYS = 30        # 減少預測天數
PROFIT_TARGET_PCT = 0.15    # 調整獲利目標為 15%
RISK_LIMIT_PCT = 0.10       # 調整風險底線為 10%
INITIAL_CAPITAL = 50000     # 調整起始資金為 50,000 點

# ==============================================================================
# 📅 快速修改：回測時間範圍
# ==============================================================================

# 原始設定 (在 rev_future_path_analyzer.py 第 307-315 行)
"""
backtest_results = run_rev_backtest(
    config=strategy_config,
    start_date="2024-11-04",  # 開始日期
    end_date="2025-06-28",    # 結束日期
    silent=False,
    range_start_time="08:46", # 開盤區間開始時間
    range_end_time="08:47",   # 開盤區間結束時間
    enable_console_log=True
)
"""

# 修改為最近3個月 (複製到主程式中)
backtest_results = run_rev_backtest(
    config=strategy_config,
    start_date="2025-04-01",  # 修改開始日期
    end_date="2025-06-28",    # 修改結束日期
    silent=False,
    range_start_time="08:45", # 修改開盤區間開始時間
    range_end_time="08:48",   # 修改開盤區間結束時間
    enable_console_log=True
)

# ==============================================================================
# ⚙️ 快速修改：策略參數
# ==============================================================================

# 原始設定 (在 rev_future_path_analyzer.py 第 255-287 行)
"""
strategy_config = StrategyConfig(
    trade_size_in_lots=3,
    stop_loss_type=StopLossType.RANGE_BOUNDARY,
    lot_rules=[...],
    range_filter=RangeFilter(...),
    trading_direction="BOTH"
)
"""

# ==============================================================================
# 🎯 常用修改1: 調整觸發點數和回檔比例
# ==============================================================================

# 修改第1口參數 (複製到主程式的 lot_rules 中)
LotRule(
    use_trailing_stop=True,
    trailing_activation=Decimal(20),      # 從15改為20點觸發
    trailing_pullback=Decimal('0.15')    # 從10%改為15%回檔
)

# 修改第2口參數
LotRule(
    use_trailing_stop=True,
    trailing_activation=Decimal(35),      # 從40改為35點觸發
    trailing_pullback=Decimal('0.12'),   # 從10%改為12%回檔
    protective_stop_multiplier=Decimal('1.5')  # 從2.0改為1.5倍保護
)

# 修改第3口參數
LotRule(
    use_trailing_stop=True,
    trailing_activation=Decimal(45),      # 從41改為45點觸發
    trailing_pullback=Decimal('0.25'),   # 從20%改為25%回檔
    protective_stop_multiplier=Decimal('1.8')  # 從2.0改為1.8倍保護
)

# ==============================================================================
# 🎯 常用修改2: 調整區間過濾
# ==============================================================================

# 修改區間過濾設定 (複製到主程式的 range_filter 中)
range_filter=RangeFilter(
    use_range_size_filter=True,
    max_range_points=Decimal(120)         # 從160改為120點上限
)

# 關閉區間過濾
range_filter=RangeFilter(
    use_range_size_filter=False           # 關閉區間過濾
)

# ==============================================================================
# 🎯 常用修改3: 調整交易方向
# ==============================================================================

# 只做多
trading_direction="LONG_ONLY"

# 只做空
trading_direction="SHORT_ONLY"

# 多空都做 (預設)
trading_direction="BOTH"

# ==============================================================================
# 🎯 常用修改4: 啟用風險管理
# ==============================================================================

# 添加風險管理設定 (複製到主程式的 StrategyConfig 中)
risk_config=RiskConfig(
    use_risk_filter=True,
    daily_loss_limit=Decimal(100),        # 每日虧損限制100點
    profit_target=Decimal(200)            # 每日獲利目標200點
)

# ==============================================================================
# 🎯 常用修改5: 使用固定停損停利
# ==============================================================================

# 修改為固定停損停利模式
LotRule(
    use_trailing_stop=False,              # 關閉移動停損
    fixed_stop_loss_points=Decimal(15),   # 固定15點停損
    fixed_tp_points=Decimal(30)           # 固定30點停利
)

# ==============================================================================
# 🔧 完整配置範例：保守型設定
# ==============================================================================

# 完整的保守型配置 (複製整段到主程式中)
strategy_config = StrategyConfig(
    trade_size_in_lots=2,                 # 減少到2口
    stop_loss_type=StopLossType.RANGE_BOUNDARY,
    lot_rules=[
        # 第1口：保守設定
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(12),      # 較小觸發點
            trailing_pullback=Decimal('0.15')    # 較大回檔比例
        ),
        # 第2口：保守設定
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(30),      # 較小觸發點
            trailing_pullback=Decimal('0.15'),   # 較大回檔比例
            protective_stop_multiplier=Decimal('1.5')  # 較小保護倍數
        )
    ],
    range_filter=RangeFilter(
        use_range_size_filter=True,
        max_range_points=Decimal(100)             # 更嚴格的區間過濾
    ),
    risk_config=RiskConfig(
        use_risk_filter=True,
        daily_loss_limit=Decimal(80),             # 較小的虧損限制
        profit_target=Decimal(120)                # 較小的獲利目標
    ),
    trading_direction="BOTH"
)

# ==============================================================================
# 🔧 完整配置範例：積極型設定
# ==============================================================================

# 完整的積極型配置 (複製整段到主程式中)
strategy_config = StrategyConfig(
    trade_size_in_lots=3,                 # 保持3口
    stop_loss_type=StopLossType.RANGE_BOUNDARY,
    lot_rules=[
        # 第1口：積極設定
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(25),      # 較大觸發點
            trailing_pullback=Decimal('0.05')    # 較小回檔比例
        ),
        # 第2口：積極設定
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(55),      # 較大觸發點
            trailing_pullback=Decimal('0.08'),   # 較小回檔比例
            protective_stop_multiplier=Decimal('3.0')  # 較大保護倍數
        ),
        # 第3口：積極設定
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(65),      # 較大觸發點
            trailing_pullback=Decimal('0.12'),   # 中等回檔比例
            protective_stop_multiplier=Decimal('3.0')  # 較大保護倍數
        )
    ],
    range_filter=RangeFilter(
        use_range_size_filter=True,
        max_range_points=Decimal(250)             # 較寬鬆的區間過濾
    ),
    trading_direction="BOTH"
)

# ==============================================================================
# 📝 使用說明
# ==============================================================================

"""
使用步驟：

1. 打開 rev_future_path_analyzer.py 文件

2. 找到要修改的部分：
   - 分析參數：第 237-241 行
   - 回測時間：第 307-315 行  
   - 策略配置：第 255-287 行

3. 複製上面對應的代碼片段，替換原有的設定

4. 保存文件並重新運行：
   python rev_future_path_analyzer.py

5. 檢查輸出結果，根據需要進一步調整參數

注意事項：
- 修改參數後建議先用較少的模擬次數測試
- 觸發點數和回檔比例會顯著影響策略表現
- 區間過濾設定會影響交易頻率
- 風險管理設定會影響最大虧損和獲利
"""
