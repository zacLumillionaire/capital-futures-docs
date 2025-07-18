# ExitGroup 屬性比對報告

## 📋 比對摘要

基於代碼檢索和分析，測試機和正式機使用**相同的** `simplified_order_tracker.py` 文件，因此ExitGroup類定義是一致的。

**比對時間**: 2025年7月17日  
**比對結果**: ✅ **完全一致**  
**共享文件**: `Capital_Official_Framework\simplified_order_tracker.py`  

## 🔍 詳細比對分析

### 測試機和正式機的架構

**測試機 (virtual_simple_integrated.py)**:
- 使用相同的 `simplified_order_tracker.py`
- 使用 `test_virtual_strategy.db` 資料庫
- 通過 `sys.path` 修改指向虛擬模組

**正式機 (simple_integrated.py)**:
- 使用相同的 `simplified_order_tracker.py`
- 使用 `multi_group_strategy.db` 資料庫
- 直接導入原始模組

### ExitGroup 類定義 (共享)

**文件位置**: `Capital_Official_Framework\simplified_order_tracker.py` 第72-108行

```python
@dataclass
class ExitGroup:
    """平倉組追蹤器 - 🔧 修復：支援口級別平倉追價機制"""
    # 基本屬性
    position_id: int
    total_lots: int          # 需要平倉的總口數
    direction: str           # 原始部位方向 (LONG/SHORT)
    exit_direction: str      # 平倉方向 (SHORT/LONG)
    target_price: float      # 目標平倉價格
    product: str             # 商品代碼

    # 🔧 修復：添加缺少的進場價格屬性（參考測試機）
    entry_price: float = None  # 原始進場價格，用於損益計算

    # 統計數據
    submitted_lots: int = 0   # 已送出平倉口數
    filled_lots: int = 0      # 已平倉口數
    cancelled_lots: int = 0   # 已取消口數

    # 🔧 修復：口級別平倉追價控制
    retry_count: int = 0      # 組級別追價次數（統計用）
    max_retries: int = 5      # 每口最大追價次數
    individual_retry_counts: dict = field(default_factory=dict)  # 每口的追價次數
    price_tolerance: float = 10.0  # 價格容差(點)

    # 🔧 新增：平倉追價行為控制開關
    enable_cancel_retry: bool = True    # 是否啟用取消追價（FOK失敗）
    enable_partial_retry: bool = False  # 是否啟用部分成交追價（口數不符）

    # 時間控制
    submit_time: float = 0    # 提交時間
    last_retry_time: float = 0  # 最後重試時間

    # 🔧 修復：口級別平倉追價狀態控制
    pending_retry_lots: int = 0  # 等待追價的口數
    is_retrying: bool = False    # 是否正在追價中
    active_retry_lots: set = field(default_factory=set)  # 正在追價的口索引
```

## ✅ 屬性完整性檢查

### 核心屬性 (6個)
| 屬性名 | 類型 | 用途 | 測試機 | 正式機 | 狀態 |
|--------|------|------|--------|--------|------|
| `position_id` | int | 部位ID | ✅ | ✅ | 一致 |
| `total_lots` | int | 總口數 | ✅ | ✅ | 一致 |
| `direction` | str | 原始部位方向 | ✅ | ✅ | 一致 |
| `exit_direction` | str | 平倉方向 | ✅ | ✅ | 一致 |
| `target_price` | float | 目標價格 | ✅ | ✅ | 一致 |
| `product` | str | 商品代碼 | ✅ | ✅ | 一致 |

### 關鍵修復屬性 (1個)
| 屬性名 | 類型 | 用途 | 測試機 | 正式機 | 狀態 |
|--------|------|------|--------|--------|------|
| `entry_price` | float | 進場價格 | ✅ | ✅ | **已修復** |

### 統計數據屬性 (3個)
| 屬性名 | 類型 | 用途 | 測試機 | 正式機 | 狀態 |
|--------|------|------|--------|--------|------|
| `submitted_lots` | int | 已送出口數 | ✅ | ✅ | 一致 |
| `filled_lots` | int | 已平倉口數 | ✅ | ✅ | 一致 |
| `cancelled_lots` | int | 已取消口數 | ✅ | ✅ | 一致 |

### 追價控制屬性 (5個)
| 屬性名 | 類型 | 用途 | 測試機 | 正式機 | 狀態 |
|--------|------|------|--------|--------|------|
| `retry_count` | int | 組級別追價次數 | ✅ | ✅ | 一致 |
| `max_retries` | int | 最大追價次數 | ✅ | ✅ | 一致 |
| `individual_retry_counts` | dict | 口級別追價次數 | ✅ | ✅ | 一致 |
| `price_tolerance` | float | 價格容差 | ✅ | ✅ | 一致 |
| `active_retry_lots` | set | 正在追價的口 | ✅ | ✅ | 一致 |

