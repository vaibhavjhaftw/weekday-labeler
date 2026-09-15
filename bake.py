#!/usr/bin/env python3
"""Bake a Fort capture package into flat files a static page can read.

The local tool answers /api/window out of the parquet on every scroll. A page
on GitHub Pages has no server to ask, so the same signal ships as one Int16
blob the browser slices in memory: 50 Hz is four times the ~14 Hz the detail
pane actually draws at its default span, and a quarter the bytes of float32.
"""
import json, math, sys
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq

PKG   = Path("/Users/weekday/Downloads/fort_sessions/guru_20260831/sessions/guru_20260831_1552")
OUT   = Path("/Users/weekday/Downloads/fort-labeler-web/data")
BASE  = 1000.0          # LSL synthetic base written by fort_capture_package.py
RATE  = 50.0
A_FS, G_FS = 40.0, 20.0                    # full scale, m/s^2 and rad/s
CH    = ["accel_x_mps2","accel_y_mps2","accel_z_mps2",
         "gyro_x_rad_s","gyro_y_rad_s","gyro_z_rad_s"]

OUT.mkdir(parents=True, exist_ok=True)
tbl = pq.ParquetFile(PKG / "capture/ml/samples.parquet").read(
    columns=["source","stream","corrected_timestamp_s", *CH])
df = tbl.to_pandas()
df = df[df["stream"] == "imu"]

span = float(df["corrected_timestamp_s"].max() - BASE)
n    = int(math.floor(span * RATE)) + 1
grid = np.arange(n) / RATE
print(f"span {span:.3f}s  ->  {n} samples/wrist at {RATE:g} Hz")

blob, wrists = [], {}
for src, name in (("fort_left","left"), ("fort_right","right")):
    w = df[df["source"] == src].sort_values("corrected_timestamp_s")
    t = w["corrected_timestamp_s"].to_numpy() - BASE
    chans = []
    for c in CH:
        v  = np.nan_to_num(w[c].to_numpy(dtype=np.float64))
        # Linear interpolation onto the uniform grid. np.interp holds the end
        # values outside [t0,t1], which is what we want at the two edges where
        # one wrist starts a beat before the other.
        g  = np.interp(grid, t, v)
        fs = A_FS if "accel" in c else G_FS
        chans.append(np.clip(np.round(g / fs * 32767.0), -32767, 32767).astype("<i2"))
    blob.append(np.stack(chans).ravel())
    wrists[name] = {"source": src, "samples": int(len(w))}
    print(f"  {name}: {len(w):,} rows  {t[0]:.3f}..{t[-1]:.3f}s")

raw = np.concatenate(blob).tobytes()
(OUT / "imu.bin").write_bytes(raw)
print(f"imu.bin {len(raw)/1e6:.2f} MB")

(OUT / "imu.json").write_text(json.dumps({
    "rate_hz": RATE, "samples": n, "span_s": span,
    "order": ["left","right"], "channels": CH,
    "scales": [A_FS/32767.0]*3 + [G_FS/32767.0]*3,
    "dtype": "int16le", "layout": "wrist-major, then channel-major, then time",
    "wrists": wrists}, indent=2))

# ---- overview: min/max envelope of |accel| per wrist, the shape drawOv() draws
BUCKETS = 3000
ov = {}
for name in ("left","right"):
    i = ["left","right"].index(name)
    arr = np.frombuffer(blob[i].tobytes(), dtype="<i2").reshape(6, n).astype(np.float32)
    mag = np.sqrt((arr[0]*A_FS/32767)**2 + (arr[1]*A_FS/32767)**2 + (arr[2]*A_FS/32767)**2)
    edges = np.linspace(0, n, BUCKETS + 1).astype(int)
    lo = [float(mag[a:b].min()) if b > a else 0.0 for a, b in zip(edges[:-1], edges[1:])]
    hi = [float(mag[a:b].max()) if b > a else 0.0 for a, b in zip(edges[:-1], edges[1:])]
    ov[name] = {"lo": [round(v,2) for v in lo], "hi": [round(v,2) for v in hi]}
(OUT / "overview.json").write_text(json.dumps({"buckets": BUCKETS, "span_s": span, "wrists": ov}))
print("overview.json", (OUT/"overview.json").stat().st_size/1e3, "kB")
