import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useInfiniteCompanies } from "@/api/companies";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { StateNotice } from "@/components/ui/state";

export function CompanyList() {
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");

  // Debounce the search so we refetch once the user pauses, not per keystroke.
  useEffect(() => {
    const id = setTimeout(() => setDebouncedQ(q.trim()), 250);
    return () => clearTimeout(id);
  }, [q]);

  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteCompanies(debouncedQ || undefined);

  const companies = data?.pages.flatMap((page) => page.items) ?? [];
  const total = data?.pages[0]?.total ?? 0;

  // Auto-load the next page when the sentinel scrolls into view.
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const node = sentinelRef.current;
    if (!node || !hasNextPage) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && !isFetchingNextPage) void fetchNextPage();
      },
      { rootMargin: "200px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-semibold">
          Companies
          {total > 0 && <span className="ml-2 text-sm text-muted-foreground">({total})</span>}
        </h1>
        <Input
          placeholder="Search by name, domain, or website…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="w-full sm:w-72"
        />
      </div>
      {isLoading && <StateNotice title="Loading companies" />}
      {isError && (
        <StateNotice
          title="Could not load companies"
          description="Refresh the page or check the API connection."
          variant="error"
        />
      )}
      {data && (
        <div className="overflow-x-auto rounded-lg border">
          <table className="min-w-[720px] w-full text-sm">
            <thead className="bg-muted/40 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-4 py-2">Name</th>
                <th className="px-4 py-2">Sector</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Complete</th>
              </tr>
            </thead>
            <tbody>
              {companies.map((c) => (
                <tr key={c.id} className="border-t hover:bg-accent/40">
                  <td className="px-4 py-2 font-medium">
                    <Link to={`/companies/${c.id}`} className="hover:underline">
                      {c.name}
                    </Link>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">{c.sector ?? "—"}</td>
                  <td className="px-4 py-2">
                    <Badge>{c.relationship_status}</Badge>
                  </td>
                  <td className="px-4 py-2 text-muted-foreground">
                    {Math.round(c.completeness_pct ?? 0)}%
                  </td>
                </tr>
              ))}
              {companies.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-muted-foreground">
                    No companies found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          {/* Sentinel + fallback button for loading more results. */}
          <div ref={sentinelRef} className="flex justify-center p-3 text-sm text-muted-foreground">
            {isFetchingNextPage
              ? "Loading more…"
              : hasNextPage
                ? `Showing ${companies.length} of ${total}`
                : companies.length > 0
                  ? `All ${total} companies loaded`
                  : null}
          </div>
        </div>
      )}
    </div>
  );
}
