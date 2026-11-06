#!/usr/bin/env python3
"""图片信息处理工具（命令行版）。

使用 OpenCV 完成两项工作：
  1. 读取图片基础信息（文件名、格式、宽高、颜色模式、文件大小）。
  2. 进行简单的图片编辑（缩放、裁剪、旋转、翻转、灰度化、格式转换）。

设计约定：
  - 所有编辑结果都保存为“新文件”，绝不会覆盖原图，并在终端提示保存位置。
  - 文件不存在 / 不是有效图片 / 参数非法时，给出明确提示后退出，不直接崩溃。
  - 带透明通道（RGBA）的 PNG 在保存为 JPG 前，先转成 RGB。
"""
import argparse
import os
import sys

import cv2


# --------------------------------------------------------------------------
# 基础工具函数
# --------------------------------------------------------------------------
def load_image(path):
    """读取图片，返回 (图像数组, 颜色模式字符串)。

    文件不存在或无法解码为有效图片时，抛出清晰的异常。
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"文件不存在: {path}")
    # IMREAD_UNCHANGED 保留透明通道，便于判断 RGBA
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"无法读取图片，可能不是有效的图片文件: {path}")
    return img, detect_color_mode(img)


def detect_color_mode(img):
    """根据数组维度判断颜色模式。"""
    if img.ndim == 2:
        return "灰度 (Grayscale)"
    if img.ndim == 3:
        channels = img.shape[2]
        if channels == 4:
            return "RGBA (带透明通道)"
        if channels == 3:
            return "RGB"
    return "未知"


def format_size(byte_count):
    """把字节数格式化为 KB 或 MB，保留两位小数。"""
    if byte_count < 1024 * 1024:
        return f"{byte_count / 1024:.2f} KB"
    return f"{byte_count / (1024 * 1024):.2f} MB"


def make_output_path(input_path, suffix, ext=None):
    """在文件名后追加后缀生成输出路径，避免覆盖原图。"""
    base, old_ext = os.path.splitext(input_path)
    target_ext = old_ext if ext is None else ext
    return f"{base}_{suffix}{target_ext}"


def save_image(path, img):
    """保存图片，失败时给出明确提示。"""
    ok = cv2.imwrite(path, img)
    if not ok:
        raise ValueError(f"保存失败，可能是格式不支持或路径无效: {path}")
    print(f"已保存到: {os.path.abspath(path)}")


# --------------------------------------------------------------------------
# 功能 1：读取图片信息
# --------------------------------------------------------------------------
def show_info(path):
    """读取并展示图片基础信息。"""
    img, mode = load_image(path)
    height, width = img.shape[:2]
    ext = os.path.splitext(path)[1].lstrip(".").upper() or "未知"
    size = os.path.getsize(path)

    print("====== 图片信息 ======")
    print(f"文件名:       {os.path.basename(path)}")
    print(f"图片格式:     {ext}")
    print(f"宽度 x 高度:  {width} x {height} 像素")
    print(f"颜色模式:     {mode}")
    print(f"文件大小:     {format_size(size)}")


# --------------------------------------------------------------------------
# 功能 2：简单编辑
# --------------------------------------------------------------------------
def resize_image(path, width=None, height=None):
    """缩放图片。只给宽或高时，按原图比例自动计算另一项。"""
    img, _ = load_image(path)
    h, w = img.shape[:2]

    if width is not None and width <= 0:
        raise ValueError("宽度必须大于 0")
    if height is not None and height <= 0:
        raise ValueError("高度必须大于 0")
    if width is None and height is None:
        raise ValueError("至少需要指定 --width 或 --height 之一")

    if width is None:
        ratio = height / h
        width = int(w * ratio)
    elif height is None:
        ratio = width / w
        height = int(h * ratio)

    width, height = int(width), int(height)
    result = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
    out = make_output_path(path, f"resized_{width}x{height}")
    save_image(out, result)
    return out


def crop_image(path, left, top, right, bottom):
    """裁剪图片，坐标顺序为 (左, 上, 右, 下)，单位像素。"""
    img, _ = load_image(path)
    h, w = img.shape[:2]

    for name, val in [("左", left), ("上", top), ("右", right), ("下", bottom)]:
        if val < 0:
            raise ValueError(f"{name}坐标不能为负数")

    if right <= left or bottom <= top:
        raise ValueError("裁剪区域不合法：右必须大于左，下必须大于上")

    if left >= w or top >= h or right > w or bottom > h:
        raise ValueError(
            f"裁剪区域越界：图片尺寸为 {w}x{h}，"
            f"请保证 0 <= 左 < 右 <= {w} 且 0 <= 上 < 下 <= {h}"
        )

    result = img[top:bottom, left:right]
    out = make_output_path(path, f"crop_{left}_{top}_{right}_{bottom}")
    save_image(out, result)
    return out


def rotate_image(path, angle):
    """旋转图片，支持 90 / 180 / 270 度。"""
    if angle not in (90, 180, 270):
        raise ValueError("仅支持 90、180、270 度旋转")

    img, _ = load_image(path)
    if angle == 90:
        result = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif angle == 180:
        result = cv2.rotate(img, cv2.ROTATE_180)
    else:
        result = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    out = make_output_path(path, f"rotate_{angle}")
    save_image(out, result)
    return out


def flip_image(path, direction):
    """翻转图片：水平 (horizontal) 或垂直 (vertical)。"""
    img, _ = load_image(path)
    if direction == "horizontal":
        result = cv2.flip(img, 1)
    elif direction == "vertical":
        result = cv2.flip(img, 0)
    else:
        raise ValueError("翻转方向仅支持 horizontal 或 vertical")

    out = make_output_path(path, f"flip_{direction}")
    save_image(out, result)
    return out


def grayscale_image(path):
    """彩色图（含 RGBA）转灰度图。"""
    img, _ = load_image(path)
    if img.ndim == 2:
        result = img  # 本来就是灰度图
    elif img.shape[2] == 4:
        result = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    else:
        result = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    out = make_output_path(path, "gray")
    save_image(out, result)
    return out


def brightness_image(path, value):
    """调整亮度：value 为增量（正数变亮，负数变暗）。"""
    img, _ = load_image(path)
    if img.ndim == 3 and img.shape[2] == 4:
        # 带透明通道时只调 RGB，避免改动 alpha
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
        bgr = cv2.convertScaleAbs(bgr, alpha=1.0, beta=value)
        result = cv2.merge([bgr, alpha])
    else:
        result = cv2.convertScaleAbs(img, alpha=1.0, beta=value)
    out = make_output_path(path, f"bright_{value}")
    save_image(out, result)
    return out


def convert_format(path, target_ext):
    """转换图片格式，例如 PNG 与 JPG 互转。"""
    target_ext = target_ext.lower().lstrip(".")
    img, _ = load_image(path)
    out = make_output_path(path, "converted", "." + target_ext)

    # 透明通道处理：保存为 JPG 前先转成 RGB，否则透明区域会变黑
    if target_ext in ("jpg", "jpeg") and img.ndim == 3 and img.shape[2] == 4:
        print("提示：原图带透明通道，已先转换为 RGB 再保存为 JPG。")
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    save_image(out, img)
    return out


# --------------------------------------------------------------------------
# 命令行入口
# --------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        description="图片信息处理工具：读取信息 + 简单编辑"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_info = sub.add_parser("info", help="读取图片基础信息")
    p_info.add_argument("image", help="图片路径")

    p_resize = sub.add_parser("resize", help="缩放图片")
    p_resize.add_argument("image")
    p_resize.add_argument("-W", "--width", type=int, default=None, help="目标宽度(像素)")
    p_resize.add_argument("-H", "--height", type=int, default=None, help="目标高度(像素)")

    p_crop = sub.add_parser("crop", help="裁剪图片")
    p_crop.add_argument("image")
    p_crop.add_argument("--left", type=int, required=True)
    p_crop.add_argument("--top", type=int, required=True)
    p_crop.add_argument("--right", type=int, required=True)
    p_crop.add_argument("--bottom", type=int, required=True)

    p_rotate = sub.add_parser("rotate", help="旋转图片")
    p_rotate.add_argument("image")
    p_rotate.add_argument("--angle", type=int, choices=[90, 180, 270], required=True)

    p_flip = sub.add_parser("flip", help="翻转图片")
    p_flip.add_argument("image")
    p_flip.add_argument("--direction", choices=["horizontal", "vertical"], required=True)

    p_gray = sub.add_parser("gray", help="灰度化")
    p_gray.add_argument("image")

    p_convert = sub.add_parser("convert", help="格式转换")
    p_convert.add_argument("image")
    p_convert.add_argument("--to", required=True, help="目标扩展名，如 jpg / png")

    p_bright = sub.add_parser("bright", help="调整亮度")
    p_bright.add_argument("image")
    p_bright.add_argument("--value", type=int, required=True,
                          help="亮度增量，正数变亮、负数变暗，例如 30 或 -30")

    return parser


def main():
    args = build_parser().parse_args()
    try:
        if args.command == "info":
            show_info(args.image)
        elif args.command == "resize":
            print("输出:", resize_image(args.image, args.width, args.height))
        elif args.command == "crop":
            print("输出:", crop_image(args.image, args.left, args.top, args.right, args.bottom))
        elif args.command == "rotate":
            print("输出:", rotate_image(args.image, args.angle))
        elif args.command == "flip":
            print("输出:", flip_image(args.image, args.direction))
        elif args.command == "gray":
            print("输出:", grayscale_image(args.image))
        elif args.command == "convert":
            print("输出:", convert_format(args.image, args.to))
        elif args.command == "bright":
            print("输出:", brightness_image(args.image, args.value))
    except (FileNotFoundError, ValueError) as e:
        # 统一在这里把错误以清晰方式输出，避免堆栈直接暴露给用户
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
