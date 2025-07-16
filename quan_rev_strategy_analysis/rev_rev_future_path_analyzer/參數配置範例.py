#!/usr/bin/env python3
"""
反轉策略未來路徑分析器 - 參數配置範例

這個文件包含各種常用的策略配置範例，您可以複製這些配置到主程式中使用。
"""

from decimal import Decimal
from rev_strategy_core import StrategyConfig, LotRule, RangeFilter, RiskConfig, StopLossType

# ==============================================================================
# 🔧 蒙地卡羅分析參數範例
# ==============================================================================

# 快速測試配置 (適合開發測試)
QUICK_TEST_PARAMS = {
    'NUM_SIMULATIONS': 500,      # 模擬次數
    'NUM_FUTURE_DAYS': 30,       # 未來預測天數
    'PROFIT_TARGET_PCT': 0.15,   # 獲利目標 15%
    'RISK_LIMIT_PCT': 0.10,      # 風險底線 10%
    'INITIAL_CAPITAL': 100000    # 起始資金
}

# 標準分析配置 (推薦使用)
STANDARD_PARAMS = {
    'NUM_SIMULATIONS': 2000,     # 模擬次數
    'NUM_FUTURE_DAYS': 60,       # 未來預測天數
    'PROFIT_TARGET_PCT': 0.20,   # 獲利目標 20%
    'RISK_LIMIT_PCT': 0.15,      # 風險底線 15%
    'INITIAL_CAPITAL': 100000    # 起始資金
}

# 詳細分析配置 (高精度分析)
DETAILED_PARAMS = {
    'NUM_SIMULATIONS': 5000,     # 模擬次數
    'NUM_FUTURE_DAYS': 120,      # 未來預測天數
    'PROFIT_TARGET_PCT': 0.25,   # 獲利目標 25%
    'RISK_LIMIT_PCT': 0.20,      # 風險底線 20%
    'INITIAL_CAPITAL': 100000    # 起始資金
}

# ==============================================================================
# 📅 回測時間區段範例
# ==============================================================================

# 最近半年數據
RECENT_6_MONTHS = {
    'start_date': "2024-11-04",
    'end_date': "2025-06-28",
    'range_start_time': "08:46",
    'range_end_time': "08:47"
}

# 完整一年數據
FULL_YEAR = {
    'start_date': "2024-01-01",
    'end_date': "2024-12-31",
    'range_start_time': "08:46",
    'range_end_time': "08:47"
}

# 自定義時間區間
CUSTOM_RANGE = {
    'start_date': "2024-06-01",
    'end_date': "2025-06-01",
    'range_start_time': "08:45",  # 可調整開盤區間
    'range_end_time': "08:48"     # 可調整開盤區間
}

# ==============================================================================
# 🎯 策略配置範例
# ==============================================================================

# 範例1: 您目前的預設配置 (驗證過的配置)
DEFAULT_CONFIG = StrategyConfig(
    trade_size_in_lots=3,
    stop_loss_type=StopLossType.RANGE_BOUNDARY,
    lot_rules=[
        # 第1口：15點觸發，10%回檔
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(15),
            trailing_pullback=Decimal('0.10')
        ),
        # 第2口：40點觸發，10%回檔，2倍保護性停損
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(40),
            trailing_pullback=Decimal('0.10'),
            protective_stop_multiplier=Decimal('2.0')
        ),
        # 第3口：41點觸發，20%回檔，2倍保護性停損
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(41),
            trailing_pullback=Decimal('0.20'),
            protective_stop_multiplier=Decimal('2.0')
        )
    ],
    range_filter=RangeFilter(
        use_range_size_filter=True,
        max_range_points=Decimal(160)
    ),
    trading_direction="BOTH"
)

# 範例2: 保守型配置 (降低風險)
CONSERVATIVE_CONFIG = StrategyConfig(
    trade_size_in_lots=2,
    stop_loss_type=StopLossType.RANGE_BOUNDARY,
    lot_rules=[
        # 第1口：較小觸發點，較大回檔比例
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(10),
            trailing_pullback=Decimal('0.15')
        ),
        # 第2口：保守設定
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(25),
            trailing_pullback=Decimal('0.15'),
            protective_stop_multiplier=Decimal('1.5')
        )
    ],
    range_filter=RangeFilter(
        use_range_size_filter=True,
        max_range_points=Decimal(100)  # 更嚴格的區間過濾
    ),
    risk_config=RiskConfig(
        use_risk_filter=True,
        daily_loss_limit=Decimal(100),  # 每日虧損限制
        profit_target=Decimal(150)      # 每日獲利目標
    ),
    trading_direction="BOTH"
)

