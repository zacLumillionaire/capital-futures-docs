#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
當沖交易點位計算模組
基於OnNewData事件進行即時損益計算
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DayTradingCalculator:
    """當沖交易點位計算器"""
    
    def __init__(self):
        # 持倉記錄
        self.positions = {}  # {序號: {方向, 價格, 口數, 時間}}
        self.trades = []     # 成交記錄
        self.total_pnl = 0   # 總損益
        
    def parse_onnewdata(self, bstr_data):
        """解析OnNewData事件資料"""
        try:
            cut_data = bstr_data.split(',')
            
            if len(cut_data) < 25:
                return None
            
            # 解析關鍵欄位
            key_no = cut_data[0] if len(cut_data) > 0 else ""          # 委託序號
            market_type = cut_data[1] if len(cut_data) > 1 else ""     # 市場類型
            data_type = cut_data[2] if len(cut_data) > 2 else ""       # 委託狀態
            order_err = cut_data[3] if len(cut_data) > 3 else ""       # 委託結果
            price = cut_data[11] if len(cut_data) > 11 else ""         # 價格
            qty = cut_data[20] if len(cut_data) > 20 else ""           # 數量
            seq_no = cut_data[47] if len(cut_data) > 47 else key_no    # 新序號
            
            # 建立解析結果
            parsed_data = {
                'key_no': key_no,
                'seq_no': seq_no,
                'market_type': market_type,
                'type': data_type,
                'order_err': order_err,
                'price': self._safe_float(price),
                'qty': self._safe_int(qty),
                'timestamp': datetime.now()
            }
            
            # 處理不同類型的回報
            if data_type == "D" and order_err == "N":
                # 成交回報 - 最重要
                return self._process_trade(parsed_data)
            elif data_type == "N" and order_err == "N":
                # 委託成功
                return self._process_order_success(parsed_data)
            elif data_type == "C":
                # 委託取消
                return self._process_order_cancel(parsed_data)
            elif data_type == "N" and order_err == "Y":
                # 委託失敗
                return self._process_order_fail(parsed_data)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"解析OnNewData失敗: {e}")
            return None
    
    def _process_trade(self, data):
        """處理成交回報"""
        try:
            price = data['price']
            qty = data['qty']
            seq_no = data['seq_no']
            
            if price > 0 and qty > 0:
                # 計算成交金額 (小台指每點50元)
                trade_value = price * qty * 50
                
                # 記錄成交
                trade_record = {
                    'seq_no': seq_no,
                    'price': price,
                    'qty': qty,
                    'value': trade_value,
                    'timestamp': data['timestamp'],
                    'type': 'trade'
                }
                
                self.trades.append(trade_record)
                
                # 更新解析結果
                data.update({
                    'trade_value': trade_value,
                    'message': f"🎉【成交】價格:{price} 數量:{qty}口 金額:{trade_value:,.0f}元",
                    'importance': 'HIGH'
                })
                
                logger.info(f"成交記錄: {seq_no} 價格:{price} 數量:{qty}口 金額:{trade_value:,.0f}元")
            
            return data
            
        except Exception as e:
            logger.error(f"處理成交回報失敗: {e}")
            return data
    
    def _process_order_success(self, data):
        """處理委託成功"""
        try:
            price = data['price']
            qty = data['qty']
            seq_no = data['seq_no']
            
            data.update({
                'message': f"✅【委託成功】序號:{seq_no} 價格:{price} 數量:{qty}口",
                'importance': 'MEDIUM'
            })
            
            return data
            
        except Exception as e:
            logger.error(f"處理委託成功失敗: {e}")
            return data
    
    def _process_order_cancel(self, data):
        """處理委託取消"""
        try:
            price = data['price']
            qty = data['qty']
            seq_no = data['seq_no']
            
            data.update({
                'message': f"🗑️【委託取消】序號:{seq_no} 價格:{price} 剩餘:{qty}口",
                'importance': 'MEDIUM'
            })
            
            return data
            
        except Exception as e:
            logger.error(f"處理委託取消失敗: {e}")
            return data
    
    def _process_order_fail(self, data):
        """處理委託失敗"""
        try:
            seq_no = data['seq_no']
            
            data.update({
                'message': f"❌【委託失敗】序號:{seq_no}",
                'importance': 'HIGH'
            })
            
            return data
            
        except Exception as e:
            logger.error(f"處理委託失敗失敗: {e}")
            return data
    
    def _safe_float(self, value):
        """安全轉換為浮點數"""
        try:
            return float(value) if value else 0.0
        except:
            return 0.0
    
    def _safe_int(self, value):
        """安全轉換為整數"""
        try:
            return int(value) if value else 0
        except:
            return 0
    
    def get_trade_summary(self):
        """取得交易摘要"""
        try:
            if not self.trades:
                return "今日尚無成交記錄"
            
            total_trades = len(self.trades)
            total_qty = sum(trade['qty'] for trade in self.trades)
            total_value = sum(trade['value'] for trade in self.trades)
            
            latest_trade = self.trades[-1]
            
            summary = f"""
📊 【當沖交易摘要】
🔢 成交筆數: {total_trades}筆
📊 總成交量: {total_qty}口
💰 總成交額: {total_value:,.0f}元
⏰ 最新成交: {latest_trade['timestamp'].strftime('%H:%M:%S')}
💵 最新價格: {latest_trade['price']}
"""
            return summary
            
        except Exception as e:
            logger.error(f"取得交易摘要失敗: {e}")
            return "交易摘要計算錯誤"
    
    def calculate_pnl(self, current_price):
        """計算當前損益 (需要當前市價)"""
        try:
            # 這裡可以實作更複雜的損益計算
            # 需要配合持倉方向 (多/空) 來計算
            pass
        except Exception as e:
            logger.error(f"計算損益失敗: {e}")
            return 0

# 全域計算器實例
daytrading_calc = DayTradingCalculator()

def parse_onnewdata_for_daytrading(bstr_data):
    """供外部調用的OnNewData解析函數"""
    return daytrading_calc.parse_onnewdata(bstr_data)

def get_daytrading_summary():
    """供外部調用的交易摘要函數"""
    return daytrading_calc.get_trade_summary()

if __name__ == "__main__":
    # 測試範例
    calc = DayTradingCalculator()
    
    # 模擬OnNewData資料
    test_data = ",TF,D,N,F020000,6363839,BNF20,TW,MTX00,,22000.0000,0.000000,,,,,,,,,1,,,20250630,14:30:15,,0000000,2315544224514,y"
    
    result = calc.parse_onnewdata(test_data)
    if result:
        print(result['message'])
        print(calc.get_trade_summary())
