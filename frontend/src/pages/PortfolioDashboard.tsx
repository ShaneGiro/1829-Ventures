import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  useFunds,
  useInvestments,
  usePortfolioMetrics,
  usePortfolioSummary,
} from "@/api/portfolioApi";
import type { Investment, PortfolioMetric } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StateNotice } from "@/components/ui/state";
import { formatCurrency, formatDecimal, formatInteger, formatPercent } from "@/lib/utils";

const HARDCODED_RETURNED_CAPITAL = 0;

type InvestmentWithLabels = Investment & {
  company_name?: string | null;
  fund_name?: string | null;
};

type ConsolidatedCompanyRow = {
  companyId: string;
  companyName: string;
  funds: string;
  investmentCount: number;
  totalInvested: number;
  firstInvestmentDate: string | null;
  latestInvestmentDate: string | null;
  valuation: number | null;
  ownershipPct: number | null;
  portfolioValue: number | null;
  returnedCapital: number;
  tvpi: number | null;
  rvpi: number | null;
  dpi: number | null;
  irr: number | null;
  reporting: string;
};

type IndividualInvestmentRow = {
  id: string;
  companyId: string;
  companyName: string;
  fund: string;
  date: string | null;
  amount: string | number | null | undefined;
  round: string;
  instrument: string;
  valuation: number | null;
  ownershipPct: string | number | null | undefined;
  portfolioValue: number | null;
  returnedCapital: number;
  tvpi: number | null;
  rvpi: number | null;
  dpi: number | null;
  irr: number | null;
  reporting: string;
};

type SortDirection = "asc" | "desc";
type SortState<Key extends string> = {
  key: Key;
  direction: SortDirection;
} | null;
type FilterState<Key extends string> = Partial<Record<Key, string>>;

type TableColumn<Row, Key extends string> = {
  key: Key;
  label: string;
  render: (row: Row) => React.ReactNode;
  filterValue: (row: Row) => string;
  sortValue: (row: Row) => string | number | null | undefined;
  className?: string;
};

type CashFlow = {
  amount: number;
  date: string;
};

type CompanyColumnKey =
  | "companyName"
  | "funds"
  | "investmentCount"
  | "totalInvested"
  | "firstInvestmentDate"
  | "latestInvestmentDate"
  | "valuation"
  | "ownershipPct"
  | "portfolioValue"
  | "returnedCapital"
  | "tvpi"
  | "rvpi"
  | "dpi"
  | "irr"
  | "reporting";

type InvestmentColumnKey =
  | "companyName"
  | "fund"
  | "date"
  | "amount"
  | "round"
  | "instrument"
  | "valuation"
  | "ownershipPct"
  | "portfolioValue"
  | "returnedCapital"
  | "tvpi"
  | "rvpi"
  | "dpi"
  | "irr"
  | "reporting";

