import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { OutreachCandidatesPage } from "@/pages/OutreachCandidatesPage";

vi.mock("@/lib/api", () => ({ api: { get: vi.fn() } }));

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <OutreachCandidatesPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("OutreachCandidatesPage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("renders an explainable candidate score and verification state", async () => {
    vi.mocked(api.get).mockResolvedValue({
      items: [
        {
          score: 88,
          score_version: "v1.3.1",
          why_this_company: "active RIT alumni founder; target funding stage",
          warnings: ["1829 fit scoring is incomplete"],
          follow_up_needed: false,
          breakdown: {},
          company: {
            id: "company-1",
            name: "Acme Photonics",
            stage: "Seed",
            alumni_founder_status: "active",
            alumni_founder_confidence: 0.9,
            operational_status: "operational",
            operational_confidence: 0.8,
            fit_score_reasons: [],
          },
        },
      ],
      total: 1,
      limit: 200,
      offset: 0,
    });

    renderPage();

    await waitFor(() => expect(screen.getByText("Acme Photonics")).toBeInTheDocument());
    expect(screen.getByText("88")).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByText("operational")).toBeInTheDocument();
    expect(screen.getByText("1 warnings")).toBeInTheDocument();
  });
});
