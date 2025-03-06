import win32gui
import win32con



def activate_window(window_name = "魔兽世界"):
    hwnd = win32gui.FindWindow(None, window_name)
    if hwnd:
        if not win32gui.IsWindowVisible(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)  # 恢复窗口
        current_active_hwnd = win32gui.GetForegroundWindow()  
        if current_active_hwnd != hwnd:
            try:
                win32gui.SetForegroundWindow(hwnd)  # 设置窗口为前景窗口
                print(f"窗口 {window_name} 已激活")
            except Exception as e:
                print(f"设置窗口为前景窗口失败: {e}")
    else:
        print(f"找不到窗口 {window_name}")



if __name__ == "__main__":
    activate_window()