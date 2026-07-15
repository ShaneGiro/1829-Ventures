import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api, API } from "@/lib/api";
import { toast } from "sonner";
import { UploadSimple, FileCsv, CheckCircle } from "@phosphor-icons/react";
import axios from "axios";

const STAGES = ["sourced", "screening", "diligence", "ic"];

export default function DealroomImport({ open, onOpenChange, fundId, onDone }) {
    const [file, setFile] = useState(null);
    const [defaultStage, setDefaultStage] = useState("sourced");
    const [busy, setBusy] = useState(false);
    const [result, setResult] = useState(null);

    const submit = async () => {
        if (!file) { toast.error("Choose a CSV file"); return; }
        setBusy(true);
        setResult(null);
        try {
            const fd = new FormData();
            fd.append("fund_id", fundId);
            fd.append("default_stage", defaultStage);
            fd.append("file", file);
            const { data } = await axios.post(`${API}/import/dealroom`, fd, {
                withCredentials: true,
                headers: { "Content-Type": "multipart/form-data" },
            });
            setResult(data);
            toast.success(`Imported ${data.imported} · updated ${data.updated}`);
            onDone && onDone();
        } catch (e) {
            toast.error(e.response?.data?.detail || "Import failed");
        } finally {
            setBusy(false);
        }
    };

    const reset = () => {
        setFile(null);
        setResult(null);
        onOpenChange(false);
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="bg-slate-900 border-slate-800 rounded-none max-w-lg" aria-describedby="import-desc">
                <DialogHeader>
                    <DialogTitle className="font-display tracking-tight flex items-center gap-2">
                        <FileCsv size={18} className="text-indigo-400" /> Import from Dealroom
                    </DialogTitle>
                    <DialogDescription id="import-desc" className="text-slate-400 text-xs">
                        Upload a Dealroom.co CSV export. Rows are matched by <span className="font-mono-data text-slate-300">Name</span>; new names create companies, existing names update fields (Tagline → one-liner, Long description → notes, Industries → sector, Growth Stage → stage, HQ, Website, Funding).
                    </DialogDescription>
                </DialogHeader>

                {!result ? (
                    <div className="space-y-4">
                        <div>
                            <Label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">CSV file</Label>
                            <label className="mt-2 flex items-center gap-3 px-3 py-6 border border-dashed border-slate-700 bg-slate-950 hover:border-indigo-500 cursor-pointer transition-colors duration-150">
                                <UploadSimple size={18} className="text-slate-500" />
                                <span className="text-sm text-slate-400">
                                    {file ? <span className="text-slate-100 font-mono-data">{file.name}</span> : "Click to select .csv"}
                                </span>
                                <input
                                    data-testid="dealroom-file-input"
                                    type="file"
                                    accept=".csv,text/csv"
                                    className="hidden"
                                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                                />
                            </label>
                        </div>
                        <div>
                            <Label className="text-[10px] uppercase tracking-[0.2em] text-slate-500">Default stage (when Growth Stage is empty)</Label>
                            <Select value={defaultStage} onValueChange={setDefaultStage}>
                                <SelectTrigger data-testid="import-default-stage" className="mt-2 bg-slate-950 border-slate-800 rounded-none h-10">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="bg-slate-900 border-slate-800 rounded-none">
                                    {STAGES.map((s) => <SelectItem key={s} value={s} className="rounded-none focus:bg-slate-800 capitalize">{s}</SelectItem>)}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="text-xs text-slate-500 bg-slate-950 border border-slate-800 p-3">
                            <div className="uppercase tracking-[0.2em] text-slate-400 text-[10px] mb-1">What gets mapped</div>
                            <ul className="space-y-1 list-disc pl-4">
                                <li>Name, Website, Tagline, Long description, HQ city/country</li>
                                <li>Industries → Sector · Growth Stage → Pipeline stage</li>
                                <li>Last round, Last funding amount → Round + Ask</li>
                                <li>Investors, Founders, Total funding, Valuation (kept as Dealroom fields)</li>
                            </ul>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-3">
                        <div className="flex items-center gap-2 text-emerald-400">
                            <CheckCircle size={18} weight="fill" />
                            <span className="font-display text-lg tracking-tight">Import complete</span>
                        </div>
                        <div className="grid grid-cols-3 gap-px bg-slate-800">
                            {["imported", "updated", "skipped"].map((k) => (
                                <div key={k} className="bg-slate-950 p-4">
                                    <div className="text-[10px] uppercase tracking-[0.25em] text-slate-500">{k}</div>
                                    <div className="font-mono-data text-2xl text-slate-50 mt-2">{result[k]}</div>
                                </div>
                            ))}
                        </div>
                        {result.errors && result.errors.length > 0 && (
                            <div className="border border-slate-800 p-3 max-h-40 overflow-auto">
                                <div className="text-[10px] uppercase tracking-[0.2em] text-amber-400 mb-2">Errors ({result.errors.length})</div>
                                {result.errors.map((e, i) => <div key={i} className="text-xs text-slate-400 font-mono-data">{e}</div>)}
                            </div>
                        )}
                    </div>
                )}

                <DialogFooter>
                    {!result ? (
                        <Button data-testid="dealroom-import-submit" onClick={submit} disabled={busy || !file}
                                className="rounded-none bg-indigo-600 hover:bg-indigo-500 h-9 transition-colors duration-150">
                            {busy ? "Importing…" : "Import"}
                        </Button>
                    ) : (
                        <Button data-testid="dealroom-import-close" onClick={reset} className="rounded-none bg-indigo-600 hover:bg-indigo-500">Done</Button>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
