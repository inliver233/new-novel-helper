import sys
import os
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import MainWindow

def main():
    """主函数，应用程序入口点"""
    app = QApplication(sys.argv)
    
    # 定义数据目录的路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(project_root, "data")
    
    # 确保数据目录存在
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    window = MainWindow(data_path=data_path)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()