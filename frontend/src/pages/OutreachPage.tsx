import { useState } from "react";
import { useCompanies } from "@/api/companies";
import { useCreateInteraction, useInteractions } from "@/api/interactions";
import { usePeople } from "@/api/people";
import { useUsers } from "@/api/users";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";

export function OutreachPage() {
  const [channel, setChannel] = useState("");
  const [followUpStatus, setFollowUpStatus] = useState("");
  const [ownerId, setOwnerId] = useState("");
  const interactions = useInteractions({
    limit: 200,
    direction: "outbound",
    channel: channel || undefined,
    follow_up_status: followUpStatus || undefined,
    created_by_id: ownerId || undefined,
  });
  const companies = useCompanies({ limit: 200 });
  const people = usePeople({ limit: 200 });
  const users = useUsers({ limit: 200 });

  const companyNames = new Map(companies.data?.items.map((item) => [item.id, item.name]));
  const peopleNames = new Map(people.data?.items.map((item) => [item.id, item.full_name]));
  const userNames = new Map(
    users.data?.items.map((item) => [item.id, item.full_name || item.email]),
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Outreach</h1>
        <p className="text-sm text-muted-foreground">
          A chronological record of team outreach and follow-up state.
        </p>
      </div>

      <LogOutreachForm />

      <Card>
        <CardHeader>
          <CardTitle>Outreach history</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-3 md:grid-cols-3">
            <FilterSelect label="Channel" value={channel} onChange={setChannel} options={["email", "linkedin", "call", "meeting", "other"]} />
            <FilterSelect label="Follow-up" value={followUpStatus} onChange={setFollowUpStatus} options={["needed", "scheduled", "complete", "none"]} />
            <label className="space-y-1 text-sm">
              <span className="font-medium">Owner</span>
              <select className="h-9 w-full rounded-md border bg-background px-2" value={ownerId} onChange={(event) => setOwnerId(event.target.value)}>
                <option value="">All owners</option>
                {users.data?.items.map((user) => <option key={user.id} value={user.id}>{user.full_name || user.email}</option>)}
              </select>
            </label>
          </div>

          {interactions.data?.items.length ? (
            <div className="divide-y rounded-md border">
              {interactions.data.items.map((interaction) => (
                <div key={interaction.id} className="grid gap-1 p-3 text-sm md:grid-cols-[10rem_1fr_10rem]">
                  <div className="text-muted-foreground">
                    {new Date(interaction.occurred_at || interaction.created_at).toLocaleString()}
                  </div>
                  <div>
                    <div className="font-medium">{interaction.summary || "Outreach"}</div>
                    <div className="text-muted-foreground">
                      {interaction.company_id ? companyNames.get(interaction.company_id) : undefined}
                      {interaction.person_id ? ` · ${peopleNames.get(interaction.person_id) || "Person"}` : ""}
                      {interaction.created_by_id ? ` · ${userNames.get(interaction.created_by_id) || "Team member"}` : ""}
                    </div>
                  </div>
                  <div className="text-right text-muted-foreground">
                    {interaction.channel || interaction.interaction_type} · {interaction.follow_up_status}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No outreach matches these filters.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function LogOutreachForm() {
  const companies = useCompanies({ limit: 200 });
  const people = usePeople({ limit: 200 });
  const createInteraction = useCreateInteraction();
  const [companyId, setCompanyId] = useState("");
  const [personId, setPersonId] = useState("");
  const [summary, setSummary] = useState("");
  const [body, setBody] = useState("");
  const [channel, setChannel] = useState("email");
  const [followUpStatus, setFollowUpStatus] = useState("none");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    await createInteraction.mutateAsync({
      interaction_type: channel === "call" ? "call" : channel === "meeting" ? "meeting" : "touchpoint",
      summary,
      body: body || undefined,
      occurred_at: new Date().toISOString(),
      company_id: companyId || undefined,
      person_id: personId || undefined,
      channel,
      direction: "outbound",
      follow_up_status: followUpStatus as "none" | "needed" | "scheduled" | "complete",
    });
    setSummary("");
    setBody("");
  }

  return (
    <Card>
      <CardHeader><CardTitle>Log outreach</CardTitle></CardHeader>
      <CardContent>
        <form className="grid gap-3 md:grid-cols-2" onSubmit={(event) => void submit(event)}>
          <FilterSelect label="Channel" value={channel} onChange={setChannel} options={["email", "linkedin", "call", "meeting", "other"]} includeAll={false} />
          <FilterSelect label="Follow-up" value={followUpStatus} onChange={setFollowUpStatus} options={["none", "needed", "scheduled", "complete"]} includeAll={false} />
          <EntitySelect label="Company" value={companyId} onChange={setCompanyId} items={companies.data?.items.map((item) => ({ id: item.id, label: item.name })) ?? []} />
          <EntitySelect label="Person" value={personId} onChange={setPersonId} items={people.data?.items.map((item) => ({ id: item.id, label: item.full_name })) ?? []} />
          <label className="space-y-1 text-sm md:col-span-2"><span className="font-medium">Summary</span><Input required value={summary} onChange={(event) => setSummary(event.target.value)} /></label>
          <label className="space-y-1 text-sm md:col-span-2"><span className="font-medium">Notes</span><Textarea value={body} onChange={(event) => setBody(event.target.value)} /></label>
          {createInteraction.error && <p className="text-sm text-destructive md:col-span-2">{createInteraction.error.message}</p>}
          <Button className="md:col-span-2 md:w-fit" disabled={createInteraction.isPending}>{createInteraction.isPending ? "Saving…" : "Log outreach"}</Button>
        </form>
      </CardContent>
    </Card>
  );
}

function FilterSelect({ label, value, onChange, options, includeAll = true }: { label: string; value: string; onChange: (value: string) => void; options: string[]; includeAll?: boolean }) {
  return <label className="space-y-1 text-sm"><span className="font-medium">{label}</span><select className="h-9 w-full rounded-md border bg-background px-2" value={value} onChange={(event) => onChange(event.target.value)}>{includeAll && <option value="">All</option>}{options.map((option) => <option key={option} value={option}>{option}</option>)}</select></label>;
}

function EntitySelect({ label, value, onChange, items }: { label: string; value: string; onChange: (value: string) => void; items: { id: string; label: string }[] }) {
  return <label className="space-y-1 text-sm"><span className="font-medium">{label}</span><select className="h-9 w-full rounded-md border bg-background px-2" value={value} onChange={(event) => onChange(event.target.value)}><option value="">None</option>{items.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}</select></label>;
}
