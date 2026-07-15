import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useFund } from "@/context/FundContext";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
    DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import {
    House, Buildings, Users, ChatCircleText, CurrencyCircleDollar, Vault, SignOut, MagnifyingGlass,
} from "@phosphor-icons/react";
import GlobalSearch from "@/components/GlobalSearch";

const NAV = [
    { to: "/", label: "Overview", icon: House, testid: "nav-overview" },
    { to: "/companies", label: "Companies", icon: Buildings, testid: "nav-companies" },
    { to: "/conversations", label: "Conversations", icon: ChatCircleText, testid: "nav-conversations" },
    { to: "/contacts", label: "Contacts", icon: Users, testid: "nav-contacts" },
    { to: "/investments", label: "Investments", icon: CurrencyCircleDollar, testid: "nav-investments" },
];

export default function Layout({ children }) {
    const { user, logout } = useAuth();
    const { funds, activeFund, switchFund } = useFund();
    const location = useLocation();
    const nav = useNavigate();
    const [searchOpen, setSearchOpen] = useState(false);

    return (
        <div className="min-h-screen flex bg-slate-950 text-slate-50">
            {/* Sidebar */}
            <aside className="w-56 shrink-0 border-r border-slate-800 flex flex-col">
                <div className="h-14 border-b border-slate-800 flex items-center gap-3 px-4">
                    <div className="h-7 w-7 border border-slate-700 flex items-center justify-center">
                        <Vault size={14} weight="regular" className="text-indigo-400" />
                    </div>
                    <div className="font-display text-sm tracking-tight">MERIDIAN</div>
                </div>

                <nav className="flex-1 py-4">
                    {NAV.map((item) => {
                        const active = item.to === "/" ? location.pathname === "/" : location.pathname.startsWith(item.to);
                        const Icon = item.icon;
                        return (
                            <Link
                                key={item.to}
                                to={item.to}
                                data-testid={item.testid}
                                className={`flex items-center gap-3 px-4 py-2.5 text-sm border-l-2 transition-colors duration-150 ${
                                    active
                                        ? "border-indigo-500 text-slate-50 bg-slate-900"
                                        : "border-transparent text-slate-400 hover:text-slate-50 hover:bg-slate-900"
                                }`}
                            >
                                <Icon size={16} weight={active ? "fill" : "regular"} />
                                <span>{item.label}</span>
                            </Link>
                        );
                    })}
                </nav>

                <div className="px-4 py-3 border-t border-slate-800 text-[10px] uppercase tracking-[0.25em] text-slate-600 font-mono-data">
                    v1.0 · confidential
                </div>
            </aside>

            {/* Main */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Top bar */}
                <header className="h-14 sticky top-0 z-30 backdrop-blur-xl bg-slate-950/70 border-b border-slate-800 flex items-center px-6 gap-6">
                    <div className="flex items-center gap-3">
                        <span className="text-[10px] uppercase tracking-[0.3em] text-slate-500">Fund</span>
                        <Select value={activeFund?.id || ""} onValueChange={switchFund}>
                            <SelectTrigger
                                data-testid="fund-switcher"
                                className="w-[220px] rounded-none bg-slate-900 border-slate-800 h-9 text-slate-50 font-display tracking-tight"
                            >
                                <SelectValue placeholder="Select fund" />
                            </SelectTrigger>
                            <SelectContent className="bg-slate-900 border-slate-800 rounded-none">
                                {funds.map((f) => (
                                    <SelectItem key={f.id} value={f.id} className="rounded-none focus:bg-slate-800 focus:text-slate-50">
                                        {f.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    <button
                        data-testid="open-search-button"
                        onClick={() => setSearchOpen(true)}
                        className="ml-auto flex items-center gap-3 px-3 h-9 border border-slate-800 bg-slate-900 hover:bg-slate-800 transition-colors duration-150 text-sm text-slate-400"
                    >
                        <MagnifyingGlass size={14} />
                        <span>Search…</span>
                        <span className="ml-6 text-[10px] font-mono-data border border-slate-700 px-1.5 py-0.5 text-slate-500">⌘K</span>
                    </button>

                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button data-testid="user-menu-trigger" variant="ghost" className="h-9 rounded-none border border-slate-800 hover:bg-slate-900 gap-2 text-slate-300">
                                <span className="h-5 w-5 avatar-round bg-indigo-600 text-white text-[10px] flex items-center justify-center font-mono-data">
                                    {(user?.name || user?.email || "U").slice(0, 1).toUpperCase()}
                                </span>
                                <span className="text-sm">{user?.name || user?.email}</span>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-slate-900 border-slate-800 rounded-none">
                            <DropdownMenuItem disabled className="text-xs text-slate-500 font-mono-data">{user?.email}</DropdownMenuItem>
                            <DropdownMenuSeparator className="bg-slate-800" />
                            <DropdownMenuItem
                                data-testid="logout-menu-item"
                                onClick={async () => { await logout(); nav("/login"); }}
                                className="rounded-none focus:bg-slate-800 focus:text-slate-50 cursor-pointer"
                            >
                                <SignOut size={14} className="mr-2" /> Sign out
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </header>

                <main className="flex-1 min-w-0">{children}</main>
            </div>

            <GlobalSearch open={searchOpen} onOpenChange={setSearchOpen} />
        </div>
    );
}
