# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor

matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.unicode_minus'] = False

BASE = os.path.dirname(os.path.abspath(__file__))
CSV  = os.path.join(BASE, "rice_yield_dataset.csv")

# ── 1. Load & encode data ─────────────────────────────────
df = pd.read_csv(CSV)
cat_cols = ['irrigation_type', 'season', 'rice_variety', 'region']
for col in cat_cols:
    if col in df.columns:
        df[col] = LabelEncoder().fit_transform(df[col].astype(str))

TARGET   = 'yield_ton_per_ha'
FEATURES = [c for c in df.columns if c != TARGET]
X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

# ── 2. Define models ──────────────────────────────────────
models = {
    "SmartAI\n(Random Forest)": RandomForestRegressor(n_estimators=100, random_state=42, max_features='sqrt', n_jobs=-1),
    "Linear\nRegression":       LinearRegression(),
    "Ridge\nRegression":        Ridge(alpha=1.0),
    "Decision\nTree":           DecisionTreeRegressor(random_state=42, max_depth=6),
    "SVR":                      SVR(kernel='rbf', C=100, epsilon=0.1),
    "KNN\n(k=5)":               KNeighborsRegressor(n_neighbors=5),
}

# ── 3. Train, predict, collect metrics ───────────────────
results = {}
for name, mdl in models.items():
    print(f"Training {name.replace(chr(10), ' ')} ...")
    mdl.fit(X_train, y_train)
    preds = mdl.predict(X_test)
    results[name] = {
        "R2":   r2_score(y_test, preds),
        "RMSE": np.sqrt(mean_squared_error(y_test, preds)),
        "MAE":  mean_absolute_error(y_test, preds),
    }

names = list(results.keys())
r2s   = [results[n]["R2"]   for n in names]
rmses = [results[n]["RMSE"] for n in names]
maes  = [results[n]["MAE"]  for n in names]

# ── 4. Colour scheme  (SmartAI highlighted) ───────────────
colors = ["#4361ee" if "SmartAI" in n else "#b0bec5" for n in names]
edge_c = ["#1a1a6e" if "SmartAI" in n else "#78909c" for n in names]

x = np.arange(len(names))
bar_w = 0.62

# ── 5. Figure (3 sub-plots) ───────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 6), facecolor="#f8f9fc")
fig.subplots_adjust(wspace=0.38, left=0.06, right=0.97, top=0.84, bottom=0.14)

metrics = [
    ("R² Score",        r2s,   True,  "#4361ee", 0.0, 1.0),
    ("RMSE ↓ (lower better)", rmses, False, "#e63946", None, None),
    ("MAE ↓ (lower better)",  maes,  False, "#f8961e", None, None),
]

for ax, (title, vals, higher_better, accent, ymin, ymax) in zip(axes, metrics):
    bars = ax.bar(x, vals, width=bar_w,
                  color=["#4361ee" if "SmartAI" in n else "#cfd8dc" for n in names],
                  edgecolor=["#1a1a6e" if "SmartAI" in n else "#90a4ae" for n in names],
                  linewidth=1.2, zorder=3)

    # Value labels on bars
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + (max(vals) * 0.015),
                f"{val:.3f}",
                ha='center', va='bottom', fontsize=9,
                fontweight='bold', color='#1a1a2e')

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9, color='#333333')
    ax.set_title(title, fontsize=13, fontweight='bold', color='#1a1a2e', pad=10)
    ax.set_facecolor("#ffffff")
    ax.grid(axis='y', linestyle='--', alpha=0.5, color='#cdd3de', zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis='y', labelsize=9, colors='#444444')
    for spine in ax.spines.values():
        spine.set_edgecolor('#cccccc')

    if ymin is not None and ymax is not None:
        ax.set_ylim(ymin, ymax)

    # Star-badge on best bar
    best_idx = int(np.argmax(vals)) if higher_better else int(np.argmin(vals))
    best_bar = bars[best_idx]
    ax.text(best_bar.get_x() + best_bar.get_width() / 2,
            best_bar.get_height() + max(vals) * 0.055,
            "★ Best", ha='center', va='bottom',
            fontsize=8.5, color='#f8961e', fontweight='bold')

# ── 6. Title & watermark ──────────────────────────────────
fig.text(0.515, 0.93,
         "Model Comparison: SmartAI (Random Forest) vs Baseline Models",
         ha='center', fontsize=15, fontweight='bold', color='#1a1a2e')
fig.text(0.515, 0.895,
         "Rice Yield Prediction  |  Metric: R², RMSE, MAE  |  20% held-out test set",
         ha='center', fontsize=9.5, color='#666680', style='italic')
fig.text(0.99, 0.01, "SmartRice AI  |  Yield Prediction Module",
         ha='right', fontsize=7.5, color='#aaaaaa', style='italic')

OUT = os.path.join(BASE, "model_comparison_rf.png")
plt.savefig(OUT, dpi=180, bbox_inches='tight', facecolor='#f8f9fc')
print(f"\n[OK] Plot saved -> {OUT}")
