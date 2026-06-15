import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { CompanyList } from "@/pages/CompanyList";

vi.mock("@/lib/api", () => ({
  api: { get: vi.fn() },
  ApiError: class extends Error {},
}));

function renderWithProviders(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CompanyList", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders companies returned by the API", async () => {
    vi.mocked(api.get).mockImplementation((path) =>
      Promise.resolve(
        path === "/companies/dealroom-columns"
          ? ["ID", "Name", "Website"]
          : {
              items: [
                {
                  id: "1",
                  name: "Acme Photonics",
                  sector: "Photonics, Imaging & Quantum",
                  relationship_status: "active",
                  completeness_pct: 80,
                },
              ],
              total: 1,
              limit: 50,
              offset: 0,
            },
      ),
    );

    renderWithProviders(<CompanyList />);

    await waitFor(() => expect(screen.getByText("Acme Photonics")).toBeInTheDocument());
    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByText("80%")).toBeInTheDocument();
  });

  it("shows an empty state when there are no companies", async () => {
    vi.mocked(api.get).mockImplementation((path) =>
      Promise.resolve(
        path === "/companies/dealroom-columns"
          ? ["ID", "Name", "Website"]
          : { items: [], total: 0, limit: 50, offset: 0 },
      ),
    );
    renderWithProviders(<CompanyList />);
    await waitFor(() => expect(screen.getByText("No companies found.")).toBeInTheDocument());
  });
});
