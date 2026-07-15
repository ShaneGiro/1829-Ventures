import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useFund } from "@/context/FundContext";
import { api } from "@/lib/api";
import { PageHeader, StagePill, EmptyState, formatMoney } from "@/components/ui-primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Plus, ArrowRight } from "@phosphor-icons/react";
import { toast } from "sonner";

const STAGES = ["sourced", "screening", "diligence", "ic", "invested", "passed"];

export default function Companies() {
    const { activeFund } = useFund();
    const nav = useNavigate();
    const [companies, setCompanies] = useState([]);
    const [filter, setFilter] = useState("all");
    const [open, setOpen] = useState(false);
    const [form, setForm] = useState({ name: "", sector: "", stage: "sourced", one_liner: "", round_stage: "", ask_amount: "", hq: "", website: "", lead_partner: "", source: "" });

    const load = async () => {
        if (!activeFund) return;
        const { data } = await api.get(`/companies`, { params: { fund_id: activeFund.id } });
        setCompanies(data);
    };

    useEffect(() => { load(); }, [activeFund]); // eslint-disable-line

    const create = async () => {
        if (!form.name.trim()) { toast.error("Name is required"); return; }
        try {
            const payload = {
                ...form,
                fund_id: activeFund.id,
                ask_amount: form.ask_amount ? Number(form.ask_amount) : null,
            };
            await api.post(`/companies`, payload);
            toast.success("Company added");
            setOpen(false);
            setForm({ name: "", sector: "", stage: "sourced", one_liner: "", round_stage: "", ask_amount: "", hq: "", website: "", lead_partner: "", source: "" });
            load();
        } catch (e) {
            toast.error("Failed to create");
        }
    };

    const filtered = filter === "all" ? companies : companies.filter((c) => c.stage === filter);
    const stageCounts = STAGES.reduce((a, s) => ({ ...a, [s]: companies.filter((c) => c.stage === s).length }), {});

    return (
        <div>
            <PageHeader
                testid="companies-header"
                overline={activeFund?.name}
                title="Companies"
                subtitle="Pipeline of sourced, screening, diligence, and invested companies."
                actions={
                    <Dialog open={open} onOpenChange={setOpen}>
                        <DialogTrigger asChild>
                            <Button data-testid="new-company-button" className="rounded-none h-9 bg-indigo-600 hover:bg-indigo-500 text-white gap-2 transition-colors duration-150">
                                <Plus size={14} /> New Company
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="bg-slate-900 border-slate-800 rounded-none max-w-xl">
                            <DialogHeader><DialogTitle className="font-display tracking-tight">Add company</DialogTitle></DialogHeader>
                            <div className="grid grid-cols-2 gap-4">
                                <FieldInput testid="company-name" label="Name" value={form.name} onChange={(v) => setForm({ ...form, name: v })} />
                                <FieldInput testid="company-sector" label="Sector" value={form.sector} onChange={(v) => setForm({ ...form, sector: v })} />
                                <div>
                                    <Label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Stage</Label>
                                    <Select value={form.stage} onValueChange={(v) => setForm({ ...form, stage: v })}>
                                        <SelectTrigger data-testid="company-stage" className="mt-2 bg-slate-950 border-slate-800 h-10 rounded-none">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent className="bg-slate-900 border-slate-800 rounded-none">
                                            {STAGES.map((s) => <SelectItem key={s} value={s} className="rounded-none capitalize focus:bg-slate-800">{s}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </div>
                                <FieldInput testid="company-round" label="Round Stage" value={form.round_stage} onChange={(v) => setForm({ ...form, round_stage: v })} placeholder="Seed, Series A…" />
                                <FieldInput testid="company-ask" label="Ask ($)" type="number" value={form.ask_amount} onChange={(v) => setForm({ ...form, ask_amount: v })} />
                                <FieldInput testid="company-hq" label="HQ" value={form.hq} onChange={(v) => setForm({ ...form, hq: v })} />
                                <FieldInput testid="company-website" label="Website" value={form.website} onChange={(v) => setForm({ ...form, website: v })} />
                                <FieldInput testid="company-lead" label="Lead Partner" value={form.lead_partner} onChange={(v) => setForm({ ...form, lead_partner: v })} />
                                <FieldInput testid="company-source" label="Source" value={form.source} onChange={(v) => setForm({ ...form, source: v })} />
                                <div className="col-span-2">
                                    <Label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">One-liner</Label>
                                    <Textarea data-testid="company-oneliner" value={form.one_liner} onChange={(e) => setForm({ ...form, one_liner: e.target.value })} rows={2}
                                              className="mt-2 bg-slate-950 border-slate-800 rounded-none focus-visible:ring-1 focus-visible:ring-indigo-500" />
                                </div>
                            </div>
                            <DialogFooter>
                                <Button data-testid="submit-company" onClick={create} className="rounded-none bg-indigo-600 hover:bg-indigo-500">Create</Button>
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                }
            />

            {/* Stage filters */}
            <div className="px-6 md:px-8 py-4 border-b border-slate-800 flex gap-2 overflow-x-auto">
                <StageChip label="All" count={companies.length} active={filter === "all"} onClick={() => setFilter("all")} testid="filter-all" />
                {STAGES.map((s) => (
                    <StageChip key={s} label={s} count={stageCounts[s]} active={filter === s} onClick={() => setFilter(s)} testid={`filter-${s}`} />
                ))}
            </div>

            {filtered.length === 0 ? (
                <div className="p-6 md:p-8">
                    <EmptyState
                        title="No companies in view"
                        description="Add your first sourced company to start building the pipeline."
                        action={<Button data-testid="empty-new-company" onClick={() => setOpen(true)} className="rounded-none bg-indigo-600 hover:bg-indigo-500">Add company</Button>}
                    />
                </div>
            ) : (
                <div className="border-t border-slate-800">
                    <div className="grid grid-cols-12 px-6 md:px-8 py-3 border-b border-slate-800 text-[10px] uppercase tracking-[0.25em] text-slate-500 font-mono-data">
                        <div className="col-span-4">Name</div>
                        <div className="col-span-2">Stage</div>
                        <div className="col-span-2">Round</div>
                        <div className="col-span-2 text-right">Ask</div>
                        <div className="col-span-2">Lead</div>
                    </div>
                    {filtered.map((c) => (
                        <button
                            key={c.id}
                            data-testid={`company-row-${c.id}`}
                            onClick={() => nav(`/companies/${c.id}`)}
                            className="w-full grid grid-cols-12 items-center px-6 md:px-8 py-3 border-b border-slate-800 hover:bg-slate-900 transition-colors duration-150 text-left group"
                        >
                            <div className="col-span-4">
                                <div className="font-display text-slate-50 tracking-tight">{c.name}</div>
                                {c.one_liner && <div className="text-xs text-slate-500 truncate mt-0.5">{c.one_liner}</div>}
                            </div>
                            <div className="col-span-2"><StagePill stage={c.stage} /></div>
                            <div className="col-span-2 text-sm text-slate-300 font-mono-data">{c.round_stage || "—"}</div>
                            <div className="col-span-2 text-right font-mono-data text-slate-300">{formatMoney(c.ask_amount)}</div>
                            <div className="col-span-2 flex items-center justify-between text-sm text-slate-300">
                                <span>{c.lead_partner || "—"}</span>
                                <ArrowRight size={14} className="text-slate-600 group-hover:text-indigo-400 transition-colors duration-150" />
                            </div>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}

function StageChip({ label, count, active, onClick, testid }) {
    return (
        <button
            data-testid={testid}
            onClick={onClick}
            className={`px-3 h-8 border text-xs uppercase tracking-[0.2em] transition-colors duration-150 flex items-center gap-2 ${
                active ? "border-indigo-500 bg-indigo-500/10 text-indigo-300" : "border-slate-800 text-slate-400 hover:bg-slate-900 hover:text-slate-50"
            }`}
        >
            <span>{label}</span>
            <span className="font-mono-data text-[10px] opacity-70">{count}</span>
        </button>
    );
}

function FieldInput({ label, value, onChange, testid, type = "text", placeholder }) {
    return (
        <div>
            <Label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">{label}</Label>
            <Input
                data-testid={testid}
                type={type}
                value={value}
                placeholder={placeholder}
                onChange={(e) => onChange(e.target.value)}
                className="mt-2 bg-slate-950 border-slate-800 h-10 rounded-none focus-visible:ring-1 focus-visible:ring-indigo-500 focus-visible:border-indigo-500"
            />
        </div>
    );
}
