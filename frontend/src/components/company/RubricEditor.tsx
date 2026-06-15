import { useEffect, useState } from "react";
import { useDealRubric, useUpdateRubric } from "@/api/deals";
import type { RubricUpdate } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/input";
import { StateNotice } from "@/components/ui/state";

const GATES: { key: keyof RubricUpdate; label: string }[] = [
  { key: "gate_rit_connection", label: "RIT connection" },
  { key: "gate_thesis_alignment", label: "Thesis alignment" },
  { key: "gate_stage_seed_to_series_a", label: "Stage: seed–Series A" },
  { key: "gate_tech_enabled", label: "Tech-enabled" },
];

const CATEGORIES: { label: string; fields: { key: keyof RubricUpdate; label: string }[] }[] = [
  {
    label: "Team (×5)",
    fields: [
      { key: "commercial_technical_balance", label: "Commercial/technical balance" },
      { key: "coachability_grit", label: "Coachability & grit" },
      { key: "talent_magnetism", label: "Talent magnetism" },
    ],
  },
  {
    label: "Tech (×4)",
    fields: [
      { key: "ip_protection", label: "IP protection" },
      { key: "external_validation", label: "External validation" },
      { key: "development_stage", label: "Development stage" },
    ],
  },
  {
    label: "Commercial (×5)",
    fields: [
      { key: "capital_efficiency", label: "Capital efficiency" },
      { key: "path_to_revenue", label: "Path to revenue" },
      { key: "market_pain", label: "Market pain" },
      { key: "unit_economics", label: "Unit economics" },
    ],
  },
  {
    label: "RIT Fit (×4)",
    fields: [
      { key: "structural_advantage", label: "Structural advantage" },
      { key: "talent_pipeline", label: "Talent pipeline" },
      { key: "mission_alignment", label: "Mission alignment" },
    ],
  },
  {
    label: "Deal Dynamics (×2)",
    fields: [
      { key: "syndicate_strength", label: "Syndicate strength" },
      { key: "valuation_discipline", label: "Valuation discipline" },
    ],
  },
];

/** In-page fillable screening rubric for the active deal — no separate page. */
export function RubricEditor({ dealId }: { dealId: string }) {
  const { data: rubric, isLoading } = useDealRubric(dealId);
  const update = useUpdateRubric(dealId);
  const [form, setForm] = useState<RubricUpdate>({});

  useEffect(() => {
    if (!rubric) return;
    const keys: (keyof RubricUpdate)[] = [
      ...GATES.map((g) => g.key),
      ...CATEGORIES.flatMap((c) => c.fields.map((f) => f.key)),
      "notes",
    ];
    const source = rubric as Record<string, unknown>;
    const next: Record<string, unknown> = {};
    for (const key of keys) {
      if (source[key] !== undefined && source[key] !== null) next[key] = source[key];
    }
    setForm(next as RubricUpdate);
  }, [rubric]);

  if (isLoading) return <StateNotice title="Loading rubric" />;

  const setScore = (key: keyof RubricUpdate, value: number | null) =>
    setForm((f) => ({ ...f, [key]: value }));
  const setGate = (key: keyof RubricUpdate, value: boolean | null) =>
    setForm((f) => ({ ...f, [key]: value }));

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <CardTitle>Screening rubric</CardTitle>
        <div className="flex flex-wrap items-center gap-3">
          {rubric?.composite_score != null && (
            <span className="text-sm font-medium">Composite: {rubric.composite_score}/100</span>
          )}
          <Button size="sm" onClick={() => update.mutate(form)} disabled={update.isPending}>
            {update.isPending ? "Saving…" : "Save rubric"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <div>
          <div className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
            Knockout gates
          </div>
          <div className="flex flex-wrap gap-4">
            {GATES.map(({ key, label }) => (
              <label key={key} className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form[key] === true}
                  onChange={(e) => setGate(key, e.target.checked ? true : false)}
                />
                {label}
              </label>
            ))}
          </div>
        </div>

        {CATEGORIES.map((cat) => (
          <div key={cat.label}>
            <div className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
              {cat.label}
            </div>
            <div className="space-y-2">
              {cat.fields.map(({ key, label }) => (
                <div key={key} className="flex items-center justify-between gap-4">
                  <span className="text-sm">{label}</span>
                  <select
                    className="h-8 rounded-md border border-border bg-background px-2 text-sm"
                    value={(form[key] as number | null | undefined) ?? ""}
                    onChange={(e) =>
                      setScore(key, e.target.value === "" ? null : Number(e.target.value))
                    }
                  >
                    <option value="">–</option>
                    {[1, 2, 3, 4, 5].map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          </div>
        ))}

        <div>
          <div className="mb-1 text-xs font-semibold uppercase text-muted-foreground">Notes</div>
          <Textarea
            value={form.notes ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
          />
        </div>
      </CardContent>
    </Card>
  );
}
