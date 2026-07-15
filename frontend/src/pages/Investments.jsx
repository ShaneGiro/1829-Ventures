import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useFund } from "@/context/FundContext";
import { api } from "@/lib/api";
import { PageHeader, EmptyState, formatMoney } from "@/components/ui-primitives";

export default function Investments() {
    const { activeFund } = useFund();
    const [items, setItems] = useState([]);
    const [companies, setCompanies] = useState({});

    const load = async () => {
        if (!activeFund) return;
        const [inv, co] = await Promise.all([
            api.get(`/investments`, { params: { fund_id: activeFund.id } }),
            api.get(`/companies`, { params: { fund_id: activeFund.id } }),
        ]);
        setItems(inv.data);
        setCompanies(Object.fromEntries(co.data.map((c) => [c.id, c.name])));
    };
    useEffect(() => { load(); }, [activeFund]); // eslint-disable-line

    const totalInvested = items.reduce((a, i) => a + (i.amount || 0), 0);
    const totalCurrent = items.reduce((a, i) => a + (i.current_value ?? i.amount ?? 0), 0);

    return (
        <div>
            <PageHeader
                testid="investments-header"
                overline={activeFund?.name}
                title="Investments"
                subtitle={`${items.length} rounds · ${formatMoney(totalInvested)} deployed · current mark ${formatMoney(totalCurrent)}`}
            />
            {items.length === 0 ? (
                <div className="p-8"><EmptyState title="No investments recorded" description="Move a company to Invested stage and record the check from its Investment tab." /></div>
            ) : (
                <div>
                    <div className="grid grid-cols-12 px-6 md:px-8 py-3 border-b border-slate-800 text-[10px] uppercase tracking-[0.25em] text-slate-500 font-mono-data">
                        <div className="col-span-3">Company</div>
                        <div className="col-span-2">Round</div>
                        <div className="col-span-2 text-right">Amount</div>
                        <div className="col-span-2 text-right">Valuation</div>
                        <div className="col-span-1 text-right">Own %</div>
                        <div className="col-span-2">Close</div>
                    </div>
                    {items.map((i) => (
                        <Link
                            to={`/companies/${i.company_id}`}
                            key={i.id}
                            data-testid={`investment-row-${i.id}`}
                            className="grid grid-cols-12 items-center px-6 md:px-8 py-3 border-b border-slate-800 hover:bg-slate-900 transition-colors duration-150"
                        >
                            <div className="col-span-3 font-display tracking-tight text-slate-50">{companies[i.company_id] || "—"}</div>
                            <div className="col-span-2 text-sm text-slate-300">{i.round_stage || "—"}</div>
                            <div className="col-span-2 text-right font-mono-data text-slate-50">{formatMoney(i.amount)}</div>
                            <div className="col-span-2 text-right font-mono-data text-slate-400">{formatMoney(i.valuation)}</div>
                            <div className="col-span-1 text-right font-mono-data text-slate-400">{i.ownership_pct != null ? `${i.ownership_pct}%` : "—"}</div>
                            <div className="col-span-2 font-mono-data text-slate-400 text-sm">{i.close_date || "—"}</div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}
