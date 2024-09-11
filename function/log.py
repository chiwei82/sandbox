import logging
import os
from datetime import datetime

## 使用 logger 記錄訊息
# logger.info("程式開始執行")
# logger.warning("這是一個 warning 訊息")
# logger.error("這是一個 error 訊息")

class Logger:
    def __init__(self, log_folder="log", log_level=logging.INFO):
        """
        初始化 Logger 類別，設定 log 資料夾位置和 log 等級。
        
        :param log_folder: 儲存 log 的資料夾名稱 (預設為 "log")
        :param log_level: log 級別 (預設為 logging.INFO)
        """
        # 獲取引用這個 Logger 的腳本的執行目錄
        current_dir = os.getcwd()  # 獲取當前執行腳本的路徑
        log_dir = os.path.join(current_dir, log_folder)

        # 如果資料夾不存在，創建資料夾
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 設定 log 檔名為當天的日期
        log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

        # 設定 logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        # 避免重複添加 handlers
        if not self.logger.handlers:
            # 建立檔案處理器
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)

            # 建立終端機輸出處理器
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(log_level)

            # 設定 log 格式
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            stream_handler.setFormatter(formatter)

            # 添加處理器到 logger
            self.logger.addHandler(file_handler)
            self.logger.addHandler(stream_handler)

    def get_logger(self):
        """
        返回 logger 物件以便在其他模組中使用。
        :return: logger 物件
        """
        return self.logger
