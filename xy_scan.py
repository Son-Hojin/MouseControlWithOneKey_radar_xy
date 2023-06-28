from pynput import keyboard

from PyQt5.QtCore import Qt,  QThread, QCoreApplication, QSettings
from PyQt5.QtGui import QPainter, QPen, QIcon, QColor
from PyQt5.QtWidgets import QMainWindow, QApplication


import time
import pyautogui
import threading
import sys
import win32gui

pyautogui.FAILSAFE = False
 
app_name = "mouse_support_xy"


click_type = 1 # 1은 단일 클릭, 2은 더블 클릭 




key_state = False # 키보드 입력 확인


target_x = 0
target_y = 0

settings = QSettings("config.ini", QSettings.IniFormat)

#키 입력용 쓰레드
class key_listener(threading.Thread):
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.rep_check = False
        # 0은 누를 때, 1은 땔 때
        self.click_state = int(settings.value("LINE/click_state"))

        self.target_key = getattr(keyboard.Key, settings.value("LINE/target_key"))
        self.change_key = getattr(keyboard.Key, settings.value("LINE/change_key"))
        self.end_key = getattr(keyboard.Key, settings.value("LINE/end_key"))

    def on_press(self, key):
        global key_state
        global click_type
        
        if self.click_state == 0:
            if self.rep_check == False:
                if key == self.target_key:
                    key_state = True
                    self.rep_check = True
                    
                elif key == self.change_key:
                    click_type = (click_type % 2) + 1
                    self.rep_check = True
            

    def on_release(self, key):
        global key_state
        global click_type
        
        if key == self.end_key:
            # Stop listener
            return False

        if self.click_state == 1:
            if key == self.target_key:
                key_state = True
            elif key == self.change_key:
                click_type = (click_type % 2) + 1
        self.rep_check = False
        

    def run(self):
        with keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release) as listener:
            listener.join()
        QCoreApplication.instance().quit()


def click(x_pos, y_pos):
    pyautogui.moveTo(x_pos, y_pos, _pause = False)
    if click_type == 1:
        pyautogui.click()
    elif click_type == 2:
        pyautogui.doubleClick()


class DisplayWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        win_control = WindowController(self)
        win_control.start()
        #thread 실행
        self.guide_line_thickness = int(settings.value("LINE/guide_line_thickness"))

        r = int(settings.value("LINE/line_color_r"))
        g = int(settings.value("LINE/line_color_g"))
        b = int(settings.value("LINE/line_color_b"))
        self.click_pen = QPen(QColor(r, g, b), self.guide_line_thickness)
        self.click_pen.setCapStyle(Qt.RoundCap)

        r = int(settings.value("LINE/d_line_color_r"))
        g = int(settings.value("LINE/d_line_color_g"))
        b = int(settings.value("LINE/d_line_color_b"))
        self.double_click_pen = QPen(QColor(r,g,b), self.guide_line_thickness, Qt.DashLine)
        self.double_click_pen.setCapStyle(Qt.RoundCap)

        self.line_opacity = float(settings.value("LINE/line_opacity"))

        self.condition = 0 # 0은 가로선 움직임, 1은 세로선 움직임

        self.max_x = pyautogui.size()[0]
        self.max_y = pyautogui.size()[1]
        
    def paintEvent(self, event):
        
        painter = QPainter(self)
        painter.setOpacity(self.line_opacity)

        # 조건 따라 펜 설정
        if click_type == 2:
            painter.setPen(self.double_click_pen)
        else:
            painter.setPen(self.click_pen)

        if target_y != 0:
            #가로선 움직일 때 (y좌표 변함)
            painter.drawLine(0, target_y, self.max_x, target_y)
            
            if self.condition != 0:
            #세로선 움직일 때 (x좌표 변함)
                painter.drawLine(target_x, 0, target_x, self.max_y)
        
    

def accurate_delay(delay):
    t = time.perf_counter() + delay/1000
    while time.perf_counter() < t:
        pass

def windowEnumerationHandler(hwnd, top_windows):
    top_windows.append((hwnd, win32gui.GetWindowText(hwnd)))

def program_to_front():
    
    top_windows = []
    win32gui.EnumWindows(windowEnumerationHandler, top_windows)
    for i in top_windows:
        if app_name in i[1].lower():
            try:
                win32gui.ShowWindow(i[0], 5)
                win32gui.SetForegroundWindow(i[0])
                break
            except:
                break

class WindowController(QThread):
    global key_state
    key_state = False
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        
        self.x_wait = int(settings.value("LINE/x_wait"))
        self.y_wait = int(settings.value("LINE/y_wait"))

        # x좌표 결정선(세로선) 횟수
        self.x_time = int(settings.value("LINE/x_time")) 
        self.y_time = int(settings.value("LINE/y_time"))

        self.x_delay = int(settings.value("LINE/x_delay"))
        self.y_delay = int(settings.value("LINE/y_delay"))

        self.current_state = 0

    def key_wait(self):
        while key_state == False:
            accurate_delay(0.1)
            pass
        return
 


    def init_point(self):
        global target_x, target_y
        target_x = 0
        target_y = 0

    def run(self):
        global key_state, target_x, target_y
        while True:
            count = 0
            if self.current_state == 0:
                self.init_point()
                self.current_state = 1

            self.parent.repaint()

            if self.current_state == 1:
                self.key_wait()

            key_state = False
            # program_to_front()
            
            #가로선 움직임
            first=True
            while key_state == False:
                target_y+=1
                self.parent.repaint()
                if first:
                    time.sleep(self.y_delay)
                    first=False
                else:
                    accurate_delay(self.y_wait)
                if target_y == self.parent.max_y:
                    count += 1
                    target_y = 0
                if count == self.y_time:
                    break

            if count == self.y_time and key_state != True:
                self.current_state = 0 # back to start
                continue
            

            self.parent.condition = 1

            self.key_wait()
            count = 0

            key_state = False
            first=True
            while key_state == False:
                target_x+=1
                self.parent.repaint()
                if first:
                    time.sleep(self.x_delay)
                    first=False
                else:
                    accurate_delay(self.x_wait)
                if target_x == self.parent.max_x:
                    count += 1
                    target_y = 0
                if count == self.x_time:
                    break
            
            if count == self.x_time and key_state != True: 
                self.current_state = 2 #back to spin , 2 is nothing
                continue
            
            x = target_x
            y = target_y
            # delete all paint and click
            self.init_point()
            self.parent.repaint() 
            click(x, y)
            

            key_state = False
            # program_to_front()
            self.current_state = 0 # successful execution
            self.parent.condition = 0
        

listener = key_listener()
listener.daemon = True
listener.start()

app = QApplication(sys.argv)
app.setApplicationDisplayName(app_name)
app.setWindowIcon(QIcon('icon/xy_scan.png'))
window = DisplayWindow()

window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
window.setAttribute(Qt.WA_NoSystemBackground, True)
window.setAttribute(Qt.WA_TranslucentBackground, True)

window.showFullScreen()



sys.exit(app.exec())