import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

const FundContext = createContext(null);

export function FundProvider({ children }) {
    const [funds, setFunds] = useState([]);
    const [activeFund, setActiveFund] = useState(null);
    const [loading, setLoading] = useState(true);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const { data } = await api.get("/funds");
            setFunds(data);
            const stored = localStorage.getItem("activeFundId");
            const found = data.find((f) => f.id === stored) || data[0] || null;
            setActiveFund(found);
        } catch {
            setFunds([]);
            setActiveFund(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    const switchFund = (id) => {
        const f = funds.find((x) => x.id === id);
        if (f) {
            setActiveFund(f);
            localStorage.setItem("activeFundId", id);
        }
    };

    return (
        <FundContext.Provider value={{ funds, activeFund, switchFund, loading, reload: load }}>
            {children}
        </FundContext.Provider>
    );
}

export const useFund = () => useContext(FundContext);
