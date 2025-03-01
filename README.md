# 魔兽世界自动化程序

这是一个用Python编写的魔兽世界自动化程序，可以帮助实现游戏中的一些自动化操作。

## 功能特点

- 自动寻路系统
  - 识别小地图导航点
  - 自动调整角色朝向
  - 智能移动控制
- 图像识别自动化
- 键盘和鼠标操作
- 可暂停/继续操作
- 详细的日志记录
- 安全的失控保护机制

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 确保已安装所有依赖
2. 配置小地图区域：
   - 在 `wow_bot.py` 中设置 `minimap_region` 的坐标和大小
   - 或者使用 `set_minimap_region()` 方法动态设置
3. 准备导航点模板：
   - 截取游戏中导航点图标
   - 保存为 `templates/nav_point.png`
4. 运行程序：
```bash
python wow_bot.py
```

## 控制按键

- F10: 开始自动寻路
- F11: 暂停/继续程序
- F12: 退出程序

## 自动寻路使用说明

1. 在游戏中设置导航点（右键点击小地图）
2. 按 F10 开始自动寻路
3. 程序会自动：
   - 识别导航点位置
   - 调整角色朝向
   - 控制角色移动
   - 到达目标点后自动停止

## 自定义配置

1. 将需要识别的游戏界面元素截图保存到 `templates` 目录
2. 根据需要修改 `wow_bot.py` 中的自动化逻辑
3. 调整小地图区域设置：
```python
bot.set_minimap_region(x=1024, y=0, width=200, height=200)
```

## 注意事项

- 使用前请确保游戏窗口处于活动状态
- 建议在测试服务器上进行测试
- 请遵守游戏使用条款
- 使用 pyautogui 的 FAILSAFE 功能：将鼠标快速移动到屏幕左上角可以紧急停止程序
- 自动寻路时注意避免碰撞和卡住

## 日志

程序运行时会自动创建日志文件，格式为 `wow_bot_YYYYMMDD_HHMMSS.log`，记录所有操作和错误信息。 