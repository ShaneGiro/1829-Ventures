import { useEffect, useState } from "react";
import {
  useCompanyRubric,
  useUpdateCompanyRubric,
} from "@/api/companies";
import { useDealRubric, useUpdateRubric } from "@/api/deals";
import type { RubricUpdate } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/input";
import { StateNotice } from "@/components/ui/state";

const GATES: { key: keyof RubricUpdate; label: string; question: string }[] = [
  {
    key: "gate_rit_connection",
    label: "RIT Connection",
    question: "Is there a founder, C-suite, or IP link to RIT?",
  },
  {
    key: "gate_thesis_alignment",
    label: "Thesis Alignment",
    question:
      "Does it fall into Photonics/Quantum, Clean Tech, Life Science, or Intelligent Systems?",
  },
  {
    key: "gate_stage_seed_to_series_a",
    label: "Stage",
    question: "Is it Seed to Series A?",
  },
  {
    key: "gate_tech_enabled",
    label: "Tech-Enabled",
    question:
      'Is there proprietary IP or a "Hard Tech" barrier to entry? We do not fund pure services/apps.',
  },
];

const CATEGORIES: {
  label: string;
  subtitle: string;
  weight: string;
  fields: { key: keyof RubricUpdate; label: string; question: string }[];
}[] = [
  {
    label: 'Team Composition: "Technical Builders"',
    subtitle: "Team (Builders)",
    weight: "Weight: 25%",
    fields: [
      {
        key: "commercial_technical_balance",
        label: "Commercial/Technical Balance",
        question:
          "Does the founding team have both deep domain expertise and a commercial leader who can sell?",
      },
      {
        key: "coachability_grit",
        label: "Coachability/Grit",
        question: "Evidence of pivoting based on data? Are they defensive or receptive?",
      },
      {
        key: "talent_magnetism",
        label: "Talent Magnetism",
        question:
          "Have they convinced high-quality people, advisors, or early hires to join for equity?",
      },
    ],
  },
  {
    label: 'Technical Defensibility: The "Moat"',
    subtitle: "Tech (Defensibility)",
    weight: "Weight: 20%",
    fields: [
      {
        key: "ip_protection",
        label: "IP Protection",
        question: "Are there patents filed/granted? Is the IP defensible or trade-secret based?",
      },
      {
        key: "external_validation",
        label: "External Validation",
        question:
          "Has the tech been validated by third parties such as journals, RIT faculty review, or paid pilots?",
      },
      {
        key: "development_stage",
        label: "Development Stage",
        question:
          'Is it a concept, prototype, or deployed product? Higher score for "Hardware in the Loop".',
      },
    ],
  },
  {
    label: 'Commercial Viability: "Capital Efficiency"',
    subtitle: "Commercial (Efficiency)",
    weight: "Weight: 25%",
    fields: [
      {
        key: "capital_efficiency",
        label: "Capital Efficiency",
        question:
          "Have they leveraged grants, competitions, or customer deposits to de-risk before asking for equity?",
      },
      {
        key: "path_to_revenue",
        label: "Path to Revenue",
        question: "Is there a clear LOI or contract pipeline?",
      },
      {
        key: "market_pain",
        label: "Market Pain",
        question: 'Is this a "Vitamin" or a "Painkiller"?',
      },
      {
        key: "unit_economics",
        label: "Unit Economics",
        question: "Do the margins make sense at scale?",
      },
    ],
  },
  {
    label: 'The RIT Leverage: "Force Multiplier"',
    subtitle: "RIT Fit (Leverage)",
    weight: "Weight: 20%",
    fields: [
      {
        key: "structural_advantage",
        label: "Structural Advantage",
        question:
          "Does 1829 Ventures investing here give them an unfair advantage through RIT facilities, faculty, or infrastructure?",
      },
      {
        key: "talent_pipeline",
        label: "Talent Pipeline",
        question: "Can they utilize RIT co-ops or hires to lower their burn rate?",
      },
      {
        key: "mission_alignment",
        label: "Mission Alignment",
        question: "Does the success of this company enhance the RIT brand?",
      },
    ],
  },
  {
    label: 'Deal Dynamics: "Risk Mitigation"',
    subtitle: "Deal Dynamics",
    weight: "Weight: 10%",
    fields: [
      {
        key: "syndicate_strength",
        label: "Syndicate Strength",
        question: 'Who is leading? Are we following a "Smart Lead" or are we the only capital?',
      },
      {
        key: "valuation_discipline",
        label: "Valuation Discipline",
        question: "Is the entry price reasonable for the stage?",
      },
    ],
  },
];

