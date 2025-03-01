import tkinter as tk
from tkinter import ttk
import pyautogui
import time
import keyboard
import cv2
import numpy as np
from PIL import ImageGrab
import sys
import logging
from datetime import datetime
import math
import win32gui
import win32process
import win32con
import win32api
import ctypes
import struct
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'wow_bot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class MovementState:
    """角色移动状态"""
    IDLE = "静止"
    WALKING = "行走"
    RUNNING = "奔跑"
    SWIMMING = "游泳"
    FALLING = "下落"
    FLYING = "飞行"

class CombatState:
    """战斗状态"""
    OUT_OF_COMBAT = "脱战"
    IN_COMBAT = "战斗中"
    CASTING = "施法中"
    STUNNED = "被击晕"
    DEAD = "死亡"

class WowCoordinatesReader:
    def __init__(self):
        self.process_handle = None
        self.handle = None
        self.process_id = None
        self.window_handle = None
        self.wow_base = None
        self.use_absolute_address = False
        self.real_address = {
            'X': 0x02CD5C24,
            'Y': 0x02CD5C2C, 
            'Z': 0x02CD5C28
        }
        
        # 坐标偏移量
        self.X_OFFSET = 0x65C24
        self.Y_OFFSET = 0x65C2C
        self.Z_OFFSET = 0x65C28
        
    def find_wow_window(self):
        """查找魔兽世界窗口"""
        self.window_handle = win32gui.FindWindow("GxWindowClass", None)
        if not self.window_handle:
            self.window_handle = win32gui.FindWindow("GxWindowClassD3d", None)
        
        if not self.window_handle:
            logging.error("未找到魔兽世界窗口")
            return False
            
        logging.info(f"找到魔兽世界窗口，句柄: {self.window_handle}")
        return True
        
    def get_process_info(self):
        """获取进程ID和句柄"""
        if not self.window_handle:
            return False
            
        _, self.process_id = win32process.GetWindowThreadProcessId(self.window_handle)
        if not self.process_id:
            logging.error("无法获取进程ID")
            return False
            
        self.process_handle = win32api.OpenProcess(
            win32con.PROCESS_VM_READ | win32con.PROCESS_QUERY_INFORMATION,
            False,
            self.process_id
        )
        
        if not self.process_handle:
            logging.error("无法打开进程")
            return False
            
        self.handle = self.process_handle.handle
        logging.info(f"成功获取进程信息，PID: {self.process_id}")
        return True
        
    def read_memory(self, address, size):
        """读取内存"""
        try:
            if not self.handle:
                return None
                
            buffer = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_ulong(0)
            
            result = ctypes.windll.kernel32.ReadProcessMemory(
                int(self.handle),
                ctypes.c_void_p(address),
                buffer,
                size,
                ctypes.byref(bytes_read)
            )
            
            if not result or bytes_read.value != size:
                return None
                
            return buffer.raw
            
        except Exception:
            return None
            
    def read_float(self, address):
        """读取浮点数值"""
        data = self.read_memory(address, 4)
        if data:
            try:
                return struct.unpack('f', data)[0]
            except struct.error:
                return None
        return None
        
    def is_valid_coordinate(self, value):
        """检查坐标值是否有效"""
        if value is None:
            return False
        if value != value or abs(value) == float('inf'):
            return False
        if abs(value) > 20000:
            return False
        return True
        
    def read_coordinates(self):
        """读取角色坐标"""
        try:
            if self.use_absolute_address:
                x_addr = self.real_address['X']
                y_addr = self.real_address['Y']
                z_addr = self.real_address['Z']
            elif self.wow_base:
                x_addr = self.wow_base + self.X_OFFSET
                y_addr = self.wow_base + self.Y_OFFSET
                z_addr = self.wow_base + self.Z_OFFSET
            else:
                x_addr = self.real_address['X']
                y_addr = self.real_address['Y']
                z_addr = self.real_address['Z']
            
            x = self.read_float(x_addr)
            y = self.read_float(y_addr)
            z = self.read_float(z_addr)
            
            if not self.is_valid_coordinate(x) or not self.is_valid_coordinate(y) or not self.is_valid_coordinate(z):
                if not self.use_absolute_address and self.real_address['X'] != 0:
                    self.use_absolute_address = True
                    return self.read_coordinates()
                return None
                
            return (x, y, z)
                
        except Exception as e:
            logging.error(f"读取坐标时出错: {e}")
            return None
            
    def initialize(self):
        """初始化坐标读取器"""
        if not self.find_wow_window():
            return False
            
        if not self.get_process_info():
            return False
        
        # 直接使用绝对地址
        self.use_absolute_address = True
        return True
        
    def close(self):
        """清理资源"""
        if self.process_handle:
            self.process_handle.close()

