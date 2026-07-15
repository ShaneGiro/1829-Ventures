import React from "react";

export function PageHeader({ overline, title, subtitle, actions, testid }) {
    return (
        <div data-testid={testid} className="px-6 md:px-8 pt-8 pb-6 border-b border-slate-800 flex items-start justify-between gap-6">
            <div>
                {overline && (
                    <div className="text-[10px] uppercase tracking-[0.3em] text-indigo-400 mb-2">{overline}</div>
                )}
                <h1 className="font-display text-3xl sm:text-4xl tracking-tighter text-slate-50">{title}</h1>
                {subtitle && <p className="text-sm text-slate-400 mt-2 max-w-2xl">{subtitle}</p>}
            </div>
            {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
        </div>
    );
}

export function Metric({ label, value, sub, trend, testid }) {
    return (
        <div data-testid={testid} className="border-r border-b border-slate-800 px-5 py-5 last:border-r-0">
            <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">{label}</div>
            <div className="font-mono-data text-3xl mt-3 text-slate-50 tracking-tight">{value}</div>
            {sub && (
                <div className={`text-xs mt-2 font-mono-data ${
                    trend === "up" ? "text-emerald-400" : trend === "down" ? "text-rose-400" : "text-slate-500"
                }`}>{sub}</div>
            )}
        </div>
    );
}

export function StagePill({ stage }) {
    const map = {
        sourced: "border-slate-700 text-slate-400 bg-slate-800/40",
        screening: "border-sky-500/40 text-sky-300 bg-sky-500/10",
        diligence: "border-amber-500/40 text-amber-300 bg-amber-500/10",
        ic: "border-indigo-500/40 text-indigo-300 bg-indigo-500/10",
        invested: "border-emerald-500/40 text-emerald-300 bg-emerald-500/10",
        passed: "border-rose-500/40 text-rose-300 bg-rose-500/10",
    };
    const label = { sourced: "Sourced", screening: "Screening", diligence: "Diligence", ic: "IC", invested: "Invested", passed: "Passed" };
    return (
        <span className={`inline-flex items-center px-2 py-0.5 text-[10px] uppercase tracking-[0.2em] border font-mono-data ${map[stage] || map.sourced}`}>
            {label[stage] || stage}
        </span>
    );
}

export function StatusPill({ status }) {
    const map = {
        not_started: "border-slate-700 text-slate-400 bg-slate-800/40",
        in_progress: "border-amber-500/40 text-amber-300 bg-amber-500/10",
        complete: "border-emerald-500/40 text-emerald-300 bg-emerald-500/10",
        blocked: "border-rose-500/40 text-rose-300 bg-rose-500/10",
    };
    const label = { not_started: "Not started", in_progress: "In progress", complete: "Complete", blocked: "Blocked" };
    return (
        <span className={`inline-flex items-center px-2 py-0.5 text-[10px] uppercase tracking-[0.2em] border font-mono-data ${map[status] || map.not_started}`}>
            {label[status] || status}
        </span>
    );
}

export function EmptyState({ title, description, action }) {
    return (
        <div className="border border-slate-800 bg-slate-900/40 p-10 relative overflow-hidden">
            <div className="absolute inset-0 opacity-[0.06] pointer-events-none"
                 style={{
                     backgroundImage: `url(https://images.pexels.com/photos/9701960/pexels-photo-9701960.jpeg)`,
                     backgroundSize: "cover",
                     backgroundPosition: "center",
                 }} />
            <div className="relative">
                <div className="text-[10px] uppercase tracking-[0.3em] text-slate-500 mb-2">No records</div>
                <div className="font-display text-xl text-slate-50 mb-2 tracking-tight">{title}</div>
                <div className="text-sm text-slate-400 max-w-md">{description}</div>
                {action && <div className="mt-6">{action}</div>}
            </div>
        </div>
    );
}

export function formatMoney(n) {
    if (n == null || isNaN(n)) return "—";
    const num = Number(n);
    if (Math.abs(num) >= 1_000_000) return `$${(num / 1_000_000).toFixed(2)}M`;
    if (Math.abs(num) >= 1_000) return `$${(num / 1_000).toFixed(1)}K`;
    return `$${num.toFixed(0)}`;
}
