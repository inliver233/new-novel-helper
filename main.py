import sys
import os
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.utils.logger import LoggerConfig

def main():
    """主函数，应用程序入口点"""
    app = QApplication(sys.argv)

    # 定义数据目录的路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(project_root, "data")

    # 确保数据目录存在
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    # 初始化日志系统
    log_dir = os.path.join(project_root, "logs")
    logger = LoggerConfig.setup_logger(log_dir=log_dir)
    logger.info("LoreMaster 应用程序启动")

    try:
        window = MainWindow(data_path=data_path)
        window.show()
        logger.info("主窗口已显示，进入事件循环")
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"应用程序启动失败: {e}")
        raise

if __name__ == "__main__":
    main()