class WowBot(WowCoordinatesReader):
    def __init__(self):
        super().__init__()
        self.running = False
        self.pause = False
        self.target_info = {
            'guid': None,
            'name': None,
            'level': 0,
            'hp': 0,
            'max_hp': 0,
            'distance': 0,
            'is_attackable': False
        }
        self.movement_state = MovementState.IDLE
        self.combat_state = CombatState.OUT_OF_COMBAT
        self.last_error = None
        
        # 设置pyautogui的安全性
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1
        
        # 小地图区域（需要根据实际游戏界面调整）
        self.minimap_region = {
            'x': 1024,  # 小地图左上角x坐标
            'y': 0,     # 小地图左上角y坐标
            'width': 200,  # 小地图宽度
            'height': 200  # 小地图高度
        }
        
        # 导航点图标模板路径
        self.nav_point_template = 'templates/nav_point.png'
        
    def set_minimap_region(self, x, y, width, height):
        """设置小地图区域
        
        Args:
            x: 小地图左上角x坐标
            y: 小地图左上角y坐标
            width: 小地图宽度
            height: 小地图高度
        """
        self.minimap_region = {
            'x': x,
            'y': y,
            'width': width,
            'height': height
        }
        logging.info(f"设置小地图区域: x={x}, y={y}, width={width}, height={height}")
        
    def get_minimap_screenshot(self):
        """获取小地图区域的截图"""
        try:
            return np.array(ImageGrab.grab(bbox=(
                self.minimap_region['x'],
                self.minimap_region['y'],
                self.minimap_region['x'] + self.minimap_region['width'],
                self.minimap_region['y'] + self.minimap_region['height']
            )))
        except Exception as e:
            logging.error(f"获取小地图截图失败: {str(e)}")
            return None
            
    def find_nav_point(self):
        """在小地图上查找导航点
        
        Returns:
            如果找到，返回导航点相对于小地图的坐标(x, y)，否则返回None
        """
        try:
            minimap = self.get_minimap_screenshot()
            if minimap is None:
                return None
                
            minimap = cv2.cvtColor(minimap, cv2.COLOR_RGB2BGR)
            template = cv2.imread(self.nav_point_template)
            
            if template is None:
                logging.error("无法加载导航点模板图像")
                return None
                
            result = cv2.matchTemplate(minimap, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= 0.8:  # 可以调整这个阈值
                h, w = template.shape[:2]
                center_x = max_loc[0] + w//2
                center_y = max_loc[1] + h//2
                return (center_x, center_y)
                
            return None
            
        except Exception as e:
            logging.error(f"查找导航点失败: {str(e)}")
            return None
            
    def calculate_direction(self, nav_point):
        """计算角色到导航点的方向
        
        Args:
            nav_point: 导航点坐标(x, y)
            
        Returns:
            方向角度（弧度）
        """
        # 小地图中心点
        center_x = self.minimap_region['width'] // 2
        center_y = self.minimap_region['height'] // 2
        
        # 计算方向
        dx = nav_point[0] - center_x
        dy = nav_point[1] - center_y
        return math.atan2(dy, dx)
        
    def adjust_direction(self, target_angle):
        """调整角色朝向
        
        Args:
            target_angle: 目标方向（弧度）
        """
        # 将鼠标移动到屏幕中心
        screen_width, screen_height = pyautogui.size()
        center_x = screen_width // 2
        center_y = screen_height // 2
        
        # 转向速度（可以调整）
        turn_speed = 0.1
        
        # 按住鼠标右键转向
        pyautogui.mouseDown(button='right')
        time.sleep(turn_speed)
        pyautogui.mouseUp(button='right')
        
    def auto_move(self):
        """自动移动到导航点"""
        nav_point = self.find_nav_point()
        if nav_point is None:
            logging.info("未找到导航点")
            return False
            
        # 计算方向
        angle = self.calculate_direction(nav_point)
        
        # 调整朝向
        self.adjust_direction(angle)
        
        # 开始移动
        pyautogui.keyDown('w')
        time.sleep(0.5)  # 移动时间可以根据距离调整
        
        # 检查是否到达目标点附近
        new_nav_point = self.find_nav_point()
        if new_nav_point is None or (
            abs(new_nav_point[0] - self.minimap_region['width']//2) < 10 and
            abs(new_nav_point[1] - self.minimap_region['height']//2) < 10
        ):
            pyautogui.keyUp('w')
            return True
            
        pyautogui.keyUp('w')
        return False
        
    def start_auto_navigation(self):
        """开始自动寻路"""
        logging.info("开始自动寻路")
        while self.running and not self.pause:
            if not self.auto_move():
                time.sleep(0.1)
            else:
                logging.info("已到达目标点")
                break
                
    def start(self):
        """启动机器人"""
        self.running = True
        logging.info("WoW机器人已启动")
        self.main_loop()
        
    def stop(self):
        """停止机器人"""
        self.running = False
        logging.info("WoW机器人已停止")
        
    def toggle_pause(self):
        """切换暂停状态"""
        self.pause = not self.pause
        status = "暂停" if self.pause else "继续"
        logging.info(f"机器人已{status}")
        
    def find_image_on_screen(self, template_path, threshold=0.8):
        """在屏幕上查找指定图像
        
        Args:
            template_path: 要查找的图像模板路径
            threshold: 匹配阈值，越高要求越精确
            
        Returns:
            如果找到，返回中心坐标(x, y)，否则返回None
        """
        try:
            # 获取屏幕截图
            screen = np.array(ImageGrab.grab())
            screen = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
            
            # 读取模板图像
            template = cv2.imread(template_path)
            
            if template is None:
                logging.error(f"无法加载模板图像: {template_path}")
                return None
                
            # 进行模板匹配
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # 计算中心点
                h, w = template.shape[:2]
                center_x = max_loc[0] + w//2
                center_y = max_loc[1] + h//2
                return (center_x, center_y)
            
            return None
            
        except Exception as e:
            logging.error(f"图像识别出错: {str(e)}")
            return None
            
    def click_at(self, x, y, right_click=False):
        """在指定位置点击
        
        Args:
            x: x坐标
            y: y坐标
            right_click: 是否右键点击
        """
        try:
            pyautogui.moveTo(x, y)
            if right_click:
                pyautogui.rightClick()
            else:
                pyautogui.click()
            logging.info(f"{'右键' if right_click else '左键'}点击坐标: ({x}, {y})")
        except Exception as e:
            logging.error(f"点击操作失败: {str(e)}")
            
    def press_key(self, key):
        """按下指定按键
        
        Args:
            key: 要按下的按键
        """
        try:
            pyautogui.press(key)
            logging.info(f"按下按键: {key}")
        except Exception as e:
            logging.error(f"按键操作失败: {str(e)}")
            
    def check_health(self):
        """检查角色血量"""
        # 这里需要根据实际游戏界面添加血量检测的逻辑
        pass
        
    def check_combat(self):
        """检查是否在战斗中"""
        # 这里需要根据实际游戏界面添加战斗状态检测的逻辑
        pass
        
    def auto_attack(self):
        """自动战斗"""
        # 这里添加具体的战斗循环逻辑
        pass
        
    def main_loop(self):
        """主循环"""
        try:
            while self.running:
                if keyboard.is_pressed('f12'):  # F12停止程序
                    self.stop()
                    break
                    
                if keyboard.is_pressed('f11'):  # F11暂停/继续
                    self.toggle_pause()
                    time.sleep(0.5)
                    
                if keyboard.is_pressed('f10'):  # F10开始自动寻路
                    self.start_auto_navigation()
                    
                if self.pause:
                    time.sleep(0.1)
                    continue
                    
                time.sleep(0.1)
                
        except Exception as e:
            logging.error(f"程序出错: {str(e)}")
            self.stop()
            
    def get_player_info(self):
        """获取玩家信息"""
        try:
            coords = self.read_coordinates()
            info = {
                'position': coords,
                'hp': 100,  # 示例值
                'max_hp': 100,  # 示例值
                'level': 60,  # 示例值
                'name': "玩家",  # 示例值
            }
            return info
        except Exception as e:
            logging.error(f"获取玩家信息失败: {e}")
            return None
            
    def get_target_info(self):
        # 实现获取目标信息的逻辑
        return {}
        
    def update_states(self):
        """更新状态"""
        # 这里可以添加实际的状态检测逻辑
        pass
        
    def combat_state(self):
        # 实现获取战斗状态的逻辑
        return ""
        
    def movement_state(self):
        # 实现获取移动状态的逻辑
        return ""
        
class BotUI:
    def __init__(self, bot):
        self.bot = bot
        self.root = tk.Tk()
        self.root.title("WoW Bot 状态")
        self.root.geometry("300x400")
        self.root.attributes('-topmost', True)  # 窗口置顶
        
        # 设置样式
        style = ttk.Style()
        style.configure("Status.TLabel", padding=5, background="#f0f0f0")
        
        # 创建状态显示区域
        self.create_status_widgets()
        
        # 创建控制按钮
        self.create_control_buttons()
        
        # 定期更新状态
        self.update_status()
        
    def create_status_widgets(self):
        # 状态框架
        status_frame = ttk.LabelFrame(self.root, text="玩家状态", padding=10)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 状态标签
        self.coords_label = ttk.Label(status_frame, text="坐标: 未知", style="Status.TLabel")
        self.coords_label.pack(fill=tk.X)
        
        self.hp_label = ttk.Label(status_frame, text="生命值: 未知", style="Status.TLabel")
        self.hp_label.pack(fill=tk.X)
        
        self.combat_label = ttk.Label(status_frame, text="战斗状态: 未知", style="Status.TLabel")
        self.combat_label.pack(fill=tk.X)
        
        self.movement_label = ttk.Label(status_frame, text="移动状态: 未知", style="Status.TLabel")
        self.movement_label.pack(fill=tk.X)
        
    def create_control_buttons(self):
        # 按钮框架
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 开始/停止按钮
        self.start_button = ttk.Button(button_frame, text="开始", command=self.bot.start)
        self.start_button.pack(fill=tk.X, pady=2)
        
        self.stop_button = ttk.Button(button_frame, text="停止", command=self.bot.stop)
        self.stop_button.pack(fill=tk.X, pady=2)
        
        self.pause_button = ttk.Button(button_frame, text="暂停/继续", command=self.bot.toggle_pause)
        self.pause_button.pack(fill=tk.X, pady=2)
        
    def update_status(self):
        # 更新坐标
        coords = self.bot.read_coordinates()
        if coords:
            self.coords_label.config(text=f"坐标: X={coords[0]:.2f}, Y={coords[1]:.2f}, Z={coords[2]:.2f}")
            
        # 更新玩家信息
        player_info = self.bot.get_player_info()
        if player_info:
            if 'hp' in player_info and 'max_hp' in player_info:
                self.hp_label.config(text=f"生命值: {player_info['hp']}/{player_info['max_hp']}")
                
        # 更新状态
        self.bot.update_states()
        self.combat_label.config(text=f"战斗状态: {self.bot.combat_state}")
        self.movement_label.config(text=f"移动状态: {self.bot.movement_state}")
        
        # 每500ms更新一次
        self.root.after(500, self.update_status)
        
    def run(self):
        self.root.mainloop()

def main():
    logging.info("正在初始化WoW机器人...")
    bot = WowBot()
    
    if bot.initialize():
        # 创建并运行UI
        ui = BotUI(bot)
        ui.run()
    else:
        print("机器人初始化失败")

if __name__ == "__main__":
    main() 