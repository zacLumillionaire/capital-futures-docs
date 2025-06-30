#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部位管理模組
負責多口部位管理、移動停利和保護性停損
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Any
from enum import Enum
import logging

from .strategy_config import StrategyConfig, LotRule, PositionType

logger = logging.getLogger(__name__)

class LotStatus(Enum):
    """口數狀態"""
    PENDING = "PENDING"     # 等待進場
    ACTIVE = "ACTIVE"       # 活躍中
    EXITED = "EXITED"       # 已出場

class ExitReason(Enum):
    """出場原因"""
    TRAILING_STOP = "TRAILING_STOP"         # 移動停利
    PROTECTIVE_STOP = "PROTECTIVE_STOP"     # 保護性停損
    RANGE_STOP = "RANGE_STOP"               # 區間停損
    EOD_CLOSE = "EOD_CLOSE"                 # 收盤平倉
    MANUAL_CLOSE = "MANUAL_CLOSE"           # 手動平倉

class LotPosition:
    """單口部位"""
    
    def __init__(self, lot_id: int, rule: LotRule, entry_price: float, 
                 position_type: PositionType, range_high: float, range_low: float):
        """
        初始化單口部位
        
        Args:
            lot_id: 口數編號 (1, 2, 3...)
            rule: 口數規則
            entry_price: 進場價格
            position_type: 部位類型 (LONG/SHORT)
            range_high: 區間高點
            range_low: 區間低點
        """
        self.lot_id = lot_id
        self.rule = rule
        self.entry_price = entry_price
        self.position_type = position_type
        self.range_high = range_high
        self.range_low = range_low
        
        # 狀態追蹤
        self.status = LotStatus.ACTIVE
        self.entry_time = datetime.now()
        self.exit_time = None
        self.exit_price = None
        self.exit_reason = None
        
        # 移動停利相關
        self.peak_price = entry_price  # 峰值價格
        self.trailing_stop_price = None
        self.trailing_activated = False
        
        # 停損設定
        self.stop_loss_price = self._calculate_initial_stop_loss()
        self.is_initial_stop = True  # 是否為初始停損
        
        # 損益計算
        self.unrealized_pnl = 0.0
        self.realized_pnl = None
        
        logger.info(f"📊 第{lot_id}口部位已建立: {position_type.value} @{entry_price}")
        logger.debug(f"   初始停損: {self.stop_loss_price}")
    
    def _calculate_initial_stop_loss(self) -> float:
        """計算初始停損價格 (使用區間另一邊)"""
        if self.position_type == PositionType.LONG:
            # 做多：停損設在區間低點
            return self.range_low
        else:
            # 做空：停損設在區間高點
            return self.range_high
    
    def update_price(self, current_price: float) -> bool:
        """
        更新價格並檢查出場條件
        
        Args:
            current_price: 當前價格
            
        Returns:
            是否需要出場
        """
        if self.status != LotStatus.ACTIVE:
            return False
        
        # 更新峰值價格
        self._update_peak_price(current_price)
        
        # 計算未實現損益
        self._calculate_unrealized_pnl(current_price)
        
        # 檢查移動停利
        if self.rule.use_trailing_stop:
            self._update_trailing_stop(current_price)
        
        # 檢查出場條件
        return self._check_exit_conditions(current_price)
    
    def _update_peak_price(self, current_price: float):
        """更新峰值價格"""
        if self.position_type == PositionType.LONG:
            # 做多：記錄最高價
            if current_price > self.peak_price:
                self.peak_price = current_price
        else:
            # 做空：記錄最低價
            if current_price < self.peak_price:
                self.peak_price = current_price
    
    def _calculate_unrealized_pnl(self, current_price: float):
        """計算未實現損益"""
        if self.position_type == PositionType.LONG:
            # 做多損益 = (當前價 - 進場價) * 50
            self.unrealized_pnl = (current_price - self.entry_price) * 50
        else:
            # 做空損益 = (進場價 - 當前價) * 50
            self.unrealized_pnl = (self.entry_price - current_price) * 50
    
    def _update_trailing_stop(self, current_price: float):
        """更新移動停利"""
        if not self.rule.trailing_activation:
            return
        
        # 檢查是否啟動移動停利
        profit_points = abs(self.peak_price - self.entry_price)
        
        if not self.trailing_activated and profit_points >= float(self.rule.trailing_activation):
            self.trailing_activated = True
            logger.info(f"🎯 第{self.lot_id}口啟動移動停利 (獲利{profit_points:.0f}點)")
        
        # 計算移動停利價格
        if self.trailing_activated:
            pullback_points = profit_points * float(self.rule.trailing_pullback)
            
            if self.position_type == PositionType.LONG:
                # 做多：從峰值回檔
                new_stop = self.peak_price - pullback_points
                if self.trailing_stop_price is None or new_stop > self.trailing_stop_price:
                    self.trailing_stop_price = new_stop
            else:
                # 做空：從峰值回檔
                new_stop = self.peak_price + pullback_points
                if self.trailing_stop_price is None or new_stop < self.trailing_stop_price:
                    self.trailing_stop_price = new_stop
    
    def _check_exit_conditions(self, current_price: float) -> bool:
        """檢查出場條件"""
        # 檢查移動停利
        if self.trailing_activated and self.trailing_stop_price:
            if self.position_type == PositionType.LONG:
                if current_price <= self.trailing_stop_price:
                    self._exit_position(current_price, ExitReason.TRAILING_STOP)
                    return True
            else:
                if current_price >= self.trailing_stop_price:
                    self._exit_position(current_price, ExitReason.TRAILING_STOP)
                    return True
        
        # 檢查停損
        if self.stop_loss_price:
            if self.position_type == PositionType.LONG:
                if current_price <= self.stop_loss_price:
                    reason = ExitReason.PROTECTIVE_STOP if not self.is_initial_stop else ExitReason.RANGE_STOP
                    self._exit_position(current_price, reason)
                    return True
            else:
                if current_price >= self.stop_loss_price:
                    reason = ExitReason.PROTECTIVE_STOP if not self.is_initial_stop else ExitReason.RANGE_STOP
                    self._exit_position(current_price, reason)
                    return True
        
        return False
    
    def _exit_position(self, exit_price: float, reason: ExitReason):
        """出場處理"""
        self.status = LotStatus.EXITED
        self.exit_price = exit_price
        self.exit_reason = reason
        self.exit_time = datetime.now()
        
        # 計算實現損益
        if self.position_type == PositionType.LONG:
            self.realized_pnl = (exit_price - self.entry_price) * 50
        else:
            self.realized_pnl = (self.entry_price - exit_price) * 50
        
        logger.info(f"🔚 第{self.lot_id}口出場: {reason.value} @{exit_price} 損益:{self.realized_pnl:+.0f}元")
    
    def update_protective_stop(self, new_stop_price: float):
        """更新保護性停損"""
        if self.status != LotStatus.ACTIVE:
            return
        
        self.stop_loss_price = new_stop_price
        self.is_initial_stop = False
        logger.info(f"🛡️ 第{self.lot_id}口更新保護停損: {new_stop_price}")
    
    def force_exit(self, exit_price: float, reason: ExitReason = ExitReason.MANUAL_CLOSE):
        """強制出場"""
        if self.status == LotStatus.ACTIVE:
            self._exit_position(exit_price, reason)
    
    def get_status_dict(self) -> Dict:
        """取得狀態字典"""
        return {
            'lot_id': self.lot_id,
            'status': self.status.value,
            'position_type': self.position_type.value,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time.isoformat(),
            'exit_price': self.exit_price,
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'exit_reason': self.exit_reason.value if self.exit_reason else None,
            'peak_price': self.peak_price,
            'trailing_activated': self.trailing_activated,
            'trailing_stop_price': self.trailing_stop_price,
            'stop_loss_price': self.stop_loss_price,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl
        }

