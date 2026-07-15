import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { ArrowRight, Vault } from "@phosphor-icons/react";

export default function Login() {
    const { login, register, user, error } = useAuth();
    const nav = useNavigate();
    const [mode, setMode] = useState("login");
    const [email, setEmail] = useState("admin@fund.com");
    const [password, setPassword] = useState("admin123");
    const [name, setName] = useState("");
    const [busy, setBusy] = useState(false);

    useEffect(() => {
        if (user && typeof user === "object") nav("/", { replace: true });
    }, [user, nav]);

    const submit = async (e) => {
        e.preventDefault();
        setBusy(true);
        let ok = false;
        if (mode === "login") ok = await login(email, password);
        else ok = await register(email, password, name);
        setBusy(false);
        if (ok) nav("/", { replace: true });
    };

    return (
        <div className="min-h-screen grid grid-cols-1 lg:grid-cols-5 bg-slate-950">
            {/* Left: Form */}
            <div className="lg:col-span-2 flex flex-col justify-between border-r border-slate-800 p-8 lg:p-14">
                <div className="flex items-center gap-3">
                    <div className="h-9 w-9 border border-slate-700 flex items-center justify-center">
                        <Vault size={18} weight="regular" className="text-indigo-400" />
                    </div>
                    <div className="font-display text-lg tracking-tight text-slate-50">MERIDIAN <span className="text-slate-500">/ CRM</span></div>
                </div>

                <div className="max-w-md w-full">
                    <div className="text-xs uppercase tracking-[0.3em] text-slate-500 mb-3">
                        {mode === "login" ? "Authenticated Access" : "Create Account"}
                    </div>
                    <h1 className="font-display text-3xl sm:text-4xl tracking-tighter text-slate-50 mb-10">
                        {mode === "login" ? "Sign in to the fund console." : "Provision a new operator."}
                    </h1>

                    <form onSubmit={submit} className="space-y-5">
                        {mode === "register" && (
                            <div>
                                <Label className="text-xs uppercase tracking-[0.2em] text-slate-500">Name</Label>
                                <Input
                                    data-testid="register-name-input"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="mt-2 bg-slate-900 border-slate-800 h-11 rounded-none focus-visible:ring-1 focus-visible:ring-indigo-500 focus-visible:border-indigo-500"
                                    required
                                />
                            </div>
                        )}
                        <div>
                            <Label className="text-xs uppercase tracking-[0.2em] text-slate-500">Email</Label>
                            <Input
                                data-testid="login-email-input"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="mt-2 bg-slate-900 border-slate-800 h-11 rounded-none focus-visible:ring-1 focus-visible:ring-indigo-500 focus-visible:border-indigo-500"
                                required
                            />
                        </div>
                        <div>
                            <Label className="text-xs uppercase tracking-[0.2em] text-slate-500">Password</Label>
                            <Input
                                data-testid="login-password-input"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="mt-2 bg-slate-900 border-slate-800 h-11 rounded-none focus-visible:ring-1 focus-visible:ring-indigo-500 focus-visible:border-indigo-500"
                                required
                            />
                        </div>

                        {error && (
                            <div data-testid="login-error" className="text-xs text-rose-400 bg-rose-400/10 border border-rose-500/30 px-3 py-2">
                                {error}
                            </div>
                        )}

                        <Button
                            data-testid="login-submit-button"
                            disabled={busy}
                            type="submit"
                            className="w-full h-11 rounded-none bg-indigo-600 hover:bg-indigo-500 text-white font-medium tracking-wide transition-colors duration-150"
                        >
                            {busy ? "Working…" : (mode === "login" ? "Enter Console" : "Create Account")}
                            <ArrowRight size={16} className="ml-2" />
                        </Button>

                        <button
                            data-testid="toggle-auth-mode"
                            type="button"
                            onClick={() => setMode(mode === "login" ? "register" : "login")}
                            className="text-xs uppercase tracking-[0.2em] text-slate-500 hover:text-slate-300 transition-colors duration-150"
                        >
                            {mode === "login" ? "→ Register new operator" : "→ Have an account? Sign in"}
                        </button>
                    </form>
                </div>

                <div className="text-xs text-slate-600 font-mono-data">
                    v1.0 · {new Date().getFullYear()} · Confidential
                </div>
            </div>

            {/* Right: Image */}
            <div
                className="hidden lg:block lg:col-span-3 relative"
                style={{
                    backgroundImage: `url(https://images.pexels.com/photos/7230895/pexels-photo-7230895.jpeg)`,
                    backgroundSize: "cover",
                    backgroundPosition: "center",
                }}
            >
                <div className="absolute inset-0 bg-slate-950/60" />
                <div className="absolute bottom-0 left-0 right-0 p-10 backdrop-blur-xl bg-slate-950/60 border-t border-slate-800">
                    <div className="text-xs uppercase tracking-[0.3em] text-indigo-400 mb-3">Fund Console</div>
                    <div className="font-display text-2xl tracking-tight text-slate-50 max-w-lg">
                        Pipeline, diligence, and portfolio metrics — for the operators shaping Beta Fund and Fund&nbsp;I.
                    </div>
                </div>
            </div>
        </div>
    );
}
