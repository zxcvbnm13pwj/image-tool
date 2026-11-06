# 图片信息处理工具（Image Tool）

## 1. 项目介绍

这是一个用 Python + OpenCV 编写的**命令行**图片处理小工具，面向“没参与过开发的人也能照着跑起来”的目标而设计。

它能做两件事：

1. **读取图片信息**：文件名、图片格式、宽高（像素）、颜色模式、文件大小。
2. **简单编辑**：缩放、裁剪、旋转（90°/180°/270°）、翻转（水平/垂直）、灰度化、格式转换（PNG ⇄ JPG）。

程序形式：**命令行（CLI）**。所有编辑都生成新文件，绝不覆盖原图，并在终端告知保存位置。

---

## 2. 环境配置

### 2.1 Python 版本
- 需要 **Python 3.9 及以上**。

在 Ubuntu 上查看 / 安装 Python：
```bash
python3 --version          # 查看版本
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 2.2 依赖安装
本项目只有一个第三方依赖：`opencv-python-headless`（无 GUI 依赖，适合命令行与服务器环境）。

我们**推荐使用 `uv` 管理环境与依赖**（更快、可复现）：

```bash
# 安装 uv（如已安装可跳过）
curl -LsSf https://astral.sh/uv/install.sh | sh
# 重新加载 shell 后，uv 即可用

# 创建虚拟环境并安装依赖（依据 pyproject.toml）
uv venv
uv pip install -e .         # 或 uv sync

# 生成 / 更新锁文件（提交到仓库）
uv lock
```

如果你暂时不想用 uv，也可以用 pip + 虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install opencv-python-headless
```

> 提示：激活环境后，终端提示符前会出现 `(.venv)`。之后运行程序都要先激活环境。

---

## 3. 运行方式

先进入项目目录并激活虚拟环境（见上方 2.2）。

### 3.1 读取图片信息
```bash
python main.py info demo.jpg
```
预期输出示例：
```
====== 图片信息 ======
文件名:       demo.jpg
图片格式:     JPG
宽度 x 高度:  1920 x 1080 像素
颜色模式:     RGB
文件大小:     345.67 KB
```

### 3.2 缩放
```bash
# 同时指定宽高
python main.py resize demo.jpg -W 800 -H 600

# 只给宽度，高度按比例自动计算
python main.py resize demo.jpg -W 800

# 只给高度，宽度按比例自动计算
python main.py resize demo.jpg -H 600
```
输出文件：`demo_resized_800x600.jpg`

### 3.3 裁剪
坐标为像素，顺序为 **左、上、右、下**（左上角原点，向右为 x、向下为 y）。
```bash
python main.py crop demo.jpg --left 100 --top 50 --right 500 --bottom 400
```
输出文件：`demo_crop_100_50_500_400.jpg`
> 若区域越界或坐标非法，会提示：`错误: 裁剪区域越界：图片尺寸为 ...`

### 3.4 旋转
```bash
python main.py rotate demo.jpg --angle 90     # 支持 90 / 180 / 270
```
输出文件：`demo_rotate_90.jpg`

### 3.5 翻转
```bash
python main.py flip demo.jpg --direction horizontal   # 或 vertical
```
输出文件：`demo_flip_horizontal.jpg`

### 3.6 灰度化
```bash
python main.py gray demo.jpg
```
输出文件：`demo_gray.jpg`

### 3.7 格式转换
```bash
python main.py convert demo.png --to jpg    # PNG 转 JPG
python main.py convert demo.jpg --to png    # JPG 转 PNG
```
输出文件：`demo_converted.jpg` 或 `demo_converted.png`
> 带透明通道的 PNG 转 JPG 时，会自动先转成 RGB（透明区域变为白色），并给出提示。

### 3.8 亮度调节
```bash
python main.py bright demo.jpg --value 30     # 变亮
python main.py bright demo.jpg --value -30    # 变暗
```
输出文件：`demo_bright_30.jpg`（或 `demo_bright_-30.jpg`）

---

## 4. 常见问题

- **提示 “文件不存在”**：检查路径是否正确，相对路径是相对“当前终端所在目录”。
- **提示 “无法读取图片”**：文件可能不是图片，或扩展名与实际格式不符。
- **依赖装不上 / 运行时报缺少 cv2**：确认已激活虚拟环境，且 `opencv-python-headless` 已安装。

---

## 5. 项目结构

```
image-tool/
├── main.py          # 程序主文件（全部功能与命令行入口）
├── pyproject.toml   # 项目元数据与依赖声明
├── .gitignore       # 忽略虚拟环境、缓存、过大的图片
└── README.md        # 本说明文件
```

---

## 6. 快速开始（一行命令）

激活环境后，用一张真实图片（如 `demo.jpg`）即可体验全部功能：

```bash
python main.py info demo.jpg && \
python main.py resize demo.jpg -W 800 && \
python main.py bright demo.jpg --value 30
```

