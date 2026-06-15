import { useState } from "react";
import { Link } from "react-router-dom";
import { useCompanies } from "@/api/companies";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { StateNotice } from "@/components/ui/state";

export function CompanyList() {
  const [q, setQ] = useState("");
  const { data, isLoading, isError } = useCompanies({ q: q || undefined, limit: 50 });

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-semibold">Companies</h1>
        <Input
          placeholder="Search…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="w-full sm:w-64"
        />
      </div>
      {isLoading && <StateNotice title="Loading companies" />}
      {isError && (
        <StateNotice
          title="Could not load companies"
          description="Refresh the page or check the API connection."
          variant="error"
        />
      )}
      {data && (
        <div className="overflow-x-auto rounded-lg border">
          <table className="min-w-[720px] w-full text-sm">
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
