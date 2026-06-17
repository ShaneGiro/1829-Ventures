import { Card, CardHeader, CardTitle, CardContent } from "ventures-crm-frontend";

// CardHeader is the bordered top section of a Card. Shown in context.
export function InCard() {
  return (
    <div style={{ maxWidth: 380 }}>
      <Card>
        <CardHeader>
          <CardTitle>Deal summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p style={{ margin: 0, fontSize: 14, color: "hsl(var(--muted-foreground))" }}>
            The header sits above the content, separated by a divider.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
