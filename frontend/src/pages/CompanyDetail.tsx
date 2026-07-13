import { useEffect, useMemo, useState, useRef } from "react";
import type { ReactNode } from "react";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  useCompany,
  useCompanyDealroomData,
  useUpdateCompany,
} from "@/api/companies";
import type { Company, CompanyUpdate } from "@/api/types";
import { useInteractions } from "@/api/interactions";
import { useTasks } from "@/api/tasks";
import { RubricEditor } from "@/components/company/RubricEditor";
import { DocumentPanel } from "@/components/document/DocumentPanel";
import { TaskCreateDialog } from "@/components/task/TaskCreateDialog";
import { TaskItem } from "@/components/task/TaskItem";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { StateNotice } from "@/components/ui/state";
import { formatDecimal } from "@/lib/utils";

const FUNDING_FIELDS = [
  "Total funding (USD M)",
  "Last round",
  "Last funding amount",
  "Last funding date",
  "First funding date",
  "Seed year",
  "Total rounds number",
  "Investors names",
  "Lead investors",
];

const SIGNAL_FIELDS = [
  "Dealroom Signal - Rating",
  "Dealroom Signal - Completeness",
  "Dealroom Signal - Team strength",
  "Dealroom Signal - Growth rate",
  "Dealroom Signal - Timing",
  "Innovation corporate rank",
  "Number of patents",
];

const WEB_FIELDS = [
  "Website traffic estimate yearly growth",
  "Website traffic estimate 6 months",
  "Website traffic rank 3/6/12 months",
  "Income streams",
];

const SOCIAL_FIELDS = ["LinkedIn", "Twitter", "Facebook", "Google Play link", "iTunes"];

