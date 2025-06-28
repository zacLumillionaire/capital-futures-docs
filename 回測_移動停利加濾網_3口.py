# 台指期開盤策略回測_完整模組化版本_V16_N口擴展版.py
import logging
from datetime import time, date
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum, auto
from app_setup import init_all_db_pools
import shared

# --- 設定日誌 ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z')
logger = logging.getLogger(__name__)

# ==============================================================================
# 1. 策略設定與輔助函式
# ==============================================================================
class StopLossType(Enum):
    RANGE_BOUNDARY = auto(); OPENING_PRICE = auto(); FIXED_POINTS = auto()

@dataclass
class StrategyConfig:
    """策略設定的中央控制面板。"""
    trade_size_in_lots: int = 3 # 可設為 1, 2, 3...
    stop_loss_type: StopLossType = StopLossType.RANGE_BOUNDARY
    fixed_stop_loss_points: Decimal = Decimal(40)
    
    # --- 各口數的出場設定 (使用列表，方便擴充) ---
    # Lot 1 (id=1) 的出場設定
    lot1_exit_config: dict = field(default_factory=lambda: {
        "use_trailing_stop": False,
        "fixed_tp_points": Decimal(20),
        "trailing_activation": Decimal(25), "trailing_pullback": Decimal('0.5')
    })
    # Lot 2 (id=2) 的出場設定
    lot2_exit_config: dict = field(default_factory=lambda: {
        "use_trailing_stop": True,
        "fixed_tp_points": None, # 通常不用固定停利
        "trailing_activation": Decimal(40), "trailing_pullback": Decimal('0.3')
    })
    # Lot 3 (id=3) 的出場設定
    lot3_exit_config: dict = field(default_factory=lambda: {
        "use_trailing_stop": True,
        "fixed_tp_points": None,
        "trailing_activation": Decimal(100), "trailing_pullback": Decimal('0.2')
    })
    
    # --- 保護性停損設定 ---
    protective_stop_multiplier: Decimal = Decimal('2.0') # 保護性停損 = 前一口獲利 * N倍


def format_config_summary(config: StrategyConfig) -> str:
    # ... (此函式內容不變，為求版面簡潔，暫時省略)
    return "Config Summary Placeholder"


# ==============================================================================
# 2. 核心交易邏輯函式
# ==============================================================================

def _run_multi_lot_logic(day_session_candles: list, trade_candles: list, config: StrategyConfig, range_high, range_low) -> Decimal:
    """處理多口分批出場的邏輯 (可擴展版)"""
    position, entry_price, entry_time, entry_candle_index = None, Decimal(0), None, -1
    lots = []

    for i, candle in enumerate(trade_candles):
        if candle['close_price'] > range_high:
            position, entry_price, entry_time, entry_candle_index = 'LONG', candle['close_price'], candle['trade_datetime'].time(), i
            logger.info(f"  📈 LONG  | 進場 {config.trade_size_in_lots} 口 | 時間: {entry_time}, 價格: {entry_price}"); break
        elif candle['low_price'] < range_low:
            position, entry_price, entry_time, entry_candle_index = 'SHORT', candle['close_price'], candle['trade_datetime'].time(), i
            logger.info(f"  📉 SHORT | 進場 {config.trade_size_in_lots} 口 | 時間: {entry_time}, 價格: {entry_price}"); break
    
    if position:
        initial_sl = range_low if position == 'LONG' else range_high
        for i in range(config.trade_size_in_lots):
            lot_configs = [config.lot1_exit_config, config.lot2_exit_config, config.lot3_exit_config]
            lot_config = lot_configs[i] if i < len(lot_configs) else lot_configs[-1] # 如果超過設定，使用最後一個
            lots.append({'id': i + 1, 'status': 'active', 'pnl': Decimal(0), 'peak_price': entry_price, 'trailing_on': False, 'stop_loss': initial_sl, 'is_initial_stop': True, 'config': lot_config})

        for exit_candle in trade_candles[entry_candle_index + 1:]:
            if all(lot['status'] != 'active' for lot in lots): break
            current_time = exit_candle['trade_datetime'].time()

            active_lots = [lot for lot in lots if lot['status'] == 'active']
            
            # 1. 檢查初始停損
            if any(lot['is_initial_stop'] for lot in active_lots):
                if (position == 'LONG' and exit_candle['close_price'] < initial_sl) or \
                   (position == 'SHORT' and exit_candle['close_price'] > initial_sl):
                    loss = (exit_candle['close_price'] - entry_price) if position == 'LONG' else (entry_price - exit_candle['close_price'])
                    for lot in active_lots: lot['pnl'], lot['status'] = loss, 'exited'
                    logger.info(f"  ❌ 初始停損 | 所有部位出場 | 時間: {current_time}, 價格: {exit_candle['close_price']}, 單口虧損: {loss}"); break
            
            # 2. 遍歷每一口在場的單，檢查各自的出場條件
            cumulative_pnl = sum(lot['pnl'] for lot in lots if lot['status'] == 'exited')

            for lot in active_lots:
                # 保護性停損檢查
                if not lot['is_initial_stop']:
                    if (position == 'LONG' and exit_candle['low_price'] <= lot['stop_loss']) or \
                       (position == 'SHORT' and exit_candle['high_price'] >= lot['stop_loss']):
                        lot['pnl'] = lot['stop_loss'] - entry_price if position == 'LONG' else entry_price - lot['stop_loss']
                        lot['status'] = 'exited'
                        logger.info(f"  🛡️ 第{lot['id']}口單觸及保護性停損 | 時間: {current_time}, 出場價: {lot['stop_loss']:.2f}, 損益: {lot['pnl']}"); continue

                # 停利檢查
                cfg = lot['config']
                if cfg['use_trailing_stop']:
                    # ... 省略移動停利實作細節 ...
                    pass
                elif cfg['fixed_tp_points']:
                    if (position == 'LONG' and exit_candle['high_price'] >= entry_price + cfg['fixed_tp_points']) or \
                       (position == 'SHORT' and exit_candle['low_price'] <= entry_price - cfg['fixed_tp_points']):
                        lot['pnl'] = cfg['fixed_tp_points']; lot['status'] = 'exited'
                        logger.info(f"  ✅ 第{lot['id']}口固定停利 | 時間: {current_time}, 損益: +{lot['pnl']}")
                        
                        # 更新下一口單的停損
                        next_lot_id = lot['id'] + 1
                        next_lot = next((l for l in lots if l['id'] == next_lot_id), None)
                        if next_lot and next_lot['status'] == 'active':
                            total_profit_so_far = cumulative_pnl + lot['pnl']
                            stop_loss_amount = total_profit_so_far * config.protective_stop_multiplier
                            new_sl = entry_price - stop_loss_amount if position == 'LONG' else entry_price + stop_loss_amount
                            next_lot['stop_loss'], next_lot['is_initial_stop'] = new_sl, False
                            logger.info(f"    - 第{next_lot_id}口單停損點更新為: {new_sl:.2f} (基於累積獲利 {total_profit_so_far})")
            
    if position:
        # ... (收盤平倉邏輯不變) ...
        pass

    return sum(lot['pnl'] for lot in lots) if lots else Decimal(0)