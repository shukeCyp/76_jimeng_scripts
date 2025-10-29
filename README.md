# WebView 应用框架

一个使用 Python + HTML/CSS/JavaScript 构建的跨平台 WebView 应用框架，可轻松打包为独立的 exe 文件。

## 📋 项目结构

```
.
├── app/
│   ├── main.py              # Python 主应用（WebView框架）
│   └── static/
│       ├── index.html       # 前端HTML界面
│       ├── styles.css       # 样式文件
│       └── script.js        # 前端脚本（与后端通信）
├── build_exe.py             # 打包脚本（生成exe）
├── build_exe.spec           # PyInstaller 配置文件
├── requirements.txt         # Python 依赖
└── README.md               # 本文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 开发运行

在开发阶段，直接运行 Python 脚本：

```bash
python app/main.py
```

应用会在新窗口中打开，显示 WebView 界面。

### 3. 打包为 exe（Windows）

#### 方法一：目录模式（推荐，更快）
```bash
python build_exe.py
```

输出文件位置：`dist/WebViewApp/WebViewApp.exe`

#### 方法二：单文件模式（文件较大但易于分发）
```bash
python build_exe.py --onefile
```

输出文件位置：`dist/WebViewApp.exe`

#### 方法三：调试模式（显示控制台）
```bash
python build_exe.py --console
```

## 🏗️ 项目组成

### Python 后端 (`app/main.py`)

提供了 `API` 类，包含可供前端调用的方法：

- `get_info()` - 获取应用信息
- `log_message(message)` - 记录消息
- `perform_calculation(a, b, operation)` - 执行计算

### 前端界面 (`app/static/`)

- **index.html** - 页面结构，包含三个功能面板
  - 应用信息显示
  - 计算器示例
  - 消息通信面板

- **styles.css** - 现代化的响应式样式
  - 支持暗色主题设计
  - 响应式布局
  - 平滑的过渡动画

- **script.js** - 前端交互逻辑
  - 与 Python 后端通信
  - 处理用户输入
  - 错误处理

## 🔄 前后端通信

### 从前端调用 Python 方法

```javascript
// 获取信息
window.pywebview.api.get_info().then(function(response) {
    console.log(response);
}).catch(function(error) {
    console.error(error);
});

// 发送消息
window.pywebview.api.log_message("Hello").then(function(response) {
    console.log(response);
});

// 执行计算
window.pywebview.api.perform_calculation(10, 5, 'add').then(function(response) {
    if (response.success) {
        console.log('结果:', response.result);
    }
});
```

### Python 调用 JavaScript

```python
# 在 API 类中获得 window 对象后，可以调用 JavaScript
api.window.evaluate_js('alert("Hello from Python")')
```

## 💡 常见操作

### 添加新的 Python API 方法

在 `app/main.py` 的 `API` 类中添加新方法：

```python
class API:
    def my_function(self, param1, param2):
        """你的函数说明"""
        result = param1 + param2
        return {'success': True, 'result': result}
```

然后在前端调用：
```javascript
window.pywebview.api.my_function(1, 2).then(response => {
    console.log(response);
});
```

### 修改窗口属性

在 `app/main.py` 的 `main()` 函数中修改：

```python
window = webview.create_window(
    title='你的应用名称',
    url=f'file://{html_file}',
    js_api=api,
    width=1200,      # 窗口宽度
    height=800,      # 窗口高度
    resizable=True,  # 是否可调整大小
    background_color='#ffffff'  # 背景颜色
)
```

### 修改前端界面

编辑 `app/static/index.html` 添加或修改 HTML 结构，编辑 `styles.css` 修改样式。

## 📦 打包注意事项

### 文件路径处理

`main.py` 中的 `get_static_path()` 函数自动处理开发和打包环境的文件路径：

```python
def get_static_path():
    # 如果是打包后的exe，使用sys._MEIPASS
    if getattr(sys, 'frozen', False):
        static_path = os.path.join(sys._MEIPASS, 'app', 'static')
    else:
        # 开发环境
        static_path = os.path.join(os.path.dirname(__file__), 'static')
    return static_path
```

### 自定义打包配置

编辑 `build_exe.spec` 文件可以自定义打包选项：

```python
# 修改应用名称
name='你的应用名',

# 改为 console=True 显示控制台窗口
console=False,

# 改为 onefile=True 生成单个 exe 文件
onefile=False,
```

## 🌐 跨平台支持

该框架支持 Windows、macOS 和 Linux：

- **Windows**: 使用 `build_exe.py` 生成 exe
- **macOS**: 可使用 PyInstaller 生成 app bundle
- **Linux**: 可使用 PyInstaller 生成可执行文件

## 🔧 故障排除

### 打包失败

1. 检查是否安装了所有依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 检查 Python 版本（推荐 3.8+）：
   ```bash
   python --version
   ```

3. 检查文件完整性：确保 `app/static/` 中的所有文件都存在

### 运行时错误

1. 开发阶段，运行 `python app/main.py` 查看错误日志
2. 打包时使用 `--console` 选项显示错误信息：
   ```bash
   python build_exe.py --console
   ```

### 文件访问错误

确保 HTML 文件路径正确。打包后的应用会在 `app/static/` 目录中查找文件。

## 📚 相关文档

- [pywebview 官方文档](https://pywebview.kivy.org/)
- [PyInstaller 官方文档](https://pyinstaller.org/)

## 📝 许可

该项目可自由使用和修改。

## 🎯 下一步

1. 根据需求修改前端界面（`app/static/`）
2. 在 `API` 类中添加你的业务逻辑
3. 使用 `build_exe.py` 打包应用
4. 将生成的 exe 文件分发给用户

祝你开发愉快！
