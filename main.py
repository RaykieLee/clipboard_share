import flet as ft
import pyperclip
import os
import time
import threading
from PIL import Image
import sys
import glob  # 添加用于文件匹配的模块
import winreg  # 添加注册表操作模块

class ClipboardMonitor:
    def __init__(self):
        self.previous_content = ""
        self.monitoring = False
        self.save_directory = self.load_directory_from_registry()  # 从注册表加载目录
        self.cleanup_thread = None
        self.my_saved_files = set()  # 记录由程序保存的文件
        
    def load_directory_from_registry(self):
        try:
            # 打开注册表键
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\ClipboardMonitor",
                0,
                winreg.KEY_READ
            )
            # 读取目录值
            directory, _ = winreg.QueryValueEx(key, "SaveDirectory")
            winreg.CloseKey(key)
            return directory
        except:
            return ""
            
    def save_directory_to_registry(self, directory):
        try:
            # 创建或打开注册表键
            key = winreg.CreateKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\ClipboardMonitor"
            )
            # 保存目录值
            winreg.SetValueEx(
                key,
                "SaveDirectory",
                0,
                winreg.REG_SZ,
                directory
            )
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"保存目录到注册表失败: {str(e)}")
            return False
        
    def start_monitoring(self):
        self.monitoring = True
        self.previous_content = pyperclip.paste()
        # 初始化已知文件列表
        if self.save_directory:
            pattern = os.path.join(self.save_directory, "*.txt")
            self.known_files = set(glob.glob(pattern))
        
        # 启动监控线程
        threading.Thread(target=self.monitor_clipboard, daemon=True).start()
        # 启动清理线程
        self.cleanup_thread = threading.Thread(target=self.cleanup_old_files, daemon=True)
        self.cleanup_thread.start()
        # 启动反向监控线程
        threading.Thread(target=self.monitor_directory, daemon=True).start()
        
    def stop_monitoring(self):
        self.monitoring = False
        
    def monitor_directory(self):
        while self.monitoring:
            try:
                if self.save_directory:
                    # 获取所有 clipboard_ 开头的txt文件
                    files = glob.glob(os.path.join(self.save_directory, "clipboard_*.txt"))
                    
                    if not files:
                        time.sleep(0.5)
                        continue
                    
                    current_time = time.time()
                    
                    # 检查每个文件
                    for file_path in files:
                        # 跳过由程序自己创建的文件
                        if file_path in self.my_saved_files:
                            continue
                            
                        try:
                            # 检查文件创建时间
                            file_creation_time = os.path.getctime(file_path)
                            # 只处理3分钟内创建的文件
                            if current_time - file_creation_time > 180:  # 180秒 = 3分钟
                                continue
                                
                            # 读取文件内容
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()
                            
                            # 如果内容与当前剪切板不同，则更新剪切板
                            current_clipboard = pyperclip.paste()
                            if file_content and file_content != current_clipboard:
                                pyperclip.copy(file_content)
                                print(f"从新文件更新剪切板: {os.path.basename(file_path)}")
                            
                            # 将文件添加到已处理列表
                            self.my_saved_files.add(file_path)
                            
                        except Exception as e:
                            print(f"处理文件时出错: {str(e)}")
                    
            except Exception as e:
                print(f"监控目录时出错: {str(e)}")
            
            time.sleep(0.5)
    
    def save_content(self, content):
        if not content.strip():
            return
            
        filename = os.path.join(self.save_directory, f"clipboard_{int(time.time())}.txt")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已保存到: {filename}")
            # 记录这是程序创建的文件
            self.my_saved_files.add(filename)
        except Exception as e:
            print(f"保存失败: {str(e)}")
    
    def cleanup_old_files(self):
        while self.monitoring:
            try:
                if self.save_directory:
                    # 获取当前时间戳
                    current_time = time.time()
                    # 获取所有clipboard开头的txt文件
                    pattern = os.path.join(self.save_directory, "clipboard_*.txt")
                    files = glob.glob(pattern)
                    
                    for file in files:
                        try:
                            # 从文件名中提取时间戳
                            filename = os.path.basename(file)
                            timestamp = int(filename.replace("clipboard_", "").replace(".txt", ""))
                            
                            # 如果文件超过10分钟，则删除
                            if current_time - timestamp > 600:  # 600秒 = 10分钟
                                os.remove(file)
                                print(f"已清理旧文件: {filename}")
                        except Exception as e:
                            print(f"清理文件时出错: {str(e)}")
                            
            except Exception as e:
                print(f"清理过程出错: {str(e)}")
            
            # 每10分钟检查一次
            time.sleep(600)  # 修改为600秒（10分钟）
    
    def monitor_clipboard(self):
        while self.monitoring:
            try:
                current_content = pyperclip.paste()
                if current_content and current_content != self.previous_content:
                    self.save_content(current_content)
                    self.previous_content = current_content
            except Exception as e:
                print(f"监控剪切板时出错: {str(e)}")
            time.sleep(0.5)

