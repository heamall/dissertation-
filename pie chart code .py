import math
import re
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------
# FILE PATH - XRD DATA
# --------------------------------
file_path = Path(r"C:\Users\heamall\Downloads\XRD quantification Feb 26[2] (1).xlsx")
output_folder = file_path.parent / "XRD_PDF_Charts"
output_folder.mkdir(exist_ok=True)

# --------------------------------
# STYLE
# --------------------------------
plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 28,
    "axes.titlesize": 40,
    "pdf.fonttype": 42,
})

TITLE_SIZE = 40
LABEL_SIZE = 28
FIGSIZE = (20, 16)

DONUT_RADIUS = 1.32
DONUT_WIDTH = 0.42

LINE_START_R = 1.42
ELBOW_R = 1.55
LABEL_R = 2.75

TOP_LIMIT = 2.20
BOTTOM_LIMIT = -2.60
MIN_LABEL_GAP = 0.62
TEXT_PAD_X = 0.12

X_PAD = 1.20
Y_PAD = 1.20
TITLE_Y = 1.03

TEXT_BLOCK_EXTRA_X = 2.20
TEXT_BLOCK_EXTRA_Y = 0.45

# --------------------------------
# LOAD DATA
# --------------------------------
df = pd.read_excel(file_path)
df.columns = df.columns.astype(str).str.strip()

df["Sample"] = df["Sample"].ffill()
df = df.dropna(subset=["Phase Name", "Weight %"]).copy()

df["Weight %"] = pd.to_numeric(df["Weight %"], errors="coerce")
df["Error %"] = pd.to_numeric(df["Error %"], errors="coerce").fillna(0)
df = df.dropna(subset=["Weight %"]).copy()

# --------------------------------
# CLEAN MINERAL NAMES
# --------------------------------
def clean_phase_name(name):
    name = str(name).strip()
    name = re.sub(r"\s*\(.*?\)", "", name)

    if re.search(r"muscovite.*2m1", name, flags=re.IGNORECASE):
        return "muscovite-2M1"

    if re.search(r"intermediate.*microcline|microcline.*intermediate", name, flags=re.IGNORECASE):
        return "intermediate microcline"

    return re.sub(r"\s+", " ", name).strip()

def format_sample_name(name):
    name = str(name).replace("-", "").strip()
    return re.sub(r"([A-Za-z]+)(\d+)", r"\1-\2", name)

df["Phase Clean"] = df["Phase Name"].apply(clean_phase_name)
df["Sample"] = df["Sample"].apply(format_sample_name)

# --------------------------------
# HELPERS
# --------------------------------
def safe_filename(text):
    return re.sub(r'[\\/*?:"<>|]', "_", str(text))

def escape_mathtext(text):
    text = str(text)
    text = text.replace("\\", r"\\")
    text = text.replace(" ", r"\ ")
    text = text.replace("_", r"\_")
    text = text.replace("%", r"\%")
    text = text.replace("&", r"\&")
    text = text.replace("#", r"\#")
    text = text.replace("{", r"\{")
    text = text.replace("}", r"\}")
    return text

# --------------------------------
# CONSISTENT COLOURS
# --------------------------------
all_minerals = sorted(df["Phase Clean"].dropna().unique())
cmap = plt.get_cmap("tab20")
colour_map = {mineral: cmap(i % cmap.N) for i, mineral in enumerate(all_minerals)}

# --------------------------------
# LABEL LAYOUT
# --------------------------------
def distribute_side(labels, min_gap=0.62, y_min=-2.60, y_max=2.20):
    if not labels:
        return labels

    labels = sorted(labels, key=lambda d: d["y_target"])
    y = [max(y_min, min(d["y_target"], y_max)) for d in labels]

    for i in range(1, len(y)):
        if y[i] - y[i - 1] < min_gap:
            y[i] = y[i - 1] + min_gap

    overflow = y[-1] - y_max
    if overflow > 0:
        y = [v - overflow for v in y]

    for i in range(len(y) - 2, -1, -1):
        if y[i + 1] - y[i] < min_gap:
            y[i] = y[i + 1] - min_gap

    underflow = y_min - y[0]
    if underflow > 0:
        y = [v + underflow for v in y]

    for label, y_final in zip(labels, y):
        label["y_final"] = y_final

    return labels

