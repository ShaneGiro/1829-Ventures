import React, { useEffect, useState } from "react";
import { CommandDialog, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem } from "@/components/ui/command";
import { useFund } from "@/context/FundContext";
import { api } from "@/lib/api";
import { useNavigate } from "react-router-dom";

export default function GlobalSearch({ open, onOpenChange }) {
    const { activeFund } = useFund();
    const [q, setQ] = useState("");
    const [results, setResults] = useState({ companies: [], contacts: [], conversations: [] });
    const nav = useNavigate();

    useEffect(() => {
        const handler = (e) => {
            if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
                e.preventDefault();
                onOpenChange(true);
            }
        };
        window.addEventListener("keydown", handler);
        return () => window.removeEventListener("keydown", handler);
    }, [onOpenChange]);

    useEffect(() => {
        if (!open || !activeFund) return;
        if (!q) {
            setResults({ companies: [], contacts: [], conversations: [] });
            return;
        }
        const t = setTimeout(async () => {
            try {
                const { data } = await api.get(`/search`, { params: { q, fund_id: activeFund.id } });
                setResults(data);
            } catch { /* noop */ }
        }, 200);
        return () => clearTimeout(t);
    }, [q, open, activeFund]);

    const go = (path) => {
        onOpenChange(false);
        setQ("");
        nav(path);
    };

    return (
        <CommandDialog open={open} onOpenChange={onOpenChange}>
            <CommandInput
                data-testid="global-search-input"
                placeholder="Search companies, contacts, conversations…"
                value={q}
                onValueChange={setQ}
            />
            <CommandList>
                <CommandEmpty>No results.</CommandEmpty>
                {results.companies.length > 0 && (
                    <CommandGroup heading="Companies">
                        {results.companies.map((c) => (
                            <CommandItem key={c.id} onSelect={() => go(`/companies/${c.id}`)} value={`c-${c.id}-${c.name}`}>
                                <span className="font-display">{c.name}</span>
                                {c.one_liner && <span className="ml-3 text-slate-500 text-xs truncate">{c.one_liner}</span>}
                            </CommandItem>
                        ))}
                    </CommandGroup>
                )}
                {results.contacts.length > 0 && (
                    <CommandGroup heading="Contacts">
                        {results.contacts.map((c) => (
                            <CommandItem key={c.id} onSelect={() => go(`/contacts`)} value={`ct-${c.id}-${c.name}`}>
                                <span>{c.name}</span>
                                {c.title && <span className="ml-3 text-slate-500 text-xs">{c.title}</span>}
                            </CommandItem>
                        ))}
                    </CommandGroup>
                )}
                {results.conversations.length > 0 && (
                    <CommandGroup heading="Conversations">
                        {results.conversations.map((c) => (
                            <CommandItem key={c.id} onSelect={() => go(`/conversations`)} value={`cv-${c.id}-${c.summary}`}>
                                <span className="truncate">{c.summary}</span>
                            </CommandItem>
                        ))}
                    </CommandGroup>
                )}
            </CommandList>
        </CommandDialog>
    );
}
