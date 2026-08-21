# -*- coding: utf-8 -*-
"""离线数据增强: 将训练集 42 张扩充到 126 张 (3x)。
增强方式: 水平翻转 / 旋转±10° / 缩放 0.8~1.2 / 亮度±20%。
标注框随之做对应几何变换, 越界部分裁剪, 面积过小或完全出界的框丢弃。
"""
import os
import random
import sys
import numpy as np
import cv2
from pathlib import Path

# 支持参数: python augment_dataset.py <src_data_dir> <dst_data_dir>
SRC_ARG = sys.argv[1] if len(sys.argv) > 1 else "yolo_dataset"
DST_ARG = sys.argv[2] if len(sys.argv) > 2 else "yolo_dataset_x3"

ROOT = Path(__file__).resolve().parents[1]
SRC_IMG = ROOT / SRC_ARG / "images" / "train"
SRC_LBL = ROOT / SRC_ARG / "labels" / "train"
DST_IMG = ROOT / DST_ARG / "images" / "train"
DST_LBL = ROOT / DST_ARG / "labels" / "train"

random.seed(2026)

def read_boxes(txt_path):
    boxes = []
    if txt_path.exists():
        for line in txt_path.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) >= 5:
                boxes.append((int(parts[0]), [float(v) for v in parts[1:5]]))
    return boxes

def write_boxes(txt_path, boxes):
    lines = [f"{c} {x:.6f} {y:.6f} {w:.6f} {h:.6f}" for c, (x, y, w, h) in boxes]
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def norm2abs(b, W, H):
    x, y, w, h = b
    return x * W, y * H, w * W, h * H

def abs2norm(b, W, H):
    x, y, w, h = b
    return x / W, y / H, w / W, h / H

def transform_boxes(boxes, M, W, H, min_area_ratio=0.002):
    """M: 2x3 变换矩阵; 输出与原图同坐标系的新框(裁剪后)."""
    out = []
    for c, b in boxes:
        x, y, w, h = norm2abs(b, W, H)
        cx, cy = x + w / 2, y + h / 2
        corners = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], dtype=np.float32)
        # 先平移使旋转绕图像中心
        t = np.array([[1, 0, W / 2 - cx], [0, 1, H / 2 - cy]], dtype=np.float32)
        inv = np.array([[1, 0, -(W / 2 - cx)], [0, 1, -(H / 2 - cy)]], dtype=np.float32)
        rot = np.array([[np.cos(0), -np.sin(0)], [np.sin(0), np.cos(0)]], dtype=np.float32)
        new_corners = corners @ rot.T + np.array([[cx, cy]])
        # 通用: 直接对每个角点应用 M (M 需为 3x3 或 2x3)
        pts = np.hstack([new_corners, np.ones((4, 1))])
        if M.shape == (2, 3):
            mapped = pts @ M.T
        else:
            mapped = pts @ M[:2].T
        xs, ys = mapped[:, 0], mapped[:, 1]
        nx, ny = xs.min(), ys.min()
        nw, nh = xs.max() - nx, ys.max() - ny
        # 裁剪到图像内
        nx = np.clip(nx, 0, W - 1)
        ny = np.clip(ny, 0, H - 1)
        nw = np.clip(nw, 0, W - nx)
        nh = np.clip(nh, 0, H - ny)
        if nw < 4 or nh < 4:
            continue
        if (nw * nh) / (W * H) < min_area_ratio:
            continue
        out.append((c, abs2norm((nx, ny, nw, nh), W, H)))
    return out

def aug_hflip(img, boxes):
    W, H = img.shape[1], img.shape[0]
    img2 = cv2.flip(img, 1)
    nb = [(c, (1 - x - w, y, w, h)) for c, (x, y, w, h) in boxes]
    return img2, nb

def aug_rotate(img, boxes, deg):
    W, H = img.shape[1], img.shape[0]
    M = cv2.getRotationMatrix2D((W / 2, H / 2), deg, 1.0)
    img2 = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    nb = transform_boxes(boxes, M, W, H)
    return img2, nb

def aug_scale(img, boxes, s):
    W, H = img.shape[1], img.shape[0]
    nW, nH = int(W * s), int(H * s)
    img2 = cv2.resize(img, (nW, nH), interpolation=cv2.INTER_LINEAR)
    nb = [(c, (x, y, w, h)) for c, (x, y, w, h) in boxes]  # 归一化坐标不变
    return img2, nb

def aug_brightness(img, boxes, delta):
    img2 = cv2.convertScaleAbs(img, alpha=1.0, beta=delta)
    return img2, boxes

def imread_unicode(p):
    return cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)

def imwrite_unicode(p, img):
    ext = "." + str(p).rsplit(".", 1)[-1]
    ok, buf = cv2.imencode(ext, img)
    if ok:
        buf.tofile(str(p))
    return ok

def main():
    if DST_IMG.exists():
        import shutil
        shutil.rmtree(DST_IMG.parent)
    DST_IMG.mkdir(parents=True, exist_ok=True)
    DST_LBL.mkdir(parents=True, exist_ok=True)

    # 复制原始训练集
    for f in sorted(SRC_IMG.iterdir()):
        img = imread_unicode(f)
        boxes = read_boxes(SRC_LBL / (f.stem + ".txt"))
        imwrite_unicode(DST_IMG / f.name, img)
        write_boxes(DST_LBL / (f.stem + ".txt"), boxes)

    n_orig, n_aug = 0, 0
    for f in sorted(SRC_IMG.iterdir()):
        img = imread_unicode(f)
        boxes = read_boxes(SRC_LBL / (f.stem + ".txt"))
        H, W = img.shape[:2]
        n_orig += 1
        variants = [
            ("hflip", aug_hflip(img, boxes)),
            ("rot_p10", aug_rotate(img, boxes, 10.0)),
            ("rot_n10", aug_rotate(img, boxes, -10.0)),
            ("scale08", aug_scale(img, boxes, 0.8)),
            ("scale12", aug_scale(img, boxes, 1.2)),
            ("bright_p", aug_brightness(img, boxes, 35)),
            ("bright_n", aug_brightness(img, boxes, -35)),
        ]
        for tag, (img2, nb) in variants:
            if not nb:
                continue
            name = f"{f.stem}_{tag}"
            imwrite_unicode(DST_IMG / (name + ".png"), img2)
            write_boxes(DST_LBL / (name + ".txt"), nb)
            n_aug += 1
    print(f"orig={n_orig} augmented={n_aug} total_train={n_orig + n_aug}")

    # 复制 val 集(增强只作用于训练集)
    import shutil
    vd = ROOT / DST_ARG
    shutil.copytree(ROOT / SRC_ARG / "images" / "val", vd / "images" / "val")
    shutil.copytree(ROOT / SRC_ARG / "labels" / "val", vd / "labels" / "val")
    # data yaml
    names = [l.strip() for l in (ROOT / "classes.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    yaml = (f"path: {str(vd).replace(os.sep, '/')}\n"
            f"train: images/train\nval: images/val\n"
            f"nc: {len(names)}\n"
            f"names:\n" + "".join(f"  {i}: {n}\n" for i, n in enumerate(names)))
    (ROOT / f"{DST_ARG}.yaml").write_text(yaml, encoding="utf-8")
    print(f"{DST_ARG}.yaml written")

if __name__ == "__main__":
    main()
