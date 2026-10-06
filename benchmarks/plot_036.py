"""Static benchmark figure; run only after all timed database work has stopped."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    audit = json.loads((ROOT / 'benchmarks/prepared-036-audit.json').read_text())
    direct = json.loads((ROOT / 'benchmarks/prepared-036-direct.json').read_text())
    reports = [json.loads((ROOT / 'benchmarks' / filename).read_text()) for filename in
        ['prepared-036-retry-control.json', 'prepared-036-write-controls.json']]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.8))
    colors = ['#506883', '#d78b36', '#008979']
    x = np.arange(3)
    for index, (variant, label) in enumerate([('baseline', '0.3.5 ordinary'), ('ordinary', '0.3.6 ordinary'), ('prepared', '0.3.6 immutable reuse')]):
        values = [audit['embedded_retry'][str(c)][variant]['median_calls_per_second'] for c in [1, 16, 64]]
        positions = x + (index-1)*.24
        axes[0].bar(positions, values, width=.22, color=colors[index], label=label, alpha=.88)
        for position, clients in zip(positions, [1, 16, 64]):
            runs = [c['successful_rps_in_window'] for c in direct['cases'] if c['clients'] == clients and c['variant'] == variant]
            axes[0].scatter([position]*3, runs, s=17, c='black', zorder=5)
    axes[0].set_yscale('log')
    axes[0].set_ylim(70000, 14000000)
    axes[0].set_xticks(x, ['1 caller', '16 callers', '64 callers'])
    axes[0].set_yticks([100000, 1000000, 10000000], ['0.1M', '1M', '10M'])
    axes[0].set_ylabel('Confirmed embedded retry calls/s (log scale)')
    axes[0].set_title('Reusing already committed immutable input', loc='left', fontweight='bold')
    axes[0].legend(frameon=False, fontsize=9, loc='upper left')
    for index, (family, variants, color) in enumerate([
        ('retry_control/retry-mixed', ['baseline-indexed0', 'indexed0'], '#008979'),
        ('write_controls/anonymous-mixed', ['baseline', 'delay0'], '#506883'),
        ('write_controls/receipt-write', ['baseline', 'delay0'], '#d78b36')]):
        for side, variant in enumerate(variants):
            position = index + (side-.5)*.30
            group = audit['groups'][family + '/' + variant]
            axes[1].bar(position, group['median_run_p99_ms'], width=.28, color=color, alpha=.42 if side==0 else .90)
            runs = [c['latency_ms']['p99'] for report in reports for c in report['cases'] if c['variant'] == variant and c['scenario'] == family.split('/')[1]]
            axes[1].scatter([position]*3, runs, c='black', s=18, zorder=5)
    axes[1].set_yscale('log')
    axes[1].set_ylim(2, 1500)
    axes[1].axhline(100, color='#ad3d3a', linestyle='--', linewidth=1)
    axes[1].set_xticks(x, ['95% retry\n(index on)', '5% new writes\n(default)', '25% new writes\n(default)'])
    axes[1].set_ylabel('Successful request p99, ms (log scale)')
    axes[1].set_title('Ordinary protocol controls still vary', loc='left', fontweight='bold')
    axes[1].text(.01, .96, 'Pale: 0.3.5   Solid: 0.3.6   Dots: individual runs', transform=axes[1].transAxes, va='top', fontsize=9)
    for axis in axes:
        axis.spines[['top', 'right']].set_visible(False)
        axis.grid(axis='y', alpha=.15)
        axis.set_axisbelow(True)
    fig.suptitle('KestrelSQL 0.3.6 | three rotating rounds on one Windows computer', fontsize=15, fontweight='bold', x=.075, ha='left')
    fig.text(.075, .025, 'Left: five-second closed loops; preparation outside retries, measured separately; zero new rows. Preparing every call stays ~0.1M/s.\nRight: 2,000 offers/s, 15 seconds, 64 workers; successful-only p99. All losses and storage stalls remain in the report; production gate fails.', fontsize=9)
    fig.tight_layout(rect=[0, .10, 1, .92])
    for suffix in ['png', 'svg']: fig.savefig(ROOT / 'portfolio' / ('perf-036-prepared.' + suffix), dpi=160)
    plt.close(fig)


if __name__ == '__main__': main()
