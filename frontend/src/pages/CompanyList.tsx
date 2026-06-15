import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  type DealroomColumnKind,
  type DealroomColumnOption,
  useDealroomColumns,
  useInfiniteCompanies,
  type CompanyFilters,
} from "@/api/companies";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StateNotice } from "@/components/ui/state";

const SECTORS = [
  "Photonics, Imaging & Quantum",
  "Clean Tech & Energy",
  "Life Sciences & Health Tech",
  "Intelligent Systems, AI & Cyber",
  "Other",
];

const RELATIONSHIP_STATUSES = [
  "identified",
  "contacted",
  "review_needed",
  "active",
  "nurture",
  "strategic",
  "inactive",
];

type TriState = "" | "yes" | "no";
type DealroomFilterValue = { operator: string; value: string; valueTo: string };

const triToBool = (v: TriState): boolean | undefined =>
  v === "yes" ? true : v === "no" ? false : undefined;

export function CompanyList() {
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  // Filter UI state.
  const [sectors, setSectors] = useState<string[]>([]);
  const [statuses, setStatuses] = useState<string[]>([]);
  const [stage, setStage] = useState("");
  const [country, setCountry] = useState("");
  const [state, setState] = useState("");
  const [city, setCity] = useState("");
  const [ritNexus, setRitNexus] = useState<TriState>("");
  const [reviewed, setReviewed] = useState<TriState>(""); // yes = reviewed, no = unreviewed
  const [hasWebsite, setHasWebsite] = useState<TriState>("");
  const [minCompleteness, setMinCompleteness] = useState("");
  const [maxCompleteness, setMaxCompleteness] = useState("");
  const [dealroomFilters, setDealroomFilters] = useState<Record<string, DealroomFilterValue>>({});

  useEffect(() => {
    const id = setTimeout(() => setDebouncedQ(q.trim()), 250);
    return () => clearTimeout(id);
  }, [q]);

  const dealroomColumns = useDealroomColumns();
  const activeDealroomFilters = useMemo(
    () =>
      Object.entries(dealroomFilters)
        .map(([column, filter]) => encodeDealroomFilter(column, filter))
        .filter((filter): filter is string => filter !== undefined),
    [dealroomFilters],
  );

  const filters = useMemo<CompanyFilters>(() => {
    const stages = splitValues(stage);
    const countries = country
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);
    const states = splitValues(state);
    const cities = splitValues(city);
    const min = Number(minCompleteness);
    const max = Number(maxCompleteness);
    return {
      sector: sectors,
      relationship_status: statuses,
      stage: stages,
      country: countries,
      state: states,
      city: cities,
      has_rit_nexus: triToBool(ritNexus),
      // "reviewed" yes → imported_unreviewed false; no → unreviewed true.
      imported_unreviewed: reviewed === "yes" ? false : reviewed === "no" ? true : undefined,
      has_website: triToBool(hasWebsite),
      min_completeness: boundedPercent(minCompleteness, min),
      max_completeness: boundedPercent(maxCompleteness, max),
      dealroom_filter: activeDealroomFilters,
    };
  }, [
    sectors,
    statuses,
    stage,
    country,
    state,
    city,
    ritNexus,
    reviewed,
    hasWebsite,
    minCompleteness,
    maxCompleteness,
    activeDealroomFilters,
  ]);

  const activeCount =
    sectors.length +
    statuses.length +
    (stage.trim() ? 1 : 0) +
    (country.trim() ? 1 : 0) +
    (state.trim() ? 1 : 0) +
    (city.trim() ? 1 : 0) +
    (ritNexus ? 1 : 0) +
    (reviewed ? 1 : 0) +
    (hasWebsite ? 1 : 0) +
    (minCompleteness !== "" ? 1 : 0) +
    (maxCompleteness !== "" ? 1 : 0) +
    activeDealroomFilters.length;

  const { data, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useInfiniteCompanies(debouncedQ || undefined, filters);

  const companies = data?.pages.flatMap((page) => page.items) ?? [];
  const total = data?.pages[0]?.total ?? 0;

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

  const toggle = (list: string[], value: string, set: (v: string[]) => void) =>
    set(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);

  const clearFilters = () => {
    setSectors([]);
    setStatuses([]);
    setStage("");
    setCountry("");
    setState("");
    setCity("");
    setRitNexus("");
    setReviewed("");
    setHasWebsite("");
    setMinCompleteness("");
    setMaxCompleteness("");
    setDealroomFilters({});
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-semibold">
          Companies
          {total > 0 && <span className="ml-2 text-sm text-muted-foreground">({total})</span>}
        </h1>
        <div className="flex items-center gap-2">
          <Input
            placeholder="Search by name, domain, website, description…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="w-full sm:w-72"
          />
          <Button variant="outline" size="sm" onClick={() => setShowFilters((s) => !s)}>
            Filters{activeCount > 0 ? ` (${activeCount})` : ""}
          </Button>
        </div>
      </div>

      {showFilters && (
        <div className="space-y-4 rounded-lg border bg-muted/20 p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Filters</h2>
            {activeCount > 0 && (
              <button
                className="text-xs text-muted-foreground hover:underline"
                onClick={clearFilters}
              >
                Clear all
              </button>
            )}
          </div>

          <FilterGroup label="Sector">
            {SECTORS.map((s) => (
              <Chip
                key={s}
                active={sectors.includes(s)}
                onClick={() => toggle(sectors, s, setSectors)}
              >
                {s}
              </Chip>
            ))}
          </FilterGroup>

          <FilterGroup label="Relationship status">
            {RELATIONSHIP_STATUSES.map((s) => (
              <Chip
                key={s}
                active={statuses.includes(s)}
                onClick={() => toggle(statuses, s, setStatuses)}
              >
                {s.replace("_", " ")}
              </Chip>
            ))}
          </FilterGroup>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <TextFilter label="Stage" value={stage} onChange={setStage} placeholder="Seed, Series A" />
            <label className="space-y-1 text-xs">
              <span className="font-medium text-muted-foreground">Country</span>
              <Input
                placeholder="e.g. United States"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
              />
            </label>
            <TextFilter label="State" value={state} onChange={setState} placeholder="NY, CA" />
            <TextFilter label="City" value={city} onChange={setCity} placeholder="Rochester" />
            <TriSelect label="RIT nexus" value={ritNexus} onChange={setRitNexus} />
            <TriSelect label="Reviewed" value={reviewed} onChange={setReviewed} />
            <TriSelect label="Has website" value={hasWebsite} onChange={setHasWebsite} />
            <label className="space-y-1 text-xs">
              <span className="font-medium text-muted-foreground">Min completeness %</span>
              <Input
                type="number"
                min={0}
                max={100}
                placeholder="0"
                value={minCompleteness}
                onChange={(e) => setMinCompleteness(e.target.value)}
              />
            </label>
            <label className="space-y-1 text-xs">
              <span className="font-medium text-muted-foreground">Max completeness %</span>
              <Input
                type="number"
                min={0}
                max={100}
                placeholder="100"
                value={maxCompleteness}
                onChange={(e) => setMaxCompleteness(e.target.value)}
              />
            </label>
          </div>

          <DealroomFilters
            columns={dealroomColumns.data ?? []}
            filters={dealroomFilters}
            onChange={setDealroomFilters}
          />
        </div>
      )}

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

function splitValues(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function boundedPercent(raw: string, parsed: number): number | undefined {
  if (raw === "" || Number.isNaN(parsed)) return undefined;
  return Math.min(100, Math.max(0, parsed));
}

function encodeDealroomFilter(column: string, filter: DealroomFilterValue): string | undefined {
  const operator = filter.operator;
  const value = filter.value.trim();
  const valueTo = filter.valueTo.trim();
  if (!operator) return undefined;
  if (operator === "present" || operator === "blank") {
    return [column, operator, "", ""].join("\t");
  }
  if (operator === "number_between" || operator === "date_between") {
    return value && valueTo ? [column, operator, value, valueTo].join("\t") : undefined;
  }
  return value ? [column, operator, value, ""].join("\t") : undefined;
}

function defaultDealroomOperator(kind: DealroomColumnKind): string {
  if (kind === "number") return "number_gte";
  if (kind === "date") return "date_gte";
  if (kind === "boolean") return "yes_no";
  return "contains";
}

function DealroomFilters({
  columns,
  filters,
  onChange,
}: {
  columns: DealroomColumnOption[];
  filters: Record<string, DealroomFilterValue>;
  onChange: (filters: Record<string, DealroomFilterValue>) => void;
}) {
  const update = (column: string, next: DealroomFilterValue | undefined) => {
    const updated = { ...filters };
    if (next) {
      updated[column] = next;
    } else {
      delete updated[column];
    }
    onChange(updated);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold text-muted-foreground">Dealroom CSV filters</h3>
        {Object.keys(filters).length > 0 && (
          <button
            type="button"
            className="text-xs text-muted-foreground hover:underline"
            onClick={() => onChange({})}
          >
            Clear Dealroom
          </button>
        )}
      </div>
      <div className="max-h-[28rem] overflow-y-auto rounded-md border bg-background">
        <div className="grid gap-0 divide-y">
          {columns.map((column) => (
            <DealroomFilterRow
              key={column.name}
              column={column}
              value={filters[column.name]}
              onChange={(next) => update(column.name, next)}
            />
          ))}
          {columns.length === 0 && (
            <div className="px-3 py-4 text-sm text-muted-foreground">
              Dealroom columns are loading.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DealroomFilterRow({
  column,
  value,
  onChange,
}: {
  column: DealroomColumnOption;
  value: DealroomFilterValue | undefined;
  onChange: (value: DealroomFilterValue | undefined) => void;
}) {
  const current = value ?? {
    operator: defaultDealroomOperator(column.kind),
    value: "",
    valueTo: "",
  };

  const setOperator = (operator: string) => {
    if (!operator) {
      onChange(undefined);
      return;
    }
    onChange({ operator, value: "", valueTo: "" });
  };

  return (
    <div className="grid gap-2 px-3 py-2 text-xs md:grid-cols-[minmax(12rem,1fr)_11rem_minmax(12rem,1fr)] md:items-center">
      <div>
        <div className="font-medium">{column.name}</div>
        <div className="text-muted-foreground">{column.kind}</div>
      </div>
      <select
        value={value ? current.operator : ""}
        onChange={(e) => setOperator(e.target.value)}
        className="h-9 w-full rounded-md border border-border bg-background px-2 text-sm"
      >
        <option value="">Any</option>
        {operatorOptions(column.kind).map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <DealroomFilterInputs column={column} value={current} active={!!value} onChange={onChange} />
    </div>
  );
}

function DealroomFilterInputs({
  column,
  value,
  active,
  onChange,
}: {
  column: DealroomColumnOption;
  value: DealroomFilterValue;
  active: boolean;
  onChange: (value: DealroomFilterValue | undefined) => void;
}) {
  if (!active || value.operator === "present" || value.operator === "blank") {
    return <div />;
  }
  if (column.kind === "boolean") {
    return (
      <select
        value={value.value}
        onChange={(e) => onChange({ ...value, value: e.target.value })}
        className="h-9 w-full rounded-md border border-border bg-background px-2 text-sm"
      >
        <option value="">Choose</option>
        <option value="yes">Yes</option>
        <option value="no">No</option>
      </select>
    );
  }

  const type = column.kind === "date" ? "date" : column.kind === "number" ? "number" : "text";
  const needsSecondValue =
    value.operator === "number_between" || value.operator === "date_between";
  return (
    <div className="grid gap-2 sm:grid-cols-2">
      <Input
        type={type}
        placeholder={inputPlaceholder(column.kind, value.operator)}
        value={value.value}
        onChange={(e) => onChange({ ...value, value: e.target.value })}
      />
      {needsSecondValue && (
        <Input
          type={type}
          placeholder="To"
          value={value.valueTo}
          onChange={(e) => onChange({ ...value, valueTo: e.target.value })}
        />
      )}
    </div>
  );
}

function operatorOptions(kind: DealroomColumnKind): { value: string; label: string }[] {
  if (kind === "number") {
    return [
      { value: "number_gte", label: "At least" },
      { value: "number_lte", label: "At most" },
      { value: "number_between", label: "Between" },
      { value: "present", label: "Has value" },
      { value: "blank", label: "Blank" },
    ];
  }
  if (kind === "date") {
    return [
      { value: "date_gte", label: "On/after" },
      { value: "date_lte", label: "On/before" },
      { value: "date_between", label: "Between" },
      { value: "present", label: "Has value" },
      { value: "blank", label: "Blank" },
    ];
  }
  if (kind === "boolean") {
    return [
      { value: "yes_no", label: "Yes/no" },
      { value: "present", label: "Has value" },
      { value: "blank", label: "Blank" },
    ];
  }
  return [
    { value: "contains", label: "Contains" },
    { value: "equals", label: "Equals" },
    { value: "present", label: "Has value" },
    { value: "blank", label: "Blank" },
  ];
}

function inputPlaceholder(kind: DealroomColumnKind, operator: string): string {
  if (kind === "date") return "From";
  if (kind === "number") return operator === "number_lte" ? "Maximum" : "Minimum";
  return "Text";
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <div className="flex flex-wrap gap-1.5">{children}</div>
    </div>
  );
}

function TextFilter({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
}) {
  return (
    <label className="space-y-1 text-xs">
      <span className="font-medium text-muted-foreground">{label}</span>
      <Input placeholder={placeholder} value={value} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}

function Chip({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full border px-2.5 py-1 text-xs transition-colors ${
        active
          ? "border-primary bg-primary text-primary-foreground"
          : "border-border bg-background hover:bg-accent"
      }`}
    >
      {children}
    </button>
  );
}

function TriSelect({
  label,
  value,
  onChange,
}: {
  label: string;
  value: TriState;
  onChange: (v: TriState) => void;
}) {
  return (
    <label className="space-y-1 text-xs">
      <span className="font-medium text-muted-foreground">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as TriState)}
        className="h-9 w-full rounded-md border border-border bg-background px-2 text-sm"
      >
        <option value="">Any</option>
        <option value="yes">Yes</option>
        <option value="no">No</option>
      </select>
    </label>
  );
}
