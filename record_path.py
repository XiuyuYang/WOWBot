import json
import math
from player import Player
from utilities import activate_window
import keyboard
import os



def distance(coord1, coord2):
    return math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

player = Player()

path_file_name = "path.txt"

def record_path():
    # 如果存在就删除
    if os.path.exists(path_file_name):
        os.remove(path_file_name)


    player.get_player_coord()
    path = [player.coord[:2]]

    while True:
        activate_window() 
        if keyboard.is_pressed("esc"):
            break
        player.get_player_coord()
        if distance(player.coord, path[-1]) > 8:
            path.append(player.coord[:2])
            print(f"记录路径: {player.coord[:2]}")


    # 将path转换为json格式
    path_json = json.dumps(path, indent=4)
    with open(path_file_name, "w") as f:
        f.write(path_json)





