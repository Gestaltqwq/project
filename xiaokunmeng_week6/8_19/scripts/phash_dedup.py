# -*- coding: utf-8 -*-
"""pHash 感知哈希近似去重: 统计子集 571 张图的视觉重复度."""
import cv2
import numpy as np
from pathlib import Path

IMG = Path(r"C:\Users\LENOVO\Downloads\运营高速公路子集\images")

def imread_u(p):
    return cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)

def phash(img, size=16):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(g, (size, size), interpolation=cv2.INTER_AREA)
    mean = small.mean()
    return (small > mean).astype(np.uint8)

def hamming(a, b):
    return np.count_nonzero(a != b)

def main():
    files = sorted(IMG.iterdir())
    hashes = []
    for p in files:
        img = imread_u(p)
        if img is None:
            print("skip", p)
            continue
        hashes.append((p, phash(img)))
    print(f"hashed={len(hashes)}")
    # 两两比较 (571^2/2 ~ 163k 次, 快)
    groups = []  # 每组取第一张为代表
    dup_pairs = 0
    thresh = 8  # 256bit 中差异 <= 8 视为近似重复
    representatives = []
    for i, (p, h) in enumerate(hashes):
        if any(hamming(h, rh) <= thresh for _, rh in representatives):
            dup_pairs += 1
            continue
        representatives.append((p, h))
    print(f"近似重复(与已保留代表图 pHash 距离<=8): {dup_pairs} / {len(hashes)}")
    print(f"保留代表图: {len(representatives)}")

    # 更宽松阈值 16 看看
    reps16 = []
    d16 = 0
    for p, h in hashes:
        if any(hamming(h, rh) <= 16 for _, rh in reps16):
            d16 += 1
            continue
        reps16.append((p, h))
    print(f"阈值16: 重复 {d16}, 保留 {len(reps16)}")

if __name__ == "__main__":
    main()
