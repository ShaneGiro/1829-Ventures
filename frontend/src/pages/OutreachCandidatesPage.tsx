import { useState } from "react";
import { Link } from "react-router-dom";
import { useOutreachCandidates } from "@/api/outreachCandidates";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StateNotice } from "@/components/ui/state";

export function OutreachCandidatesPage() {
  const [includeRecent, setIncludeRecent] = useState(false);
  const candidates = useOutreachCandidates(includeRecent);

  if (candidates.isLoading) return <StateNotice title="Loading outreach candidates" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">Outreach Candidates</h1>
          <p className="text-sm text-muted-foreground">
            Explainable ranking for the RIT alumni founder target segment.
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={includeRecent}
            onChange={(event) => setIncludeRecent(event.target.checked)}
          />
          Include recent outreach
        </label>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{candidates.data?.total ?? 0} candidates</CardTitle>
        </CardHeader>
        <CardContent>
          {candidates.error && (
            <p className="text-sm text-destructive">{candidates.error.message}</p>
          )}
          {candidates.data?.items.length ? (
            <div className="divide-y rounded-md border">
              {candidates.data.items.map((candidate) => (
                <div
                  key={candidate.company.id}
                  className="grid gap-3 p-4 lg:grid-cols-[5rem_minmax(14rem,1fr)_12rem_12rem_8rem]"
                >
                  <div>
                    <div className="text-2xl font-semibold">{Math.round(candidate.score)}</div>
                    <div className="text-xs text-muted-foreground">score</div>
                  </div>
                  <div className="min-w-0">
                    <Link
                      className="font-medium hover:underline"
                      to={`/companies/${candidate.company.id}`}
                    >
                      {candidate.company.name}
                    </Link>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {candidate.why_this_company}
                    </p>
                    {!!candidate.warnings.length && (
                      <details className="mt-2 text-xs text-amber-700">
                        <summary>{candidate.warnings.length} warnings</summary>
                        <ul className="ml-4 list-disc pt-1">
                          {candidate.warnings.map((warning) => (
                            <li key={warning}>{warning}</li>
                          ))}
                        </ul>
                      </details>
                    )}
                  </div>
                  <VerificationBadge
                    label="RIT founder"
                    status={candidate.company.alumni_founder_status}
                    confidence={candidate.company.alumni_founder_confidence}
                  />
                  <VerificationBadge
                    label="Operating"
                    status={candidate.company.operational_status}
                    confidence={candidate.company.operational_confidence}
                  />
                  <div className="text-sm">
                    <div>{candidate.company.stage || "Stage unknown"}</div>
                    <Link className="text-primary hover:underline" to="/outreach">
                      Log outreach
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No eligible candidates. Verify company founder and operational evidence first.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function VerificationBadge({
  label,
  status,
  confidence,
}: {
  label: string;
  status: string;
  confidence?: number | null;
}) {
  return (
    <div className="space-y-1 text-sm">
      <div className="text-xs text-muted-foreground">{label}</div>
      <Badge
        className={
          status === "active" || status === "operational"
            ? "border-emerald-300 bg-emerald-50 text-emerald-800"
            : undefined
        }
      >
        {status.replaceAll("_", " ")}
      </Badge>
      <div className="text-xs text-muted-foreground">
        {confidence === null || confidence === undefined
          ? "Not scored"
          : `${Math.round(confidence * 100)}% confidence`}
      </div>
    </div>
  );
}
