#!/usr/bin/env python3
import threading
import time
import os
import ctypes
from copy import deepcopy
from PIL import ImageGrab
from pykeyboard import PyKeyboardEvent
from pymouse import PyMouse
import tkinter as tk
from tkinter import ttk
from tkinter import IntVar

# Параметры окна игры (измените при необходимости)
WINDOW_WIDTH = 408
WINDOW_HEIGHT = 720
X0 = 90   # X верхней ячейки в левом столбце
Y0 = 396  # Y верхней ячейки в левом столбце
DX = 37   # Дельта X между двумя горизонтальными ячейками
DY = 44   # Дельта Y между двумя вертикальными ячейками
SCRCPY_PATH = "scrcpy"    # Путь к scrcpy

# Инициализация PyMouse
mouse = PyMouse()

# Флаг для остановки автоматизации
kill = False

class KeyDown(PyKeyboardEvent):
    def __init__(self):
        super().__init__()

    def tap(self, keycode, character, press):
        global kill
        if press and keycode == 121:  # Код клавиши F10
            kill = True

def rgb_to_num(rgb, mode_value):
    red = rgb[0]
    if red <= 20:
        return 1
    if mode_value == 0:  # Режим Hard
        if red >= 60:
            return 2
        elif red <= 35:
            return 2
        elif red <= 45:
            return 3
        elif red <= 60:
            return 4
        else:
            return 0
    else:  # Режим Expert
        if red <= 35:
            return 2
        elif red <= 45:
            return 3
        elif red <= 60:
            return 4
        elif red <= 75:
            return 5
        elif red <= 90:
            return 6
        else:
            return 0

def pack_coords(x, y, x0, y0, dx, dy):
    outx = x0 + x * dx
    outy = y0 - x * 0.5 * dy + y * dy
    return int(outx), int(outy)

def click_num(x, y, num_clicks, root):
    adjusted_x = int(x + root.winfo_x() + root.winfo_width())
    adjusted_y = int(y + root.winfo_y())
    for _ in range(num_clicks):
        mouse.click(adjusted_x, adjusted_y)
        time.sleep(0.05)

def run_scrcpy():
    os.system(f"{SCRCPY_PATH} --stay-awake -m {WINDOW_HEIGHT} -b 1M")

def grab_screen(window_x, window_y, width, height, mode_value, x0, y0, dx, dy):
    screen = ImageGrab.grab((window_x, window_y, window_x + width, window_y + height))
    colors = []
    for y in range(7):
        row = []
        for x in range(7):
            if abs(x - y) <= 3:
                coords = pack_coords(x, y, x0, y0, dx, dy)
                rgb = screen.getpixel(coords)
                color_num = rgb_to_num(rgb, mode_value)
                row.append(color_num)
            else:
                row.append(0)
        colors.append(row)
    return colors

XYS_OFFSETS = [(-1, -1), (0, -1), (-1, 0), (0, 0), (1, 0), (0, 1), (1, 1)]

def simulate_click(x, y, clicks, colors, mode_value):
    for dx, dy in XYS_OFFSETS:
        x2 = x + dx
        y2 = y + dy
        if 0 <= x2 <= 6 and 0 <= y2 <= 6 and colors[y2][x2] >= 1:
            colors[y2][x2] += clicks
            limit = 2 if mode_value == 0 else 6
            while colors[y2][x2] > limit:
                colors[y2][x2] -= limit

def click_or_simulate(colors, click_flag, root, x0, y0, dx, dy, mode_value):
    for y in range(7):
        for x in reversed(range(7)):
            color = colors[y][x]
            if abs(x - y) <= 3 and color > 1 and abs(x - y - 1) <= 3 and y < 6:
                cx, cy = pack_coords(x, y + 1, x0, y0, dx, dy)
                num_clicks = (7 - color) if mode_value == 1 else 1
                if click_flag:
                    click_num(cx + 5, cy + 5, num_clicks, root)
                    time.sleep(0.1)
                simulate_click(x, y + 1, num_clicks, colors, mode_value)
                return True
    return False

NUM_DICT_HARD = {
    "1121":[0,1,0,0],
    "1212":[0,1,1,0],
    "1222":[0,0,1,0],
    "2112":[1,0,0,0],
    "2122":[0,0,0,1],
    "2211":[0,0,1,1],
    "2221":[1,0,1,0]
}

