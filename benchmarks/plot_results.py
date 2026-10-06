"""Render the published measurements; no database execution or benchmark timing."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent.parent / "work"
os.environ.setdefault("MPLCONFIGDIR", str(WORK / "matplotlib-config"))


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    scale = json.loads((ROOT / "benchmarks" / "large-results.json").read_text())
    windows = json.loads((ROOT / "benchmarks" / "random-window-results.json").read_text())
    colors = ["#147D73", "#7356B3"]
    labels = ["10M", "50M", "100M", "100M\n5% late"]
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.6), layout="constrained")
    fig.set_facecolor("#FAFBFC")
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})
    fig.suptitle("KestrelSQL 0.2 | measured scale and tradeoffs", fontsize=20, weight="bold", x=.03, ha="left")
    for ax in axes:
        ax.set_facecolor("#FAFBFC")
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines[["left", "bottom"]].set_color("#BBC4CE")
        ax.grid(axis="y", color="#DEE4EB", linewidth=.6)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", labelsize=10)

    def bars(ax, first, second, ticks, names, logarithmic=False):
        x = np.arange(len(ticks))
        for offset, values, color, name in zip([-.19, .19], [first, second], colors, names):
            rects = ax.bar(x + offset, values, .35, color=color, label=name)
            ax.bar_label(rects, labels=[f"{v:.2f}" if v < 10 else f"{v:.1f}" for v in values],
                         padding=4, fontsize=9)
        ax.set_xticks(x, ticks)
        if logarithmic:
            ax.set_yscale("log")

    bars(axes[0], [r["kestrel_median_us"] / 1000 for r in windows["runs"]],
         [r["duckdb_median_us"] / 1000 for r in windows["runs"]], labels,
         ["Kestrel", "DuckDB"], logarithmic=True)
    axes[0].set_title("Indexed random windows", loc="left", fontsize=13, weight="bold", pad=16)
    axes[0].set_ylabel("Median latency (ms; logarithmic)")
    axes[0].set_ylim(.1, 1200)
    axes[0].legend(frameon=False, loc="upper left")

    bars(axes[1], [r["kestrel"]["peak_working_set_bytes"] / 2**20 for r in scale["runs"]],
         [r["duckdb"]["peak_working_set_bytes"] / 2**20 for r in scale["runs"]], labels,
         ["Kestrel", "DuckDB"])
    axes[1].set_title("Peak process memory", loc="left", fontsize=13, weight="bold", pad=16)
    axes[1].set_ylabel("OS peak working set (MiB)")
    axes[1].set_ylim(0, 430)

    ordered = next(r for r in scale["runs"] if r["rows"] == 100_000_000 and not r["late"])
    general = [q for q in ordered["comparison"] if q["name"] in ["unordered_filter", "grouped"]]
    bars(axes[2], [q["kestrel_us"] / 1e6 for q in general],
         [q["duckdb_us"] / 1e6 for q in general], ["Unordered\nfilter", "Grouping"],
         ["Kestrel", "DuckDB"], logarithmic=True)
    axes[2].set_title("100M general operators", loc="left", fontsize=13, weight="bold", pad=16)
    axes[2].set_ylabel("Median latency (seconds; logarithmic)")
    axes[2].set_ylim(.1, 60)
    fig.supxlabel("One execution thread per engine; live Windows machine; uncontrolled OS caches.\n"
                  "Windows: 31 distinct SQL queries / Kestrel pipe+JSON vs DuckDB Python. Memory excludes kernel cache.\n"
                  "General operators: 7 repetitions / Kestrel Rust API vs DuckDB Python. Full methods and raw samples: SCALE.md.",
                  fontsize=9, color="#526073", ha="left", x=.03)
    out = ROOT / "portfolio"
    fig.savefig(out / "scale-chart.png", dpi=180, facecolor=fig.get_facecolor())
    fig.savefig(out / "scale-chart.svg", facecolor=fig.get_facecolor())
    plt.close(fig)
    (out / "chart-runtime.json").write_text(json.dumps({"matplotlib": matplotlib.__version__,
        "numpy": np.__version__, "source_reports": ["large-results.json", "random-window-results.json"]}, indent=2)+"\n")
    print("Rendered portfolio/scale-chart.png and .svg")


if __name__ == "__main__":
    main()
