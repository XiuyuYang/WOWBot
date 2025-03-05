import tkinter as tk
from tkinter import messagebox
import input_simulator
import player
import threading
import time
import win32gui
import win32con


def activate_window(window_name):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # 恢复窗口
        win32gui.SetForegroundWindow(hwnd)  # 设置窗口为前景窗口
        print(f"窗口 {window_name} 已激活")
    else:
        print(f"找不到窗口 {window_name}")

class WowBotUI:
    def __init__(self, master):
        self.master = master
        master.title("WoW Bot")

        self.player = player.Player()  # 创建玩家实例
        self.player.get_player_name()  # 初始化时获取玩家名称

        self.label = tk.Label(master, text="WoW Bot")
        self.label.pack()

        # 显示玩家名称
        self.name_label = tk.Label(master, text=f"玩家: {self.player.name}")
        self.name_label.pack()

        self.coord_label = tk.Label(master, text="坐标: X=0, Y=0, Z=0")
        self.coord_label.pack()

        self.quit_button = tk.Button(master, text="退出", command=master.quit)
        self.quit_button.pack()

        # 启动定时更新坐标
        self.update_coordinates()

    def update_coordinates(self):
        self.player.get_player_coord()  # 获取玩家坐标
        coords = self.player.coord
        coord_message = f"坐标: X={coords[0]:.2f}, Y={coords[1]:.2f}, Z={coords[2]:.2f}"
        self.coord_label.config(text=coord_message)  # 更新坐标标签
        self.master.after(100, self.update_coordinates)  # 每1000毫秒（1秒）更新一次

def main():
    root = tk.Tk()
    app = WowBotUI(root)
    root.mainloop() 

if __name__ == "__main__":
    main()


