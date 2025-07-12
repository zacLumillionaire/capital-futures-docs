#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔧 分步查詢實現方案
替代複雜JOIN查詢，降低風險
"""

def _get_position_info_step_by_step(self, position_id: int) -> Optional[Dict]:
    """分步查詢版本 - 🔧 替代複雜JOIN"""
    try:
        from datetime import date
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 🔧 步驟1：查詢部位基本信息（簡單快速）
            cursor.execute('''
                SELECT * FROM position_records 
                WHERE id = ? AND status = 'ACTIVE'
            ''', (position_id,))
            
            position_row = cursor.fetchone()
            if not position_row:
                return None
            
            # 轉換為字典
            columns = [description[0] for description in cursor.description]
            position_data = dict(zip(columns, position_row))
            
            # 🔧 步驟2：查詢策略組信息（有索引支持）
            group_id = position_data.get('group_id')
            if group_id:
                cursor.execute('''
                    SELECT range_high, range_low, direction as group_direction
                    FROM strategy_groups
                    WHERE group_id = ? AND date = ?
                    ORDER BY id DESC
                    LIMIT 1
                ''', (group_id, date.today().isoformat()))
                
                group_row = cursor.fetchone()
                if group_row:
                    # 🔧 步驟3：合併信息
                    position_data['range_high'] = group_row[0]
                    position_data['range_low'] = group_row[1]
                    position_data['group_direction'] = group_row[2]
                else:
                    # 策略組信息缺失，記錄警告但不失敗
                    logger.warning(f"找不到策略組信息: group_id={group_id}, date={date.today().isoformat()}")
                    # 使用默認值或從部位信息推導
                    position_data['range_high'] = None
                    position_data['range_low'] = None
                    position_data['group_direction'] = position_data.get('direction')
            
            return position_data

    except Exception as e:
        logger.error(f"分步查詢部位資訊失敗: {e}")
        return None

def _get_position_info_with_fallback(self, position_id: int) -> Optional[Dict]:
    """帶回退機制的查詢 - 🔧 最安全的實現"""
    
    # 🔧 方案1：嘗試分步查詢（推薦）
    try:
        result = self._get_position_info_step_by_step(position_id)
        if result:
            return result
    except Exception as e:
        logger.warning(f"分步查詢失敗，嘗試原始查詢: {e}")
    
    # 🔧 方案2：回退到原始JOIN查詢
    try:
        return self._get_position_info_original(position_id)
    except Exception as e:
        logger.error(f"原始查詢也失敗: {e}")
        return None

def _get_position_info_original(self, position_id: int) -> Optional[Dict]:
    """原始JOIN查詢 - 🔧 保留作為備用"""
    try:
        from datetime import date
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT pr.*, sg.range_high, sg.range_low, sg.direction as group_direction
                FROM position_records pr
                JOIN (
                    SELECT * FROM strategy_groups
                    WHERE date = ?
                    ORDER BY id DESC
                ) sg ON pr.group_id = sg.group_id
                WHERE pr.id = ? AND pr.status = 'ACTIVE'
            ''', (date.today().isoformat(), position_id))

            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None

    except Exception as e:
        logger.error(f"原始查詢部位資訊失敗: {e}")
        return None

# 🔧 實施方案：漸進式替換
"""
階段1：添加新方法（不影響現有功能）
- 添加 _get_position_info_step_by_step
- 添加 _get_position_info_with_fallback
- 保留原始 _get_position_info

階段2：測試新方法
- 在測試環境驗證分步查詢
- 對比性能和準確性
- 確認無數據不一致問題

階段3：漸進替換
- 修改 _get_position_info 調用 _get_position_info_with_fallback
- 監控運行狀況
- 如有問題立即回滾

階段4：清理代碼
- 確認穩定運行後移除原始方法
- 簡化代碼結構
"""

# 🔧 風險評估
"""
🟡 中低風險原因：
✅ 保留原始查詢作為回退
✅ 分步查詢邏輯簡單清晰
✅ 可以漸進式實施
✅ 隨時可以回滾

⚠️ 需要注意：
- 兩次查詢之間的數據一致性
- 策略組信息缺失的處理
- 性能是否真的有改善

🔧 緩解措施：
- 使用事務確保一致性
- 完善異常處理
- 充分測試後再部署
"""
