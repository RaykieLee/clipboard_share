import tkinter as tk
from tkinter import messagebox, filedialog
import pyperclip
import os
import time
import threading
import pystray
from PIL import Image
import sys
import os.path

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

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("剪切板内容保存工具")
        self.monitor = ClipboardMonitor()
        
        # 设置程序图标
        self.icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(self.icon_path):
            self.icon_image = Image.open(self.icon_path)
            # 为 tkinter 窗口设置图标
            icon_photo = tk.PhotoImage(file=self.icon_path)
            self.root.iconphoto(True, icon_photo)
        else:
            self.icon_image = Image.new('RGB', (64, 64), 'black')  # 默认图标
            
        self.setup_gui()
        self.setup_tray()
        
    def setup_gui(self):
        self.root.geometry("600x80")
        self.root.protocol('WM_DELETE_WINDOW', self.hide_window)
        
        frame = tk.Frame(self.root)
        frame.pack(padx=5, pady=5)
        
        self.path_entry = tk.Entry(frame, width=50)
        self.path_entry.pack(side=tk.LEFT, padx=5)
        
        select_button = tk.Button(frame, text="选择目录", command=self.select_directory)
        select_button.pack(side=tk.LEFT, padx=2)
        
        save_button = tk.Button(frame, text="保存", command=self.save_clipboard)
        save_button.pack(side=tk.LEFT, padx=2)
        
        self.monitor_button = tk.Button(frame, text="开始监控", command=self.toggle_monitoring)
        self.monitor_button.pack(side=tk.LEFT, padx=2)
        
        self.status_label = tk.Label(self.root, text="状态: 已停止")
        self.status_label.pack(pady=5)

    def setup_tray(self):
        menu = (
            pystray.MenuItem('显示', self.show_window),
            pystray.MenuItem('退出', self.quit_app)
        )
        
        # 使用自定义图标创建系统托盘图标
        self.icon = pystray.Icon(
            "clipboard_monitor",
            self.icon_image,  # 使用加载的图标
            "剪切板监控",
            menu
        )
        
    def run(self):
        # 启动托盘图标
        threading.Thread(target=self.icon.run, daemon=True).start()
        self.root.mainloop()

    def hide_window(self):
        self.root.withdraw()  # 隐藏窗口
        
    def show_window(self):
        self.root.deiconify()  # 显示窗口
        self.root.lift()  # 将窗口提到最前
        
    def quit_app(self):
        self.monitor.stop_monitoring()
        self.icon.stop()
        self.root.destroy()
        sys.exit()

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, directory)
            self.monitor.save_directory = directory

    def toggle_monitoring(self):
        if self.monitor.monitoring:
            self.monitor.stop_monitoring()
            self.monitor_button.config(text="开始监控")
            self.status_label.config(text="状态: 已停止")
        else:
            if not self.path_entry.get():
                messagebox.showerror("错误", "请先选择保存目录")
                return
            self.monitor.save_directory = self.path_entry.get()
            self.monitor.start_monitoring()
            self.monitor_button.config(text="停止监控")
            self.status_label.config(text="状态: 监控中")

    def save_clipboard(self):
        clipboard_content = pyperclip.paste()
        directory = self.path_entry.get()
        
        if not directory:
            messagebox.showerror("错误", "请先选择保存目录")
            return
        
        filename = os.path.join(directory, f"clipboard_{int(time.time())}.txt")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(clipboard_content)
            messagebox.showinfo("成功", f"内容已保存到: {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"保存文件失败: {str(e)}")

if __name__ == "__main__":
    app = App()
    app.run()