# 範例3: 積極型配置 (追求更高收益)
AGGRESSIVE_CONFIG = StrategyConfig(
    trade_size_in_lots=3,
    stop_loss_type=StopLossType.RANGE_BOUNDARY,
    lot_rules=[
        # 第1口：較大觸發點，較小回檔比例
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(20),
            trailing_pullback=Decimal('0.05')
        ),
        # 第2口：積極設定
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(50),
            trailing_pullback=Decimal('0.05'),
            protective_stop_multiplier=Decimal('3.0')
        ),
        # 第3口：最積極設定
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(60),
            trailing_pullback=Decimal('0.10'),
            protective_stop_multiplier=Decimal('3.0')
        )
    ],
    range_filter=RangeFilter(
        use_range_size_filter=True,
        max_range_points=Decimal(200)  # 較寬鬆的區間過濾
    ),
    trading_direction="BOTH"
)

# 範例4: 只做多配置
LONG_ONLY_CONFIG = StrategyConfig(
    trade_size_in_lots=2,
    stop_loss_type=StopLossType.RANGE_BOUNDARY,
    lot_rules=[
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(15),
            trailing_pullback=Decimal('0.10')
        ),
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(35),
            trailing_pullback=Decimal('0.15'),
            protective_stop_multiplier=Decimal('2.0')
        )
    ],
    range_filter=RangeFilter(
        use_range_size_filter=True,
        max_range_points=Decimal(160)
    ),
    trading_direction="LONG_ONLY"
)

# 範例5: 只做空配置
SHORT_ONLY_CONFIG = StrategyConfig(
    trade_size_in_lots=2,
    stop_loss_type=StopLossType.RANGE_BOUNDARY,
    lot_rules=[
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(15),
            trailing_pullback=Decimal('0.10')
        ),
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(35),
            trailing_pullback=Decimal('0.15'),
            protective_stop_multiplier=Decimal('2.0')
        )
    ],
    range_filter=RangeFilter(
        use_range_size_filter=True,
        max_range_points=Decimal(160)
    ),
    trading_direction="SHORT_ONLY"
)

# 範例6: 固定停損停利配置
FIXED_STOP_CONFIG = StrategyConfig(
    trade_size_in_lots=2,
    stop_loss_type=StopLossType.FIXED_POINTS,
    fixed_stop_loss_points=Decimal(20),  # 固定20點停損
    lot_rules=[
        # 第1口：固定停損停利
        LotRule(
            use_trailing_stop=False,
            fixed_stop_loss_points=Decimal(15),
            fixed_tp_points=Decimal(30)
        ),
        # 第2口：固定停損停利
        LotRule(
            use_trailing_stop=False,
            fixed_stop_loss_points=Decimal(20),
            fixed_tp_points=Decimal(40)
        )
    ],
    range_filter=RangeFilter(
        use_range_size_filter=True,
        max_range_points=Decimal(160)
    ),
    trading_direction="BOTH"
)

# 範例7: 無區間過濾配置
NO_FILTER_CONFIG = StrategyConfig(
    trade_size_in_lots=3,
    stop_loss_type=StopLossType.RANGE_BOUNDARY,
    lot_rules=[
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(15),
            trailing_pullback=Decimal('0.10')
        ),
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(40),
            trailing_pullback=Decimal('0.10'),
            protective_stop_multiplier=Decimal('2.0')
        ),
        LotRule(
            use_trailing_stop=True,
            trailing_activation=Decimal(41),
            trailing_pullback=Decimal('0.20'),
            protective_stop_multiplier=Decimal('2.0')
        )
    ],
    range_filter=RangeFilter(
        use_range_size_filter=False  # 關閉區間過濾
    ),
    trading_direction="BOTH"
)

# ==============================================================================
# 🔧 如何使用這些配置
# ==============================================================================

"""
使用方法：

1. 在 rev_future_path_analyzer.py 中，找到 strategy_config = StrategyConfig(...) 這一段
2. 將整段替換為以上任一配置，例如：

   # 使用保守型配置
   strategy_config = CONSERVATIVE_CONFIG

3. 同時可以修改分析參數，例如：
   
   # 使用快速測試參數
   NUM_SIMULATIONS = QUICK_TEST_PARAMS['NUM_SIMULATIONS']
   NUM_FUTURE_DAYS = QUICK_TEST_PARAMS['NUM_FUTURE_DAYS']
   PROFIT_TARGET_PCT = QUICK_TEST_PARAMS['PROFIT_TARGET_PCT']
   RISK_LIMIT_PCT = QUICK_TEST_PARAMS['RISK_LIMIT_PCT']
   INITIAL_CAPITAL = QUICK_TEST_PARAMS['INITIAL_CAPITAL']

4. 修改回測時間範圍：
   
   backtest_results = run_rev_backtest(
       config=strategy_config,
       start_date=FULL_YEAR['start_date'],
       end_date=FULL_YEAR['end_date'],
       range_start_time=FULL_YEAR['range_start_time'],
       range_end_time=FULL_YEAR['range_end_time'],
       silent=False,
       enable_console_log=True
   )
"""
