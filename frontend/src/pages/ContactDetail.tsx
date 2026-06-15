import { useParams } from "react-router-dom";
import { usePerson, usePersonAffiliations } from "@/api/people";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StateNotice } from "@/components/ui/state";

export function ContactDetail() {
  const { personId } = useParams<{ personId: string }>();
  const { data: person, isLoading } = usePerson(personId);
  const { data: affiliations } = usePersonAffiliations(personId);

  if (isLoading) return <StateNotice title="Loading contact" />;
  if (!person) return <StateNotice title="Contact not found" />;

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="break-words text-2xl font-semibold">{person.full_name}</h1>
        {person.title && <p className="text-sm text-muted-foreground">{person.title}</p>}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Contact</CardTitle>
        </CardHeader>
        <CardContent className="space-y-1 text-sm">
          <Field label="Email" value={person.email} />
          <Field label="Phone" value={person.phone} />
          <Field label="LinkedIn" value={person.linkedin_url} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>RIT affiliations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {affiliations?.length ? (
            affiliations.map((a) => (
              <div key={a.id}>
                {[a.rit_relationship, a.program, a.graduation_year].filter(Boolean).join(" · ") ||
                  "Affiliation"}
              </div>
            ))
          ) : (
            <p className="text-muted-foreground">No affiliations recorded.</p>
          )}
        </CardContent>
      </Card>
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
