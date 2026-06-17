import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from "ventures-crm-frontend";

export function CompanyCard() {
  return (
    <div style={{ maxWidth: 380 }}>
      <Card>
        <CardHeader>
          <CardTitle>Northwind Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <p style={{ margin: 0, fontSize: 14, color: "hsl(var(--muted-foreground))" }}>
            B2B analytics platform for supply-chain operators. Sourced via Dealroom.
          </p>
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <Badge>Series A</Badge>
            <Badge>SaaS</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function WithAction() {
  return (
    <div style={{ maxWidth: 380 }}>
      <Card>
        <CardHeader>
          <CardTitle>Follow-up task</CardTitle>
        </CardHeader>
        <CardContent>
          <p style={{ margin: "0 0 12px", fontSize: 14 }}>
            Send diligence questionnaire to the founder before Friday.
          </p>
          <Button size="sm">Mark complete</Button>
        </CardContent>
      </Card>
    </div>
  );
}

export function Plain() {
  return (
    <div style={{ maxWidth: 380 }}>
      <Card>
        <CardContent>
          <p style={{ margin: 0, fontSize: 14 }}>
            A bare card with content only — no header.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
