import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { StateNotice } from "@/components/ui/state";
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
      {isLoading && <StateNotice title="Loading pipeline" />}
      {isError && (
        <StateNotice
          title="Could not load analytics"
          description="Refresh the page or check that the backend is running."
          variant="error"
        />
      )}
      {data && (
        <div className="grid gap-4 sm:grid-cols-2">
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
