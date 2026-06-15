import { useMemo } from "react";
import { Link } from "react-router-dom";
import { useCompanies } from "@/api/companies";
import { useDeals, useDealStatuses } from "@/api/deals";
import type { Deal } from "@/api/types";
import { Badge } from "@/components/ui/badge";

const UNASSIGNED = "__unassigned__";

export function PipelineBoard() {
  const { data: statuses } = useDealStatuses();
  const { data: deals, isLoading } = useDeals({ limit: 200 });
  const { data: companies } = useCompanies({ limit: 200 });

  const companyName = useMemo(() => {
    const map = new Map<string, string>();
    companies?.items.forEach((c) => map.set(c.id, c.name));
    return map;
  }, [companies]);

  const columns = useMemo(() => {
    const ordered = [...(statuses?.items ?? [])].sort((a, b) => a.sort_order - b.sort_order);
    return [...ordered, { id: UNASSIGNED, name: "Unassigned", sort_order: 999 }];
  }, [statuses]);

  const byStatus = useMemo(() => {
    const groups = new Map<string, Deal[]>();
    deals?.items.forEach((d) => {
      const key = d.deal_status_id ?? UNASSIGNED;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(d);
    });
    return groups;
  }, [deals]);

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading pipeline…</p>;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Pipeline</h1>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {columns.map((col) => {
          const items = byStatus.get(col.id) ?? [];
          return (
            <div key={col.id} className="w-64 shrink-0">
              <div className="mb-2 flex items-center justify-between px-1">
                <span className="text-sm font-medium">{col.name}</span>
                <Badge>{items.length}</Badge>
              </div>
              <div className="space-y-2">
                {items.map((d) => (
                  <Link
                    key={d.id}
                    to={`/companies/${d.company_id}`}
                    className="block rounded-md border bg-background p-3 text-sm hover:bg-accent/40"
                  >
                    <div className="font-medium">
                      {d.name || companyName.get(d.company_id) || "Untitled deal"}
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">{d.investment_status}</div>
                  </Link>
                ))}
                {items.length === 0 && (
                  <div className="rounded-md border border-dashed p-3 text-center text-xs text-muted-foreground">
                    Empty
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
