# -*- coding: utf-8 -*-
import pandas as pd
for e in ['e1_base','e2_lr_low','e3_lr_high','e4_box_low','e5_box_high','e6_data_x3']:
    d = pd.read_csv(f'8_19/runs/{e}/results.csv')
    first = d.iloc[0]
    best = d.loc[d['metrics/mAP50-95(B)'].idxmax()]
    last = d.iloc[-1]
    print(f"{e:12s} epochs={len(d):3d}  ep1: box={first['train/box_loss']:.3f} cls={first['train/cls_loss']:.3f} "
          f"| best_ep={int(best['epoch'])} mAP50-95={best['metrics/mAP50-95(B)']:.4f} "
          f"| last: box={last['train/box_loss']:.3f} cls={last['train/cls_loss']:.3f} "
          f"valbox={last['val/box_loss']:.3f} valcls={last['val/cls_loss']:.3f}")
