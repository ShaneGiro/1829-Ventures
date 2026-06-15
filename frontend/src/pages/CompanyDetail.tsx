import { useParams } from "react-router-dom";
import { useCompany, useCompanyCompleteness } from "@/api/companies";
import { useDeals } from "@/api/deals";
import { useInteractions } from "@/api/interactions";
import { useTasks } from "@/api/tasks";
import { useDocuments } from "@/api/documents";
import { RubricEditor } from "@/components/company/RubricEditor";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StateNotice } from "@/components/ui/state";

export function CompanyDetail() {
  const { companyId } = useParams<{ companyId: string }>();
  const { data: company, isLoading } = useCompany(companyId);
  const { data: completeness } = useCompanyCompleteness(companyId);
  const { data: deals } = useDeals({ company_id: companyId });
  const { data: interactions } = useInteractions({ company_id: companyId, limit: 10 });
  const { data: tasks } = useTasks({ company_id: companyId, limit: 10 });
  const { data: documents } = useDocuments({ company_id: companyId, limit: 10 });

  if (isLoading) return <StateNotice title="Loading company" />;
  if (!company) return <StateNotice title="Company not found" />;

  const activeDeal = deals?.items.find((d) => !d.archived_at) ?? deals?.items[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="break-words text-2xl font-semibold">{company.name}</h1>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
            <Badge>{company.relationship_status}</Badge>
            {company.sector && <span>{company.sector}</span>}
            {company.website && (
              <a href={company.website} className="hover:underline" target="_blank" rel="noreferrer">
                {company.website}
              </a>
            )}
          </div>
        </div>
        <div className="sm:text-right">
          <div className="text-xs uppercase text-muted-foreground">Completeness</div>
          <div className="text-xl font-semibold">
            {Math.round(completeness?.completeness_pct ?? company.completeness_pct ?? 0)}%
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          {activeDeal ? (
            <RubricEditor dealId={activeDeal.id} />
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Screening rubric</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                No active deal yet — create a deal to score this company.
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Recent interactions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {interactions?.items.length ? (
                interactions.items.map((i) => (
                  <div key={i.id} className="text-sm">
                    <span className="font-medium">{i.interaction_type}</span>
                    {i.summary ? ` — ${i.summary}` : ""}
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No interactions yet.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1 text-sm">
              <Field label="Stage" value={company.stage} />
              <Field
                label="Location"
                value={[company.city, company.state, company.country].filter(Boolean).join(", ")}
              />
              <Field label="Domain" value={company.domain} />
              <Field label="Source" value={company.source_system} />
              <Field label="Dealroom ID" value={company.dealroom_id} />
              <Field label="RIT nexus" value={company.has_rit_nexus ? "Yes" : "No"} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Open tasks</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              {tasks?.items.length ? (
                tasks.items.map((t) => (
                  <div key={t.id} className="text-sm">
                    {t.title} <Badge>{t.status}</Badge>
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No tasks.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Documents</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              {documents?.items.length ? (
                documents.items.map((d) => (
                  <div key={d.id} className="truncate text-sm">
                    {d.filename}
                  </div>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No documents.</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="min-w-0 break-words text-right">{value || "—"}</span>
    </div>
  );
}
