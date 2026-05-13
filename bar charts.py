import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

# =========================
# FILE PATH
# =========================
file_path = r"C:\Users\heamall\Downloads\XRF_exact_format.xlsx - Sheet1.csv"

# =========================
# STYLE
# =========================
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.titlesize": 24,
    "axes.labelsize": 16,
    "xtick.labelsize": 14,
    "ytick.labelsize": 14,
    "legend.fontsize": 12,
    "legend.title_fontsize": 12,
    "pdf.fonttype": 42,
})

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(file_path)

row_label_col = df.columns[0]
sample_col = "SAMPLE"

# =========================
# FORMAT SAMPLE NAMES
# GK1 -> GK-1
# =========================
def format_sample_name(name):
    name = str(name).replace("-", "").strip()
    return re.sub(r"([A-Za-z]+)(\d+)", r"\1-\2", name)

# =========================
# FORMAT OXIDE LABELS
# Al2O3 -> Al₂O₃
# =========================
def pretty_oxide_label(oxide):
    subscript_map = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    return str(oxide).translate(subscript_map)

# =========================
# KEEP ONLY REAL OXIDES
# Ignore Ka / La / Lb X-ray lines
# =========================
oxide_cols = [
    col for col in df.columns
    if col not in [row_label_col, sample_col, "Sum Before Norm."]
    and (
        col.endswith("O")
        or col.endswith("O2")
        or col.endswith("O3")
        or col.endswith("O5")
        or col.endswith("O7")
    )
]

# =========================
# EXTRACT AVERAGE VALUES
# =========================
records = []

for i in range(len(df)):
    sample_name = df.loc[i, sample_col]

    if pd.notna(sample_name):
        sample_name = format_sample_name(sample_name)

        if i + 1 < len(df) and str(df.loc[i + 1, row_label_col]).strip().lower() == "average":
            avg_row = pd.to_numeric(df.loc[i + 1, oxide_cols], errors="coerce")

            record = {"Sample": sample_name}
            for col in oxide_cols:
                record[col] = avg_row[col]

            records.append(record)

plot_df = pd.DataFrame(records)

# =========================
# GROUPS
# =========================
def get_group(sample):
    return sample.split("-")[0]

plot_df["Group"] = plot_df["Sample"].apply(get_group)

# =========================
# COLOURS
# =========================
map_palette = [
    "#C39035",
    "#9C5E2F",
    "#C24F7E",
    "#A06FCD",
    "#EC1C00",
    "#F4831F",
    "#8ED7F6",
    "#0194DA",
]

oxide_colour_map = {}
for i, oxide in enumerate(oxide_cols):
    oxide_colour_map[oxide] = map_palette[i % len(map_palette)]

preferred_map = {
    "SiO2": "#C39035",
    "Al2O3": "#9C5E2F",
    "Fe2O3": "#C24F7E",
    "CaO": "#A06FCD",
    "K2O": "#EC1C00",
    "MgO": "#F4831F",
    "Na2O": "#8ED7F6",
    "TiO2": "#0194DA",
}
for oxide, colour in preferred_map.items():
    if oxide in oxide_cols:
        oxide_colour_map[oxide] = colour

# =========================
# OUTPUT FOLDER
# =========================
output_folder = os.path.dirname(file_path)

# =========================
# FIXED Y SCALE
# =========================
y_min = 0
y_max = 60

# =========================
# PLOT
# =========================
groups = plot_df["Group"].unique()

for group in groups:
    group_data = plot_df[plot_df["Group"] == group]

    if group_data.empty:
        continue

    samples = group_data["Sample"].tolist()
    x = np.arange(len(samples))

    bar_width = 0.08
    offsets = [-bar_width, 0, bar_width]

    fig, ax = plt.subplots(figsize=(12, 7))

    oxides_used = set()

    for idx, (_, row) in enumerate(group_data.iterrows()):
        oxide_values = row[oxide_cols].dropna()
        oxide_values = oxide_values[oxide_values > 0]

        if oxide_values.empty:
            continue

        # top 3 by abundance
        top_oxides = oxide_values.sort_values(ascending=False).head(3)

        # then alphabetical
        sorted_oxides = sorted(top_oxides.index)
        top_oxides = top_oxides[sorted_oxides]

        for j, (oxide, value) in enumerate(top_oxides.items()):
            xpos = x[idx] + offsets[j]

            ax.bar(
                xpos,
                value,
                width=bar_width,
                color=oxide_colour_map[oxide],
                edgecolor="black",
                linewidth=0.8
            )

            oxides_used.add(oxide)

    # =========================
    # FORMAT
    # =========================
    ax.set_xticks(x)
    ax.set_xticklabels(samples)
    ax.set_xlabel("Sample")
    ax.set_ylabel("Average concentration (%)")
    ax.set_title(f"{group} samples: major oxides", weight="bold")

    ax.set_xlim(-0.6, len(samples) - 0.4)
    ax.set_ylim(y_min, y_max)
    ax.set_yticks(np.arange(0, 61, 10))

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    # =========================
    # LEGEND OUTSIDE
    # =========================
    legend_items = [
        Patch(
            facecolor=oxide_colour_map[o],
            edgecolor="black",
            label=pretty_oxide_label(o)
        )
        for o in sorted(oxides_used)
    ]

    ax.legend(
        handles=legend_items,
        title="Major oxides",
        loc="upper left",
        bbox_to_anchor=(1.02, 1.0),
        frameon=True
    )

    plt.tight_layout(rect=[0, 0, 0.82, 1])

    output_pdf = os.path.join(output_folder, f"{group}_major_oxides_bar_chart.pdf")
    plt.savefig(output_pdf, dpi=300, bbox_inches="tight")
    plt.close()

print("Done. PDFs saved in:")
print(output_folder)