import time
from pynput.keyboard import Controller
from pynput import keyboard
import win32gui
import win32con

class InputSimulator:
    def __init__(self):
        self.keyboard = keyboard.Controller()
        self.pressed_keys = []
    
    def press_key(self, key):
        self.keyboard.press(key)
        self.pressed_keys.append(key)

    def move_forward(self):
        if keyboard.Key.up not in self.pressed_keys:
            self.press_key(keyboard.Key.up)
    def move_backward(self):
        if keyboard.Key.down not in self.pressed_keys:
            self.press_key(keyboard.Key.down)
    def stop_move(self):
        self.keyboard.release(keyboard.Key.up)
        self.keyboard.release(keyboard.Key.down)
        if keyboard.Key.up in self.pressed_keys:
            self.pressed_keys.remove(keyboard.Key.up)
        if keyboard.Key.down in self.pressed_keys:
            self.pressed_keys.remove(keyboard.Key.down)

    def turn_left(self):
        if keyboard.Key.right in self.pressed_keys:
            self.keyboard.release(keyboard.Key.right)
            self.pressed_keys.remove(keyboard.Key.right)
        if keyboard.Key.left not in self.pressed_keys:  
            self.press_key(keyboard.Key.left)
    def turn_right(self):
        if keyboard.Key.left in self.pressed_keys:
            self.keyboard.release(keyboard.Key.left)
            self.pressed_keys.remove(keyboard.Key.left)
        if keyboard.Key.right not in self.pressed_keys:  
            self.press_key(keyboard.Key.right)
    def stop_turn(self):
        self.keyboard.release(keyboard.Key.left)
        self.keyboard.release(keyboard.Key.right)
        if keyboard.Key.left in self.pressed_keys:
            self.pressed_keys.remove(keyboard.Key.left)
        if keyboard.Key.right in self.pressed_keys:
            self.pressed_keys.remove(keyboard.Key.right)


if __name__ == "__main__":
    from wow_bot import activate_window
    activate_window("魔兽世界")

    input_simulator = InputSimulator()
    input_simulator.turn_left()
    time.sleep(1)
    input_simulator.stop_turn()
