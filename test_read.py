# test_read.py
import csv
import logging
import os

# --- 設定日誌 ---
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)
logger = logging.getLogger(__name__)

def read_first_lines(file_path, num_lines=10):
    """
    讀取並印出 CSV 檔案的前幾行。
    """
    logger.info(f"🔍 正在檢查檔案路徑: {file_path}")
    if not os.path.exists(file_path):
        logger.error(f"❌ 檔案不存在或路徑錯誤: {file_path}")
        return
    logger.info(f"✅ 檔案已找到: {file_path}")

    try:
        logger.info(f"📖 正在嘗試開啟並讀取檔案的前 {num_lines} 行...")
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            logger.info("✅ 檔案開啟成功。正在讀取內容...")
            for i, row in enumerate(reader):
                if i < num_lines:
                    # 使用 logger.info 來印出，確保格式一致
                    logger.info(f"  行 {i+1}: {row}")
                else:
                    break
            logger.info(f"🏁 已成功讀取並顯示前 {i+1} 行。")

    except Exception as e:
        logger.error(f"❌ 讀取檔案時發生錯誤: {e}", exc_info=True)

if __name__ == '__main__':
    # 檔案路徑與 data_import.py 中設定的相同
    csv_file_path = "/Users/z/chrome下載/TX00_台指近_分鐘線 - TX00_台指近_分鐘線.csv"
    read_first_lines(csv_file_path, num_lines=10)
