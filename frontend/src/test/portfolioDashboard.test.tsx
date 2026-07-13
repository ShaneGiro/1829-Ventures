import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { PortfolioDashboard } from "@/pages/PortfolioDashboard";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn() } }));

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <PortfolioDashboard />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("PortfolioDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockImplementation((path) => {
      if (path === "/funds") {
        return Promise.resolve({
          items: [{ id: "fund-1", name: "Fund 1", status: "active" }],
          total: 1,
          limit: 200,
          offset: 0,
        });
      }
      if (path === "/investments") {
        return Promise.resolve({
          items: [
            {
              id: "investment-1",
              company_id: "company-1",
              company_name: "Acme Photonics",
              fund_id: "fund-1",
              fund_name: "Fund 1",
              amount: "100000",
              investment_date: "2025-01-15",
              ownership_pct: "10",
              currency: "USD",
              created_at: "2025-01-15T00:00:00Z",
              updated_at: "2025-01-15T00:00:00Z",
            },
          ],
          total: 1,
          limit: 200,
          offset: 0,
        });
      }
      if (path === "/portfolio-metrics") {
        return Promise.resolve({
          items: [
            {
              id: "metric-1",
              company_id: "company-1",
              investment_id: "investment-1",
              valuation_mark: "200000",
              dpi: "0.42",
              tvpi: "2.42",
              irr: "0.33",
              reporting_date: "2025-12-31",
              created_at: "2025-12-31T00:00:00Z",
              updated_at: "2025-12-31T00:00:00Z",
            },
          ],
          total: 1,
          limit: 200,
          offset: 0,
        });
      }
      return Promise.reject(new Error(`Unexpected API path: ${path}`));
    });
  });

  it("labels legacy values and hides unsourced return metrics", async () => {
    renderPage();

    await waitFor(() => expect(screen.getAllByText("Acme Photonics")).toHaveLength(2));

    expect(screen.getByText("Legacy / unreconciled portfolio data")).toBeInTheDocument();
    expect(screen.getByText(/not yet been reconciled to Workday/i)).toBeInTheDocument();
    expect(screen.getAllByText("Legacy estimated value")).toHaveLength(3);
    expect(screen.getAllByText("$200,000.00").length).toBeGreaterThan(0);

    expect(screen.queryByText("Returned capital")).not.toBeInTheDocument();
    expect(screen.queryByText("TVPI")).not.toBeInTheDocument();
    expect(screen.queryByText("DPI")).not.toBeInTheDocument();
    expect(screen.queryByText("RVPI")).not.toBeInTheDocument();
    expect(screen.queryByText("IRR")).not.toBeInTheDocument();
    expect(screen.queryByText("$42,000.00")).not.toBeInTheDocument();
    expect(screen.queryByText("2.42")).not.toBeInTheDocument();
    expect(screen.queryByText("0.33%")).not.toBeInTheDocument();
  });
});
