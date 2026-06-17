import { Card, CardHeader, CardTitle, CardContent } from "ventures-crm-frontend";

// CardTitle is the heading used inside a CardHeader. Shown in context.
export function InCard() {
  return (
    <div style={{ maxWidth: 380 }}>
      <Card>
        <CardHeader>
          <CardTitle>Acme Robotics</CardTitle>
        </CardHeader>
        <CardContent>
          <p style={{ margin: 0, fontSize: 14, color: "hsl(var(--muted-foreground))" }}>
            The title is a small, semibold heading for the card.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
