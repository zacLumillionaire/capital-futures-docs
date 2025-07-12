#!/usr/bin/env python3
"""
MDD 搜索配置文件
用於定義不同的搜索策略和參數範圍
"""

class MDDSearchConfig:
    """MDD 搜索配置類"""
    
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
                'individual': {
                    'lot1': [40, 60, 80],
                    'lot2': [40, 60, 80], 
                    'lot3': [40, 60, 80]
                }
            },
            'time_intervals': [
                ("10:30", "10:31"),
                ("11:30", "11:31"),
                ("12:30", "12:31")
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
                'individual': {
                    'lot1': list(range(30, 101, 10)),
                    'lot2': list(range(30, 101, 10)),
                    'lot3': list(range(30, 101, 10))
                }
            },
            'time_intervals': [
                ("10:30", "10:31"),
                ("10:30", "10:32"),
                ("11:30", "11:31"),
                ("11:30", "11:32"),
                ("12:30", "12:31"),
                ("12:30", "12:32"),
                ("09:00", "09:01"),
                ("13:30", "13:31")
            ],
            'estimated_combinations': {
                'unified': 11 * 16 * 16 * 8 * 8,      # ~180,224 組合
                'individual': 11 * 16 * 16 * 8 * 8 * 8 * 8  # ~11,534,336 組合 (太大!)
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
                'individual': {
                    'lot1': [50, 55, 60, 65, 70],
                    'lot2': [50, 55, 60, 65, 70],
                    'lot3': [50, 55, 60, 65, 70]
                }
            },
            'time_intervals': [
                ("11:30", "11:31"),  # 重點關注這個時段
                ("11:30", "11:32"),
                ("10:30", "10:31"),
                ("12:30", "12:31")
            ],
            'estimated_combinations': {
                'unified': 5 * 5 * 5 * 5 * 4,      # ~2,500 組合
                'individual': 5 * 5 * 5 * 5 * 5 * 5 * 4  # ~62,500 組合
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
                'individual': {
                    'lot1': [60, 80],
                    'lot2': [60, 80],
                    'lot3': [60, 80]
                }
            },
            'time_intervals': [
                ("09:00", "09:01"),  # 開盤第一分鐘
                ("09:00", "09:02"),  # 開盤前兩分鐘
                ("10:30", "10:31"),  # 早盤活躍
                ("10:30", "10:32"),
                ("11:00", "11:01"),  # 中午前
                ("11:30", "11:31"),  # 中午震盪
                ("11:30", "11:32"),
                ("12:00", "12:01"),  # 午休前
                ("12:30", "12:31"),  # 午後開始
                ("12:30", "12:32"),
                ("13:00", "13:01"),  # 下午時段
                ("13:30", "13:31"),  # 尾盤時段
                ("13:30", "13:32")
            ],
            'estimated_combinations': {
                'unified': 2 * 2 * 2 * 2 * 13,     # ~416 組合
                'individual': 2 * 2 * 2 * 2 * 2 * 2 * 13  # ~1,664 組合
            }
        }

    @staticmethod
    def get_user_custom_search_config():
        """用戶自定義搜索配置 - 根據用戶具體需求設計"""
        return {
            'stop_loss_ranges': {
                'lot1': [15, 20, 25, 30, 45, 50, 55, 60, 65, 70],  # 第1口: 10個值
                'lot2': [15, 20, 25, 30, 45, 50, 55, 60, 65, 70],  # 第2口: 10個值
                'lot3': [15, 20, 25, 30, 45, 50, 55, 60, 65, 70]   # 第3口: 10個值
            },
            'take_profit_ranges': {
                'unified': [40, 50, 60, 70, 80],        # 統一停利: 5個值
                'individual': {
                    'lot1': [40, 50, 60, 70, 80],       # 第1口: 5個值
                    'lot2': [40, 50, 60, 70, 80],       # 第2口: 5個值
                    'lot3': [40, 50, 60, 70, 80]        # 第3口: 5個值
                }
            },
            'time_intervals': [
                ("10:00", "10:02"),  # 10:00-10:02
                ("10:30", "10:32"),  # 10:30-10:32
                ("11:00", "11:02"),  # 11:00-11:02
                ("11:30", "11:32"),  # 11:30-11:32
                ("12:00", "12:02"),  # 12:00-12:02
                ("12:30", "12:32"),  # 12:30-12:32
                ("13:00", "13:02")   # 13:00-13:02
            ],
            'estimated_combinations': {
                'unified': 10 * 10 * 10 * 5 * 7,       # 35,000 組合
                'individual': 10 * 10 * 10 * 5 * 5 * 5 * 7  # 875,000 組合
            }
        }

    @staticmethod
    def get_range_boundary_config():
        """區間邊緣停利配置 - 使用策略原設計的區間邊緣停利功能"""
        return {
            'stop_loss_ranges': {
                'lot1': [15, 20, 25, 30, 45, 50, 55, 60, 65, 70],  # 第1口: 10個值
                'lot2': [15, 20, 25, 30, 45, 50, 55, 60, 65, 70],  # 第2口: 10個值
                'lot3': [15, 20, 25, 30, 45, 50, 55, 60, 65, 70]   # 第3口: 10個值
            },
            'take_profit_mode': 'range_boundary',  # 關鍵差異: 使用區間邊緣停利
            'time_intervals': [
                ("10:00", "10:02"),  # 10:00-10:02
                ("10:30", "10:32"),  # 10:30-10:32
                ("11:00", "11:02"),  # 11:00-11:02
                ("11:30", "11:32"),  # 11:30-11:32
                ("12:00", "12:02"),  # 12:00-12:02
                ("12:30", "12:32"),  # 12:30-12:32
                ("13:00", "13:02")   # 13:00-13:02
            ],
            'estimated_combinations': {
                'range_boundary': 10 * 10 * 10 * 7,    # 7,000 組合 (無停利參數)
            }
        }

    @staticmethod
    def get_time_interval_analysis_config():
        """時間區間分析配置 - GUI 自定義配置"""
        return {'analysis_mode': 'per_time_interval', 'stop_loss_ranges': {'lot1': [15, 20, 25, 30], 'lot2': [20, 25, 30, 40], 'lot3': [20, 25, 30]}, 'take_profit_modes': ['unified_fixed', 'individual_fixed', 'range_boundary'], 'take_profit_ranges': {'unified': [55], 'individual': [30, 40]}, 'time_intervals': [('10:30', '10:32'), ('12:00', '12:02')], 'estimated_combinations': {'per_interval_analysis': 'GUI 自定義配置'}}
        """時間區間分析配置 - GUI 自定義配置"""
        """時間區間分析配置 - 每個區間找最小MDD，比較統一停利vs各口獨立停利vs區間邊緣停利"""
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
            'time_interval_analysis': MDDSearchConfig.get_time_interval_analysis_config()
        }
        return configs.get(config_name, configs['quick'])
    @staticmethod
    def print_config_summary():
        """打印所有配置的摘要"""
        configs = ['quick', 'detailed', 'focused', 'time_focus', 'user_custom', 'range_boundary', 'time_interval_analysis']
        print("📊 MDD 搜索配置摘要")
        print("=" * 60)
        for config_name in configs:
            config = MDDSearchConfig.get_config_by_name(config_name)
            print(f"\n🎯 {config_name.upper()} 配置:")
            print(f"   停損範圍: L1={len(config['stop_loss_ranges']['lot1'])}, "
                  f"L2={len(config['stop_loss_ranges']['lot2'])}, "
                  f"L3={len(config['stop_loss_ranges']['lot3'])}")
            print(f"   時間區間: {len(config['time_intervals'])} 個")
            print(f"   預估組合數:")
            if 'unified' in config['estimated_combinations']:
                print(f"     統一停利: {config['estimated_combinations']['unified']:,}")
            if 'individual' in config['estimated_combinations']:
                print(f"     獨立停利: {config['estimated_combinations']['individual']:,}")
            if 'range_boundary' in config['estimated_combinations']:
                print(f"     區間邊緣停利: {config['estimated_combinations']['range_boundary']:,}")
            if 'per_interval_analysis' in config['estimated_combinations']:
                print(f"     時間區間分析: {config['estimated_combinations']['per_interval_analysis']:,}")
                print(f"     說明: {config['estimated_combinations']['breakdown']}")
if __name__ == "__main__":
    MDDSearchConfig.print_config_summary()
