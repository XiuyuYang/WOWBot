import ctypes
import win32gui
import win32process
import win32con
import win32api
import struct
import logging
import os
import time
from datetime import datetime
import math
from enum import Enum, auto

# 简化日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class WowOffsets:
    """魔兽世界内存偏移常量"""
    # 玩家相关
    PLAYER_BASE = 0x00400000
    PLAYER_NAME = 0x00C79D18
    PLAYER_CLASS = 0x00C79D30
    PLAYER_LEVEL = 0x00C79D1C
    PLAYER_HP = 0x00C79D24
    PLAYER_MAX_HP = 0x00C79D28
    PLAYER_MANA = 0x00C79D2C
    PLAYER_MAX_MANA = 0x00C79D30
    
    # 目标相关
    TARGET_GUID = 0x00BD07B0
    TARGET_HP = 0x00BD07B8
    TARGET_MAX_HP = 0x00BD07BC
    TARGET_NAME = 0x00BD07C0
    TARGET_LEVEL = 0x00BD07C4
    
    # 战斗相关
    PLAYER_IN_COMBAT = 0x00C79D34
    PLAYER_CASTING = 0x00C79D38
    SPELL_COOLDOWN = 0x00C79D3C

class MovementState(Enum):
    """角色移动状态"""
    IDLE = auto()          # 静止
    WALKING = auto()       # 行走
    RUNNING = auto()       # 奔跑
    SWIMMING = auto()      # 游泳
    FALLING = auto()       # 下落
    FLYING = auto()        # 飞行

