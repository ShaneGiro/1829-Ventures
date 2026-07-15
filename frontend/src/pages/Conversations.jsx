import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useFund } from "@/context/FundContext";
import { api } from "@/lib/api";
import { PageHeader, EmptyState } from "@/components/ui-primitives";
import { Trash } from "@phosphor-icons/react";

export default function Conversations() {
    const { activeFund } = useFund();
    const [items, setItems] = useState([]);
    const [companies, setCompanies] = useState({});

    const load = async () => {
        if (!activeFund) return;
        const [cv, co] = await Promise.all([
            api.get(`/conversations`, { params: { fund_id: activeFund.id } }),
            api.get(`/companies`, { params: { fund_id: activeFund.id } }),
        ]);
        setItems(cv.data);
        setCompanies(Object.fromEntries(co.data.map((c) => [c.id, c.name])));
    };
    useEffect(() => { load(); }, [activeFund]); // eslint-disable-line

    const remove = async (id) => { await api.delete(`/conversations/${id}`); load(); };

    return (
        <div>
            <PageHeader
                testid="conversations-header"
                overline={activeFund?.name}
                title="Conversations"
                subtitle="A running log of intros, calls, and meetings across the pipeline."
            />
            {items.length === 0 ? (
                <div className="p-8"><EmptyState title="No conversations logged" description="Open any company and log your first conversation to build institutional memory." /></div>
            ) : (
                <div>
                    {items.map((c) => (
                        <div key={c.id} data-testid={`conversation-row-${c.id}`} className="px-6 md:px-8 py-4 border-b border-slate-800 hover:bg-slate-900 transition-colors duration-150">
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-3">
                                    <span className="text-xs font-mono-data text-slate-400">{c.date}</span>
                                    <span className="text-[10px] uppercase tracking-[0.25em] text-slate-500">{c.channel}</span>
                                    {c.company_id && (
                                        <Link to={`/companies/${c.company_id}`} className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors duration-150">
                                            {companies[c.company_id] || "—"}
                                        </Link>
                                    )}
                                </div>
                                <button data-testid={`delete-conv-${c.id}`} onClick={() => remove(c.id)} className="text-slate-600 hover:text-rose-400 transition-colors duration-150"><Trash size={14} /></button>
                            </div>
                            <div className="text-sm text-slate-200 whitespace-pre-wrap">{c.summary}</div>
                            {c.next_steps && <div className="text-xs mt-2 text-indigo-300"><span className="uppercase tracking-[0.2em] text-slate-500">Next → </span>{c.next_steps}</div>}
                            {c.attendees && <div className="text-xs mt-1 text-slate-500">Attendees: {c.attendees}</div>}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
