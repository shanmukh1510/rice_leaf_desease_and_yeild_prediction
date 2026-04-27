# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
========================================================
  Rice Yield Ensemble Model -- Predicted vs Actual
  Scatter Plot with Hyaline Linear Correspondence
========================================================
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import pickle
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
from scipy import stats
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

matplotlib.rcParams['font.family'] = 'DejaVu Sans'
matplotlib.rcParams['axes.unicode_minus'] = False

# ── 1. Load Data ─────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
CSV  = os.path.join(BASE, "rice_yield_dataset.csv")
PKL  = os.path.join(BASE, "rice_yield_model.pkl")
FEAT = os.path.join(BASE, "feature_columns.pkl")

df = pd.read_csv(CSV)

# ── 2. Encode categoricals ───────────────────────────────
cat_cols = ['irrigation_type', 'season', 'rice_variety', 'region']
df_enc = df.copy()
le_map = {}
for col in cat_cols:
    le = LabelEncoder()
    df_enc[col] = le.fit_transform(df_enc[col].astype(str))
    le_map[col] = le

TARGET = 'yield_ton_per_ha'
FEATURES = [c for c in df_enc.columns if c != TARGET]

X = df_enc[FEATURES]
y = df_enc[TARGET]

# ── 3. Train ensemble directly (robust, no pkl dependency) ──
print("[INFO] Training fresh ensemble model on rice_yield_dataset.csv ...")
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor, VotingRegressor
from sklearn.linear_model import Ridge

gbr = GradientBoostingRegressor(n_estimators=50, max_depth=5,
                                learning_rate=0.07, subsample=0.85,
                                random_state=42)
rfr = RandomForestRegressor(n_estimators=50, random_state=42,
                            max_features='sqrt', n_jobs=-1)
rr  = Ridge(alpha=1.0)
model = VotingRegressor([('gbr', gbr), ('rfr', rfr), ('rr', rr)])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)
model.fit(X_train, y_train)
y_pred_plot   = model.predict(X_test)
y_actual_plot = y_test.values
print(f"[INFO] Ensemble trained. Test samples: {len(y_actual_plot):,}")

# ── 4. Metrics ───────────────────────────────────────────
r2   = r2_score(y_actual_plot, y_pred_plot)
rmse = np.sqrt(mean_squared_error(y_actual_plot, y_pred_plot))
mae  = mean_absolute_error(y_actual_plot, y_pred_plot)
pcc  = np.corrcoef(y_actual_plot, y_pred_plot)[0, 1]

# Perfect-fit line range
lo = min(y_actual_plot.min(), y_pred_plot.min()) - 0.2
hi = max(y_actual_plot.max(), y_pred_plot.max()) + 0.2
line_x = np.linspace(lo, hi, 400)

# Regression line (OLS)
slope, intercept, r_val, p_val, _ = stats.linregress(y_actual_plot, y_pred_plot)
reg_y = slope * line_x + intercept

# ── 5. Custom colour map (violet → amber, vivid on white) ─
cmap_custom = LinearSegmentedColormap.from_list(
    "rice_cmap",
    ["#4361ee", "#4cc9f0", "#7bf1a8", "#f8961e", "#e63946"],
    N=512
)

# Colour each point by density (KDE)
from scipy.stats import gaussian_kde
xy    = np.vstack([y_actual_plot, y_pred_plot])
kde   = gaussian_kde(xy)(xy)
order = kde.argsort()

# ── 6. Figure Layout ─────────────────────────────────────
fig = plt.figure(figsize=(13, 10), facecolor="#ffffff")
gs  = GridSpec(1, 1, figure=fig, left=0.10, right=0.94,
               bottom=0.10, top=0.88)
ax  = fig.add_subplot(gs[0])
ax.set_facecolor("#f8f9fc")

# ── Grid ─────────────────────────────────────────────────
ax.grid(color="#dce3ee", linewidth=0.7, linestyle='--', alpha=0.8, zorder=0)
ax.set_axisbelow(True)

# ── Scatter with density colour ──────────────────────────
sc = ax.scatter(
    y_actual_plot[order],
    y_pred_plot[order],
    c=kde[order],
    cmap=cmap_custom,
    s=38,
    alpha=0.82,
    edgecolors='none',
    zorder=3,
    label='Sample predictions'
)