NUM_DICT_EXPERT = {
    "1141":[0,3,0,0],
    "1216":[0,1,1,2],
    "1246":[2,0,1,4],
    "1315":[4,0,0,2],
    "1345":[2,1,0,0],
    "1414":[0,3,1,0],
    "1444":[0,0,1,0],
    "1513":[4,2,0,0],
    "1543":[0,1,0,2],
    "1612":[2,1,1,0],
    "1642":[0,2,1,4],
    "2116":[1,4,0,0],
    "2146":[0,0,0,5],
    "2215":[0,4,1,1],
    "2245":[0,1,1,1],
    "2314":[1,0,0,4],
    "2344":[4,0,0,1],
    "2413":[1,1,1,0],
    "2443":[3,0,1,2],
    "2512":[5,0,0,0],
    "2542":[2,0,0,3],
    "2611":[0,2,1,3],
    "2641":[1,0,1,4],
    "3115":[0,0,0,4],
    "3145":[2,5,0,0],
    "3214":[0,1,1,0],
    "3244":[0,4,1,0],
    "3313":[4,0,0,0],
    "3343":[1,0,0,3],
    "3412":[3,0,1,1],
    "3442":[0,0,1,4],
    "3511":[0,4,0,0],
    "3541":[0,1,0,0],
    "3616":[1,0,1,3],
    "3646":[4,0,1,0],
    "4114":[3,0,0,0],
    "4144":[0,0,0,3],
    "4213":[2,0,1,1],
    "4243":[1,2,1,0],
    "4312":[1,0,0,2],
    "4342":[0,2,0,1],
    "4411":[0,0,1,3],
    "4441":[3,0,1,0],
    "4516":[1,2,0,0],
    "4546":[2,0,0,1],
    "4615":[0,2,1,1],
    "4645":[1,0,1,2],
    "5113":[0,0,0,2],
    "5143":[0,3,0,2],
    "5212":[0,1,1,4],
    "5242":[2,0,1,0],
    "5311":[0,2,0,0],
    "5341":[0,5,0,0],
    "5416":[0,3,1,2],
    "5446":[0,0,1,2],
    "5515":[2,0,0,0],
    "5545":[0,1,0,4],
    "5614":[1,0,1,1],
    "5644":[0,2,1,0],
    "6112":[0,3,0,1],
    "6142":[0,0,0,1],
    "6211":[2,0,1,5],
    "6241":[0,1,1,3],
    "6316":[1,0,0,0],
    "6346":[1,3,0,0],
    "6415":[0,0,1,1],
    "6445":[0,3,1,1],
    "6514":[0,1,0,3],
    "6544":[3,1,0,0],
    "6613":[0,2,1,5],
    "6643":[1,0,1,0]
}

def auto_click(colors, root, x0, y0, dx, dy, mode_value):
    global kill
    colors_tmp = deepcopy(colors)
    while not kill and click_or_simulate(colors_tmp, False, root, x0, y0, dx, dy, mode_value):
        pass
    bottom_row = colors_tmp[6][3:7][::-1]
    bottom_num = ''.join(str(num) for num in bottom_row)
    if bottom_num == "1111":
        click_top = [0, 0, 0, 0]
    else:
        dict_choice = NUM_DICT_EXPERT if mode_value == 1 else NUM_DICT_HARD
        click_top = dict_choice.get(bottom_num, [0, 0, 0, 0])
    for x in range(4):
        if click_top[x] > 0:
            cx, cy = pack_coords(x, 0, x0, y0, dx, dy)
            click_num(cx + 5, cy + 5, click_top[x], root)
            time.sleep(0.1)
            simulate_click(x, 0, click_top[x], colors, mode_value)
    while not kill and click_or_simulate(colors, True, root, x0, y0, dx, dy, mode_value):
        pass

def automate(root, x0, y0, dx, dy, window_width, window_height, mode_value):
    global kill
    kill = False
    click_num(100, 100, 10, root)  # Возможно, требуется для фокуса
    final_colors = [
        [2,2,2,2,0,0,0],
        [2,2,2,2,2,0,0],
        [2,2,2,2,2,2,0],
        [2,2,2,2,2,2,2],
        [0,2,2,2,2,2,2],
        [0,0,2,2,2,2,2],
        [0,0,0,2,2,2,2]
    ]
    while not kill:
        colors = grab_screen(
            root.winfo_x() + root.winfo_width(),
            root.winfo_y(),
            window_width,
            window_height,
            mode_value,
            x0, y0, dx, dy
        )
        if colors == final_colors:
            click_num(250, 690, 1, root)  # Нажатие кнопки для продолжения
            time.sleep(0.5)
            continue
        auto_click(colors, root, x0, y0, dx, dy, mode_value)
        time.sleep(0.1)

def take_screenshot(root, x0, y0, dx, dy, window_width, window_height, mode_value):
    colors = grab_screen(
        root.winfo_x() + root.winfo_width(),
        root.winfo_y(),
        window_width,
        window_height,
        mode_value,
        x0, y0, dx, dy
    )
    screen = ImageGrab.grab((
        root.winfo_x() + root.winfo_width(),
        root.winfo_y(),
        root.winfo_x() + root.winfo_width() + window_width,
        root.winfo_y() + window_height
    ))
    screen.save("arrowpuzzle.png")

def main():
    root = tk.Tk()
    root.geometry("200x200+100+100")
    root.title("ArrowPuzzleAuto")

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except:
        pass

    style = ttk.Style()
    try:
        style.theme_use("vista")
    except:
        style.theme_use("default")

    mode = IntVar(value=1)

    ttk.Button(root, text="Run scrcpy", command=lambda: threading.Thread(target=run_scrcpy, daemon=True).start()).place(relx=0, rely=0, relheight=0.2, relwidth=1)
    ttk.Button(root, text="Automate", command=lambda: threading.Thread(target=automate, args=(root, X0, Y0, DX, DY, WINDOW_WIDTH, WINDOW_HEIGHT, mode.get()), daemon=True).start()).place(relx=0, rely=0.8, relheight=0.2, relwidth=1)
    ttk.Button(root, text="Screenshot", command=lambda: take_screenshot(root, X0, Y0, DX, DY, WINDOW_WIDTH, WINDOW_HEIGHT, mode.get())).place(relx=0.5, rely=0.4, relheight=0.2, relwidth=0.5)
    ttk.Radiobutton(root, text="Hard", variable=mode, value=0).place(relx=0, rely=0.6, relheight=0.2, relwidth=0.5)
    ttk.Radiobutton(root, text="Expert", variable=mode, value=1).place(relx=0.5, rely=0.6, relheight=0.2, relwidth=0.5)
    ttk.Label(root, text="F10 to stop").place(relx=0, rely=0.4, relheight=0.2, relwidth=0.5)

    threading.Thread(target=KeyDown().run, daemon=True).start()

    root.mainloop()

if __name__ == "__main__":
    main()