/** PDF-aligned fillable screening rubric. Stores values in the persisted rubric row. */
export function RubricEditor({
  dealId,
  companyId,
}: {
  dealId?: string;
  companyId?: string;
}) {
  const companyRubric = useCompanyRubric(companyId);
  const dealRubric = useDealRubric(companyId ? undefined : dealId);
  const updateCompany = useUpdateCompanyRubric(companyId ?? "");
  const updateDeal = useUpdateRubric(dealId ?? "");
  const rubric = companyId ? companyRubric.data : dealRubric.data;
  const isLoading = companyId ? companyRubric.isLoading : dealRubric.isLoading;
  const isSaving = companyId ? updateCompany.isPending : updateDeal.isPending;
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
  const save = () => {
    if (companyId) updateCompany.mutate(form);
    else updateDeal.mutate(form);
  };

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle>1829 Ventures Screening Rubric</CardTitle>
          <p className="mt-1 text-sm text-muted-foreground">
            Score each sub-category on a scale of 1 weak to 5 exceptional.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {rubric?.composite_score != null && (
            <span className="text-sm font-medium">Total: {rubric.composite_score}/100</span>
          )}
          <Button size="sm" onClick={save} disabled={isSaving}>
            {isSaving ? "Saving..." : "Save rubric"}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        <ScoreBands />
        <div>
          <div className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
            Knockout Gate
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {GATES.map(({ key, label, question }) => (
              <div key={key} className="rounded-md border p-3">
                <div className="font-medium">{label}</div>
                <p className="mt-1 text-sm text-muted-foreground">{question}</p>
                <select
                  className="mt-2 h-8 rounded-md border border-border bg-background px-2 text-sm"
                  value={
                    form[key] === true ? "true" : form[key] === false ? "false" : ""
                  }
                  onChange={(e) =>
                    setGate(
                      key,
                      e.target.value === "" ? null : e.target.value === "true",
                    )
                  }
                >
                  <option value="">Unanswered</option>
                  <option value="true">Pass</option>
                  <option value="false">Fail</option>
                </select>
              </div>
            ))}
          </div>
        </div>

        {CATEGORIES.map((cat) => (
          <div key={cat.label} className="rounded-md border p-3">
            <div className="mb-3 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="font-semibold">{cat.label}</div>
                <div className="text-sm text-muted-foreground">{cat.subtitle}</div>
              </div>
              <BadgeLike>{cat.weight}</BadgeLike>
            </div>
            <div className="space-y-3">
              {cat.fields.map(({ key, label, question }) => (
                <div key={key} className="grid gap-2 md:grid-cols-[minmax(0,1fr)_6rem]">
                  <div>
                    <div className="text-sm font-medium">{label}</div>
                    <p className="text-sm text-muted-foreground">{question}</p>
                  </div>
                  <select
                    className="h-9 rounded-md border border-border bg-background px-2 text-sm"
                    value={(form[key] as number | null | undefined) ?? ""}
                    onChange={(e) =>
                      setScore(key, e.target.value === "" ? null : Number(e.target.value))
                    }
                  >
                    <option value="">-</option>
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
          <div className="mb-1 text-xs font-semibold uppercase text-muted-foreground">
            Rubric notes
          </div>
          <Textarea
            value={form.notes ?? ""}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
          />
        </div>
      </CardContent>
    </Card>
  );
}

function ScoreBands() {
  return (
    <div className="grid gap-2 text-sm md:grid-cols-3">
      <Band label="80-100" value="Move to deep diligence immediately." />
      <Band label="70-79" value='Hold. Can we fix the missing key element?' />
      <Band label="Below 70" value="Move on to the next deal." />
    </div>
  );
}

function Band({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-muted/20 p-3">
      <div className="font-semibold">{label}</div>
      <div className="text-muted-foreground">{value}</div>
    </div>
  );
}

function BadgeLike({ children }: { children: React.ReactNode }) {
  return (
    <span className="w-fit rounded-md border bg-background px-2 py-1 text-xs text-muted-foreground">
      {children}
    </span>
  );
}
