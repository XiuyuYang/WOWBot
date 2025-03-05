from imp import reload
import tkinter as tk
from tkinter import messagebox
import player
reload(player)

class WowBotUI:
    def __init__(self, master):
        self.master = master
        master.title("WoW Bot")

        # self.player = player.Player()  # 创建玩家实例

        self.label = tk.Label(master, text="WoW Bot")
        self.label.pack()

        self.status_button = tk.Button(master, text="获取玩家状态", command=self.show_status)
        self.status_button.pack()

        self.coord_button = tk.Button(master, text="获取玩家坐标", command=self.show_coordinates)
        self.coord_button.pack()

        self.quit_button = tk.Button(master, text="退出", command=master.quit)
        self.quit_button.pack()

    def show_status(self):
        return
        self.player.get_player_name()  # 获取玩家名称
        status_message = f"玩家: {self.player.name}"
        messagebox.showinfo("玩家状态", status_message)

    def show_coordinates(self):
        return
        self.player.get_player_coord()  # 获取玩家坐标
        coords = self.player.coord
        coord_message = f"坐标: X={coords[0]}, Y={coords[1]}, Z={coords[2]}"
        messagebox.showinfo("玩家坐标", coord_message)

if __name__ == "__main__":
    root = tk.Tk()
    app = WowBotUI(root)
    root.mainloop() 