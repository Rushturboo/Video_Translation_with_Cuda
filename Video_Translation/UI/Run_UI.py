import sys
import UI
from PyQt5.QtWidgets import QApplication,QMainWindow
from Translation import translate as tr

class MainWindow(QMainWindow, UI.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)  # 设置界面

        # 绑定按钮点击事件
        self.pushButton.clicked.connect(self.on_button_click)
        self.pushButton_2.clicked.connect(self.on_button_2_click)

    def on_button_click(self):
        tr.video_path = tr.get_file_path()
        #print("按钮被点击了")

    def on_button_2_click(self):
        tr.run()
        print("🎉 翻译完成，视频已保存为:", tr.output_video_path)


if __name__ == '__main__':
    # 只有直接运行这个脚本，才会往下执行
    # 别的脚本文件执行，不会调用这个条件句
    # 实例化，传参

    app = QApplication(sys.argv)
    # 创建对象
    mainWindow = MainWindow()
    # 创建窗口
    mainWindow.show()
    # 进入程序的主循环，并通过exit函数确保主循环安全结束(该释放资源的一定要释放)
    sys.exit(app.exec_())

# def test():
#     print("success")