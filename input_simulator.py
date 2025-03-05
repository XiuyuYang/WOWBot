import time
from pynput.keyboard import Controller
from pynput import keyboard
import win32gui
import win32con

class InputSimulator:
    def __init__(self):
        self.keyboard = keyboard.Controller()

    def move_forward(self):
        self.keyboard.press(keyboard.Key.up)

    def move_backward(self):
        self.keyboard.press(keyboard.Key.down)

    def stop_move(self):
        self.keyboard.release(keyboard.Key.up)
        self.keyboard.release(keyboard.Key.down)

    def turn_left(self):
        self.keyboard.press(keyboard.Key.left)

    def turn_right(self):
        self.keyboard.press(keyboard.Key.right)

    def stop_turn(self):
        self.keyboard.release(keyboard.Key.left)
        self.keyboard.release(keyboard.Key.right)


