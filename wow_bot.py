import sys
import time

import record_path

from PyQt5 import QtWidgets, uic, QtCore
from player import Player
from utilities import activate_window

class WoWBot(QtWidgets.QMainWindow):
    def __init__(self):
        super(WoWBot, self).__init__()
        uic.loadUi('WoWBot.ui', self)  # 加载 UI 文件
        self.player = Player()
        self.player.load_path()

        self.connect_function()
        self.update_name()

        # 设置定时器以定期更新坐标
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_coordinates)
        self.timer.start(100)  # 每1000毫秒（1秒）更新一次
    
    def update_name(self):
        self.player.get_player_name()
        self.playername.setText(self.player.name)

    def update_coordinates(self):
        self.player.get_player_coord()  # 获取玩家坐标
        coords = self.player.coord
        coord_message = f"X={coords[0]:.2f}, Y={coords[1]:.2f}, Z={coords[2]:.2f}"
        self.playercoord.setText(coord_message)  # 更新坐标标签
    
    def connect_function(self):
        self.autoattack.clicked.connect(self.auto_attack)
        self.recordpath.clicked.connect(self.record_path)
        self.stop.clicked.connect(self.stop_all)
    
    def auto_attack(self):
        self.player.stop = False
        activate_window("魔兽世界")
        self.timer.timeout.connect(self.player.auto_attack)

    def record_path(self):
        record_path.record_path()

    def stop_all(self):
        self.player.stop_all()  

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = WoWBot()
    window.show()
    sys.exit(app.exec_())
