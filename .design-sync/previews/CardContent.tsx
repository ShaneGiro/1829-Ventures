import { Card, CardHeader, CardTitle, CardContent, Badge } from "ventures-crm-frontend";

// CardContent is the padded body region of a Card. Shown in context.
export function InCard() {
  return (
    <div style={{ maxWidth: 380 }}>
      <Card>
        <CardHeader>
          <CardTitle>Investment notes</CardTitle>
        </CardHeader>
        <CardContent>
          <p style={{ margin: "0 0 12px", fontSize: 14 }}>
            Strong founding team with prior exits. Revenue growing ~18% MoM.
          </p>
          <div style={{ display: "flex", gap: 8 }}>
            <Badge>High priority</Badge>
            <Badge>Warm intro</Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