def build_label_layout(wedges, minerals, weights, errors):
    label_items = []

    for wedge, mineral, weight, error in zip(wedges, minerals, weights, errors):
        angle_deg = (wedge.theta1 + wedge.theta2) / 2
        theta = math.radians(angle_deg)

        side = "right" if math.cos(theta) >= 0 else "left"

        label_items.append({
            "side": side,
            "x_slice": DONUT_RADIUS * math.cos(theta),
            "y_slice": DONUT_RADIUS * math.sin(theta),
            "x_line_start": LINE_START_R * math.cos(theta),
            "y_line_start": LINE_START_R * math.sin(theta),
            "y_target": LABEL_R * math.sin(theta),
            "mineral": mineral,
            "weight": weight,
            "error": error,
        })

    left = distribute_side(
        [d for d in label_items if d["side"] == "left"],
        MIN_LABEL_GAP,
        BOTTOM_LIMIT,
        TOP_LIMIT
    )

    right = distribute_side(
        [d for d in label_items if d["side"] == "right"],
        MIN_LABEL_GAP,
        BOTTOM_LIMIT,
        TOP_LIMIT
    )

    final_items = left + right

    for d in final_items:
        side_sign = 1 if d["side"] == "right" else -1

        x_text = side_sign * LABEL_R
        y_text = d["y_final"]

        if d["side"] == "right":
            ha = "left"
            x_line_end = x_text - TEXT_PAD_X
            x_text_min = x_text
            x_text_max = x_text + TEXT_BLOCK_EXTRA_X
        else:
            ha = "right"
            x_line_end = x_text + TEXT_PAD_X
            x_text_min = x_text - TEXT_BLOCK_EXTRA_X
            x_text_max = x_text

        d["label_text"] = (
            rf"$\bf{{{escape_mathtext(d['mineral'])}}}$" + "\n"
            f"{d['weight']:.2f} wt% ± {d['error']:.2f}"
        )

        d["x_text"] = x_text
        d["y_text"] = y_text
        d["x_elbow_1"] = side_sign * ELBOW_R
        d["y_elbow_1"] = y_text
        d["x_elbow_2"] = side_sign * (LABEL_R - 0.30)
        d["y_elbow_2"] = y_text
        d["x_line_end"] = x_line_end
        d["y_line_end"] = y_text
        d["ha"] = ha

        d["x_text_min"] = x_text_min
        d["x_text_max"] = x_text_max
        d["y_text_min"] = y_text - TEXT_BLOCK_EXTRA_Y
        d["y_text_max"] = y_text + TEXT_BLOCK_EXTRA_Y

    return final_items

def collect_layout_extents(layout):
    xs = [-DONUT_RADIUS, DONUT_RADIUS]
    ys = [-DONUT_RADIUS, DONUT_RADIUS]

    for d in layout:
        xs.extend([
            d["x_slice"],
            d["x_line_start"],
            d["x_elbow_1"],
            d["x_elbow_2"],
            d["x_line_end"],
            d["x_text_min"],
            d["x_text_max"],
        ])

        ys.extend([
            d["y_slice"],
            d["y_line_start"],
            d["y_elbow_1"],
            d["y_elbow_2"],
            d["y_line_end"],
            d["y_text_min"],
            d["y_text_max"],
        ])

    return min(xs), max(xs), min(ys), max(ys)

# --------------------------------
# FIRST PASS: GLOBAL FRAME
# --------------------------------
samples = df["Sample"].dropna().unique()
sample_plot_data = []