class ClipboardApp:
    def __init__(self):
        self.monitor = ClipboardMonitor()
        self.page = None
        self.file_picker = None
        
    def main(self, page: ft.Page):
        self.page = page
        self.page.title = "剪切板监控工具"
        
        # 更新窗口属性，设置更小的尺寸
        self.page.window.width = 370
        self.page.window.height = 90
        self.page.window.resizable = False
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 0
        
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
        self.select_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.FOLDER_OPEN),
                    # 如果有保存的目录，显示目录名，否则显示"选择目录"
                    ft.Text(os.path.basename(self.monitor.save_directory) if self.monitor.save_directory else "选择目录")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.BLUE_400,
            ),
            on_click=self.select_directory,
        )
        
        self.monitor_button = ft.ElevatedButton(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.icons.PLAY_CIRCLE),
                    ft.Text("开始监控")
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                # 如果有保存的目录，设置为绿色，否则设置为灰色
                bgcolor=ft.colors.GREEN_400 if self.monitor.save_directory else ft.colors.GREY_400,
            ),
            on_click=self.toggle_monitoring,
            # 如果有保存的目录，启用按钮，否则禁用
            disabled=not bool(self.monitor.save_directory)
        )
        
        # 简化布局，减少内边距
        content = ft.Row(
            controls=[
                self.select_button,
                ft.Container(width=10),  # 减小按钮间距
                self.monitor_button,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0,
        )
        
        # 添加一个最小的容器来包裹按钮行
        container = ft.Container(
            content=content,
            padding=5,  # 减小内边距
        )
        
        self.page.add(container)
        
        # 更新窗口事件处理方式
        def handle_window_event(e):
            if e.data == "close":
                self.monitor.stop_monitoring()  # 停止所有监控
                self.page.window.destroy()  # 关闭窗口
                sys.exit(0)  # 退出程序
        
        self.page.window.on_event = handle_window_event
        
        # 如果有保存的目录，自动开始监控
        if self.monitor.save_directory:
            self.monitor.start_monitoring()
            self.monitor_button.content.controls[0].name = ft.icons.STOP_CIRCLE
            self.monitor_button.content.controls[1].value = "停止监控"
            self.monitor_button.style.bgcolor = ft.colors.RED_400
            self.page.update()
    
    def on_directory_selected(self, e: ft.FilePickerResultEvent):
        if e.path:
            path_display = os.path.basename(e.path)
            # 更新选择按钮的文本和图标
            self.select_button.content.controls[1].value = path_display
            # 设置保存目录并保存到注册表
            self.monitor.save_directory = e.path
            self.monitor.save_directory_to_registry(e.path)
            # 启用监控按钮并设置为绿色
            self.monitor_button.disabled = False
            self.monitor_button.style.bgcolor = ft.colors.GREEN_400
            self.page.update()
    
    async def select_directory(self, e):
        self.file_picker.get_directory_path()
        self.page.update()
    
    async def toggle_monitoring(self, e):
        if self.monitor.monitoring:
            self.monitor.stop_monitoring()
            self.monitor_button.content.controls[0].name = ft.icons.PLAY_CIRCLE
            self.monitor_button.content.controls[1].value = "开始监控"
            self.monitor_button.style.bgcolor = ft.colors.GREEN_400
        else:
            if not self.monitor.save_directory:  # 添加目录检查
                print("未设置保存目录")
                return
            self.monitor.start_monitoring()
            self.monitor_button.content.controls[0].name = ft.icons.STOP_CIRCLE
            self.monitor_button.content.controls[1].value = "停止监控"
            self.monitor_button.style.bgcolor = ft.colors.RED_400
        self.page.update()

def main():
    app = ClipboardApp()
    ft.app(target=app.main, assets_dir="assets")

if __name__ == "__main__":
    main()