class MultiLotPositionManager:
    """多口部位管理器"""
    
    def __init__(self, config: StrategyConfig):
        """
        初始化多口部位管理器
        
        Args:
            config: 策略配置
        """
        self.config = config
        self.lots: List[LotPosition] = []
        self.position_type = None
        self.entry_price = None
        self.range_high = None
        self.range_low = None
        
        # 統計資料
        self.total_realized_pnl = 0.0
        self.total_unrealized_pnl = 0.0
        self.active_lots_count = 0
        
        logger.info(f"📊 多口部位管理器已初始化 (預設{config.trade_size_in_lots}口)")
    
    def open_position(self, signal_type: str, entry_price: float, 
                     range_high: float, range_low: float) -> bool:
        """
        開倉多口部位
        
        Args:
            signal_type: 信號類型 ('LONG', 'SHORT')
            entry_price: 進場價格
            range_high: 區間高點
            range_low: 區間低點
            
        Returns:
            是否成功開倉
        """
        try:
            self.position_type = PositionType.LONG if signal_type == 'LONG' else PositionType.SHORT
            self.entry_price = entry_price
            self.range_high = range_high
            self.range_low = range_low
            
            # 創建各口部位
            for i in range(self.config.trade_size_in_lots):
                lot_id = i + 1
                rule = self.config.lot_rules[i]
                
                lot = LotPosition(
                    lot_id=lot_id,
                    rule=rule,
                    entry_price=entry_price,
                    position_type=self.position_type,
                    range_high=range_high,
                    range_low=range_low
                )
                
                self.lots.append(lot)
            
            self.active_lots_count = len(self.lots)
            
            logger.info(f"🚀 開倉完成: {signal_type} {self.config.trade_size_in_lots}口 @{entry_price}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 開倉失敗: {e}")
            return False
    
    def update_position(self, current_price: float) -> List[int]:
        """
        更新部位狀態
        
        Args:
            current_price: 當前價格
            
        Returns:
            出場的口數列表
        """
        exited_lots = []
        
        for lot in self.lots:
            if lot.status == LotStatus.ACTIVE:
                if lot.update_price(current_price):
                    exited_lots.append(lot.lot_id)
                    self.active_lots_count -= 1
                    self.total_realized_pnl += lot.realized_pnl
                    
                    # 更新後續口數的保護性停損
                    self._update_protective_stops(lot)
        
        # 更新總未實現損益
        self._calculate_total_unrealized_pnl()
        
        return exited_lots
    
    def _update_protective_stops(self, exited_lot: LotPosition):
        """更新後續口數的保護性停損"""
        if exited_lot.realized_pnl <= 0:
            return  # 只有獲利出場才更新保護停損
        
        cumulative_pnl = self.total_realized_pnl
        
        for lot in self.lots:
            if (lot.lot_id > exited_lot.lot_id and 
                lot.status == LotStatus.ACTIVE and 
                lot.rule.protective_stop_multiplier):
                
                # 計算保護停損價格
                protection_amount = cumulative_pnl * float(lot.rule.protective_stop_multiplier)
                protection_points = protection_amount / 50  # 轉換為點數
                
                if self.position_type == PositionType.LONG:
                    # 做多：在進場價上方設保護停損
                    new_stop = lot.entry_price + protection_points
                    if new_stop > lot.stop_loss_price:
                        lot.update_protective_stop(new_stop)
                else:
                    # 做空：在進場價下方設保護停損
                    new_stop = lot.entry_price - protection_points
                    if new_stop < lot.stop_loss_price:
                        lot.update_protective_stop(new_stop)
    
    def _calculate_total_unrealized_pnl(self):
        """計算總未實現損益"""
        self.total_unrealized_pnl = sum(
            lot.unrealized_pnl for lot in self.lots 
            if lot.status == LotStatus.ACTIVE
        )
    
    def close_all_positions(self, current_price: float, 
                           reason: ExitReason = ExitReason.EOD_CLOSE) -> int:
        """
        平倉所有部位
        
        Args:
            current_price: 當前價格
            reason: 平倉原因
            
        Returns:
            平倉的口數
        """
        closed_count = 0
        
        for lot in self.lots:
            if lot.status == LotStatus.ACTIVE:
                lot.force_exit(current_price, reason)
                self.total_realized_pnl += lot.realized_pnl
                closed_count += 1
        
        self.active_lots_count = 0
        self.total_unrealized_pnl = 0.0
        
        logger.info(f"🔚 強制平倉 {closed_count}口 原因:{reason.value}")
        return closed_count
    
    def has_position(self) -> bool:
        """檢查是否有部位"""
        return self.active_lots_count > 0
    
    def get_position_summary(self) -> Dict:
        """取得部位摘要"""
        return {
            'position_type': self.position_type.value if self.position_type else None,
            'entry_price': self.entry_price,
            'total_lots': len(self.lots),
            'active_lots': self.active_lots_count,
            'total_realized_pnl': self.total_realized_pnl,
            'total_unrealized_pnl': self.total_unrealized_pnl,
            'total_pnl': self.total_realized_pnl + self.total_unrealized_pnl,
            'lots_detail': [lot.get_status_dict() for lot in self.lots]
        }
    
    def reset_position(self):
        """重置部位"""
        self.lots.clear()
        self.position_type = None
        self.entry_price = None
        self.range_high = None
        self.range_low = None
        self.total_realized_pnl = 0.0
        self.total_unrealized_pnl = 0.0
        self.active_lots_count = 0
        logger.info("🔄 部位管理器已重置")

if __name__ == "__main__":
    # 測試部位管理器
    print("🧪 測試部位管理模組")
    
    from .strategy_config import StrategyConfig
    
    # 創建3口策略配置
    config = StrategyConfig(trade_size_in_lots=3)
    
    # 創建部位管理器
    manager = MultiLotPositionManager(config)
    
    # 模擬開倉
    success = manager.open_position('LONG', 22000, 22050, 21980)
    print(f"開倉結果: {success}")
    
    # 模擬價格變化
    prices = [22010, 22020, 22015, 22025, 22030, 22020, 22040, 22035]
    
    for price in prices:
        exited = manager.update_position(price)
        if exited:
            print(f"價格{price}: 第{exited}口出場")
        
        summary = manager.get_position_summary()
        print(f"價格{price}: 活躍{summary['active_lots']}口 損益{summary['total_pnl']:+.0f}元")
    
    print("✅ 部位管理測試完成")
