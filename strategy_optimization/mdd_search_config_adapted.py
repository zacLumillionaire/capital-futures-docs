#!/usr/bin/env python3
"""
MDD 搜索配置文件 - 適配版本
專為 strategy_optimization 項目使用
用於定義不同的搜索策略和參數範圍
"""

class MDDSearchConfig:
    """MDD 搜索配置類 - 適配版本"""
    
    @staticmethod
    def get_quick_search_config():
        """快速搜索配置 - 較少組合數量，適合初步探索"""
        return {
            'stop_loss_ranges': {
                'lot1': list(range(10, 31, 5)),    # 10,15,20,25,30 (5個值)
                'lot2': list(range(20, 46, 5)),    # 20,25,30,35,40,45 (6個值)
                'lot3': list(range(25, 51, 5))     # 25,30,35,40,45,50 (6個值)
            },
            'take_profit_ranges': {
                'unified': list(range(40, 81, 20)),  # 40,60,80 (3個值)
                'individual': [40, 60, 80]  # 簡化為列表
            },
            'time_intervals': [
                ("10:30", "10:32"),
                ("11:30", "11:32"),
                ("12:30", "12:32")
            ],
            'estimated_combinations': {
                'unified': 5 * 6 * 6 * 3 * 3,      # ~1,620 組合
                'individual': 5 * 6 * 6 * 3 * 3 * 3 * 3  # ~14,580 組合
            }
        }
    
    @staticmethod
    def get_detailed_search_config():
        """詳細搜索配置 - 更細緻的參數範圍"""
        return {
            'stop_loss_ranges': {
                'lot1': list(range(10, 31, 2)),    # 10,12,14,...,30 (11個值)
                'lot2': list(range(15, 46, 2)),    # 15,17,19,...,45 (16個值)
                'lot3': list(range(20, 51, 2))     # 20,22,24,...,50 (16個值)
            },
            'take_profit_ranges': {
                'unified': list(range(30, 101, 10)),  # 30,40,50,...,100 (8個值)
                'individual': list(range(30, 101, 10))
            },
            'time_intervals': [
                ("10:00", "10:02"),
                ("10:30", "10:32"),
                ("11:00", "11:02"),
                ("11:30", "11:32"),
                ("12:00", "12:02"),
                ("12:30", "12:32"),
                ("13:00", "13:02")
            ],
            'estimated_combinations': {
                'unified': 11 * 16 * 16 * 8 * 7,    # ~156,352 組合
                'individual': 11 * 16 * 16 * 8 * 8 * 8 * 7  # ~10,006,528 組合
            }
        }
    
    @staticmethod
    def get_focused_search_config():
        """聚焦搜索配置 - 基於已知好結果的鄰近搜索"""
        return {
            'stop_loss_ranges': {
                'lot1': [12, 14, 15, 16, 18],      # 圍繞15點
                'lot2': [22, 24, 25, 26, 28],      # 圍繞25點
                'lot3': [28, 29, 30, 31, 32]       # 圍繞30點
            },
            'take_profit_ranges': {
                'unified': [50, 55, 60, 65, 70],   # 圍繞60點
                'individual': [50, 55, 60, 65, 70]
            },
            'time_intervals': [
                ("11:30", "11:32"),  # 重點關注這個時段
                ("10:30", "10:32"),
                ("12:30", "12:32")
            ],
            'estimated_combinations': {
                'unified': 5 * 5 * 5 * 5 * 3,      # ~1,875 組合
                'individual': 5 * 5 * 5 * 5 * 5 * 5 * 3  # ~46,875 組合
            }
        }
    
    @staticmethod
    def get_time_interval_focus_config():
        """時間區間重點搜索 - 測試更多時間區間組合"""
        return {
            'stop_loss_ranges': {
                'lot1': [15, 20],                  # 簡化停損範圍
                'lot2': [25, 30],
                'lot3': [30, 35]
            },
            'take_profit_ranges': {
                'unified': [60, 80],               # 簡化停利範圍
                'individual': [60, 80]
            },
            'time_intervals': [
                ("09:00", "09:02"),  # 開盤前兩分鐘
                ("10:30", "10:32"),  # 早盤活躍
                ("11:00", "11:02"),  # 中午前
                ("11:30", "11:32"),  # 中午震盪
                ("12:00", "12:02"),  # 午休前
                ("12:30", "12:32"),  # 午後開始
                ("13:00", "13:02"),  # 下午時段
                ("13:30", "13:32")   # 尾盤時段
            ],
            'estimated_combinations': {
                'unified': 2 * 2 * 2 * 2 * 8,      # ~256 組合
                'individual': 2 * 2 * 2 * 2 * 2 * 8  # ~1,024 組合
            }
        }
    
    @staticmethod
    def get_user_custom_search_config():
        """用戶自定義搜索配置"""
        return {
            'stop_loss_ranges': {
                'lot1': [15],  # 用戶可自定義
                'lot2': [25],
                'lot3': [35]
            },
            'take_profit_ranges': {
                'unified': [60],
                'individual': [60]
            },
            'time_intervals': [
                ("11:30", "11:32")  # 用戶可自定義
            ],
            'estimated_combinations': {
                'unified': 1,
                'individual': 1
            }
        }
    
    @staticmethod
    def get_range_boundary_config():
        """區間邊緣停利配置"""
        return {
            'take_profit_mode': 'range_boundary',
            'stop_loss_ranges': {
                'lot1': list(range(15, 71, 5)),    # 15,20,25,...,70 (12個值)
                'lot2': list(range(15, 71, 5)),    # 15,20,25,...,70 (12個值)
                'lot3': list(range(15, 71, 5))     # 15,20,25,...,70 (12個值)
            },
            'time_intervals': [
                ("10:30", "10:32"),
                ("11:30", "11:32"),
                ("12:30", "12:32")
            ],
            'estimated_combinations': {
                'range_boundary': 220 * 3  # 220 停損組合 × 3 時間區間 = 660
            }
        }
    
    @staticmethod
    def get_time_interval_analysis_config():
        """時間區間分析配置 - 每個區間找最小MDD，比較統一停利vs各口獨立停利vs區間邊緣停利"""
        return {
            'analysis_mode': 'per_time_interval',
            'stop_loss_ranges': {
                'lot1': [15],  # 第1口停損值
                'lot2': [15],  # 第2口停損值
                'lot3': [15]   # 第3口停損值
            },
            'take_profit_modes': ['unified_fixed', 'individual_fixed', 'range_boundary'],  # 三種停利模式
            'take_profit_ranges': {
                'unified': [55],        # 統一停利
                'individual': [30, 40, 50, 60]              # 各口獨立停利
            },
            'time_intervals': [
                ("10:30", "10:32"),  # 10:30-10:32
                ("12:00", "12:02"),  # 12:00-12:02
                ("13:00", "13:02")   # 13:00-13:02
            ],
            'estimated_combinations': {
                'per_interval_analysis': 1 * (1 + 64 + 1) * 3,  # 66 總組合
                'breakdown': '1 停損組合 × 66 停利模式 (1統一+64各口獨立+1區間) × 3 時間區間'
            }
        }

    @staticmethod
    def get_comprehensive_time_interval_config():
        """綜合時間區間配置 - 更多時間區間和參數組合"""
        return {
            'analysis_mode': 'per_time_interval',
            'stop_loss_ranges': {
                'lot1': [15, 20, 25],  # 3個值
                'lot2': [15, 20, 25],  # 3個值
                'lot3': [15, 20, 25]   # 3個值
            },
            'take_profit_ranges': {
                'unified': [50, 60, 70],        # 統一停利 3個值
                'individual': [40, 50, 60, 70]  # 各口獨立停利 4個值
            },
            'time_intervals': [
                ("09:00", "09:02"),  # 開盤
                ("10:00", "10:02"),  # 早盤
                ("10:30", "10:32"),  # 早盤活躍
                ("11:00", "11:02"),  # 中午前
                ("11:30", "11:32"),  # 中午震盪
                ("12:00", "12:02"),  # 午休前
                ("12:30", "12:32"),  # 午後開始
                ("13:00", "13:02"),  # 下午時段
                ("13:30", "13:32")   # 尾盤
            ],
            'estimated_combinations': {
                'per_interval_analysis': 10 * (3 + 64 + 1) * 9,  # 6,120 總組合
                'breakdown': '10 停損組合 × 68 停利模式 (3統一+64各口獨立+1區間) × 9 時間區間'
            }
        }

    @staticmethod
    def get_config_by_name(config_name):
        """根據名稱獲取配置"""
        configs = {
            'quick': MDDSearchConfig.get_quick_search_config(),
            'detailed': MDDSearchConfig.get_detailed_search_config(),
            'focused': MDDSearchConfig.get_focused_search_config(),
            'time_focus': MDDSearchConfig.get_time_interval_focus_config(),
            'user_custom': MDDSearchConfig.get_user_custom_search_config(),
            'range_boundary': MDDSearchConfig.get_range_boundary_config(),
            'time_interval_analysis': MDDSearchConfig.get_time_interval_analysis_config(),
            'comprehensive_time_interval': MDDSearchConfig.get_comprehensive_time_interval_config()
        }
        return configs.get(config_name, configs['quick'])

    @staticmethod
    def list_all_configs():
        """列出所有可用配置"""
        configs = {
            'quick': '快速搜索 - 較少組合，適合初步探索',
            'detailed': '詳細搜索 - 更細緻的參數範圍',
            'focused': '聚焦搜索 - 基於已知好結果的鄰近搜索',
            'time_focus': '時間區間重點 - 測試更多時間區間',
            'user_custom': '用戶自定義 - 可自行調整參數',
            'range_boundary': '區間邊緣停利 - 動態停利模式',
            'time_interval_analysis': '時間區間分析 - 每個區間找最小MDD',
            'comprehensive_time_interval': '綜合時間區間 - 更全面的時間區間分析'
        }
        return configs
