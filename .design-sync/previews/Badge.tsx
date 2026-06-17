import { Badge } from "ventures-crm-frontend";

export function PipelineStages() {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
      <Badge>Sourced</Badge>
      <Badge>Initial review</Badge>
      <Badge>Outreach</Badge>
      <Badge>Diligence</Badge>
      <Badge>Closed</Badge>
    </div>
  );
}

export function Metadata() {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
      <Badge>Series A</Badge>
      <Badge>Fintech</Badge>
      <Badge>San Francisco</Badge>
      <Badge>12 employees</Badge>
    </div>
  );
}
