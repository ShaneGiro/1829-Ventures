import React, { useEffect, useState } from "react";
import { useFund } from "@/context/FundContext";
import { api } from "@/lib/api";
import { PageHeader, EmptyState } from "@/components/ui-primitives";
import { Trash } from "@phosphor-icons/react";

export default function Contacts() {
    const { activeFund } = useFund();
    const [items, setItems] = useState([]);
    const [companies, setCompanies] = useState({});

    const load = async () => {
        if (!activeFund) return;
        const [ct, co] = await Promise.all([
            api.get(`/contacts`, { params: { fund_id: activeFund.id } }),
            api.get(`/companies`, { params: { fund_id: activeFund.id } }),
        ]);
        setItems(ct.data);
        setCompanies(Object.fromEntries(co.data.map((c) => [c.id, c.name])));
    };
    useEffect(() => { load(); }, [activeFund]); // eslint-disable-line

    const remove = async (id) => { await api.delete(`/contacts/${id}`); load(); };

    return (
        <div>
            <PageHeader
                testid="contacts-header"
                overline={activeFund?.name}
                title="Contacts"
                subtitle="Founders, co-investors, LPs, and advisors. Add contacts from any company detail page."
            />
            {items.length === 0 ? (
                <div className="p-8"><EmptyState title="No contacts yet" description="Open a company and add founders or co-investors from its Contacts tab." /></div>
            ) : (
                <div>
                    <div className="grid grid-cols-12 px-6 md:px-8 py-3 border-b border-slate-800 text-[10px] uppercase tracking-[0.25em] text-slate-500 font-mono-data">
                        <div className="col-span-3">Name</div>
                        <div className="col-span-2">Role</div>
                        <div className="col-span-3">Company</div>
                        <div className="col-span-3">Email</div>
                        <div className="col-span-1"></div>
                    </div>
                    {items.map((c) => (
                        <div key={c.id} data-testid={`contact-row-${c.id}`} className="grid grid-cols-12 items-center px-6 md:px-8 py-3 border-b border-slate-800 hover:bg-slate-900 transition-colors duration-150">
                            <div className="col-span-3"><div className="font-display text-slate-50 tracking-tight">{c.name}</div><div className="text-xs text-slate-500">{c.title || "—"}</div></div>
                            <div className="col-span-2 text-sm text-slate-300 capitalize">{c.role || "—"}</div>
                            <div className="col-span-3 text-sm text-slate-300">{companies[c.company_id] || "—"}</div>
                            <div className="col-span-3 text-sm text-slate-400 font-mono-data truncate">{c.email || "—"}</div>
                            <div className="col-span-1 flex justify-end"><button data-testid={`delete-contact-${c.id}`} onClick={() => remove(c.id)} className="text-slate-600 hover:text-rose-400 transition-colors duration-150"><Trash size={14} /></button></div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
