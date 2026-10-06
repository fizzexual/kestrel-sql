"""Static portfolio figure from audited medians; run only after timed jobs stop."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]


def main():
    audit=json.loads((ROOT/'benchmarks/retry-035-audit.json').read_text())
    direct=json.loads((ROOT/'benchmarks/retry-035-direct.json').read_text())
    network=json.loads((ROOT/'benchmarks/retry-035-final-retry.json').read_text())
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,'font.size':10})
    fig,axes=plt.subplots(1,2,figsize=(11,5.8),gridspec_kw={'wspace':.36})
    colors={'baseline':'#8796a9','candidate':'#008774'}
    for variant,offset,label in [('baseline',-.17,'0.3.4 queued'),('candidate',.17,'0.3.5 opt-in')]:
        values=[audit['embedded_retry'][str(c)][variant]['median_calls_per_second']/1000 for c in [1,16,64]]
        positions=[i+offset for i in range(3)]
        axes[0].bar(positions,values,width=.31,color=colors[variant],label=label)
        for i,c in enumerate([1,16,64]):
            raw=[r['successful_rps_in_window']/1000 for r in direct['cases'] if r['clients']==c and r['variant']==variant]
            axes[0].scatter([positions[i]]*3,raw,color='#25334b',s=16,zorder=3)
    axes[0].set_xticks([0,1,2],['1','16','64'])
    axes[0].set_xlabel('Caller threads')
    axes[0].set_ylabel('Successful embedded retries / second (thousands)')
    axes[0].set_title('Embedded API: known 100-row retries',loc='left',fontweight='bold')
    axes[0].legend(frameon=False,loc='upper left')
    for i,(variant,label,color) in enumerate([('baseline','0.3.4 queued',colors['baseline']),('indexed0','0.3.5 opt-in',colors['candidate'])]):
        g=audit['groups']['final_retry/retry-mixed/'+variant]
        axes[1].bar(i,g['median_run_p99_ms'],width=.5,color=color)
        raw=[c['latency_ms']['p99'] for c in network['cases'] if c['scenario']=='retry-mixed' and c['variant']==variant]
        axes[1].scatter([i]*3,raw,color='#25334b',s=23,zorder=3)
        axes[1].text(i,g['median_run_p99_ms']*1.22,f"{g['median_run_p99_ms']:.1f} ms",ha='center',fontsize=10)
    axes[1].set_yscale('log')
    axes[1].set_ylim(5,6000)
    axes[1].set_xticks([0,1],['0.3.4 queued','0.3.5 opt-in'])
    axes[1].set_ylabel('Median successful-request run p99 (ms, log scale)')
    axes[1].set_title('JSON client: 95% retries / 5% new writes',loc='left',fontweight='bold')
    axes[1].axhline(100,color='#b9673f',linestyle='--',linewidth=1)
    fig.suptitle('KestrelSQL: measured opt-in retry improvement',x=.07,ha='left',fontsize=18,fontweight='bold',y=.97)
    fig.text(.07,.885,'Three alternating rounds · 1M base rows · 50K retained IDs · shared Windows desktop',color='#536174',fontsize=11)
    fig.text(.07,.04,'Bars = run medians; dots = individual runs. Embedded calls are closed-loop; JSON arrivals are 2,000/s.\nSuccess percentiles exclude loss. New-write tails, overload failures and the unsuccessful always-enabled trial remain in PERFORMANCE_035.md.',fontsize=9,color='#536174')
    fig.subplots_adjust(top=.79,bottom=.23,left=.09,right=.97)
    for suffix in ['png','svg']:
        fig.savefig(ROOT/'portfolio'/('perf-035-retries.'+suffix),dpi=170,facecolor='white')


if __name__=='__main__':
    main()
