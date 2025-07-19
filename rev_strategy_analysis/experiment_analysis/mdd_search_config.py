
#!/usr/bin/env python3
"""
MDD 搜索配置文件
用於定義不同的搜索策略和參數範圍
"""

class MDDSearchConfig:
    """MDD 搜索配置類"""

    @staticmethod
    def get_time_interval_analysis_config():
        """時間區間分析配置 - 每個區間找最小MDD，比較統一停利vs各口獨立停利vs區間邊緣停利"""
        return {
            'analysis_mode': 'per_time_interval',
            'stop_loss_ranges': {
                'lot1': [15],  # 第1口停損值
                'lot2': [40],  # 第2口停損值
                'lot3': [41]   # 第3口停損值
            },
            'take_profit_modes': ['unified_fixed', 'individual_fixed', 'range_boundary'],  # 三種停利模式
            'take_profit_ranges': {
                'unified': [55],        # 統一停利
                'individual': [30, 40, 50, 60]              # 各口獨立停利
            },
            'time_intervals': [
                ("08:46", "08:47")  # 測試時間區間
            ],
            'estimated_combinations': {
                'per_interval_analysis': 1 * (1 + 64 + 1) * 1,  # 66 總組合
                'breakdown': '1 停損組合 × 66 停利模式 (1統一+64各口獨立+1區間) × 1 時間區間'
            }
        }

    @staticmethod
    def get_config_by_name(config_name):
        """根據名稱獲取配置"""
        configs = {
            'time_interval_analysis': MDDSearchConfig.get_time_interval_analysis_config()
        }
        return configs.get(config_name, configs['time_interval_analysis'])

# 任務3測試配置
TIME_INTERVAL_ANALYSIS_CONFIG = "temp_task3_config.json"