class CombatState(Enum):
    """战斗状态"""
    OUT_OF_COMBAT = auto() # 非战斗状态
    IN_COMBAT = auto()     # 战斗中
    CASTING = auto()       # 施法中
    STUNNED = auto()       # 被击晕
    DEAD = auto()          # 死亡

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
        
    def find_module_base(self, module_name):
        """获取指定模块的基址"""
        try:
            needed_size = ctypes.c_uint(0)
            module_handles = (ctypes.c_void_p * 1024)()
            
            # 获取函数并设置正确的参数类型
            EnumProcessModules = ctypes.windll.psapi.EnumProcessModules
            EnumProcessModules.argtypes = [
                ctypes.c_void_p,  # hProcess
                ctypes.POINTER(ctypes.c_void_p),  # lphModule
                ctypes.c_uint,  # cb
                ctypes.POINTER(ctypes.c_uint)  # lpcbNeeded
            ]
            EnumProcessModules.restype = ctypes.c_bool
            
            GetModuleFileNameExW = ctypes.windll.psapi.GetModuleFileNameExW
            GetModuleFileNameExW.argtypes = [
                ctypes.c_void_p,  # hProcess
                ctypes.c_void_p,  # hModule
                ctypes.c_wchar_p,  # lpFilename
                ctypes.c_uint  # nSize
            ]
            GetModuleFileNameExW.restype = ctypes.c_uint
            
            # 确保handle是c_void_p类型
            process_handle = ctypes.c_void_p(self.handle)
            
            if not EnumProcessModules(
                process_handle,
                module_handles,
                ctypes.sizeof(module_handles),
                ctypes.byref(needed_size)
            ):
                error_code = ctypes.GetLastError()
                logging.error(f"枚举进程模块失败，错误码: {error_code}")
                return None
            
            module_count = min(needed_size.value // ctypes.sizeof(ctypes.c_void_p), 1024)
            
            for i in range(module_count):
                module_base = module_handles[i]
                if not module_base:
                    continue
                    
                module_name_buffer = ctypes.create_unicode_buffer(260)
                if GetModuleFileNameExW(process_handle, module_base, module_name_buffer, 260):
                    full_path = module_name_buffer.value
                    base_module_name = os.path.basename(full_path).lower()
                    
                    # 获取模块地址，修复'int' object has no attribute 'value'错误
                    if isinstance(module_base, ctypes.c_void_p):
                        module_base_value = module_base.value
                    else:
                        module_base_value = int(module_base)
                    
                    if base_module_name == module_name.lower():
                        logging.info(f"找到目标模块 {module_name}，基址: 0x{module_base_value:X}")
                        return module_base_value
                    
                    if module_name.lower() in base_module_name:
                        logging.info(f"找到类似模块: {base_module_name}，基址: 0x{module_base_value:X}")
            
            logging.warning(f"未找到模块 {module_name}")
            return None
        except Exception as e:
            logging.error(f"查找模块基址时出错: {str(e)}")
            return None
    
    def search_memory_for_coordinates(self, sample_x=-171.4080048, sample_y=-9339.459961, sample_z=63.6859436, tolerance=1.0):
        """简化版内存扫描"""
        try:
            logging.info("开始扫描内存查找坐标...")
            
            start_address = 0x00400000
            end_address = 0x7FFFFFFF
            block_size = 4096
            current_address = start_address
            matched_addresses = []
            
            # 每100MB记录一次进度，减少日志输出
            while current_address < end_address:
                if (current_address - start_address) % (100 * 1024 * 1024) == 0:
                    mb_scanned = (current_address - start_address) / (1024 * 1024)
                    logging.info(f"已扫描内存: {int(mb_scanned)} MB")
                
                try:
                    mem_data = self.read_memory(current_address, block_size)
                    if not mem_data:
                        current_address += block_size
                        continue
                        
                    for i in range(0, len(mem_data) - 4):
                        value_bytes = mem_data[i:i+4]
                        try:
                            value = struct.unpack('f', value_bytes)[0]
                            
                            if abs(value - sample_x) < tolerance:
                                possible_address = current_address + i
                                
                                potential_y = self.read_float(possible_address + 8)
                                potential_z = self.read_float(possible_address + 4)
                                
                                if (potential_y is not None and potential_z is not None and
                                    abs(potential_y - sample_y) < tolerance and 
                                    abs(potential_z - sample_z) < tolerance):
                                    
                                    logging.info(f"找到匹配的坐标集: X={value}, Y={potential_y}, Z={potential_z}")
                                    matched_addresses.append(possible_address)
                                    
                        except (struct.error, ValueError):
                            pass
                            
                except Exception:
                    pass
                    
                current_address += block_size
                
                if len(matched_addresses) >= 3:
                    break
                    
            if matched_addresses:
                self.real_address = {
                    'X': matched_addresses[0],
                    'Y': matched_addresses[0] + 8,
                    'Z': matched_addresses[0] + 4
                }
                self.use_absolute_address = True
                return True
                
            return False
                
        except Exception as e:
            logging.error(f"扫描内存时出错: {e}")
            return False

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
        
        # 直接查找wow.exe模块
        wow_base = self.find_module_base("wow.exe")
        if wow_base:
            self.wow_base = wow_base
            logging.info(f"使用wow.exe基址: 0x{wow_base:X}")
            
            # 测试读取
            test_coords = self.read_coordinates()
            if test_coords and all(self.is_valid_coordinate(c) for c in test_coords):
                return True
                
            # 如果测试读取失败，尝试内存扫描
            if self.search_memory_for_coordinates():
                return True
            
            # 最后尝试绝对地址
            self.use_absolute_address = True
            return True
        else:
            logging.error("无法找到wow.exe模块")
            # 尝试使用绝对地址
            self.use_absolute_address = True
            return True
        
    def close(self):
        """清理资源"""
        if self.process_handle:
            self.process_handle.close()

class WowBot(WowCoordinatesReader):
    """WoW机器人基础类"""
    def __init__(self):
        super().__init__()
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
        
    def get_player_info(self):
        """获取玩家信息"""
        try:
            if not self.wow_base:
                return None
                
            info = {
                'name': self.read_string(self.wow_base + WowOffsets.PLAYER_NAME),
                'level': self.read_int(self.wow_base + WowOffsets.PLAYER_LEVEL),
                'hp': self.read_int(self.wow_base + WowOffsets.PLAYER_HP),
                'max_hp': self.read_int(self.wow_base + WowOffsets.PLAYER_MAX_HP),
                'mana': self.read_int(self.wow_base + WowOffsets.PLAYER_MANA),
                'max_mana': self.read_int(self.wow_base + WowOffsets.PLAYER_MAX_MANA),
                'position': self.read_coordinates()
            }
            return info
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"获取玩家信息失败: {e}")
            return None
            
    def get_target_info(self):
        """获取目标信息"""
        try:
            if not self.wow_base:
                return None
                
            # 读取目标基本信息
            guid = self.read_int64(self.wow_base + WowOffsets.TARGET_GUID)
            if not guid:
                self.target_info = {'guid': None}
                return None
                
            # 更新目标信息
            self.target_info = {
                'guid': guid,
                'name': self.read_string(self.wow_base + WowOffsets.TARGET_NAME),
                'level': self.read_int(self.wow_base + WowOffsets.TARGET_LEVEL),
                'hp': self.read_int(self.wow_base + WowOffsets.TARGET_HP),
                'max_hp': self.read_int(self.wow_base + WowOffsets.TARGET_MAX_HP)
            }
            
            # 计算与目标的距离
            target_pos = self.get_target_position()
            if target_pos:
                player_pos = self.read_coordinates()
                if player_pos:
                    self.target_info['distance'] = self.calculate_distance(player_pos, target_pos)
            
            return self.target_info
            
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"获取目标信息失败: {e}")
            return None
            
    def get_target_position(self):
        """获取目标位置"""
        # TODO: 实现目标位置读取
        return None
        
    def calculate_distance(self, pos1, pos2):
        """计算两点间距离"""
        if not pos1 or not pos2:
            return float('inf')
            
        x1, y1, z1 = pos1
        x2, y2, z2 = pos2
        return math.sqrt((x2-x1)**2 + (y2-y1)**2 + (z2-z1)**2)
        
    def move_to_coordinates(self, target_x, target_y, target_z, precision=0.5):
        """移动到指定坐标"""
        try:
            current_pos = self.read_coordinates()
            if not current_pos:
                raise Exception("无法获取当前位置")
                
            distance = self.calculate_distance(current_pos, (target_x, target_y, target_z))
            if distance <= precision:
                return True
                
            # TODO: 实现具体的移动逻辑
            return False
            
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"移动到指定坐标失败: {e}")
            return False
            
    def face_target(self):
        """面向目标"""
        try:
            target_pos = self.get_target_position()
            if not target_pos:
                return False
                
            # TODO: 实现面向目标的逻辑
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"面向目标失败: {e}")
            return False
            
    def cast_spell(self, spell_id):
        """释放技能"""
        try:
            if not self.is_spell_ready(spell_id):
                return False
                
            # TODO: 实现释放技能的逻辑
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"释放技能失败: {e}")
            return False
            
    def is_spell_ready(self, spell_id):
        """检查技能是否可用"""
        try:
            # TODO: 实现检查技能冷却的逻辑
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"检查技能状态失败: {e}")
            return False
            
    def update_states(self):
        """更新状态信息"""
        try:
            # 更新战斗状态
            in_combat = self.read_bool(self.wow_base + WowOffsets.PLAYER_IN_COMBAT)
            is_casting = self.read_bool(self.wow_base + WowOffsets.PLAYER_CASTING)
            
            if in_combat:
                self.combat_state = CombatState.IN_COMBAT
                if is_casting:
                    self.combat_state = CombatState.CASTING
            else:
                self.combat_state = CombatState.OUT_OF_COMBAT
                
            # TODO: 实现移动状态检测
            self.movement_state = MovementState.IDLE
            
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"更新状态失败: {e}")
            return False
            
    def read_string(self, address, max_length=128):
        """读取以null结尾的字符串"""
        try:
            data = self.read_memory(address, max_length)
            if not data:
                return None
                
            # 查找字符串结束符
            null_pos = data.find(b'\x00')
            if null_pos != -1:
                data = data[:null_pos]
                
            return data.decode('utf-8', errors='ignore')
            
        except Exception:
            return None
            
    def read_int(self, address):
        """读取32位整数"""
        data = self.read_memory(address, 4)
        if data:
            return struct.unpack('i', data)[0]
        return None
        
    def read_int64(self, address):
        """读取64位整数"""
        data = self.read_memory(address, 8)
        if data:
            return struct.unpack('q', data)[0]
        return None
        
    def read_bool(self, address):
        """读取布尔值"""
        data = self.read_memory(address, 1)
        if data:
            return struct.unpack('?', data)[0]
        return None
        
    def get_last_error(self):
        """获取最后一次错误信息"""
        return self.last_error

