import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { usePerson, usePersonAffiliations, useUpdatePerson } from "@/api/people";
import type { PersonUpdate } from "@/api/types";
import { DocumentPanel } from "@/components/document/DocumentPanel";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input, Textarea } from "@/components/ui/input";
import { StateNotice } from "@/components/ui/state";

const EMPTY_FORM: PersonUpdate = {
  full_name: "",
  email: null,
  phone: null,
  linkedin_url: null,
  title: null,
  notes: null,
};

export function ContactDetail() {
  const { personId } = useParams<{ personId: string }>();
  const { data: person, isLoading } = usePerson(personId);
  const { data: affiliations } = usePersonAffiliations(personId);
  const updatePerson = useUpdatePerson(personId ?? "");
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState<PersonUpdate>(EMPTY_FORM);

  useEffect(() => {
    if (!person) return;
    setForm({
      full_name: person.full_name,
      email: person.email,
      phone: person.phone,
      linkedin_url: person.linkedin_url,
      title: person.title,
      notes: person.notes,
    });
  }, [person]);

  if (isLoading) return <StateNotice title="Loading contact" />;
  if (!person) return <StateNotice title="Contact not found" />;

  function updateField(field: keyof PersonUpdate, value: string) {
    setForm((current) => ({ ...current, [field]: value || null }));
  }

  async function save() {
    await updatePerson.mutateAsync(form);
    setIsEditing(false);
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="break-words text-2xl font-semibold">{person.full_name}</h1>
          {person.title && <p className="text-sm text-muted-foreground">{person.title}</p>}
        </div>
        <Button variant="outline" onClick={() => setIsEditing((value) => !value)}>
          {isEditing ? "Cancel" : "Edit profile"}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Contact</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {isEditing ? (
            <>
              <ProfileInput label="Name" value={form.full_name} onChange={(v) => updateField("full_name", v)} />
              <ProfileInput label="Title" value={form.title} onChange={(v) => updateField("title", v)} />
              <ProfileInput label="Email" type="email" value={form.email} onChange={(v) => updateField("email", v)} />
              <ProfileInput label="Phone" value={form.phone} onChange={(v) => updateField("phone", v)} />
              <ProfileInput label="LinkedIn" type="url" value={form.linkedin_url} onChange={(v) => updateField("linkedin_url", v)} />
              <label className="block space-y-1">
                <span className="text-xs font-medium">Notes</span>
                <Textarea value={form.notes ?? ""} onChange={(event) => updateField("notes", event.target.value)} />
              </label>
              {updatePerson.error && <p className="text-destructive">{updatePerson.error.message}</p>}
              <Button onClick={() => void save()} disabled={updatePerson.isPending}>
                {updatePerson.isPending ? "Saving…" : "Save"}
              </Button>
            </>
          ) : (
            <>
              <Field label="Email" value={person.email} />
              <Field label="Phone" value={person.phone} />
              <Field label="LinkedIn" value={person.linkedin_url} />
              <Field label="Notes" value={person.notes} />
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>RIT affiliations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          {affiliations?.length ? (
            affiliations.map((affiliation) => (
              <div key={affiliation.id}>
                {[affiliation.rit_relationship, affiliation.program, affiliation.graduation_year]
                  .filter(Boolean)
                  .join(" · ") || "Affiliation"}
              </div>
            ))
          ) : (
            <p className="text-muted-foreground">No affiliations recorded.</p>
          )}
        </CardContent>
      </Card>

      <DocumentPanel personId={person.id} />
    </div>
  );
}

function ProfileInput({
  label,
  value,
  type = "text",
  onChange,
}: {
  label: string;
  value?: string | null;
  type?: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block space-y-1">
      <span className="text-xs font-medium">{label}</span>
      <Input type={type} value={value ?? ""} onChange={(event) => onChange(event.target.value)} />
    </label>
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