# ── Perfect-fit line (1 : 1) ─────────────────────────────
ax.plot(line_x, line_x,
        color='#2d3a4a',
        lw=1.8,
        ls='--',
        alpha=0.70,
        zorder=4,
        label='Perfect fit  (y = x)')

# ── OLS Regression line ──────────────────────────────────
ax.plot(line_x, reg_y,
        color='#e63946',
        lw=2.4,
        zorder=5,
        label=f'Regression  (slope={slope:.3f})')

# Confidence band (+-1.96 SE of regression)
n   = len(y_actual_plot)
x_m = y_actual_plot.mean()
se  = rmse * np.sqrt(1/n + (line_x - x_m)**2 /
                     ((n - 1) * y_actual_plot.var()))
ax.fill_between(line_x,
                reg_y - 1.96 * se,
                reg_y + 1.96 * se,
                alpha=0.13,
                color='#e63946',
                zorder=2,
                label='95 % confidence band')

# ── Colour-bar ───────────────────────────────────────────
cb = fig.colorbar(sc, ax=ax, pad=0.02, fraction=0.035)
cb.set_label('Point Density (KDE)', color='#333333',
             fontsize=10, labelpad=10)
cb.ax.yaxis.set_tick_params(color='#333333')
plt.setp(cb.ax.yaxis.get_ticklabels(), color='#333333', fontsize=8)
cb.outline.set_edgecolor('#aaaaaa')

# ── Axes labels & ticks ──────────────────────────────────
ax.set_xlabel('Actual Yield  (tons / hectare)',
              fontsize=13, color='#222222', labelpad=10)
ax.set_ylabel('Predicted Yield  (tons / hectare)',
              fontsize=13, color='#222222', labelpad=10)
ax.tick_params(colors='#444444', labelsize=10)
for spine in ax.spines.values():
    spine.set_edgecolor('#bbbbbb')

# ── Legend ───────────────────────────────────────────────
leg = ax.legend(
    fontsize=9.5,
    loc='upper left',
    framealpha=0.85,
    edgecolor='#cccccc',
    facecolor='#ffffff',
    labelcolor='#222222'
)

# ── Metric annotation box ────────────────────────────────
metrics_txt = (
    f"  R2 Score      :  {r2:.4f}\n"
    f"  Pearson r     :  {pcc:.4f}\n"
    f"  RMSE          :  {rmse:.4f}\n"
    f"  MAE           :  {mae:.4f}\n"
    f"  n (test set)  :  {len(y_actual_plot):,}"
)
ax.text(
    0.975, 0.04,
    metrics_txt,
    transform=ax.transAxes,
    ha='right', va='bottom',
    fontsize=9.5,
    color='#1a1a2e',
    fontfamily='monospace',
    bbox=dict(
        boxstyle='round,pad=0.6',
        facecolor='#eef2fb',
        edgecolor='#aab4cc',
        alpha=0.95,
        linewidth=1.2
    ),
    zorder=10
)

# ── Main Title ───────────────────────────────────────────
fig.text(
    0.52, 0.94,
    "Ensemble Regression Model  --  Predicted vs Actual Rice Yield",
    ha='center', va='bottom',
    fontsize=15.5, fontweight='bold',
    color='#1a1a2e'
)
fig.text(
    0.52, 0.905,
    "Digital Scatter Plot  |  Hyaline Linear Correspondence  |  Backdoor Projection (tons / hectare)",
    ha='center', va='bottom',
    fontsize=9.5,
    color='#555577',
    style='italic'
)

# ── Watermark ────────────────────────────────────────────
fig.text(
    0.99, 0.01,
    "SmartRice AI  |  RiceYield Ensemble",
    ha='right', va='bottom',
    fontsize=7.5,
    color='#aaaaaa',
    style='italic'
)

# ── Save & Show ──────────────────────────────────────────
OUT = os.path.join(BASE, "scatter_yield_vs_actual.png")
plt.savefig(OUT, dpi=180, bbox_inches='tight',
            facecolor='white', edgecolor='none')
print(f"\n[OK] Plot saved -> {OUT}")
plt.show()