global_xmin = float("inf")
global_xmax = float("-inf")
global_ymin = float("inf")
global_ymax = float("-inf")

for sample in samples:
    sample_df = df[df["Sample"] == sample].reset_index(drop=True)

    weights = sample_df["Weight %"].to_numpy()
    errors = sample_df["Error %"].to_numpy()
    minerals = sample_df["Phase Clean"].tolist()
    colours = [colour_map[m] for m in minerals]

    fig_tmp, ax_tmp = plt.subplots(figsize=FIGSIZE)

    wedges, _ = ax_tmp.pie(
        weights,
        colors=colours,
        startangle=90,
        counterclock=False,
        radius=DONUT_RADIUS,
        wedgeprops=dict(width=DONUT_WIDTH, edgecolor="white", linewidth=1)
    )

    layout = build_label_layout(wedges, minerals, weights, errors)
    xmin, xmax, ymin, ymax = collect_layout_extents(layout)

    global_xmin = min(global_xmin, xmin)
    global_xmax = max(global_xmax, xmax)
    global_ymin = min(global_ymin, ymin)
    global_ymax = max(global_ymax, ymax)

    plt.close(fig_tmp)

    sample_plot_data.append({
        "sample": sample,
        "weights": weights,
        "errors": errors,
        "minerals": minerals,
        "colours": colours,
    })

XMIN = global_xmin - X_PAD
XMAX = global_xmax + X_PAD
YMIN = global_ymin - Y_PAD
YMAX = global_ymax + Y_PAD

# --------------------------------
# SECOND PASS: RENDER PDFS
# --------------------------------
for item in sample_plot_data:
    sample = item["sample"]
    weights = item["weights"]
    errors = item["errors"]
    minerals = item["minerals"]
    colours = item["colours"]

    fig, ax = plt.subplots(figsize=FIGSIZE)

    wedges, _ = ax.pie(
        weights,
        colors=colours,
        startangle=90,
        counterclock=False,
        radius=DONUT_RADIUS,
        wedgeprops=dict(width=DONUT_WIDTH, edgecolor="white", linewidth=1)
    )

    layout = build_label_layout(wedges, minerals, weights, errors)

    for d in layout:
        ax.plot([d["x_slice"], d["x_line_start"]],
                [d["y_slice"], d["y_line_start"]],
                color="black", lw=1.6)

        ax.plot([d["x_line_start"], d["x_elbow_1"]],
                [d["y_line_start"], d["y_elbow_1"]],
                color="black", lw=1.6)

        ax.plot([d["x_elbow_1"], d["x_elbow_2"]],
                [d["y_elbow_1"], d["y_elbow_2"]],
                color="black", lw=1.6)

        ax.plot([d["x_elbow_2"], d["x_line_end"]],
                [d["y_elbow_2"], d["y_line_end"]],
                color="black", lw=1.6)

        ax.text(
            d["x_text"],
            d["y_text"],
            d["label_text"],
            ha=d["ha"],
            va="center",
            fontsize=LABEL_SIZE,
            color="black"
        )

    ax.set_title(
        f"XRD Quantification of Sample {sample}",
        fontsize=TITLE_SIZE,
        y=TITLE_Y
    )

    ax.set_aspect("equal")
    ax.set_xlim(XMIN, XMAX)
    ax.set_ylim(YMIN, YMAX)

    plt.subplots_adjust(top=0.88, left=0.05, right=0.95, bottom=0.05)

    pdf_path = output_folder / f"{safe_filename(sample)}_XRD_quantification.pdf"
    plt.savefig(pdf_path, format="pdf", bbox_inches="tight", pad_inches=0.35)
    plt.close(fig)

print("Saved PDFs to:")
print(output_folder)
print()
print("Global frame used for all charts:")
print(f"X limits: {XMIN:.2f} to {XMAX:.2f}")
print(f"Y limits: {YMIN:.2f} to {YMAX:.2f}")
