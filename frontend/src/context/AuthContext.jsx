import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, formatApiErrorDetail } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null); // null=checking, false=unauth, object=auth
    const [error, setError] = useState("");

    const check = useCallback(async () => {
        try {
            const { data } = await api.get("/auth/me");
            setUser(data);
        } catch {
            setUser(false);
        }
    }, []);

    useEffect(() => {
        check();
    }, [check]);

    const login = async (email, password) => {
        setError("");
        try {
            const { data } = await api.post("/auth/login", { email, password });
            setUser(data);
            return true;
        } catch (e) {
            setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
            return false;
        }
    };

    const register = async (email, password, name) => {
        setError("");
        try {
            const { data } = await api.post("/auth/register", { email, password, name });
            setUser(data);
            return true;
        } catch (e) {
            setError(formatApiErrorDetail(e.response?.data?.detail) || e.message);
            return false;
        }
    };

    const logout = async () => {
        try {
            await api.post("/auth/logout");
        } catch {
            /* ignore */
        }
        setUser(false);
    };

    return (
        <AuthContext.Provider value={{ user, login, register, logout, error, setError }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => useContext(AuthContext);
