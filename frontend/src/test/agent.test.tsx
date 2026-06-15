import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { PolicyPanel } from "@/components/agent/PolicyPanel";

vi.mock("@/lib/api", () => ({
  api: { get: vi.fn(), put: vi.fn() },
  ApiError: class extends Error {},
}));

function withProviders(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe("PolicyPanel", () => {
  beforeEach(() => vi.clearAllMocks());

  it("flips an authorized tool to blocked via the policy endpoint", async () => {
    vi.mocked(api.get).mockResolvedValue([
      { id: "1", tool: "update_investment_amount", field_name: null, state: "authorized" },
    ]);
    vi.mocked(api.put).mockResolvedValue({});

    withProviders(<PolicyPanel />);

    const button = await screen.findByRole("button", { name: "Block" });
    fireEvent.click(button);

    await waitFor(() =>
      expect(api.put).toHaveBeenCalledWith("/agent/policies", {
        tool: "update_investment_amount",
        field_name: null,
        state: "blocked",
      }),
    );
  });

  it("shows authorized/blocked state badges", async () => {
    vi.mocked(api.get).mockResolvedValue([
      { id: "1", tool: "add_company_note", field_name: null, state: "authorized" },
    ]);
    withProviders(<PolicyPanel />);
    expect(await screen.findByText("authorized")).toBeInTheDocument();
  });
});
