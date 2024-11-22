import flet as ft
import pyperclip
import os
import time
import threading
from PIL import Image
import sys

class ClipboardMonitor:
    def __init__(self):
        self.previous_content = pyperclip.paste()
        self.monitoring = False
        self.save_directory = ""
        
    def start_monitoring(self):
        self.monitoring = True
        threading.Thread(target=self.monitor_clipboard, daemon=True).start()
        
    def stop_monitoring(self):
        self.monitoring = False
        
    def monitor_clipboard(self):
        while self.monitoring:
            current_content = pyperclip.paste()
            if current_content != self.previous_content and self.save_directory:
                self.save_content(current_content)
                self.previous_content = current_content
            time.sleep(0.5)

    def save_content(self, content):
        filename = os.path.join(self.save_directory, f"clipboard_{int(time.time())}.txt")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"保存失败: {str(e)}")

class ClipboardApp:
    def __init__(self):
        self.monitor = ClipboardMonitor()
        self.page = None
        self.file_picker = None
        
    def main(self, page: ft.Page):
        self.page = page
        self.page.title = "剪切板监控工具"
        
        # 更新窗口属性的设置方式
        self.page.window.width = 600
        self.page.window.height = 200
        self.page.window.resizable = False
        self.page.theme_mode = ft.ThemeMode.LIGHT
        
        # 设置图标
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.page.window.icon = icon_path
            
        # 初始化 FilePicker
        self.file_picker = ft.FilePicker(
            on_result=self.on_directory_selected
        )
        self.page.overlay.append(self.file_picker)
        
        # 创建界面元素
        self.path_text = ft.TextField(
            label="保存目录",
            read_only=True,
            width=400,
            border_color=ft.colors.BLUE_400,
        )
        
        self.status_text = ft.Text(
            "状态: 已停止",
            color=ft.colors.GREY_700,
            size=14
        )
        
        select_button = ft.ElevatedButton(
            "选择目录",
            icon=ft.icons.FOLDER_OPEN,
            on_click=self.select_directory,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.BLUE_400,
            )
        )
        
        self.monitor_button = ft.ElevatedButton(
            "开始监控",
            icon=ft.icons.PLAY_CIRCLE,
            on_click=self.toggle_monitoring,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.GREEN_400,
            )
        )
        
        save_button = ft.ElevatedButton(
            "保存当前",
            icon=ft.icons.SAVE,
            on_click=self.save_clipboard,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.BLUE_400,
            )
        )
        
        # 布局
        content = ft.Column(
            controls=[
                ft.Container(
                    content=ft.Row(
                        controls=[
                            self.path_text,
                            select_button,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=10
                ),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            save_button,
                            self.monitor_button,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    padding=10
                ),
                ft.Container(
                    content=self.status_text,
                    alignment=ft.alignment.center,
                    padding=10
                ),
            ],
            spacing=0,
        )
        
        self.page.add(content)
        
        # 更新窗口事件处理方式
        self.page.window.prevent_close = True
        
        def handle_window_event(e):
            if e.data == "close":
                self.page.window.visible = False
                e.prevent_default()
        
        self.page.window.on_event = handle_window_event
    
    def on_directory_selected(self, e: ft.FilePickerResultEvent):
        if e.path:
            self.path_text.value = e.path
            self.monitor.save_directory = e.path
            self.page.update()
    
    async def select_directory(self, e):
        self.file_picker.get_directory_path()
        self.page.update()
    
    async def toggle_monitoring(self, e):
        if self.monitor.monitoring:
            self.monitor.stop_monitoring()
            self.monitor_button.text = "开始监控"
            self.monitor_button.icon = ft.icons.PLAY_CIRCLE
            self.monitor_button.style.bgcolor = ft.colors.GREEN_400
            self.status_text.value = "状态: 已停止"
            self.status_text.color = ft.colors.GREY_700
        else:
            if not self.path_text.value:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("请先选择保存目录"))
                )
                return
            self.monitor.save_directory = self.path_text.value
            self.monitor.start_monitoring()
            self.monitor_button.text = "停止监控"
            self.monitor_button.icon = ft.icons.STOP_CIRCLE
            self.monitor_button.style.bgcolor = ft.colors.RED_400
            self.status_text.value = "状态: 监控中"
            self.status_text.color = ft.colors.GREEN_600
        self.page.update()
    
    async def save_clipboard(self, e):
        if not self.path_text.value:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("请先选择保存目录"))
            )
            return
            
        clipboard_content = pyperclip.paste()
        filename = os.path.join(self.path_text.value, f"clipboard_{int(time.time())}.txt")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(clipboard_content)
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"已保存到: {filename}"),
                    bgcolor=ft.colors.GREEN_400
                )
            )
        except Exception as e:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"保存失败: {str(e)}"),
                    bgcolor=ft.colors.RED_400
                )
            )

def main():
    app = ClipboardApp()
    ft.app(target=app.main, assets_dir="assets")

if __name__ == "__main__":
    main()