### 行為控制屬性 (2個)
| 屬性名 | 類型 | 用途 | 測試機 | 正式機 | 狀態 |
|--------|------|------|--------|--------|------|
| `enable_cancel_retry` | bool | 啟用取消追價 | ✅ | ✅ | 一致 |
| `enable_partial_retry` | bool | 啟用部分追價 | ✅ | ✅ | 一致 |

### 時間控制屬性 (2個)
| 屬性名 | 類型 | 用途 | 測試機 | 正式機 | 狀態 |
|--------|------|------|--------|--------|------|
| `submit_time` | float | 提交時間 | ✅ | ✅ | 一致 |
| `last_retry_time` | float | 最後重試時間 | ✅ | ✅ | 一致 |

### 狀態控制屬性 (2個)
| 屬性名 | 類型 | 用途 | 測試機 | 正式機 | 狀態 |
|--------|------|------|--------|--------|------|
| `pending_retry_lots` | int | 等待追價口數 | ✅ | ✅ | 一致 |
| `is_retrying` | bool | 是否追價中 | ✅ | ✅ | 一致 |

## 🔧 方法完整性檢查

### 屬性方法 (1個)
| 方法名 | 用途 | 測試機 | 正式機 | 狀態 |
|--------|------|--------|--------|------|
| `remaining_lots` | 剩餘口數 | ✅ | ✅ | 一致 |

### 核心方法 (4個)
| 方法名 | 用途 | 測試機 | 正式機 | 狀態 |
|--------|------|--------|--------|------|
| `get_current_lot_index()` | 獲取當前口索引 | ✅ | ✅ | 一致 |
| `needs_retry_for_lot()` | 檢查是否需要追價 | ✅ | ✅ | 一致 |
| `increment_retry_for_lot()` | 增加追價次數 | ✅ | ✅ | 一致 |
| `complete_retry_for_lot()` | 完成追價 | ✅ | ✅ | 一致 |

## 📊 使用方式比對

### 註冊方式比對

**測試機使用方式** (從測試腳本):
```python
# 簡化平倉追價測試.py 第25-32行
exit_group = ExitGroup(
    position_id=127,
    total_lots=3,
    direction="LONG",
    exit_direction="SHORT", 
    target_price=22675.0,
    product="TM0000"
)
```

**正式機使用方式** (從 register_exit_group):
```python
# simplified_order_tracker.py 第711-722行
exit_group = ExitGroup(
    position_id=position_id,
    total_lots=total_lots,
    direction=direction,
    exit_direction=exit_direction,
    target_price=target_price,
    product=product,
    entry_price=entry_price,  # 🔧 修復：添加進場價格
    enable_cancel_retry=self.default_enable_cancel_retry,
    enable_partial_retry=self.default_enable_partial_retry
)
```

### 關鍵差異分析

**測試腳本中的簡化使用**:
- 只傳遞基本參數
- 其他屬性使用預設值
- 主要用於功能測試

**正式機中的完整使用**:
- 傳遞完整參數，包括 `entry_price`
- 設置追價行為控制開關
- 用於實際交易執行

## 🎯 結論

### ✅ 完全一致性確認

1. **類定義一致**: 測試機和正式機使用相同的 `ExitGroup` 類
2. **屬性齊全**: 所有21個屬性都存在且類型一致
3. **方法完整**: 所有5個方法都存在且邏輯一致
4. **功能對等**: 兩者具有相同的追價控制能力

### 🔧 修復狀態確認

1. **entry_price 屬性**: ✅ 已添加，解決平倉成交回調失敗問題
2. **口級別追價**: ✅ 完整支援，包含所有必要的控制屬性
3. **FIFO匹配**: ✅ 支援時間戳和狀態管理
4. **錯誤處理**: ✅ 包含完整的調試和容錯機制

### 📋 使用建議

1. **參數傳遞**: 確保在註冊平倉組時傳遞 `entry_price`
2. **行為控制**: 根據需要設置 `enable_cancel_retry` 和 `enable_partial_retry`
3. **狀態監控**: 利用統計屬性監控追價執行狀態
4. **調試支援**: 使用時間控制屬性進行問題診斷

## 🎉 總結

**ExitGroup 屬性比對結果**: ✅ **完全一致且齊全**

測試機和正式機的 ExitGroup 類定義完全相同，包含所有必要的屬性和方法。之前的平倉追價問題不是因為屬性缺失，而是因為：

1. **使用方式問題**: 註冊時沒有傳遞 `entry_price`
2. **訂單註冊問題**: 追價下單後沒有註冊新訂單
3. **FIFO匹配問題**: 沒有按時間順序匹配

所有這些問題都已在最近的修復中解決，ExitGroup 類本身是完整和正確的。
