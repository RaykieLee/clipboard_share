![](https://cdn.jsdelivr.net/gh/GayHub1/images@master/img/20241122171201.png)
# 剪切板监控工具

一个简单的剪切板监控工具，可以自动保存剪切板内容到指定目录。
日常中可以将指定目录设为多台电脑的共享目录，这样就可以在多台电脑之间共享剪切板内容。

## 功能特点

- 监控剪切板变化并自动保存
- 支持系统托盘运行
- 可选择保存目录
- 支持手动保存当前剪切板内容

## 安装依赖

```
pip install -r requirements.txt
```

## 运行

```
python main.py
```
## 打包

```
flet pack main.py
```

## 使用

- 运行打包后的exe文件，选择保存目录
- 点击开始按钮，即可开始监控剪切板
- 监控到的内容会保存到指定目录，并根据文件名中的时间戳来区分内容
- 如果内容超过10分钟没有被访问，则会被自动清理
- 点击退出按钮，程序退出
