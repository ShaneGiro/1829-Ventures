import React, { useEffect, useState } from "react";
import { useFund } from "@/context/FundContext";
import { api, API } from "@/lib/api";
import { PageHeader, Metric, formatMoney } from "@/components/ui-primitives";
import { Button } from "@/components/ui/button";
import { TrendUp, ChartPieSlice, Buildings, CurrencyCircleDollar, DownloadSimple } from "@phosphor-icons/react";

const STAGE_ORDER = ["sourced", "screening", "diligence", "ic", "invested", "passed"];
const STAGE_LABEL = { sourced: "Sourced", screening: "Screening", diligence: "Diligence", ic: "IC", invested: "Invested", passed: "Passed" };

export default function Dashboard() {
    const { activeFund } = useFund();
    const [metrics, setMetrics] = useState(null);

    useEffect(() => {
        if (!activeFund) return;
        api.get(`/metrics/portfolio`, { params: { fund_id: activeFund.id } })
            .then((r) => setMetrics(r.data))
            .catch(() => setMetrics(null));
    }, [activeFund]);

    if (!activeFund) return null;
    if (!metrics) {
        return (
            <div className="p-8 text-xs uppercase tracking-[0.3em] text-slate-500">Loading metrics…</div>
        );
    }

    const deploymentPct = metrics.committed_capital > 0
        ? Math.min(100, (metrics.deployed_capital / metrics.committed_capital) * 100)
        : 0;

    const irrPct = metrics.irr != null ? (metrics.irr * 100).toFixed(1) + "%" : "—";
    const exportUrl = `${API}/export/lp-report?fund_id=${activeFund.id}`;

    return (
        <div>
            <PageHeader
                testid="dashboard-header"
                overline={activeFund.name}
                title="Portfolio Overview"
                subtitle={`Vintage ${activeFund.vintage || "—"} · Committed ${formatMoney(activeFund.committed_capital)}`}
                actions={
                    <a href={exportUrl} data-testid="export-lp-report">
                        <Button variant="outline" className="rounded-none h-9 border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-200 gap-2 transition-colors duration-150">
                            <DownloadSimple size={14} /> Export LP Report
                        </Button>
                    </a>
                }
            />

            {/* Metrics row */}
            <div className="grid grid-cols-2 md:grid-cols-5 border-b border-slate-800">
                <Metric testid="metric-deployed" label="Deployed Capital" value={formatMoney(metrics.deployed_capital)}
                        sub={`${deploymentPct.toFixed(0)}% of committed`} trend="neutral" />
                <Metric testid="metric-dry-powder" label="Dry Powder" value={formatMoney(metrics.dry_powder)}
                        sub={`of ${formatMoney(metrics.committed_capital)}`} trend="neutral" />
                <Metric testid="metric-moic" label="MOIC" value={`${metrics.moic.toFixed(2)}x`}
                        sub={metrics.moic >= 1 ? "at or above cost" : "below cost"} trend={metrics.moic >= 1 ? "up" : "down"} />
                <Metric testid="metric-irr" label="IRR (XIRR)" value={irrPct}
                        sub={metrics.irr != null ? "annualized" : "add cash flows"} trend={metrics.irr != null && metrics.irr > 0 ? "up" : metrics.irr != null ? "down" : "neutral"} />
                <Metric testid="metric-investments" label="Investments" value={String(metrics.num_investments)}
                        sub={`${metrics.num_invested_companies} portfolio cos`} trend="neutral" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-px bg-slate-800">
                {/* Deployment bar */}
                <div className="lg:col-span-2 bg-slate-950 p-6">
                    <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-slate-500 mb-4">
                        <TrendUp size={12} /> Deployment Progress
                    </div>
                    <div className="font-mono-data text-4xl text-slate-50 tracking-tight">
                        {formatMoney(metrics.deployed_capital)}
                        <span className="text-slate-500"> / {formatMoney(metrics.committed_capital)}</span>
                    </div>
                    <div className="mt-6 h-2 bg-slate-900 border border-slate-800">
                        <div className="h-full bg-indigo-600 transition-all duration-500"
                             style={{ width: `${deploymentPct}%` }} />
                    </div>
                    <div className="mt-4 flex items-center justify-between text-xs font-mono-data text-slate-500">
                        <span>0</span>
                        <span>{deploymentPct.toFixed(1)}%</span>
                        <span>100%</span>
                    </div>
                </div>

                {/* Sector */}
                <div className="bg-slate-950 p-6">
                    <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-slate-500 mb-4">
                        <ChartPieSlice size={12} /> Sector Allocation
                    </div>
                    {Object.keys(metrics.sector_breakdown).length === 0 ? (
                        <div className="text-sm text-slate-500">No invested companies yet.</div>
                    ) : (
                        <div className="space-y-3">
                            {Object.entries(metrics.sector_breakdown).map(([s, count]) => (
                                <div key={s} className="flex items-center justify-between text-sm">
                                    <span className="text-slate-300">{s}</span>
                                    <span className="font-mono-data text-slate-50">{count}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Pipeline stages */}
            <div className="p-6 md:p-8">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-slate-500 mb-4">
                    <Buildings size={12} /> Pipeline Snapshot
                </div>
                <div className="grid grid-cols-2 md:grid-cols-6 border border-slate-800">
                    {STAGE_ORDER.map((s) => (
                        <div key={s} className="border-r last:border-r-0 border-b md:border-b-0 border-slate-800 px-4 py-4">
                            <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">{STAGE_LABEL[s]}</div>
                            <div className="font-mono-data text-2xl mt-2 text-slate-50">
                                {metrics.stage_breakdown[s] || 0}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="px-6 md:px-8 pb-10 flex items-center gap-3 text-xs text-slate-500">
                <CurrencyCircleDollar size={14} className="text-indigo-400" />
                Marks: current value uses <span className="font-mono-data text-slate-300">current_value</span> if set, otherwise investment amount.
            </div>
        </div>
    );
}
