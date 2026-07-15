import React, { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { api } from "@/lib/api";
import { useFund } from "@/context/FundContext";
import { PageHeader, StagePill, StatusPill, EmptyState, formatMoney } from "@/components/ui-primitives";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { Plus, Trash, CaretLeft } from "@phosphor-icons/react";
import { toast } from "sonner";

const STAGES = ["sourced", "screening", "diligence", "ic", "invested", "passed"];
const DILIGENCE_CATEGORIES = ["Legal", "Financial", "Tech", "Market", "Team"];
const DILIGENCE_STATUSES = ["not_started", "in_progress", "complete", "blocked"];

export default function CompanyDetail() {
    const { id } = useParams();
    const nav = useNavigate();
    const { activeFund } = useFund();
    const [company, setCompany] = useState(null);
    const [conversations, setConversations] = useState([]);
    const [diligence, setDiligence] = useState([]);
    const [investments, setInvestments] = useState([]);
    const [contacts, setContacts] = useState([]);

    const loadAll = useCallback(async () => {
        try {
            const { data: c } = await api.get(`/companies/${id}`);
            setCompany(c);
            const fund_id = c.fund_id;
            const [conv, dil, inv, ct] = await Promise.all([
                api.get(`/conversations`, { params: { fund_id, company_id: id } }),
                api.get(`/diligence`, { params: { fund_id, company_id: id } }),
                api.get(`/investments`, { params: { fund_id, company_id: id } }),
                api.get(`/contacts`, { params: { fund_id, company_id: id } }),
            ]);
            setConversations(conv.data);
            setDiligence(dil.data);
            setInvestments(inv.data);
            setContacts(ct.data);
        } catch {
            toast.error("Could not load company");
            nav("/companies");
        }
    }, [id, nav]);

    useEffect(() => { loadAll(); }, [loadAll]);

    const updateCompany = async (patch) => {
        await api.patch(`/companies/${id}`, patch);
        loadAll();
    };

    const removeCompany = async () => {
        if (!window.confirm("Delete this company and all its diligence/investments?")) return;
        await api.delete(`/companies/${id}`);
        toast.success("Deleted");
        nav("/companies");
    };

    if (!company) return <div className="p-8 text-xs uppercase tracking-[0.3em] text-slate-500">Loading…</div>;

    return (
        <div>
            <div className="px-6 md:px-8 py-3 border-b border-slate-800">
                <Link data-testid="back-to-companies" to="/companies" className="text-xs text-slate-500 hover:text-slate-200 inline-flex items-center gap-1 transition-colors duration-150">
                    <CaretLeft size={12} /> All companies
                </Link>
            </div>

            <PageHeader
                testid="company-detail-header"
                overline={company.sector || "Company"}
                title={company.name}
                subtitle={company.one_liner || company.description || " "}
                actions={
                    <div className="flex items-center gap-2">
                        <StagePill stage={company.stage} />
                        <Select value={company.stage} onValueChange={(v) => updateCompany({ stage: v })}>
                            <SelectTrigger data-testid="change-stage" className="w-[160px] rounded-none bg-slate-900 border-slate-800 h-9 text-xs uppercase tracking-[0.2em]">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-900 border-slate-800 rounded-none">
                                {STAGES.map((s) => <SelectItem key={s} value={s} className="rounded-none capitalize focus:bg-slate-800">{s}</SelectItem>)}
                            </SelectContent>
                        </Select>
                        <Button data-testid="delete-company" variant="ghost" onClick={removeCompany}
                                className="rounded-none h-9 border border-slate-800 text-slate-400 hover:text-rose-400 hover:bg-slate-900">
                            <Trash size={14} />
                        </Button>
                    </div>
                }
            />

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-px bg-slate-800">
                {/* Sidebar */}
                <aside className="lg:col-span-1 bg-slate-950 p-6 space-y-5">
                    <EditableField testid="edit-sector" label="Sector" value={company.sector} onSave={(v) => updateCompany({ sector: v })} />
                    <EditableField testid="edit-round" label="Round" value={company.round_stage} onSave={(v) => updateCompany({ round_stage: v })} />
                    <EditableField testid="edit-ask" label="Ask ($)" mono value={company.ask_amount ? String(company.ask_amount) : ""} onSave={(v) => updateCompany({ ask_amount: v ? Number(v) : null })} />
                    <EditableField testid="edit-hq" label="HQ" value={company.hq} onSave={(v) => updateCompany({ hq: v })} />
                    <EditableField testid="edit-website" label="Website" value={company.website} onSave={(v) => updateCompany({ website: v })} />
                    <EditableField testid="edit-lead" label="Lead Partner" value={company.lead_partner} onSave={(v) => updateCompany({ lead_partner: v })} />
                    <EditableField testid="edit-source" label="Source" value={company.source} onSave={(v) => updateCompany({ source: v })} />

                    {(company.dealroom_url || company.dealroom_total_funding_usd_m || company.dealroom_investors || company.dealroom_founders) && (
                        <div className="pt-4 mt-4 border-t border-slate-800 space-y-3">
                            <div className="text-[10px] uppercase tracking-[0.3em] text-indigo-400">Dealroom</div>
                            {company.dealroom_url && (
                                <div>
                                    <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">Profile</div>
                                    <a data-testid="dealroom-link" href={company.dealroom_url} target="_blank" rel="noreferrer" className="mt-1 block text-xs text-indigo-400 hover:text-indigo-300 transition-colors duration-150 break-all">{company.dealroom_url}</a>
                                </div>
                            )}
                            {company.dealroom_total_funding_usd_m != null && (
                                <Info label="Total funding (USDm)" value={String(company.dealroom_total_funding_usd_m)} mono />
                            )}
                            {company.dealroom_valuation_usd != null && (
                                <Info label="DR Valuation ($)" value={formatMoney(company.dealroom_valuation_usd)} mono />
                            )}
                            {company.dealroom_founders && (
                                <div>
                                    <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">Founders</div>
                                    <div className="mt-1 text-xs text-slate-300">{company.dealroom_founders}</div>
                                </div>
                            )}
                            {company.dealroom_investors && (
                                <div>
                                    <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">Investors</div>
                                    <div className="mt-1 text-xs text-slate-300 line-clamp-4">{company.dealroom_investors}</div>
                                </div>
                            )}
                        </div>
                    )}
                </aside>

                {/* Tabs */}
                <div className="lg:col-span-3 bg-slate-950">
                    <Tabs defaultValue="overview" className="w-full">
                        <TabsList className="rounded-none bg-transparent border-b border-slate-800 w-full justify-start h-auto p-0 gap-0">
                            {["overview", "conversations", "diligence", "investment", "contacts"].map((t) => (
                                <TabsTrigger
                                    key={t}
                                    value={t}
                                    data-testid={`tab-${t}`}
                                    className="rounded-none bg-transparent border-b-2 border-transparent data-[state=active]:border-indigo-500 data-[state=active]:bg-transparent data-[state=active]:text-slate-50 text-slate-400 hover:text-slate-50 py-3 px-5 text-xs uppercase tracking-[0.2em] transition-colors duration-150 data-[state=active]:shadow-none"
                                >
                                    {t}
                                </TabsTrigger>
                            ))}
                        </TabsList>

                        <TabsContent value="overview" className="p-6">
                            <OverviewEditor company={company} onSave={updateCompany} />
                        </TabsContent>
                        <TabsContent value="conversations" className="p-6">
                            <ConversationsPanel companyId={company.id} fundId={company.fund_id} items={conversations} reload={loadAll} />
                        </TabsContent>
                        <TabsContent value="diligence" className="p-6">
                            <DiligencePanel companyId={company.id} fundId={company.fund_id} items={diligence} reload={loadAll} />
                        </TabsContent>
                        <TabsContent value="investment" className="p-6">
                            <InvestmentsPanel companyId={company.id} fundId={company.fund_id} items={investments} reload={loadAll} />
                        </TabsContent>
                        <TabsContent value="contacts" className="p-6">
                            <ContactsPanel companyId={company.id} fundId={company.fund_id} items={contacts} reload={loadAll} />
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </div>
    );
}

function Info({ label, value, mono, link }) {
    return (
        <div>
            <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">{label}</div>
            <div className={`mt-1 text-sm ${mono ? "font-mono-data" : ""} text-slate-200`}>
                {value ? (link ? <a href={value.startsWith("http") ? value : `https://${value}`} target="_blank" rel="noreferrer" className="text-indigo-400 hover:text-indigo-300 transition-colors duration-150 break-all">{value}</a> : value) : <span className="text-slate-600">—</span>}
            </div>
        </div>
    );
}

function EditableField({ label, value, onSave, mono, testid, placeholder }) {
    const [editing, setEditing] = useState(false);
    const [v, setV] = useState(value || "");
    useEffect(() => { setV(value || ""); }, [value]);
    const save = async () => { setEditing(false); if (v !== (value || "")) await onSave(v || null); };
    return (
        <div>
            <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">{label}</div>
            {editing ? (
                <input
                    data-testid={testid}
                    autoFocus
                    value={v}
                    onChange={(e) => setV(e.target.value)}
                    onBlur={save}
                    onKeyDown={(e) => { if (e.key === "Enter") save(); if (e.key === "Escape") { setV(value || ""); setEditing(false); } }}
                    placeholder={placeholder}
                    className={`mt-1 w-full bg-slate-900 border border-slate-700 focus:border-indigo-500 outline-none px-2 py-1 text-sm ${mono ? "font-mono-data" : ""} text-slate-100`}
                />
            ) : (
                <button data-testid={testid} onClick={() => setEditing(true)}
                        className={`mt-1 w-full text-left text-sm ${mono ? "font-mono-data" : ""} text-slate-200 hover:text-indigo-300 transition-colors duration-150 py-0.5 border-b border-transparent hover:border-slate-700`}>
                    {value || <span className="text-slate-600">— click to add</span>}
                </button>
            )}
        </div>
    );
}

function OverviewEditor({ company, onSave }) {
    const [desc, setDesc] = useState(company.description || "");
    return (
        <div>
            <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500 mb-3">Notes</div>
            <Textarea
                data-testid="company-description"
                rows={12}
                value={desc}
                onChange={(e) => setDesc(e.target.value)}
                placeholder="Team, product, traction, market, why now…"
                className="bg-slate-900 border-slate-800 rounded-none focus-visible:ring-1 focus-visible:ring-indigo-500"
            />
            <Button data-testid="save-description" onClick={() => onSave({ description: desc })}
                    className="mt-4 rounded-none bg-indigo-600 hover:bg-indigo-500 h-9 transition-colors duration-150">Save</Button>
        </div>
    );
}

function ConversationsPanel({ companyId, fundId, items, reload }) {
    const [open, setOpen] = useState(false);
    const [form, setForm] = useState({ date: new Date().toISOString().slice(0, 10), channel: "meeting", attendees: "", summary: "", next_steps: "", sentiment: "neutral" });

    const create = async () => {
        if (!form.summary.trim()) { toast.error("Summary required"); return; }
        await api.post(`/conversations`, { ...form, fund_id: fundId, company_id: companyId });
        toast.success("Conversation logged");
        setOpen(false);
        setForm({ date: new Date().toISOString().slice(0, 10), channel: "meeting", attendees: "", summary: "", next_steps: "", sentiment: "neutral" });
        reload();
    };

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">{items.length} entries</div>
                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger asChild>
                        <Button data-testid="new-conversation" className="rounded-none h-8 bg-indigo-600 hover:bg-indigo-500 gap-2"><Plus size={12} /> Log conversation</Button>
                    </DialogTrigger>
                    <DialogContent className="bg-slate-900 border-slate-800 rounded-none max-w-lg">
                        <DialogHeader><DialogTitle className="font-display tracking-tight">New conversation</DialogTitle></DialogHeader>
                        <div className="space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                                <Fld label="Date"><Input data-testid="conv-date" type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                                <Fld label="Channel">
                                    <Select value={form.channel} onValueChange={(v) => setForm({ ...form, channel: v })}>
                                        <SelectTrigger data-testid="conv-channel" className="bg-slate-950 border-slate-800 rounded-none"><SelectValue /></SelectTrigger>
                                        <SelectContent className="bg-slate-900 border-slate-800 rounded-none">
                                            {["meeting", "call", "email", "event", "intro"].map((x) => <SelectItem key={x} value={x} className="capitalize rounded-none focus:bg-slate-800">{x}</SelectItem>)}
                                        </SelectContent>
                                    </Select>
                                </Fld>
                            </div>
                            <Fld label="Attendees"><Input data-testid="conv-attendees" value={form.attendees} onChange={(e) => setForm({ ...form, attendees: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            <Fld label="Summary"><Textarea data-testid="conv-summary" rows={3} value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            <Fld label="Next steps"><Textarea data-testid="conv-next" rows={2} value={form.next_steps} onChange={(e) => setForm({ ...form, next_steps: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            <Fld label="Sentiment">
                                <Select value={form.sentiment} onValueChange={(v) => setForm({ ...form, sentiment: v })}>
                                    <SelectTrigger data-testid="conv-sentiment" className="bg-slate-950 border-slate-800 rounded-none"><SelectValue /></SelectTrigger>
                                    <SelectContent className="bg-slate-900 border-slate-800 rounded-none">
                                        {["positive", "neutral", "negative"].map((x) => <SelectItem key={x} value={x} className="capitalize rounded-none focus:bg-slate-800">{x}</SelectItem>)}
                                    </SelectContent>
                                </Select>
                            </Fld>
                        </div>
                        <DialogFooter><Button data-testid="submit-conversation" onClick={create} className="rounded-none bg-indigo-600 hover:bg-indigo-500">Save</Button></DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
            {items.length === 0 ? <EmptyState title="No conversations yet" description="Log intros, calls, meetings, and follow-ups to build a running memory." /> : (
                <div className="border border-slate-800">
                    {items.map((c) => (
                        <div key={c.id} className="border-b border-slate-800 last:border-b-0 p-4 hover:bg-slate-900 transition-colors duration-150">
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-3 text-xs">
                                    <span className="font-mono-data text-slate-400">{c.date}</span>
                                    <span className="uppercase tracking-[0.2em] text-slate-500">{c.channel}</span>
                                    {c.sentiment && <span className={`text-[10px] uppercase tracking-[0.2em] px-1.5 py-0.5 border ${c.sentiment === "positive" ? "text-emerald-300 border-emerald-500/30 bg-emerald-500/10" : c.sentiment === "negative" ? "text-rose-300 border-rose-500/30 bg-rose-500/10" : "text-slate-400 border-slate-700 bg-slate-800/40"}`}>{c.sentiment}</span>}
                                </div>
                                <span className="text-xs text-slate-500">{c.attendees}</span>
                            </div>
                            <div className="text-sm text-slate-200 whitespace-pre-wrap">{c.summary}</div>
                            {c.next_steps && <div className="mt-2 text-xs text-indigo-300"><span className="uppercase tracking-[0.2em] text-slate-500">Next → </span>{c.next_steps}</div>}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function DiligencePanel({ companyId, fundId, items, reload }) {
    const [open, setOpen] = useState(false);
    const [form, setForm] = useState({ category: "Legal", item: "", owner: "", status: "not_started", due_date: "", notes: "" });

    const create = async () => {
        if (!form.item.trim()) { toast.error("Item required"); return; }
        await api.post(`/diligence`, { ...form, fund_id: fundId, company_id: companyId });
        toast.success("Diligence item added");
        setOpen(false);
        setForm({ category: "Legal", item: "", owner: "", status: "not_started", due_date: "", notes: "" });
        reload();
    };

    const setStatus = async (id, status) => {
        await api.patch(`/diligence/${id}`, { status });
        reload();
    };
    const remove = async (id) => { await api.delete(`/diligence/${id}`); reload(); };

    const grouped = DILIGENCE_CATEGORIES.reduce((a, cat) => ({ ...a, [cat]: items.filter((i) => i.category === cat) }), {});

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">{items.length} items · {items.filter((i) => i.status === "complete").length} complete</div>
                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger asChild>
                        <Button data-testid="new-diligence" className="rounded-none h-8 bg-indigo-600 hover:bg-indigo-500 gap-2"><Plus size={12} /> Add item</Button>
                    </DialogTrigger>
                    <DialogContent className="bg-slate-900 border-slate-800 rounded-none max-w-lg">
                        <DialogHeader><DialogTitle className="font-display tracking-tight">New diligence item</DialogTitle></DialogHeader>
                        <div className="space-y-3">
                            <Fld label="Category">
                                <Select value={form.category} onValueChange={(v) => setForm({ ...form, category: v })}>
                                    <SelectTrigger data-testid="dil-category" className="bg-slate-950 border-slate-800 rounded-none"><SelectValue /></SelectTrigger>
                                    <SelectContent className="bg-slate-900 border-slate-800 rounded-none">
                                        {DILIGENCE_CATEGORIES.map((c) => <SelectItem key={c} value={c} className="rounded-none focus:bg-slate-800">{c}</SelectItem>)}
                                    </SelectContent>
                                </Select>
                            </Fld>
                            <Fld label="Item"><Input data-testid="dil-item" value={form.item} onChange={(e) => setForm({ ...form, item: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            <div className="grid grid-cols-2 gap-3">
                                <Fld label="Owner"><Input data-testid="dil-owner" value={form.owner} onChange={(e) => setForm({ ...form, owner: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                                <Fld label="Due"><Input data-testid="dil-due" type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            </div>
                            <Fld label="Notes"><Textarea data-testid="dil-notes" rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                        </div>
                        <DialogFooter><Button data-testid="submit-diligence" onClick={create} className="rounded-none bg-indigo-600 hover:bg-indigo-500">Add</Button></DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
            {items.length === 0 ? <EmptyState title="Diligence checklist empty" description="Add items across Legal, Financial, Tech, Market, and Team categories." /> : (
                <div className="space-y-6">
                    {DILIGENCE_CATEGORIES.map((cat) => grouped[cat].length > 0 && (
                        <div key={cat}>
                            <div className="text-[10px] uppercase tracking-[0.3em] text-indigo-400 mb-2">{cat}</div>
                            <div className="border border-slate-800">
                                {grouped[cat].map((d) => (
                                    <div key={d.id} className="grid grid-cols-12 items-center border-b border-slate-800 last:border-b-0 px-4 py-3 hover:bg-slate-900 transition-colors duration-150">
                                        <div className="col-span-5 text-sm text-slate-100">{d.item}{d.notes && <div className="text-xs text-slate-500 mt-1">{d.notes}</div>}</div>
                                        <div className="col-span-2 text-xs text-slate-400">{d.owner || "—"}</div>
                                        <div className="col-span-2 text-xs font-mono-data text-slate-400">{d.due_date || "—"}</div>
                                        <div className="col-span-2">
                                            <Select value={d.status} onValueChange={(v) => setStatus(d.id, v)}>
                                                <SelectTrigger data-testid={`dil-status-${d.id}`} className="bg-slate-950 border-slate-800 rounded-none h-8 text-xs"><SelectValue /></SelectTrigger>
                                                <SelectContent className="bg-slate-900 border-slate-800 rounded-none">
                                                    {DILIGENCE_STATUSES.map((s) => <SelectItem key={s} value={s} className="rounded-none focus:bg-slate-800 text-xs">{s.replace("_", " ")}</SelectItem>)}
                                                </SelectContent>
                                            </Select>
                                        </div>
                                        <div className="col-span-1 flex justify-end">
                                            <button data-testid={`delete-dil-${d.id}`} onClick={() => remove(d.id)} className="text-slate-600 hover:text-rose-400 transition-colors duration-150"><Trash size={14} /></button>
                                        </div>
                                        <div className="col-span-12 mt-2"><StatusPill status={d.status} /></div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function InvestmentsPanel({ companyId, fundId, items, reload }) {
    const [open, setOpen] = useState(false);
    const [expanded, setExpanded] = useState(null);
    const [form, setForm] = useState({ amount: "", round_stage: "", valuation: "", ownership_pct: "", close_date: "", board_seat: false, pro_rata: false, current_value: "", notes: "" });
    const [flowForm, setFlowForm] = useState({ date: new Date().toISOString().slice(0, 10), amount: "", kind: "distribution" });

    const create = async () => {
        if (!form.amount) { toast.error("Amount required"); return; }
        const payload = {
            fund_id: fundId, company_id: companyId,
            amount: Number(form.amount),
            round_stage: form.round_stage || null,
            valuation: form.valuation ? Number(form.valuation) : null,
            ownership_pct: form.ownership_pct ? Number(form.ownership_pct) : null,
            close_date: form.close_date || null,
            board_seat: !!form.board_seat, pro_rata: !!form.pro_rata,
            current_value: form.current_value ? Number(form.current_value) : null,
            notes: form.notes || null,
        };
        await api.post(`/investments`, payload);
        toast.success("Investment recorded");
        setOpen(false);
        setForm({ amount: "", round_stage: "", valuation: "", ownership_pct: "", close_date: "", board_seat: false, pro_rata: false, current_value: "", notes: "" });
        reload();
    };

    const remove = async (id) => { await api.delete(`/investments/${id}`); reload(); };

    const updateMark = async (id, cv) => {
        await api.patch(`/investments/${id}`, { current_value: cv === "" ? null : Number(cv) });
        reload();
    };

    const addFlow = async (invId) => {
        if (!flowForm.amount || !flowForm.date) { toast.error("Date and amount required"); return; }
        let amt = Number(flowForm.amount);
        if (flowForm.kind === "call" && amt > 0) amt = -amt;
        if (flowForm.kind === "distribution" && amt < 0) amt = Math.abs(amt);
        await api.post(`/investments/${invId}/cash-flows`, { date: flowForm.date, amount: amt, kind: flowForm.kind });
        setFlowForm({ date: new Date().toISOString().slice(0, 10), amount: "", kind: "distribution" });
        reload();
    };

    const removeFlow = async (invId, idx) => {
        await api.delete(`/investments/${invId}/cash-flows/${idx}`);
        reload();
    };

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">{items.length} rounds</div>
                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger asChild>
                        <Button data-testid="new-investment" className="rounded-none h-8 bg-indigo-600 hover:bg-indigo-500 gap-2"><Plus size={12} /> Record investment</Button>
                    </DialogTrigger>
                    <DialogContent className="bg-slate-900 border-slate-800 rounded-none max-w-lg">
                        <DialogHeader><DialogTitle className="font-display tracking-tight">New investment</DialogTitle></DialogHeader>
                        <div className="grid grid-cols-2 gap-3">
                            <Fld label="Amount ($)"><Input data-testid="inv-amount" type="number" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none font-mono-data" /></Fld>
                            <Fld label="Round"><Input data-testid="inv-round" value={form.round_stage} onChange={(e) => setForm({ ...form, round_stage: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            <Fld label="Valuation ($)"><Input data-testid="inv-valuation" type="number" value={form.valuation} onChange={(e) => setForm({ ...form, valuation: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none font-mono-data" /></Fld>
                            <Fld label="Ownership %"><Input data-testid="inv-ownership" type="number" step="0.01" value={form.ownership_pct} onChange={(e) => setForm({ ...form, ownership_pct: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none font-mono-data" /></Fld>
                            <Fld label="Close date"><Input data-testid="inv-close" type="date" value={form.close_date} onChange={(e) => setForm({ ...form, close_date: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            <Fld label="Current value ($)"><Input data-testid="inv-current" type="number" value={form.current_value} onChange={(e) => setForm({ ...form, current_value: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none font-mono-data" /></Fld>
                            <label className="flex items-center gap-2 text-sm text-slate-300"><input data-testid="inv-board" type="checkbox" checked={form.board_seat} onChange={(e) => setForm({ ...form, board_seat: e.target.checked })} /> Board seat</label>
                            <label className="flex items-center gap-2 text-sm text-slate-300"><input data-testid="inv-prorata" type="checkbox" checked={form.pro_rata} onChange={(e) => setForm({ ...form, pro_rata: e.target.checked })} /> Pro-rata rights</label>
                            <div className="col-span-2"><Fld label="Notes"><Textarea data-testid="inv-notes" rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld></div>
                        </div>
                        <DialogFooter><Button data-testid="submit-investment" onClick={create} className="rounded-none bg-indigo-600 hover:bg-indigo-500">Save</Button></DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
            {items.length === 0 ? <EmptyState title="No investment yet" description="Record the check size, round, valuation and terms when this deal closes." /> : (
                <div className="space-y-4">
                    {items.map((i) => {
                        const flows = i.cash_flows || [];
                        const totalDist = flows.filter((f) => f.amount > 0).reduce((a, f) => a + f.amount, 0);
                        const totalCalled = flows.filter((f) => f.amount < 0).reduce((a, f) => a + Math.abs(f.amount), 0);
                        const cvOrAmt = i.current_value ?? i.amount;
                        const moic = i.amount ? cvOrAmt / i.amount : 0;
                        const isOpen = expanded === i.id;
                        return (
                            <div key={i.id} className="border border-slate-800">
                                <div className="grid grid-cols-12 items-center px-4 py-3 border-b border-slate-800 hover:bg-slate-900 transition-colors duration-150">
                                    <div className="col-span-2 text-sm text-slate-200">{i.round_stage || "—"}</div>
                                    <div className="col-span-2 text-right font-mono-data text-slate-50">{formatMoney(i.amount)}</div>
                                    <div className="col-span-2 text-right font-mono-data text-slate-400">{formatMoney(i.valuation)}</div>
                                    <div className="col-span-2 text-right font-mono-data text-slate-400">{i.ownership_pct != null ? `${i.ownership_pct}%` : "—"}</div>
                                    <div className="col-span-2 font-mono-data text-slate-400 text-sm">{i.close_date || "—"}</div>
                                    <div className="col-span-1 text-right font-mono-data text-emerald-400">{formatMoney(i.current_value)}</div>
                                    <div className="col-span-1 flex justify-end gap-2">
                                        <button data-testid={`toggle-flows-${i.id}`} onClick={() => setExpanded(isOpen ? null : i.id)}
                                                className="text-xs uppercase tracking-[0.2em] text-indigo-400 hover:text-indigo-300 transition-colors duration-150 px-2">
                                            {isOpen ? "−" : "+"}
                                        </button>
                                        <button data-testid={`delete-inv-${i.id}`} onClick={() => remove(i.id)} className="text-slate-600 hover:text-rose-400 transition-colors duration-150"><Trash size={14} /></button>
                                    </div>
                                </div>
                                {isOpen && (
                                    <div className="p-4 bg-slate-900/40 space-y-4">
                                        <div className="grid grid-cols-4 gap-px bg-slate-800">
                                            <div className="bg-slate-950 p-3">
                                                <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">Called</div>
                                                <div className="font-mono-data text-lg text-slate-50 mt-1">{formatMoney(totalCalled || i.amount)}</div>
                                            </div>
                                            <div className="bg-slate-950 p-3">
                                                <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">Distributed</div>
                                                <div className="font-mono-data text-lg text-emerald-400 mt-1">{formatMoney(totalDist)}</div>
                                            </div>
                                            <div className="bg-slate-950 p-3">
                                                <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">Current Mark</div>
                                                <input
                                                    data-testid={`inv-mark-${i.id}`}
                                                    type="number"
                                                    defaultValue={i.current_value ?? ""}
                                                    onBlur={(e) => updateMark(i.id, e.target.value)}
                                                    placeholder="0"
                                                    className="mt-1 w-full bg-slate-900 border border-slate-800 focus:border-indigo-500 outline-none px-2 py-1 text-lg font-mono-data text-slate-50"
                                                />
                                            </div>
                                            <div className="bg-slate-950 p-3">
                                                <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">MOIC</div>
                                                <div className={`font-mono-data text-lg mt-1 ${moic >= 1 ? "text-emerald-400" : "text-rose-400"}`}>
                                                    {i.amount ? `${moic.toFixed(2)}x` : "—"}
                                                </div>
                                            </div>
                                        </div>

                                        <div>
                                            <div className="text-[10px] uppercase tracking-[0.3em] text-indigo-400 mb-2">Cash Flow Schedule</div>
                                            {flows.length === 0 ? (
                                                <div className="text-xs text-slate-500 mb-3">No flows yet. Add capital calls and distributions below.</div>
                                            ) : (
                                                <div className="border border-slate-800 mb-3">
                                                    {flows.map((f, idx) => (
                                                        <div key={idx} className="grid grid-cols-12 items-center px-3 py-2 border-b border-slate-800 last:border-b-0 hover:bg-slate-900 transition-colors duration-150">
                                                            <div className="col-span-3 font-mono-data text-xs text-slate-300">{f.date}</div>
                                                            <div className="col-span-3 text-xs uppercase tracking-[0.2em] text-slate-500">{f.kind || (f.amount < 0 ? "call" : "distribution")}</div>
                                                            <div className={`col-span-5 text-right font-mono-data text-sm ${f.amount < 0 ? "text-rose-400" : "text-emerald-400"}`}>
                                                                {f.amount < 0 ? "−" : "+"}{formatMoney(Math.abs(f.amount))}
                                                            </div>
                                                            <div className="col-span-1 flex justify-end">
                                                                <button data-testid={`del-flow-${i.id}-${idx}`} onClick={() => removeFlow(i.id, idx)} className="text-slate-600 hover:text-rose-400 transition-colors duration-150"><Trash size={12} /></button>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                            <div className="grid grid-cols-12 gap-2 items-end">
                                                <div className="col-span-3">
                                                    <Label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Date</Label>
                                                    <Input data-testid={`flow-date-${i.id}`} type="date" value={flowForm.date} onChange={(e) => setFlowForm({ ...flowForm, date: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none h-9" />
                                                </div>
                                                <div className="col-span-3">
                                                    <Label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Kind</Label>
                                                    <Select value={flowForm.kind} onValueChange={(v) => setFlowForm({ ...flowForm, kind: v })}>
                                                        <SelectTrigger data-testid={`flow-kind-${i.id}`} className="bg-slate-950 border-slate-800 rounded-none h-9"><SelectValue /></SelectTrigger>
                                                        <SelectContent className="bg-slate-900 border-slate-800 rounded-none">
                                                            <SelectItem value="call" className="rounded-none focus:bg-slate-800">Capital call</SelectItem>
                                                            <SelectItem value="distribution" className="rounded-none focus:bg-slate-800">Distribution</SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                </div>
                                                <div className="col-span-4">
                                                    <Label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Amount ($)</Label>
                                                    <Input data-testid={`flow-amount-${i.id}`} type="number" value={flowForm.amount} onChange={(e) => setFlowForm({ ...flowForm, amount: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none h-9 font-mono-data" />
                                                </div>
                                                <Button data-testid={`add-flow-${i.id}`} onClick={() => addFlow(i.id)} className="col-span-2 rounded-none h-9 bg-indigo-600 hover:bg-indigo-500 text-white transition-colors duration-150">Add</Button>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

function ContactsPanel({ companyId, fundId, items, reload }) {
    const [open, setOpen] = useState(false);
    const [form, setForm] = useState({ name: "", role: "founder", title: "", email: "", phone: "", linkedin: "", notes: "" });

    const create = async () => {
        if (!form.name.trim()) { toast.error("Name required"); return; }
        await api.post(`/contacts`, { ...form, fund_id: fundId, company_id: companyId });
        toast.success("Contact added");
        setOpen(false);
        setForm({ name: "", role: "founder", title: "", email: "", phone: "", linkedin: "", notes: "" });
        reload();
    };
    const remove = async (id) => { await api.delete(`/contacts/${id}`); reload(); };

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">{items.length} people</div>
                <Dialog open={open} onOpenChange={setOpen}>
                    <DialogTrigger asChild>
                        <Button data-testid="new-contact" className="rounded-none h-8 bg-indigo-600 hover:bg-indigo-500 gap-2"><Plus size={12} /> Add contact</Button>
                    </DialogTrigger>
                    <DialogContent className="bg-slate-900 border-slate-800 rounded-none max-w-lg">
                        <DialogHeader><DialogTitle className="font-display tracking-tight">New contact</DialogTitle></DialogHeader>
                        <div className="grid grid-cols-2 gap-3">
                            <Fld label="Name"><Input data-testid="ct-name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            <Fld label="Role">
                                <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
                                    <SelectTrigger data-testid="ct-role" className="bg-slate-950 border-slate-800 rounded-none"><SelectValue /></SelectTrigger>
                                    <SelectContent className="bg-slate-900 border-slate-800 rounded-none">
                                        {["founder", "co-investor", "lp", "advisor", "other"].map((r) => <SelectItem key={r} value={r} className="rounded-none focus:bg-slate-800 capitalize">{r}</SelectItem>)}
                                    </SelectContent>
                                </Select>
                            </Fld>
                            <Fld label="Title"><Input data-testid="ct-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            <Fld label="Email"><Input data-testid="ct-email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            <Fld label="Phone"><Input data-testid="ct-phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            <Fld label="LinkedIn"><Input data-testid="ct-linkedin" value={form.linkedin} onChange={(e) => setForm({ ...form, linkedin: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld>
                            <div className="col-span-2"><Fld label="Notes"><Textarea data-testid="ct-notes" rows={2} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className="bg-slate-950 border-slate-800 rounded-none" /></Fld></div>
                        </div>
                        <DialogFooter><Button data-testid="submit-contact" onClick={create} className="rounded-none bg-indigo-600 hover:bg-indigo-500">Save</Button></DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
            {items.length === 0 ? <EmptyState title="No contacts linked" description="Add founders, advisors and co-investors tied to this company." /> : (
                <div className="border border-slate-800">
                    {items.map((c) => (
                        <div key={c.id} className="grid grid-cols-12 items-center px-4 py-3 border-b border-slate-800 last:border-b-0 hover:bg-slate-900 transition-colors duration-150">
                            <div className="col-span-3"><div className="font-display text-slate-50 tracking-tight">{c.name}</div><div className="text-xs text-slate-500 capitalize">{c.role}</div></div>
                            <div className="col-span-3 text-sm text-slate-300">{c.title || "—"}</div>
                            <div className="col-span-3 text-sm text-slate-400 font-mono-data truncate">{c.email || "—"}</div>
                            <div className="col-span-2 text-sm text-slate-400 font-mono-data">{c.phone || "—"}</div>
                            <div className="col-span-1 flex justify-end"><button data-testid={`delete-ct-${c.id}`} onClick={() => remove(c.id)} className="text-slate-600 hover:text-rose-400 transition-colors duration-150"><Trash size={14} /></button></div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function Fld({ label, children }) {
    return (
        <div>
            <Label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">{label}</Label>
            <div className="mt-2">{children}</div>
        </div>
    );
}
