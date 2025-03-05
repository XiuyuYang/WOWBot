from memory_reader import MemoryReader
from input_simulator import InputSimulator
import struct



class Player(MemoryReader):
    def __init__(self):
        super().__init__()
        self.input_simulator = InputSimulator()

        self.name = None
        self.coord = None   
        self.offsets = {
            "player_name": 0x827D88,
            "player_coord_x": 0x65C24,
            "player_coord_y": 0x65C24 + 8,
            "player_coord_z": 0x65C24 + 4
        }
        
    
    def get_player_name(self):
        name_address = self.base_address + self.offsets["player_name"]
        name = self.pm.read_bytes(name_address, 100)
        if name:
            string_value = name.split(b'\x00')[0].decode('utf-8', errors='ignore')
            self.name = string_value
    
    def get_player_coord(self):
        player_coord_x = struct.unpack('f', self.pm.read_bytes(self.fmod_base + self.offsets["player_coord_x"], 4))[0]
        player_coord_y = struct.unpack('f', self.pm.read_bytes(self.fmod_base + self.offsets["player_coord_y"], 4))[0]
        player_coord_z = struct.unpack('f', self.pm.read_bytes(self.fmod_base + self.offsets["player_coord_z"], 4))[0]
        self.coord = (player_coord_x, player_coord_y, player_coord_z)

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





