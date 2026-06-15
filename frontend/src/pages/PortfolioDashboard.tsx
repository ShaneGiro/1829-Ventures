import { useFunds, usePortfolioSummary } from "@/api/portfolioApi";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StateNotice } from "@/components/ui/state";

function fmt(value: string | number | null | undefined): string {
  if (value == null) return "—";
  return String(value);
}

export function PortfolioDashboard() {
  const { data: summary, isLoading, isError } = usePortfolioSummary();
  const { data: funds, isError: fundsError } = useFunds();

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Portfolio</h1>
      {isLoading && <StateNotice title="Loading portfolio" />}
      {(isError || fundsError) && (
        <StateNotice
          title="Could not load portfolio"
          description="Refresh the page or check the API connection."
          variant="error"
        />
      )}

      {summary && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <Stat label="Investments" value={fmt(summary.total_investments)} />
          <Stat label="Invested" value={fmt(summary.total_invested_amount)} />
          <Stat label="Valuation mark" value={fmt(summary.total_valuation_mark)} />
          <Stat label="Avg TVPI" value={fmt(summary.average_tvpi)} />
          <Stat label="Avg DPI" value={fmt(summary.average_dpi)} />
          <Stat label="Avg IRR" value={fmt(summary.average_irr)} />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>By fund</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            {summary?.by_fund.length ? (
              summary.by_fund.map((f) => (
                <div key={f.key} className="flex justify-between">
                  <span>{f.key}</span>
                  <span className="text-muted-foreground">{fmt(f.value)}</span>
                </div>
              ))
            ) : (
              <p className="text-muted-foreground">No fund data.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Funds</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            {funds?.items.map((f) => (
              <div key={f.id} className="flex justify-between">
                <span>{f.name}</span>
                <span className="text-muted-foreground">{f.status}</span>
              </div>
            ))}
            {funds?.items.length === 0 && <p className="text-muted-foreground">No funds.</p>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border p-4">
      <div className="text-sm text-muted-foreground">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}
