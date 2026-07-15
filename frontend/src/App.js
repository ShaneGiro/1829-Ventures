import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { FundProvider } from "@/context/FundContext";
import { Toaster } from "@/components/ui/sonner";

import Login from "@/pages/Login";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import Companies from "@/pages/Companies";
import CompanyDetail from "@/pages/CompanyDetail";
import Contacts from "@/pages/Contacts";
import Conversations from "@/pages/Conversations";
import Investments from "@/pages/Investments";

function ProtectedRoute({ children }) {
    const { user } = useAuth();
    if (user === null) {
        return (
            <div className="min-h-screen flex items-center justify-start px-10 bg-slate-950">
                <div className="text-xs uppercase tracking-[0.3em] text-slate-500">Loading…</div>
            </div>
        );
    }
    if (!user) return <Navigate to="/login" replace />;
    return (
        <FundProvider>
            <Layout>{children}</Layout>
        </FundProvider>
    );
}

function App() {
    return (
        <div className="App">
            <BrowserRouter>
                <AuthProvider>
                    <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route
                            path="/"
                            element={
                                <ProtectedRoute>
                                    <Dashboard />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/companies"
                            element={
                                <ProtectedRoute>
                                    <Companies />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/companies/:id"
                            element={
                                <ProtectedRoute>
                                    <CompanyDetail />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/contacts"
                            element={
                                <ProtectedRoute>
                                    <Contacts />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/conversations"
                            element={
                                <ProtectedRoute>
                                    <Conversations />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/investments"
                            element={
                                <ProtectedRoute>
                                    <Investments />
                                </ProtectedRoute>
                            }
                        />
                    </Routes>
                    <Toaster theme="dark" position="top-right" />
                </AuthProvider>
            </BrowserRouter>
        </div>
    );
}

export default App;
