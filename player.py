import json
import time
import keyboard
from memory_reader import MemoryReader
from input_simulator import InputSimulator
import struct
import math
from utilities import activate_window


class Player(MemoryReader):
    def __init__(self):
        super().__init__()
        self.input_simulator = InputSimulator()
        self.stop = False

        self.name = None
        self.coord = None 
        self.target_coords = None
        self.target_index = 0
        self.distance_to_target = None

        self.offsets = {
            "player_name": self.base_address + 0x827D88,
            "player_coord_x": self.fmod_base + 0x65C24,
            "player_coord_y": self.fmod_base + 0x65C24 + 8,
            "player_coord_z": self.fmod_base + 0x65C24 + 4,
            "player_orientation_1": self.fmod_base + 0x47314,
            "player_orientation_2": self.fmod_base + 0x4731C,
            "player_health": self.base_address + 0x008E86E4
        }
        
    
    def get_player_name(self):
        name = self.pm.read_bytes(self.offsets["player_name"], 100)
        if name:
            string_value = name.split(b'\x00')[0].decode('utf-8', errors='ignore')
            self.name = string_value
            print(f"玩家名称: {self.name}")
    
    def get_player_coord(self):
        player_coord_x = struct.unpack('f', self.pm.read_bytes(self.offsets["player_coord_x"], 4))[0]
        player_coord_y = struct.unpack('f', self.pm.read_bytes(self.offsets["player_coord_y"], 4))[0]
        player_coord_z = struct.unpack('f', self.pm.read_bytes(self.offsets["player_coord_z"], 4))[0]
        self.coord = (player_coord_x, player_coord_y, player_coord_z)
        return self.coord
    
    # 获取玩家朝向
    def get_player_orientation(self):
        orientation_1 = struct.unpack('f', self.pm.read_bytes(self.offsets["player_orientation_1"], 4))[0]
        orientation_2 = struct.unpack('f', self.pm.read_bytes(self.offsets["player_orientation_2"], 4))[0]
        # 归一化
        orientation = (orientation_1 / math.sqrt(orientation_1**2 + orientation_2**2), orientation_2 / math.sqrt(orientation_1**2 + orientation_2**2))
        self.orientation = orientation
        return self.orientation

    def move_forward(self):
        self.input_simulator.move_forward()

    def move_backward(self):
        self.input_simulator.move_backward()
    
    def stop_move(self):
        self.input_simulator.stop_move()

    def turn_left(self):
        self.input_simulator.turn_left()

    def turn_right(self):
        self.input_simulator.turn_right()

    def stop_turn(self):
            self.input_simulator.stop_turn()
    

    def stop_all(self):
        print("停止所有动作")
        self.stop = True
        self.stop_move()
        self.stop_turn()
    
    def face_to_target(self, target_coord):
        player_coord = self.get_player_coord()
        # target_orientation = (player_coord[0] - target_coord[0], player_coord[1] - target_coord[1])
        target_orientation = (target_coord[0] - player_coord[0], target_coord[1] - player_coord[1])
        # 归一化
        target_orientation = (target_orientation[0] / math.sqrt(target_orientation[0]**2 + target_orientation[1]**2), target_orientation[1] / math.sqrt(target_orientation[0]**2 + target_orientation[1]**2))       
        player_orientation = self.get_player_orientation()
        # 确认应该左转还是右转
        cross_product = target_orientation[0] * player_orientation[1] - target_orientation[1] * player_orientation[0]

        # 朝向保留两位小数
        player_orientation = (round(player_orientation[0], 2), round(player_orientation[1], 2))
        target_orientation = (round(target_orientation[0], 2), round(target_orientation[1], 2))
        # print(f"玩家朝向: {player_orientation}, 目标朝向: {target_orientation}, 交叉乘积: {cross_product}")

        alignment_score = (player_orientation[0] - target_orientation[0])**2 + (player_orientation[1] - target_orientation[1])**2 
        # print(f"朝向误差: {alignment_score}")

        # 如果交叉乘积小于0.1，则停止转动   
        if abs(cross_product) < 0.1 and alignment_score < 2:
            self.stop_turn()
        elif cross_product < 0:
            self.turn_left()
        else:
            self.turn_right()
    
    def get_player_health(self):
        health_offsets = [0x8, 0x1CC, 0x28, 0x24, 0x4, 0x8, 0x58]
        health_base = self.base_address + 0x008E86E4
        health_address = self.get_pointer_address(health_base, health_offsets)
        print(health_address)
        health = self.pm.read_int(health_address)
        return health


    def move_to_target(self, target_coord):
        self.distance_to_target = math.sqrt((self.coord[0] - target_coord[0])**2 + (self.coord[1] - target_coord[1])**2)
        if self.distance_to_target > 1:
            # print(f"距离: {self.distance_to_target:.2f}")
            self.move_forward()
        else:
            self.stop_move()
    
    
    def move(self):
        self.get_player_coord()
        self.get_player_orientation()
        self.face_to_target(self.target_coords[self.target_index])
        self.move_to_target(self.target_coords[self.target_index])
        if self.distance_to_target < 2:
            self.target_index += 1
            if self.target_index >= len(self.target_coords):
                self.target_coords.reverse()   
                self.target_index = 0
        return True


    def load_path(self):
        with open("path.txt", "r") as f:
            self.target_coords = json.loads(f.read())
    
    def auto_attack(self):
        if self.stop:
            return
        self.move()



if __name__ == "__main__":
    player = Player()
    print(player.get_player_health())
    print(player.get_player_coord())
    print(player.get_player_orientation())
    player.get_player_name()




    
