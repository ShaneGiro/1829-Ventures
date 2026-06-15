import { useState } from "react";
import { Link } from "react-router-dom";
import { usePeople } from "@/api/people";
import { Input } from "@/components/ui/input";
import { StateNotice } from "@/components/ui/state";

export function PeopleList() {
  const [q, setQ] = useState("");
  const { data, isLoading, isError } = usePeople({ q: q || undefined, limit: 50 });

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-semibold">People</h1>
        <Input
          placeholder="Search…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="w-full sm:w-64"
        />
      </div>
      {isLoading && <StateNotice title="Loading people" />}
      {isError && (
        <StateNotice
          title="Could not load people"
          description="Refresh the page or check the API connection."
          variant="error"
        />
      )}
      {data && (
        <div className="overflow-x-auto rounded-lg border">
          <table className="min-w-[640px] w-full text-sm">
            <thead className="bg-muted/40 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Title</th>
                <th className="px-4 py-2">Email</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((p) => (
                <tr key={p.id} className="border-t hover:bg-accent/40">
                  <td className="px-4 py-2 font-medium">
                    <Link to={`/people/${p.id}`} className="hover:underline">
                      {p.full_name}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">{p.title ?? "—"}</td>
                  <td className="px-4 py-2 text-muted-foreground">{p.email ?? "—"}</td>
                </tr>
              ))}
              {data.items.length === 0 && (
                <tr>
                  <td colSpan={3} className="px-4 py-6 text-center text-muted-foreground">
                    No people found.
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