export function CompanyDetail() {
  const { companyId } = useParams<{ companyId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  // Go back to wherever the user came from; fall back to the company list when
  // this page was opened directly (no in-app history to return to).
  const goBack = () => {
    if (location.key === "default") navigate("/companies");
    else navigate(-1);
  };
  const { data: company, isLoading } = useCompany(companyId);
  const { data: dealroom } = useCompanyDealroomData(companyId);
  const { data: interactions } = useInteractions({ company_id: companyId, limit: 10 });
  const updateCompany = useUpdateCompany(companyId ?? "");

  if (isLoading) return <StateNotice title="Loading company" />;
  if (!company) return <StateNotice title="Company not found" />;

  const raw = (dealroom?.raw ?? {}) as Record<string, unknown>;
  const normalized = (dealroom?.normalized ?? {}) as Record<string, unknown>;
  const description = text(raw["Long description"]) || company.description;
  const tagline = text(raw.Tagline);
  const metricSeries = getMetricSeries(raw);
  const metricYears = getMetricYears(raw, metricSeries);

  return (
    <div className="space-y-6">
      <button
        type="button"
        onClick={goBack}
        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </button>

      <CompanyHeader
        name={company.name}
        status={company.relationship_status}
        sector={company.sector}
        website={company.website}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(22rem,1fr)]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>What they do</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {tagline && <p className="text-base font-medium">{tagline}</p>}
              <p className="whitespace-pre-wrap text-sm leading-6 text-muted-foreground">
                {description || "No Dealroom description or CRM description has been captured yet."}
              </p>
              <div className="grid gap-3 md:grid-cols-3">
                <ObjectBlock label="Industries" values={splitStructured(raw.Industries)} />
                <ObjectBlock label="Sub industries" values={splitStructured(raw["Sub industries"])} />
                <ObjectBlock
                  label="Tags"
                  values={firstNonEmpty(splitStructured(raw["All tags"]), splitStructured(raw.Tags))}
                />
              </div>
            </CardContent>
          </Card>

          <MetricExplorer series={metricSeries} years={metricYears} />

          <Card>
            <CardHeader>
              <CardTitle>Funding history</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <FieldGrid fields={pickFields(raw, FUNDING_FIELDS)} />
              <FundingRounds raw={raw} normalized={normalized} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Team and founders</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <FieldGrid
                fields={pickFields(raw, [
                  "Team (Dealroom)",
                  "Team (Editorial)",
                  "Employees Range",
                  "Employees latest number",
                  "Founders",
                  "Founders statuses",
                  "Founders universities",
                  "Founders backgrounds",
                  "Founders linkedin",
                ])}
              />
              <Founders normalized={normalized} />
            </CardContent>
          </Card>

          <RubricEditor companyId={companyId} />

          <RawDealroomFields raw={raw} />
        </div>

        <div className="space-y-6">
          <CompanyProfileCard company={company} importRow={dealroom?.row_number} />

          <Card>
            <CardHeader>
              <CardTitle>Dealroom signals</CardTitle>
            </CardHeader>
            <CardContent>
              <SignalBars fields={pickFields(raw, SIGNAL_FIELDS)} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Web, product, and traction</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <FieldGrid
                fields={pickFields(raw, WEB_FIELDS).filter(
                  (f) =>
                    ![
                      "Website traffic estimate yearly growth",
                      "Website traffic estimate 6 months",
                      "Website traffic rank 3/6/12 months",
                    ].includes(f.label),
                )}
                compact
              />
              <ObjectBlock label="Technologies" values={splitStructured(raw.Technologies)} />
              <ObjectBlock
                label="Tech stack"
                values={splitStructured(raw["Tech stack data (by PredictLeads)"])}
              />
              <ExternalLinks fields={pickFields(raw, SOCIAL_FIELDS)} />
            </CardContent>
          </Card>

          <CompanyTasks companyId={company.id} />

          <CompanyNotes
            initialValue={company.thesis_notes ?? ""}
            onSave={(notes) => updateCompany.mutate({ thesis_notes: notes })}
            isSaving={updateCompany.isPending}
          />

          <Card>
            <CardHeader>
              <CardTitle>Recent interactions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {interactions?.items.length ? (
                interactions.items.map((i) => (
                  <div key={i.id} className="text-sm">
                    <span className="font-medium">{i.interaction_type}</span>
                    {i.summary ? ` - ${i.summary}` : ""}
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No interactions yet.</p>
              )}
            </CardContent>
          </Card>

          <DocumentPanel companyId={company.id} />
        </div>
      </div>
    </div>
  );
}

function CompanyProfileCard({ company, importRow }: { company: Company; importRow?: number | null }) {
  const updateCompany = useUpdateCompany(company.id);
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState<CompanyUpdate>({});

  function beginEditing() {
    setForm({
      name: company.name,
      website: company.website,
      description: company.description,
      sector: company.sector,
      stage: company.stage,
      city: company.city,
      state: company.state,
      country: company.country,
      relationship_status: company.relationship_status,
      has_rit_nexus: company.has_rit_nexus,
      rit_source_channel: company.rit_source_channel,
    });
    setIsEditing(true);
  }

  function updateField(field: keyof CompanyUpdate, value: string) {
    setForm((current) => ({ ...current, [field]: value || null }));
  }

  async function save() {
    await updateCompany.mutateAsync(form);
    setIsEditing(false);
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <CardTitle>Profile</CardTitle>
          <Button variant="outline" size="sm" onClick={isEditing ? () => setIsEditing(false) : beginEditing}>
            {isEditing ? "Cancel" : "Edit"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {isEditing ? (
          <>
            {(["name", "website", "sector", "stage", "city", "state", "country", "rit_source_channel"] as const).map((field) => (
              <label key={field} className="block space-y-1">
                <span className="text-xs font-medium">{field.replaceAll("_", " ")}</span>
                <Input value={String(form[field] ?? "")} onChange={(event) => updateField(field, event.target.value)} />
              </label>
            ))}
            <label className="block space-y-1">
              <span className="text-xs font-medium">Description</span>
              <Textarea value={form.description ?? ""} onChange={(event) => updateField("description", event.target.value)} />
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={form.has_rit_nexus ?? false}
                onChange={(event) => setForm((current) => ({ ...current, has_rit_nexus: event.target.checked }))}
              />
              RIT nexus
            </label>
            {updateCompany.error && <p className="text-destructive">{updateCompany.error.message}</p>}
            <Button onClick={() => void save()} disabled={updateCompany.isPending}>
              {updateCompany.isPending ? "Saving…" : "Save profile"}
            </Button>
          </>
        ) : (
          <>
            <Field label="Stage" value={company.stage} />
            <Field label="Location" value={[company.city, company.state, company.country].filter(Boolean).join(", ")} />
            <Field label="Domain" value={company.domain} />
            <Field label="Source" value={company.source_system} />
            <Field label="Dealroom ID" value={company.dealroom_id} />
            <Field label="Import row" value={importRow?.toString()} />
            <Field label="RIT nexus" value={company.has_rit_nexus ? "Yes" : "No"} />
          </>
        )}
      </CardContent>
    </Card>
  );
}

const CHART_INSET_PX = 32; // matches Tailwind inset-8 (2rem = 32px)

function CompanyHeader({
  name,
  status,
  sector,
  website,
}: {
  name: string;
  status: string;
  sector?: string | null;
  website?: string | null;
}) {
  return (
    <div className="min-w-0">
      <div className="min-w-0">
        <h1 className="break-words text-2xl font-semibold">{name}</h1>
        <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <Badge>{status}</Badge>
          {sector && <span>{sector}</span>}
          {website && (
            <a href={website} className="hover:underline" target="_blank" rel="noreferrer">
              {website}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricExplorer({ series, years }: { series: MetricSeries[]; years: number[] }) {
  const [selected, setSelected] = useState("");
  const [chartType, setChartType] = useState<"line" | "bar">("line");
  const active = useMemo(
    () => series.find((item) => item.label === selected) ?? series[0],
    [selected, series],
  );

  if (!active) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Metrics over time</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          No Dealroom time-series metrics are available for this company.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle>Metrics over time</CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={active.label}
              onChange={(e) => setSelected(e.target.value)}
              className="h-9 rounded-md border border-border bg-background px-2 text-sm"
            >
              {series.map((item) => (
                <option key={item.label} value={item.label}>
                  {item.label}
                </option>
              ))}
            </select>
            <select
              value={chartType}
              onChange={(e) => setChartType(e.target.value as "line" | "bar")}
              className="h-9 rounded-md border border-border bg-background px-2 text-sm"
            >
              <option value="line">Line</option>
              <option value="bar">Bar</option>
            </select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {chartType === "line" ? (
          <LineSeriesChart series={active} years={years} />
        ) : (
          <BarSeriesChart series={active} years={years} />
        )}
      </CardContent>
    </Card>
  );
}

function LineSeriesChart({ series, years }: { series: MetricSeries; years: number[] }) {
  const chartInnerRef = useRef<HTMLDivElement | null>(null);
  const [innerSize, setInnerSize] = useState({ w: 0, h: 0 });
  const byYear = new Map(series.points.map((point) => [point.year, point.value]));
  const linePoints = interpolateLinePoints(years, series.points);

  useEffect(() => {
    function measure() {
      const el = chartInnerRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      setInnerSize({ w: rect.width, h: rect.height });
    }
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  if (!linePoints.length) return <p className="text-sm text-muted-foreground">No values to chart.</p>;
  const scale = chartScale(linePoints.map((point) => point.value));
  const chartWidth = 1000;
  const points = linePoints.map((point, index) => {
    const x =
      years.length === 1 ? chartWidth / 2 : (index / Math.max(years.length - 1, 1)) * chartWidth;
    const y = valueToY(point.value, scale);
    return { ...point, x, y };
  });
  const polyline = points.map((point) => `${point.x},${point.y}`).join(" ");
  const actualPoints = points.filter((point) => byYear.has(point.year));

  const scaleX = innerSize.w && chartWidth ? innerSize.w / chartWidth : 1;
  const scaleY = innerSize.h ? innerSize.h / 100 : 1;
  const desiredPixelRadius = 4; // desired visible radius in px
  const rx = scaleX ? desiredPixelRadius / scaleX : 4;
  const ry = scaleY ? desiredPixelRadius / scaleY : 4;

  return (
    <ChartFrame
      scale={scale}
      years={years}
      innerWidth={innerSize.w}
      insetPx={CHART_INSET_PX}
      alignToBars={false}
    >
      <div className="rounded-md border bg-background h-64 relative">
        <div ref={chartInnerRef} className="absolute inset-8 w-auto h-auto">
          <div className="pointer-events-none absolute inset-0">
            {scale.ticks.map((tick) => (
              <div
                key={tick}
                className="absolute left-0 right-0 border-t border-muted"
                style={{ top: `${valueToY(tick, scale)}%` }}
              />
            ))}
          </div>
          <svg viewBox={`0 0 ${chartWidth} 100`} className="w-full h-full overflow-visible" preserveAspectRatio="none">
            <polyline
              points={polyline}
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              vectorEffect="non-scaling-stroke"
            />
            {actualPoints.map((point) => (
              <ellipse
                key={point.year}
                cx={point.x}
                cy={point.y}
                rx={rx}
                ry={ry}
                className="fill-primary"
              >
                <title>{`${point.year}: ${formatNumber(point.value)}`}</title>
              </ellipse>
            ))}
          </svg>
        </div>
      </div>
    </ChartFrame>
  );
}

function BarSeriesChart({ series, years }: { series: MetricSeries; years: number[] }) {
  const scale = chartScale(series.points.map((point) => point.value));
  const byYear = new Map(series.points.map((point) => [point.year, point.value]));
  const barInnerRef = useRef<HTMLDivElement | null>(null);
  const [barInnerWidth, setBarInnerWidth] = useState(0);

  useEffect(() => {
    function measure() {
      const el = barInnerRef.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      setBarInnerWidth(rect.width);
    }
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);
  return (
    <ChartFrame
      scale={scale}
      years={years}
      innerWidth={barInnerWidth}
      insetPx={CHART_INSET_PX}
      alignToBars={true}
    >
      <div className="relative flex h-64 items-end gap-1 overflow-x-auto rounded-md border bg-background p-8">
        <div ref={barInnerRef} className="pointer-events-none absolute inset-8">
          {scale.ticks.map((tick) => (
            <div
              key={tick}
              className="absolute left-0 right-0 border-t border-muted"
              style={{ top: `${valueToY(tick, scale)}%` }}
            />
          ))}
        </div>
        {years.map((year) => {
          const value = byYear.get(year);
          const height = value === undefined ? 0 : Math.max(2, valueToHeight(value, scale));
          return (
            <div key={year} className="relative flex h-full min-w-8 flex-1 flex-col justify-end">
              <div className="relative flex flex-1 items-end">
                <div
                  className={`w-full rounded-t ${value === undefined ? "bg-muted/40" : "bg-primary"
                    }`}
                  style={{ height: value === undefined ? "2px" : `${height}%` }}
                  title={
                    value === undefined ? `${year}: no data` : `${year}: ${formatNumber(value)}`
                  }
                />
              </div>
            </div>
          );
        })}
      </div>
    </ChartFrame>
  );
}

interface ChartScale {
  min: number;
  max: number;
  range: number;
  ticks: number[];
}

function ChartFrame({
  scale,
  years,
  children,
  innerWidth,
  insetPx,
  alignToBars,
}: {
  scale: ChartScale;
  years: number[];
  children: ReactNode;
  innerWidth?: number;
  insetPx?: number;
  alignToBars?: boolean;
}) {
  return (
    <div className="grid grid-cols-[6.5rem_minmax(0,1fr)] gap-3">
      <YAxis scale={scale} />
      <div className="min-w-0 space-y-2">
        {children}
        <YearAxis years={years} innerWidth={innerWidth} insetPx={insetPx} alignToBars={alignToBars} />
      </div>
    </div>
  );
}

function YAxis({ scale }: { scale: ChartScale }) {
  const labels = uniqueAxisLabels([...scale.ticks].reverse());
  return (
    <div className="flex h-64 flex-col justify-between py-6 text-right text-xs text-muted-foreground">
      {labels.map(({ tick, label }) => (
        <span key={tick} className="tabular-nums">
          {label}
        </span>
      ))}
    </div>
  );
}

function YearAxis({
  years,
  innerWidth,
  insetPx,
  alignToBars,
}: {
  years: number[];
  innerWidth?: number;
  insetPx?: number;
  alignToBars?: boolean;
}) {
  const visible = years; // show every year
  if (!years.length) return null;
  return (
    <div className="relative text-xs text-muted-foreground">
      {visible.map((year) => {
        const index = years.indexOf(year);
        const leftPercent = years.length === 1 ? 50 : (index / Math.max(years.length - 1, 1)) * 100;
        let style: Record<string, string> = {};
        if (innerWidth && typeof insetPx === "number") {
          if (alignToBars) {
            const slotWidth = innerWidth / years.length;
            const leftPx = insetPx + (index + 0.5) * slotWidth;
            style = { left: `${leftPx}px` };
          } else {
            const leftPx = insetPx + (leftPercent / 100) * innerWidth;
            style = { left: `${leftPx}px` };
          }
        } else {
          style = { left: `${leftPercent}%` };
        }
        return (
          <div key={year} style={style} className="absolute top-0 -translate-x-1/2">
            {year}
          </div>
        );
      })}
    </div>
  );
}

function chartScale(values: number[]): ChartScale {
  const numericValues = values.filter((value) => Number.isFinite(value));
  const rawMin = Math.min(...numericValues, 0);
  const rawMax = Math.max(...numericValues, 0);
  const positiveOnly = rawMin >= 0;
  const includeZeroMin = positiveOnly ? 0 : rawMin;
  const includeZeroMax = rawMax <= 0 ? 0 : rawMax;
  const span = includeZeroMax - includeZeroMin || Math.abs(includeZeroMax) || 1;
  const step = niceStep(span / 4);
  const min = positiveOnly ? 0 : normalizeAxisValue(Math.floor(includeZeroMin / step) * step);
  const max =
    normalizeAxisValue(Math.ceil(includeZeroMax / step) * step) || (positiveOnly ? step * 4 : step);
  const count = Math.max(2, Math.round((max - min) / step) + 1);
  const ticks = dedupeNumbers(
    Array.from({ length: count }, (_, index) => normalizeAxisValue(min + index * step)).filter(
      (tick) => tick >= min && tick <= max,
    ),
  );
  return { min, max, range: max - min || 1, ticks };
}

function interpolateLinePoints(
  years: number[],
  points: { year: number; value: number }[],
): { year: number; value: number }[] {
  const known = [...points].sort((a, b) => a.year - b.year);
  if (!known.length) return [];
  return years.map((year) => {
    const exact = known.find((point) => point.year === year);
    if (exact) return exact;
    const previous = [...known].reverse().find((point) => point.year < year);
    const next = known.find((point) => point.year > year);
    if (!previous) return { year, value: next?.value ?? known[0].value };
    if (!next) return { year, value: previous.value };
    const progress = (year - previous.year) / (next.year - previous.year);
    return {
      year,
      value: previous.value + (next.value - previous.value) * progress,
    };
  });
}

function valueToY(value: number, scale: ChartScale): number {
  return clamp(100 - ((value - scale.min) / scale.range) * 100, 0, 100);
}

function valueToHeight(value: number, scale: ChartScale): number {
  return clamp(((value - scale.min) / scale.range) * 100, 0, 100);
}

function uniqueAxisLabels(ticks: number[]): { tick: number; label: string }[] {
  const seen = new Set<string>();
  return ticks.map((tick) => {
    const label = formatAxisNumber(tick);
    if (seen.has(label)) return { tick, label: "" };
    seen.add(label);
    return { tick, label };
  });
}

function normalizeAxisValue(value: number): number {
  return Math.abs(value) < 1e-9 ? 0 : Number(value.toPrecision(12));
}

function dedupeNumbers(values: number[]): number[] {
  return [...new Set(values.map(normalizeAxisValue))];
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function niceStep(value: number): number {
  const exponent = Math.floor(Math.log10(value || 1));
  const base = 10 ** exponent;
  const fraction = value / base;
  if (fraction <= 1) return base;
  if (fraction <= 2) return 2 * base;
  if (fraction <= 5) return 5 * base;
  return 10 * base;
}

function FundingRounds({
  raw,
  normalized,
}: {
  raw: Record<string, unknown>;
  normalized: Record<string, unknown>;
}) {
  const normalizedRounds = Array.isArray(normalized.funding_rounds)
    ? (normalized.funding_rounds as Record<string, unknown>[])
    : [];
  const rounds = normalizedRounds.length
    ? normalizedRounds.map((round, index) => ({
      type: text(round.round_type),
      amount: text(round.amount),
      currency: text(round.currency),
      date: text(round.date),
      valuation: valuationForRound(raw, text(round.date)),
      investors: Array.isArray(round.investors)
        ? round.investors.map((item) => text(item)).filter(Boolean)
        : [],
      key: `${index}`,
    }))
    : splitParallel(raw, [
      "Each round type",
      "Each round amount",
      "Each round currency",
      "Each round date",
      "Each round investors",
    ]).map((row, index) => ({
      type: row["Each round type"],
      amount: row["Each round amount"],
      currency: row["Each round currency"],
      date: row["Each round date"],
      valuation: valuationForRound(raw, row["Each round date"]),
      investors: splitInvestors(row["Each round investors"]),
      key: `${index}`,
    }));

  if (!rounds.length) {
    return <p className="text-sm text-muted-foreground">No round-level history captured.</p>;
  }
  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="min-w-[680px] w-full text-sm">
        <thead className="bg-muted/40 text-left text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">Round</th>
            <th className="px-3 py-2">Amount</th>
            <th className="px-3 py-2">Round valuation</th>
            <th className="px-3 py-2">Date</th>
            <th className="px-3 py-2">Participants</th>
          </tr>
        </thead>
        <tbody>
          {rounds.map((round) => (
            <tr key={round.key} className="border-t">
              <td className="px-3 py-2">{round.type || "-"}</td>
              <td className="px-3 py-2">
                {[round.amount, round.currency].filter(Boolean).join(" ") || "-"}
              </td>
              <td className="px-3 py-2">{round.valuation || "-"}</td>
              <td className="px-3 py-2">{formatMonthYear(round.date) || "-"}</td>
              <td className="px-3 py-2">
                <ValueList values={Array.isArray(round.investors) ? round.investors : []} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Founders({ normalized }: { normalized: Record<string, unknown> }) {
  const founders = Array.isArray(normalized.founders)
    ? (normalized.founders as Record<string, unknown>[])
    : [];
  if (!founders.length) return null;
  return (
    <div className="grid gap-2 md:grid-cols-2">
      {founders.map((founder, index) => (
        <div key={`${text(founder.name)}-${index}`} className="rounded-md border p-3 text-sm">
          <div className="font-medium">{text(founder.name) || "Unnamed founder"}</div>
          <div className="mt-1 space-y-1 text-muted-foreground">
            <div>{text(founder.status)}</div>
            <div>{text(founder.university)}</div>
            <div>{text(founder.background)}</div>
            {text(founder.linkedin_url) && (
              <a
                className="inline-flex items-center gap-1 text-primary hover:underline"
                href={text(founder.linkedin_url)}
                target="_blank"
                rel="noreferrer"
              >
                LinkedIn <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function SignalBars({ fields }: { fields: FieldPair[] }) {
  if (!fields.length) return <p className="text-sm text-muted-foreground">No signals captured.</p>;
  return (
    <div className="space-y-3">
      {fields.map((field) => {
        const value = numeric(field.value);
        return (
          <div key={field.label} className="space-y-1 text-sm">
            <div className="flex justify-between gap-3">
              <span className="text-muted-foreground">{field.label}</span>
              <span>{formatChipValue(field.value, field.label)}</span>
            </div>
            {value !== undefined && (
              <div className="h-2 overflow-hidden rounded bg-muted">
                <div
                  className="h-full rounded bg-primary"
                  style={{ width: `${Math.max(4, Math.min(100, value))}%` }}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function RawDealroomFields({ raw }: { raw: Record<string, unknown> }) {
  const [filter, setFilter] = useState("");
  const rows = Object.entries(raw)
    .map(([label, value]) => ({ label, value: text(value) }))
    .filter((row) => row.value)
    .filter((row) => row.label.toLowerCase().includes(filter.toLowerCase()));

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <CardTitle>All Dealroom CSV fields</CardTitle>
          <Input
            className="sm:w-72"
            placeholder="Filter fields"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
      </CardHeader>
      <CardContent>
        {rows.length ? (
          <div className="max-h-[32rem] overflow-auto rounded-md border">
            <table className="min-w-[720px] w-full text-sm">
              <tbody>
                {rows.map((row) => (
                  <tr key={row.label} className="border-t first:border-t-0">
                    <td className="w-64 bg-muted/30 px-3 py-2 font-medium">{row.label}</td>
                    <td className="px-3 py-2 text-muted-foreground">
                      <StructuredCell value={row.value} label={row.label} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No Dealroom CSV payload is linked.</p>
        )}
      </CardContent>
    </Card>
  );
}

function CompanyTasks({ companyId }: { companyId: string }) {
  const { data, isLoading, isError } = useTasks({ company_id: companyId, limit: 25 });
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <CardTitle>Tasks</CardTitle>
        <Button size="sm" onClick={() => setDialogOpen(true)}>
          Add task
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        {isLoading && <p className="text-sm text-muted-foreground">Loading tasks…</p>}
        {isError && <p className="text-sm text-destructive">Could not load tasks.</p>}
        {data?.items.length
          ? data.items.map((t) => <TaskItem key={t.id} task={t} />)
          : !isLoading && <p className="text-sm text-muted-foreground">No tasks yet.</p>}
      </CardContent>
      <TaskCreateDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        defaultCompanyId={companyId}
      />
    </Card>
  );
}

function CompanyNotes({
  initialValue,
  onSave,
  isSaving,
}: {
  initialValue: string;
  onSave: (notes: string) => void;
  isSaving: boolean;
}) {
  const [notes, setNotes] = useState(initialValue);

  useEffect(() => {
    setNotes(initialValue);
  }, [initialValue]);

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <CardTitle>Company notes</CardTitle>
        <Button size="sm" onClick={() => onSave(notes)} disabled={isSaving}>
          {isSaving ? "Saving..." : "Save notes"}
        </Button>
      </CardHeader>
      <CardContent>
        <Textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add thesis notes, diligence context, follow-ups, or internal observations."
        />
      </CardContent>
    </Card>
  );
}

function FieldGrid({ fields, compact = false }: { fields: FieldPair[]; compact?: boolean }) {
  if (!fields.length) return <p className="text-sm text-muted-foreground">No data captured.</p>;
  return (
    <div className={`grid gap-3 ${compact ? "" : "md:grid-cols-2"}`}>
      {fields.map((field) => (
        <FieldBlock key={field.label} label={field.label} value={field.value} />
      ))}
    </div>
  );
}

function ObjectBlock({ label, values }: { label: string; values: string[] }) {
  return (
    <div className="min-w-0 rounded-md border p-3 text-sm">
      <div className="text-xs font-medium uppercase text-muted-foreground">{label}</div>
      <div className="mt-2">
        <ValueList values={values} chip label={label} />
      </div>
    </div>
  );
}

function ValueList({ values, chip = false, label }: { values: string[]; chip?: boolean; label?: string }) {
  const cleaned = values.map((value) => value.trim()).filter(Boolean);
  if (!cleaned.length) return <span>-</span>;
  return (
    <div className={chip ? "flex flex-wrap gap-1.5" : "space-y-1"}>
      {cleaned.map((value, index) => (
        <div
          key={`${value}-${index}`}
          className={
            chip
              ? "rounded-md border bg-muted/30 px-2 py-1 text-xs"
              : "rounded-sm bg-muted/30 px-2 py-1"
          }
        >
          {chip ? formatChipValue(value, label) : formatMonthYear(value)}
        </div>
      ))}
    </div>
  );
}

function StructuredCell({ value, chip = false, label }: { value: string; chip?: boolean; label?: string }) {
  const values = splitStructured(value);
  if (values.length <= 1) {
    if (chip) return <ValueList values={values.filter(Boolean)} chip label={label} />;
    return <span>{formatMonthYear(value)}</span>;
  }
  return <ValueList values={values} chip={chip} label={label} />;
}

function FieldBlock({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="min-w-0 rounded-md border p-3 text-sm">
      <div className="text-xs font-medium uppercase text-muted-foreground">{label}</div>
      <div className="mt-1 break-words">
        {value ? <StructuredCell value={value} chip label={label} /> : "-"}
      </div>
    </div>
  );
}

function ExternalLinks({ fields }: { fields: FieldPair[] }) {
  const links = fields.filter((field) => /^https?:\/\//i.test(field.value));
  if (!links.length) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {links.map((field) => (
        <a
          key={field.label}
          href={field.value}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs hover:bg-accent"
        >
          {field.label} <ExternalLink className="h-3 w-3" />
        </a>
      ))}
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="min-w-0 break-words text-right">{value || "-"}</span>
    </div>
  );
}

interface FieldPair {
  label: string;
  value: string;
}

interface MetricSeries {
  label: string;
  points: { year: number; value: number }[];
}

function pickFields(raw: Record<string, unknown>, labels: string[]): FieldPair[] {
  return labels
    .map((label) => ({ label, value: text(raw[label]) }))
    .filter((field): field is FieldPair => Boolean(field.value));
}

function getMetricSeries(raw: Record<string, unknown>): MetricSeries[] {
  const explicitSourceLabels = new Set([
    "Revenue (USD) (2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "EV/Revenue (2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "EBITDA (USD) (2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
    "EV/EBITDA (2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
  ]);
  const explicit = [
    parseNamedSeries(
      "Revenue",
      "Revenue (USD) (2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
      raw,
    ),
    parseNamedSeries(
      "EV/Revenue",
      "EV/Revenue (2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
      raw,
    ),
    parseNamedSeries(
      "EBITDA",
      "EBITDA (USD) (2016,2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
      raw,
    ),
    parseNamedSeries(
      "EV/EBITDA",
      "EV/EBITDA (2017,2018,2019,2020,2021,2022,2023,2024,2025,2026,2027)",
      raw,
    ),
  ];
  const direct = Object.entries(raw)
    .filter(([label]) => !explicitSourceLabels.has(label))
    .map(([label, value]) => parseSeries(label, text(value)))
    .filter((series): series is MetricSeries => Boolean(series && series.points.length >= 2));
  return dedupeSeries([
    ...explicit,
    cumulativeFundingSeries(raw),
    historicalValuationSeries(raw),
    ...direct,
    websiteTrafficSeries(raw),
  ]);
}

function parseNamedSeries(
  displayLabel: string,
  sourceLabel: string,
  raw: Record<string, unknown>,
): MetricSeries | undefined {
  const series = parseSeries(sourceLabel, text(raw[sourceLabel]));
  return series ? { ...series, label: displayLabel } : undefined;
}

function parseSeries(label: string, rawValue: string): MetricSeries | undefined {
  const match = label.match(/\(([^)]+)\)\s*$/);
  if (!match || !rawValue) return undefined;
  const years = match[1]
    .split(",")
    .map((item) => Number(item.trim()))
    .filter((year) => Number.isInteger(year) && year >= 1900);
  if (years.length < 2) return undefined;
  const values = splitCell(rawValue).map(numeric);
  const points = years
    .map((year, index) => ({ year, value: values[index] }))
    .filter((point): point is { year: number; value: number } => point.value !== undefined);
  return points.length ? { label: label.replace(/\s*\([^)]+\)\s*$/, ""), points } : undefined;
}

function cumulativeFundingSeries(raw: Record<string, unknown>): MetricSeries | undefined {
  const rows = splitParallel(raw, ["Each round amount", "Each round date"]);
  const byYear = new Map<number, number>();
  for (const row of rows) {
    const year = yearFromText(row["Each round date"]);
    const amount = numeric(row["Each round amount"]);
    if (year === undefined || amount === undefined) continue;
    byYear.set(year, (byYear.get(year) ?? 0) + amount);
  }
  if (!byYear.size) return undefined;
  const currentYear = new Date().getFullYear();
  const firstYear = Math.min(...byYear.keys());
  let running = 0;
  const cumulative = new Map<number, number>();
  for (let year = firstYear; year <= currentYear; year += 1) {
    running += byYear.get(year) ?? 0;
    cumulative.set(year, running);
  }
  return mapToSeries("Cumulative funding", cumulative);
}

function historicalValuationSeries(raw: Record<string, unknown>): MetricSeries | undefined {
  const dates = splitStructured(raw["Historical valuations - dates"]);
  const values = splitStructured(raw["Historical valuations - values (USD M)"]).map(numeric);
  const byYear = new Map<number, number>();
  dates.forEach((date, index) => {
    const year = yearFromText(date);
    const value = values[index];
    if (year !== undefined && value !== undefined) byYear.set(year, value);
  });
  if (!byYear.size) return undefined;
  const currentYear = new Date().getFullYear();
  const firstYear = Math.min(...byYear.keys());
  let latest = byYear.get(firstYear) ?? 0;
  const carried = new Map<number, number>();
  for (let year = firstYear; year <= currentYear; year += 1) {
    latest = byYear.get(year) ?? latest;
    carried.set(year, latest);
  }
  return mapToSeries("Historical valuation", carried);
}

function websiteTrafficSeries(raw: Record<string, unknown>): MetricSeries | undefined {
  const rankValues = splitStructured(raw["Website traffic rank 3/6/12 months"]).map(numeric);
  if (rankValues.length >= 2) {
    const currentYear = new Date().getFullYear();
    const byYear = new Map<number, number>();
    const labels = [currentYear, currentYear, currentYear - 1];
    rankValues.slice(0, 3).forEach((value, index) => {
      if (value !== undefined) byYear.set(labels[index], value);
    });
    const rankSeries = mapToSeries("Website traffic rank", byYear);
    if (rankSeries) return rankSeries;
  }
  const growth = numeric(text(raw["Website traffic estimate yearly growth"]));
  const current = numeric(text(raw["Website traffic estimate 6 months"]));
  if (growth === undefined || current === undefined) return undefined;
  const currentYear = new Date().getFullYear();
  return {
    label: "Website traffic estimate",
    points: [
      { year: currentYear - 1, value: current / (1 + growth / 100) },
      { year: currentYear, value: current },
    ],
  };
}

function mapToSeries(label: string, values: Map<number, number>): MetricSeries | undefined {
  const points = [...values.entries()]
    .map(([year, value]) => ({ year, value }))
    .sort((a, b) => a.year - b.year);
  return points.length >= 2 ? { label, points } : undefined;
}

function dedupeSeries(series: (MetricSeries | undefined)[]): MetricSeries[] {
  const seen = new Set<string>();
  const result: MetricSeries[] = [];
  for (const item of series) {
    if (!item || seen.has(item.label)) continue;
    seen.add(item.label);
    result.push(item);
  }
  return result;
}

function getMetricYears(raw: Record<string, unknown>, series: MetricSeries[]): number[] {
  const currentYear = new Date().getFullYear();
  const candidates = [
    numeric(text(raw["Launch year"])),
    numeric(text(raw["Seed year"])),
    yearFromText(text(raw["First funding date"])),
    ...series.flatMap((item) => item.points.map((point) => point.year)),
  ].filter((year): year is number => year !== undefined && year >= 1900 && year <= currentYear);
  const start = Math.min(...candidates, currentYear);
  return Array.from({ length: currentYear - start + 1 }, (_, index) => start + index);
}

function splitParallel(raw: Record<string, unknown>, labels: string[]): Record<string, string>[] {
  const columns = labels.map((label) => ({ label, values: splitCell(text(raw[label])) }));
  const count = Math.max(...columns.map((column) => column.values.length), 0);
  return Array.from({ length: count }, (_, index) =>
    Object.fromEntries(columns.map((column) => [column.label, column.values[index] ?? ""])),
  ).filter((row) => Object.values(row).some(Boolean));
}

function splitCell(value: string): string[] {
  if (!value) return [];
  return value
    .split(";")
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitStructured(value: unknown): string[] {
  const rendered = text(value);
  if (!rendered) return [];
  const separator = rendered.includes(";") ? ";" : ",";
  return rendered
    .split(separator)
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitInvestors(value: string): string[] {
  if (!value) return [];
  return value
    .split(/\+\+|;|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formatMonthYear(value: string): string {
  if (!value) return value;
  const trimmed = value.trim();
  const m = trimmed.match(/^([A-Za-z]{3})[/-](\d{4})$/);
  if (m) {
    const month = m[1];
    return month[0].toUpperCase() + month.slice(1).toLowerCase() + " " + m[2];
  }
  return value;
}

function formatChipValue(value: string, label?: string): string {
  if (!value) return value;
  const trimmed = value.trim();
  const percentMatch = trimmed.match(/^([\d,.-]+)\s*%$/);
  const numericStr = percentMatch ? percentMatch[1] : trimmed;
  const n = Number(numericStr.replace(/,/g, ""));
  if (Number.isFinite(n)) {
    const twoDecimalLabels = new Set([
      "Total funding (USD M)",
      "Last funding amount",
    ]);
    const lower = (label || "").toLowerCase();
    const isTwoDecimal = twoDecimalLabels.has(label || "") ||
      lower.includes("total fund") ||
      lower.includes("last fund");
    if (isTwoDecimal) {
      return new Intl.NumberFormat("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(n);
    }
    const percentLabels = new Set(["Website traffic estimate yearly growth"]);
    const isPercent = percentLabels.has(label || "") || lower.includes("website traffic estimate yearly growth") || lower.includes("yearly growth");
    return isPercent ? `${Math.round(n)}%` : `${Math.round(n)}`;
  }
  return formatMonthYear(value);
}

function firstNonEmpty(...values: string[][]): string[] {
  return values.find((items) => items.length > 0) ?? [];
}

function yearFromText(value: string): number | undefined {
  const match = value.match(/\b(19|20)\d{2}\b/);
  if (!match) return undefined;
  const year = Number(match[0]);
  return Number.isInteger(year) ? year : undefined;
}

function valuationForRound(raw: Record<string, unknown>, roundDate: string): string {
  const valuationDates = splitStructured(raw["Historical valuations - dates"]);
  const valuationValues = splitStructured(raw["Historical valuations - values (USD M)"]);
  if (!valuationDates.length || !valuationValues.length) return "";
  const exact = valuationDates.findIndex((date) => date === roundDate);
  if (exact >= 0 && valuationValues[exact]) return `${valuationValues[exact]} USD M`;
  const year = roundDate.slice(0, 4);
  const yearMatch = valuationDates.findIndex((date) => date.startsWith(year));
  return yearMatch >= 0 && valuationValues[yearMatch] ? `${valuationValues[yearMatch]} USD M` : "";
}

function text(value: unknown): string {
  if (value === null || value === undefined) return "";
  if (Array.isArray(value)) return value.map(text).filter(Boolean).join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value).trim();
}

function numeric(value: string): number | undefined {
  const parsed = Number(value.replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : undefined;
}

function formatNumber(value: number): string {
  return formatDecimal(value);
}

function formatAxisNumber(value: number): string {
  const normalized = normalizeAxisValue(value);
  return new Intl.NumberFormat("en-US", {
    notation: Math.abs(normalized) >= 10000 ? "compact" : "standard",
    maximumFractionDigits: Math.abs(normalized) < 10 ? 2 : 1,
  }).format(normalized);
}
