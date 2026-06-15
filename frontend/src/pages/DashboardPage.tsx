import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { components } from "@/types/api";

type PipelineSummary = components["schemas"]["PipelineSummary"];

export function DashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["analytics", "pipeline"],
    queryFn: () => api.get<PipelineSummary>("/analytics/pipeline"),
  });

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Dashboard</h1>
      {isLoading && <p className="text-sm text-muted-foreground">Loading pipeline…</p>}
      {isError && <p className="text-sm text-muted-foreground">Could not load analytics.</p>}
      {data && (
        <div className="grid grid-cols-2 gap-4">
          <StatCard label="Companies" value={data.total_companies} />
          <StatCard label="Deals" value={data.total_deals} />
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border p-4">
      <div className="text-sm text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}
