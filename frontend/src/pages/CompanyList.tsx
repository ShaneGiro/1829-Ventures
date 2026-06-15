import { useState } from "react";
import { Link } from "react-router-dom";
import { useCompanies } from "@/api/companies";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

export function CompanyList() {
  const [q, setQ] = useState("");
  const { data, isLoading, isError } = useCompanies({ q: q || undefined, limit: 50 });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Companies</h1>
        <Input
          placeholder="Search…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="w-64"
        />
      </div>
      {isLoading && <p className="text-sm text-muted-foreground">Loading…</p>}
      {isError && <p className="text-sm text-muted-foreground">Could not load companies.</p>}
      {data && (
        <div className="overflow-hidden rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted/40 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Sector</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Complete</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((c) => (
                <tr key={c.id} className="border-t hover:bg-accent/40">
                  <td className="px-4 py-2 font-medium">
                    <Link to={`/companies/${c.id}`} className="hover:underline">
                      {c.name}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">{c.sector ?? "—"}</td>
                  <td className="px-4 py-2">
                    <Badge>{c.relationship_status}</Badge>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {Math.round((c.completeness_pct ?? 0))}%
                  </td>
                </tr>
              ))}
              {data.items.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-muted-foreground">
                    No companies found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