def get_coordinates_hex(coords):
    """获取坐标的十六进制表示"""
    if not coords:
        return None
        
    x, y, z = coords
    x_hex = hex(struct.unpack('<I', struct.pack('<f', x))[0])
    y_hex = hex(struct.unpack('<I', struct.pack('<f', y))[0])
    z_hex = hex(struct.unpack('<I', struct.pack('<f', z))[0])
    
    return (x_hex, y_hex, z_hex)

def main():
    # 命令行参数解析
    import argparse
    parser = argparse.ArgumentParser(description='魔兽世界坐标读取工具 (命令行版)')
    parser.add_argument('-c', '--count', type=int, default=0, help='指定读取次数，0表示无限读取')
    parser.add_argument('-d', '--delay', type=float, default=1.0, help='刷新间隔(秒)')
    parser.add_argument('-t', '--time', type=int, default=0, help='运行时间(秒)，0表示无限运行')
    parser.add_argument('--hex', action='store_true', help='显示十六进制坐标值')
    parser.add_argument('-q', '--quiet', action='store_true', help='静默模式，减少输出')
    args = parser.parse_args()
    
    # 静默模式下调整日志级别
    if args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    
    print("=== 魔兽世界坐标读取器 (命令行版) ===")
    
    reader = WowCoordinatesReader()
    
    # 初始化
    print("正在连接游戏...")
    if not reader.initialize():
        print("初始化失败，无法连接到游戏")
        return
    
    print("连接成功，开始读取坐标...")
    
    try:
        count = 0
        start_time = time.time()
        last_coords = None
        
        # 主循环
        while True:
            # 检查是否达到次数限制
            if args.count > 0 and count >= args.count:
                print(f"已完成 {args.count} 次坐标读取")
                break
                
            # 检查是否达到时间限制
            if args.time > 0 and (time.time() - start_time) >= args.time:
                print(f"已运行 {args.time} 秒")
                break
                
            # 读取坐标
            coords = reader.read_coordinates()
            count += 1
            
            if coords:
                x, y, z = coords
                
                # 判断坐标是否变化（如果启用了quiet模式）
                if args.quiet and coords == last_coords and count > 1:
                    # 只在坐标变化时输出
                    pass
                else:
                    print(f"[{count}] 坐标: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
                    
                    # 显示十六进制值
                    if args.hex:
                        hex_coords = get_coordinates_hex(coords)
                        if hex_coords:
                            x_hex, y_hex, z_hex = hex_coords
                            print(f"    十六进制: X={x_hex}, Y={y_hex}, Z={z_hex}")
                
                last_coords = coords
            else:
                print(f"[{count}] 无法读取坐标")
                
            # 延时
            time.sleep(args.delay)
            
    except KeyboardInterrupt:
        print("\n用户中断程序")
    finally:
        reader.close()
        print("=== 程序已退出 ===")

def bot_example():
    bot = WowBot()
    if not bot.initialize():
        print("初始化失败")
        return
        
    try:
        # 获取玩家信息
        player_info = bot.get_player_info()
        if player_info:
            print(f"玩家信息: {player_info}")
            
        # 获取目标信息
        target_info = bot.get_target_info()
        if target_info:
            print(f"目标信息: {target_info}")
            
        # 更新状态
        bot.update_states()
        print(f"战斗状态: {bot.combat_state}")
        print(f"移动状态: {bot.movement_state}")
        
    except KeyboardInterrupt:
        print("\n程序已停止")
    finally:
        bot.close()

if __name__ == "__main__":
    # main()  # 原始坐标读取器
    bot_example()  # 机器人示例 