import { useParams } from "react-router-dom";
import { useCompany, useCompanyCompleteness } from "@/api/companies";
import { useDeals } from "@/api/deals";
import { useInteractions } from "@/api/interactions";
import { useTasks } from "@/api/tasks";
import { useDocuments } from "@/api/documents";
import { RubricEditor } from "@/components/company/RubricEditor";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function CompanyDetail() {
  const { companyId } = useParams<{ companyId: string }>();
  const { data: company, isLoading } = useCompany(companyId);
  const { data: completeness } = useCompanyCompleteness(companyId);
  const { data: deals } = useDeals({ company_id: companyId });
  const { data: interactions } = useInteractions({ company_id: companyId, limit: 10 });
  const { data: tasks } = useTasks({ company_id: companyId, limit: 10 });
  const { data: documents } = useDocuments({ company_id: companyId, limit: 10 });

  if (isLoading) return <p className="text-sm text-muted-foreground">Loading…</p>;
  if (!company) return <p className="text-sm text-muted-foreground">Company not found.</p>;

  const activeDeal = deals?.items.find((d) => !d.archived_at) ?? deals?.items[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{company.name}</h1>
          <div className="mt-1 flex items-center gap-2 text-sm text-muted-foreground">
            <Badge>{company.relationship_status}</Badge>
            {company.sector && <span>{company.sector}</span>}
            {company.website && (
              <a href={company.website} className="hover:underline" target="_blank" rel="noreferrer">
                {company.website}
              </a>
            )}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs uppercase text-muted-foreground">Completeness</div>
          <div className="text-xl font-semibold">
            {Math.round(completeness?.completeness_pct ?? company.completeness_pct ?? 0)}%
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
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
      <span className="text-right">{value || "—"}</span>
    </div>
  );
}