export function PortfolioDashboard() {
  const { data: summary, isLoading, isError } = usePortfolioSummary();
  const { data: funds, isError: fundsError } = useFunds();
  const { data: investments, isError: investmentsError } = useInvestments({ limit: 200 });
  const { data: metrics, isError: metricsError } = usePortfolioMetrics({ limit: 200 });

  const metricByInvestment = useMemo(() => {
    const map = new Map<string, PortfolioMetric>();
    metrics?.items.forEach((metric) => {
      if (metric.investment_id) map.set(metric.investment_id, metric);
    });
    return map;
  }, [metrics?.items]);

  const allInvestments = useMemo(
    () => (investments?.items as InvestmentWithLabels[] | undefined) ?? [],
    [investments?.items]
  );

  const fundOptions = useMemo(() => {
    const names = new Set<string>();
    allInvestments.forEach((investment) => {
      names.add(investment.fund_name ?? "Unassigned fund");
    });
    return [...names].sort((a, b) => a.localeCompare(b));
  }, [allInvestments]);

  const [selectedFunds, setSelectedFunds] = useState<string[]>([]);
  const [fundDropdownOpen, setFundDropdownOpen] = useState(false);
  const [companyFilters, setCompanyFilters] = useState<FilterState<CompanyColumnKey>>({});
  const [investmentFilters, setInvestmentFilters] = useState<FilterState<InvestmentColumnKey>>({});
  const [companySort, setCompanySort] = useState<SortState<CompanyColumnKey>>({
    key: "companyName",
    direction: "asc",
  });
  const [investmentSort, setInvestmentSort] = useState<SortState<InvestmentColumnKey>>({
    key: "date",
    direction: "asc",
  });
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (fundOptions.length > 0 && selectedFunds.length === 0) {
      setSelectedFunds(fundOptions);
    }
  }, [fundOptions, selectedFunds.length]);

  useEffect(() => {
    if (!fundDropdownOpen) return;

    const handleOutsideClick = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setFundDropdownOpen(false);
      }
    };

    window.addEventListener("mousedown", handleOutsideClick);
    return () => window.removeEventListener("mousedown", handleOutsideClick);
  }, [fundDropdownOpen]);

  const isAllFundsSelected = selectedFunds.length === fundOptions.length;
  const selectedFundsLabel =
    isAllFundsSelected || selectedFunds.length === 0
      ? "All funds"
      : selectedFunds.length === 1
      ? selectedFunds[0]
      : `${selectedFunds.length} funds`;

  const toggleFundSelection = (fundName: string) => {
    setSelectedFunds((prev) => {
      if (prev.includes(fundName)) {
        const next = prev.filter((name) => name !== fundName);
        return next.length ? next : prev;
      }
      return [...prev, fundName];
    });
  };

  const filteredInvestments = useMemo(
    () =>
      allInvestments
        .filter((investment) => {
          if (selectedFunds.length === 0 || isAllFundsSelected) return true;
          return selectedFunds.includes(investment.fund_name ?? "Unassigned fund");
        })
        .sort((a, b) => {
          const fundCompare = (a.fund_name ?? "").localeCompare(b.fund_name ?? "");
          if (fundCompare !== 0) return fundCompare;
          return (a.investment_date ?? "").localeCompare(b.investment_date ?? "");
        }),
    [allInvestments, selectedFunds, isAllFundsSelected]
  );

  const filteredSummary = useMemo(() => {
    const totalPositionValue = filteredInvestments.reduce((sum, investment) => {
      return sum + (investmentPortfolioValue(investment, metricByInvestment.get(investment.id)) ?? 0);
    }, 0);
    const totalReturnedCapital = sumValues(
      filteredInvestments.map((investment) =>
        investmentReturnedCapital(investment, metricByInvestment.get(investment.id))
      )
    );
    const totalPortfolioValue = totalPositionValue + totalReturnedCapital;

    const totalInvestedAmount = sumValues(filteredInvestments.map((investment) => investment.amount));
    const portfolioDpi = totalInvestedAmount ? totalReturnedCapital / totalInvestedAmount : null;
    const portfolioTvpi = totalInvestedAmount ? totalPortfolioValue / totalInvestedAmount : null;
    const portfolioRvpi = totalInvestedAmount
      ? (totalPortfolioValue - totalReturnedCapital) / totalInvestedAmount
      : null;
    const portfolioIrr = calculateXirr(
      cashFlowsForInvestments(filteredInvestments, metricByInvestment)
    );

    return {
      totalInvestments: filteredInvestments.length,
      totalInvestedAmount,
      totalPortfolioValue,
      totalReturnedCapital,
      portfolioDpi,
      portfolioTvpi,
      portfolioRvpi,
      portfolioIrr,
    };
  }, [filteredInvestments, metricByInvestment]);

  const filteredByFund = useMemo(() => {
    const totals = new Map<string, number>();
    filteredInvestments.forEach((investment) => {
      const fundName = investment.fund_name ?? "Unassigned fund";
      totals.set(fundName, (totals.get(fundName) ?? 0) + (toNumber(investment.amount) ?? 0));
    });
    return [...totals.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [filteredInvestments]);

  const consolidatedRows = useMemo<ConsolidatedCompanyRow[]>(() => {
    const byCompany = new Map<string, InvestmentWithLabels[]>();
    filteredInvestments.forEach((investment) => {
      if (!byCompany.has(investment.company_id)) byCompany.set(investment.company_id, []);
      byCompany.get(investment.company_id)!.push(investment);
    });

    return [...byCompany.entries()]
      .map(([companyId, companyInvestments]) => {
        const sorted = [...companyInvestments].sort((a, b) =>
          (a.investment_date ?? "").localeCompare(b.investment_date ?? "")
        );
        const latest = sorted[sorted.length - 1];
        const latestMetric = metricByInvestment.get(latest.id);
        const totalInvested = sumValues(sorted.map((investment) => investment.amount));
        const positionValue = sumValues(
          sorted.map((investment) =>
            investmentPortfolioValue(investment, metricByInvestment.get(investment.id))
          )
        );
        const returnedCapital = sumValues(
          sorted.map((investment) =>
            investmentReturnedCapital(investment, metricByInvestment.get(investment.id))
          )
        );
        const portfolioValue = positionValue + returnedCapital;
        const tvpi = totalInvested ? portfolioValue / totalInvested : null;
        const rvpi = totalInvested ? (portfolioValue - returnedCapital) / totalInvested : null;
        const dpi = totalInvested ? returnedCapital / totalInvested : null;
        const irr = calculateXirr(cashFlowsForInvestments(sorted, metricByInvestment));
        const ownershipValues = sorted
          .map((investment) => toNumber(investment.ownership_pct))
          .filter((value): value is number => value !== null);

        return {
          companyId,
          companyName: latest.company_name ?? companyId,
          funds: [...new Set(sorted.map((investment) => investment.fund_name ?? "Unassigned fund"))]
            .sort((a, b) => a.localeCompare(b))
            .join(", "),
          investmentCount: sorted.length,
          totalInvested,
          firstInvestmentDate: sorted[0]?.investment_date ?? null,
          latestInvestmentDate: latest.investment_date ?? null,
          valuation: investmentValuation(latest),
          ownershipPct: ownershipValues.length ? sumValues(ownershipValues) : null,
          portfolioValue,
          returnedCapital,
          tvpi,
          rvpi,
          dpi,
          irr,
          reporting: reportingLabel(latestMetric),
        };
      })
      .sort((a, b) => a.companyName.localeCompare(b.companyName));
  }, [filteredInvestments, metricByInvestment]);

  const individualRows = useMemo<IndividualInvestmentRow[]>(
    () =>
      filteredInvestments.map((investment) => {
        const metric = metricByInvestment.get(investment.id);
        const positionValue = investmentPortfolioValue(investment, metric);
        const cost = toNumber(investment.amount);
        const returnedCapital = investmentReturnedCapital(investment, metric);
        const portfolioValue = (positionValue ?? 0) + returnedCapital;
        const tvpi = cost ? portfolioValue / cost : null;
        const rvpi = cost ? (portfolioValue - returnedCapital) / cost : null;
        const dpi = cost ? returnedCapital / cost : null;
        const irr = calculateXirr(cashFlowsForInvestment(investment, metric));
        return {
          id: investment.id,
          companyId: investment.company_id,
          companyName: investment.company_name ?? investment.company_id,
          fund: investment.fund_name ?? "Unassigned fund",
          date: investment.investment_date ?? null,
          amount: investment.amount,
          round: investment.round_name ?? "",
          instrument: investment.instrument ?? "",
          valuation: investmentValuation(investment),
          ownershipPct: investment.ownership_pct,
          portfolioValue,
          returnedCapital,
          tvpi,
          rvpi,
          dpi,
          irr,
          reporting: reportingLabel(metric),
        };
      }),
    [filteredInvestments, metricByInvestment]
  );

  const companyColumns = useMemo<TableColumn<ConsolidatedCompanyRow, CompanyColumnKey>[]>(
    () => [
      {
        key: "companyName",
        label: "Company",
        className: "min-w-52 font-medium",
        render: (row) => (
          <Link
            to={`/companies/${row.companyId}`}
            className="text-primary underline-offset-4 hover:underline"
          >
            {row.companyName}
          </Link>
        ),
        filterValue: (row) => row.companyName,
        sortValue: (row) => row.companyName,
      },
      {
        key: "funds",
        label: "Fund",
        render: (row) => row.funds,
        filterValue: (row) => row.funds,
        sortValue: (row) => row.funds,
      },
      {
        key: "investmentCount",
        label: "Investments",
        render: (row) => formatInteger(row.investmentCount),
        filterValue: (row) => formatInteger(row.investmentCount),
        sortValue: (row) => row.investmentCount,
      },
      {
        key: "totalInvested",
        label: "Total invested",
        render: (row) => formatCurrency(row.totalInvested),
        filterValue: (row) => formatCurrency(row.totalInvested),
        sortValue: (row) => row.totalInvested,
      },
      {
        key: "firstInvestmentDate",
        label: "First date",
        render: (row) => formatDate(row.firstInvestmentDate),
        filterValue: (row) => formatDate(row.firstInvestmentDate),
        sortValue: (row) => row.firstInvestmentDate,
      },
      {
        key: "latestInvestmentDate",
        label: "Latest date",
        render: (row) => formatDate(row.latestInvestmentDate),
        filterValue: (row) => formatDate(row.latestInvestmentDate),
        sortValue: (row) => row.latestInvestmentDate,
      },
      {
        key: "valuation",
        label: "Valuation",
        render: (row) => formatCurrency(row.valuation),
        filterValue: (row) => formatCurrency(row.valuation),
        sortValue: (row) => row.valuation,
      },
      {
        key: "ownershipPct",
        label: "Ownership",
        render: (row) => formatPercent(row.ownershipPct),
        filterValue: (row) => formatPercent(row.ownershipPct),
        sortValue: (row) => row.ownershipPct,
      },
      {
        key: "portfolioValue",
        label: "Portfolio value",
        render: (row) => formatCurrency(row.portfolioValue),
        filterValue: (row) => formatCurrency(row.portfolioValue),
        sortValue: (row) => row.portfolioValue,
      },
      {
        key: "returnedCapital",
        label: "Returned capital",
        render: (row) => formatCurrency(row.returnedCapital),
        filterValue: (row) => formatCurrency(row.returnedCapital),
        sortValue: (row) => row.returnedCapital,
      },
      {
        key: "tvpi",
        label: "TVPI",
        render: (row) => formatDecimal(row.tvpi),
        filterValue: (row) => formatDecimal(row.tvpi),
        sortValue: (row) => row.tvpi,
      },
      {
        key: "rvpi",
        label: "RVPI",
        render: (row) => formatDecimal(row.rvpi),
        filterValue: (row) => formatDecimal(row.rvpi),
        sortValue: (row) => row.rvpi,
      },
      {
        key: "dpi",
        label: "DPI",
        render: (row) => formatDecimal(row.dpi),
        filterValue: (row) => formatDecimal(row.dpi),
        sortValue: (row) => row.dpi,
      },
      {
        key: "irr",
        label: "IRR",
        render: (row) => formatPercent(row.irr),
        filterValue: (row) => formatPercent(row.irr),
        sortValue: (row) => row.irr,
      },
      {
        key: "reporting",
        label: "Reporting",
        render: (row) => row.reporting || "—",
        filterValue: (row) => row.reporting,
        sortValue: (row) => row.reporting,
      },
    ],
    []
  );

  const investmentColumns = useMemo<TableColumn<IndividualInvestmentRow, InvestmentColumnKey>[]>(
    () => [
      {
        key: "companyName",
        label: "Company",
        className: "min-w-52 font-medium",
        render: (row) => (
          <Link
            to={`/companies/${row.companyId}`}
            className="text-primary underline-offset-4 hover:underline"
          >
            {row.companyName}
          </Link>
        ),
        filterValue: (row) => row.companyName,
        sortValue: (row) => row.companyName,
      },
      {
        key: "fund",
        label: "Fund",
        render: (row) => row.fund,
        filterValue: (row) => row.fund,
        sortValue: (row) => row.fund,
      },
      {
        key: "date",
        label: "Date",
        render: (row) => formatDate(row.date),
        filterValue: (row) => formatDate(row.date),
        sortValue: (row) => row.date,
      },
      {
        key: "amount",
        label: "Amount",
        render: (row) => formatCurrency(row.amount),
        filterValue: (row) => formatCurrency(row.amount),
        sortValue: (row) => toNumber(row.amount),
      },
      {
        key: "round",
        label: "Round",
        render: (row) => row.round || "—",
        filterValue: (row) => row.round,
        sortValue: (row) => row.round,
      },
      {
        key: "instrument",
        label: "Instrument",
        render: (row) => row.instrument || "—",
        filterValue: (row) => row.instrument,
        sortValue: (row) => row.instrument,
      },
      {
        key: "valuation",
        label: "Valuation",
        render: (row) => formatCurrency(row.valuation),
        filterValue: (row) => formatCurrency(row.valuation),
        sortValue: (row) => row.valuation,
      },
      {
        key: "ownershipPct",
        label: "Ownership",
        render: (row) => formatPercent(row.ownershipPct),
        filterValue: (row) => formatPercent(row.ownershipPct),
        sortValue: (row) => toNumber(row.ownershipPct),
      },
      {
        key: "portfolioValue",
        label: "Portfolio value",
        render: (row) => formatCurrency(row.portfolioValue),
        filterValue: (row) => formatCurrency(row.portfolioValue),
        sortValue: (row) => row.portfolioValue,
      },
      {
        key: "returnedCapital",
        label: "Returned capital",
        render: (row) => formatCurrency(row.returnedCapital),
        filterValue: (row) => formatCurrency(row.returnedCapital),
        sortValue: (row) => row.returnedCapital,
      },
      {
        key: "tvpi",
        label: "TVPI",
        render: (row) => formatDecimal(row.tvpi),
        filterValue: (row) => formatDecimal(row.tvpi),
        sortValue: (row) => row.tvpi,
      },
      {
        key: "rvpi",
        label: "RVPI",
        render: (row) => formatDecimal(row.rvpi),
        filterValue: (row) => formatDecimal(row.rvpi),
        sortValue: (row) => row.rvpi,
      },
      {
        key: "dpi",
        label: "DPI",
        render: (row) => formatDecimal(row.dpi),
        filterValue: (row) => formatDecimal(row.dpi),
        sortValue: (row) => row.dpi,
      },
      {
        key: "irr",
        label: "IRR",
        render: (row) => formatPercent(row.irr),
        filterValue: (row) => formatPercent(row.irr),
        sortValue: (row) => row.irr,
      },
      {
        key: "reporting",
        label: "Reporting",
        render: (row) => row.reporting || "—",
        filterValue: (row) => row.reporting,
        sortValue: (row) => row.reporting,
      },
    ],
    []
  );

  const visibleCompanyRows = useMemo(
    () => applyTableState(consolidatedRows, companyColumns, companyFilters, companySort),
    [consolidatedRows, companyColumns, companyFilters, companySort]
  );

  const visibleInvestmentRows = useMemo(
    () => applyTableState(individualRows, investmentColumns, investmentFilters, investmentSort),
    [individualRows, investmentColumns, investmentFilters, investmentSort]
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-semibold">Portfolio</h1>
        <div ref={dropdownRef} className="relative">
          <Button
            variant="outline"
            size="sm"
            aria-expanded={fundDropdownOpen}
            aria-haspopup="true"
            onClick={() => setFundDropdownOpen((prev) => !prev)}
          >
            {selectedFundsLabel}
          </Button>
          {fundDropdownOpen && (
            <div className="absolute right-0 z-20 mt-2 w-60 overflow-hidden rounded-md border bg-background text-sm shadow-lg">
              <div className="border-b p-2">
                <label className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-2 hover:bg-muted">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-muted text-primary focus:ring-primary"
                    checked={isAllFundsSelected}
                    onChange={() => setSelectedFunds(fundOptions)}
                  />
                  <span>All funds</span>
                </label>
              </div>
              <div className="space-y-1 p-2">
                {fundOptions.map((fundName) => (
                  <label
                    key={fundName}
                    className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-2 hover:bg-muted"
                  >
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded border-muted text-primary focus:ring-primary"
                      checked={selectedFunds.includes(fundName)}
                      onChange={() => toggleFundSelection(fundName)}
                    />
                    <span>{fundName}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      {isLoading && <StateNotice title="Loading portfolio" />}
      {(isError || fundsError || investmentsError || metricsError) && (
        <StateNotice
          title="Could not load portfolio"
          description="Refresh the page or check the API connection."
          variant="error"
        />
      )}

      {summary && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <Stat label="Investments" value={formatInteger(filteredSummary.totalInvestments)} />
          <Stat label="Invested" value={formatCurrency(filteredSummary.totalInvestedAmount)} />
          <Stat label="Portfolio value" value={formatCurrency(filteredSummary.totalPortfolioValue)} />
          <Stat label="Returned capital" value={formatCurrency(filteredSummary.totalReturnedCapital)} />
          <Stat label="TVPI" value={formatDecimal(filteredSummary.portfolioTvpi)} />
          <Stat label="RVPI" value={formatDecimal(filteredSummary.portfolioRvpi)} />
          <Stat label="DPI" value={formatDecimal(filteredSummary.portfolioDpi)} />
          <Stat label="IRR" value={formatPercent(filteredSummary.portfolioIrr)} />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>By fund</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            {filteredByFund.length ? (
              filteredByFund.map(([fundName, value]) => (
                <div key={fundName} className="flex justify-between">
                  <span>{fundName}</span>
                  <span className="text-muted-foreground">{formatCurrency(value)}</span>
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

      <Card>
        <CardHeader>
          <CardTitle>Portfolio companies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto rounded-md border">
            <table className="min-w-full table-fixed border-separate border-spacing-0 text-left text-sm">
              <thead className="bg-background align-top">
                <tr>
                  {companyColumns.map((column) => (
                    <SortableHeaderCell
                      key={column.key}
                      active={companySort?.key === column.key}
                      direction={companySort?.key === column.key ? companySort.direction : null}
                      onSort={() => setCompanySort(nextSort(companySort, column.key))}
                    >
                      {column.label}
                    </SortableHeaderCell>
                  ))}
                </tr>
                <tr>
                  {companyColumns.map((column) => (
                    <FilterHeaderCell
                      key={column.key}
                      value={companyFilters[column.key] ?? ""}
                      onChange={(value) =>
                        setCompanyFilters((prev) => ({ ...prev, [column.key]: value }))
                      }
                    />
                  ))}
                </tr>
              </thead>
              <tbody>
                {visibleCompanyRows.map((row) => (
                  <tr key={row.companyId} className="odd:bg-muted/30">
                    {companyColumns.map((column) => (
                      <BodyCell key={column.key} className={column.className}>
                        {column.render(row)}
                      </BodyCell>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {visibleCompanyRows.length === 0 && (
            <p className="p-4 text-sm text-muted-foreground">No portfolio companies.</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Individual investments</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto rounded-md border">
            <table className="min-w-full table-fixed border-separate border-spacing-0 text-left text-sm">
              <thead className="bg-background align-top">
                <tr>
                  {investmentColumns.map((column) => (
                    <SortableHeaderCell
                      key={column.key}
                      active={investmentSort?.key === column.key}
                      direction={investmentSort?.key === column.key ? investmentSort.direction : null}
                      onSort={() => setInvestmentSort(nextSort(investmentSort, column.key))}
                    >
                      {column.label}
                    </SortableHeaderCell>
                  ))}
                </tr>
                <tr>
                  {investmentColumns.map((column) => (
                    <FilterHeaderCell
                      key={column.key}
                      value={investmentFilters[column.key] ?? ""}
                      onChange={(value) =>
                        setInvestmentFilters((prev) => ({ ...prev, [column.key]: value }))
                      }
                    />
                  ))}
                </tr>
              </thead>
              <tbody>
                {visibleInvestmentRows.map((row) => (
                  <tr key={row.id} className="odd:bg-muted/30">
                    {investmentColumns.map((column) => (
                      <BodyCell key={column.key} className={column.className}>
                        {column.render(row)}
                      </BodyCell>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {visibleInvestmentRows.length === 0 && (
            <p className="p-4 text-sm text-muted-foreground">No investments.</p>
          )}
        </CardContent>
      </Card>
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

function SortableHeaderCell({
  active,
  children,
  direction,
  onSort,
}: {
  active: boolean;
  children: React.ReactNode;
  direction: SortDirection | null;
  onSort: () => void;
}) {
  const indicator = active ? (direction === "asc" ? "▲" : "▼") : "↕";
  return (
    <th className="whitespace-nowrap border-b px-3 py-2 font-medium overflow-hidden text-ellipsis">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-2 text-left"
        onClick={onSort}
      >
        <span className="overflow-hidden text-ellipsis">{children}</span>
        <span className="text-[10px] text-muted-foreground">{indicator}</span>
      </button>
    </th>
  );
}

function FilterHeaderCell({
  onChange,
  value,
}: {
  onChange: (value: string) => void;
  value: string;
}) {
  return (
    <th className="border-b px-2 py-2">
      <input
        type="search"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-8 w-full rounded-md border bg-background px-2 text-xs outline-none focus:ring-2 focus:ring-ring"
      />
    </th>
  );
}

function BodyCell({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <td className={`max-w-72 overflow-hidden text-ellipsis whitespace-nowrap border-b px-3 py-2 align-top ${className}`}>
      {children}
    </td>
  );
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function reportingLabel(metric: PortfolioMetric | undefined): string {
  return [metric?.reporting_period, formatDate(metric?.reporting_date)]
    .filter((value) => value && value !== "—")
    .join(" · ");
}

function toNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const parsed = typeof value === "number" ? value : Number(value.replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : null;
}

function sumValues(values: Array<string | number | null | undefined>): number {
  return values.reduce<number>((sum, value) => sum + (toNumber(value) ?? 0), 0);
}

function investmentValuation(investment: InvestmentWithLabels): number | null {
  return (
    toNumber(investment.post_money_valuation) ??
    toNumber(investment.pre_money_valuation)
  );
}

function investmentPortfolioValue(
  investment: InvestmentWithLabels,
  metric: PortfolioMetric | undefined
): number | null {
  const markedValue = toNumber(metric?.valuation_mark);
  if (markedValue !== null) return markedValue;
  const valuation = investmentValuation(investment);
  const ownershipPct = toNumber(investment.ownership_pct);
  if (valuation === null || ownershipPct === null) return null;
  return (ownershipPct / 100) * valuation;
}

function investmentReturnedCapital(
  investment: InvestmentWithLabels,
  metric: PortfolioMetric | undefined
): number {
  const amount = toNumber(investment.amount);
  const dpi = toNumber(metric?.dpi);
  if (amount === null || dpi === null) return HARDCODED_RETURNED_CAPITAL;
  return amount * dpi;
}

function cashFlowsForInvestments(
  investments: InvestmentWithLabels[],
  metricByInvestment: Map<string, PortfolioMetric>
): CashFlow[] {
  return investments.flatMap((investment) =>
    cashFlowsForInvestment(investment, metricByInvestment.get(investment.id))
  );
}

function cashFlowsForInvestment(
  investment: InvestmentWithLabels,
  metric: PortfolioMetric | undefined
): CashFlow[] {
  const amount = toNumber(investment.amount);
  if (amount === null || amount <= 0 || !investment.investment_date) return [];

  const terminalDate = metric?.reporting_date ?? todayIsoDate();
  const returnedCapital = investmentReturnedCapital(investment, metric);
  const positionValue = investmentPortfolioValue(investment, metric) ?? 0;

  const flows: CashFlow[] = [{ amount: -amount, date: investment.investment_date }];
  if (returnedCapital !== 0) flows.push({ amount: returnedCapital, date: terminalDate });
  if (positionValue !== 0) flows.push({ amount: positionValue, date: terminalDate });
  return flows;
}

function calculateXirr(cashFlows: CashFlow[]): number | null {
  const validFlows = cashFlows
    .map((flow) => ({ ...flow, time: Date.parse(`${flow.date}T00:00:00`) }))
    .filter((flow) => Number.isFinite(flow.time) && flow.amount !== 0)
    .sort((a, b) => a.time - b.time);

  if (
    validFlows.length < 2 ||
    !validFlows.some((flow) => flow.amount < 0) ||
    !validFlows.some((flow) => flow.amount > 0)
  ) {
    return null;
  }

  const firstTime = validFlows[0].time;
  const years = validFlows.map((flow) => (flow.time - firstTime) / (365 * 24 * 60 * 60 * 1000));
  if (years.every((year) => year === 0)) return null;

  const npv = (rate: number) =>
    validFlows.reduce(
      (total, flow, index) => total + flow.amount / (1 + rate) ** years[index],
      0
    );

  let low = -0.999999;
  let high = 1;
  let lowValue = npv(low);
  let highValue = npv(high);

  for (let i = 0; i < 100 && lowValue * highValue > 0; i += 1) {
    high *= 2;
    highValue = npv(high);
    if (high > 1_000_000) return null;
  }

  if (lowValue * highValue > 0) return null;

  for (let i = 0; i < 100; i += 1) {
    const mid = (low + high) / 2;
    const midValue = npv(mid);
    if (Math.abs(midValue) < 0.000001) return mid;
    if (lowValue * midValue <= 0) {
      high = mid;
      highValue = midValue;
    } else {
      low = mid;
      lowValue = midValue;
    }
  }

  return (low + high) / 2;
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function nextSort<Key extends string>(
  current: SortState<Key>,
  key: Key
): SortState<Key> {
  if (current?.key !== key) return { key, direction: "asc" };
  return { key, direction: current.direction === "asc" ? "desc" : "asc" };
}

function applyTableState<Row, Key extends string>(
  rows: Row[],
  columns: TableColumn<Row, Key>[],
  filters: FilterState<Key>,
  sort: SortState<Key>
): Row[] {
  const filtered = rows.filter((row) =>
    columns.every((column) => {
      const filter = (filters[column.key] ?? "").trim().toLowerCase();
      if (!filter) return true;
      return column.filterValue(row).toLowerCase().includes(filter);
    })
  );

  if (!sort) return filtered;

  const sortColumn = columns.find((column) => column.key === sort.key);
  if (!sortColumn) return filtered;

  return [...filtered].sort((a, b) => {
    const direction = sort.direction === "asc" ? 1 : -1;
    return compareSortValues(sortColumn.sortValue(a), sortColumn.sortValue(b)) * direction;
  });
}

function compareSortValues(
  a: string | number | null | undefined,
  b: string | number | null | undefined
): number {
  if (a === null || a === undefined || a === "") return b === null || b === undefined || b === "" ? 0 : 1;
  if (b === null || b === undefined || b === "") return -1;
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a).localeCompare(String(b), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}
