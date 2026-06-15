import { useAgentEvents } from "@/api/agentApi";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const STATUS_STYLE: Record<string, string> = {
  processed: "border-green-500 text-green-700",
  policy_blocked: "border-red-500 text-red-700",
  agent_unavailable: "border-amber-500 text-amber-700",
  failed: "border-red-500 text-red-700",
};

/** Feed of what Ritchie did (authorized writes) and attempted (policy_blocked). */
export function AgentAuditLog() {
  const { data, isLoading, isError } = useAgentEvents({ limit: 50 });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ritchie activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {isLoading && <p className="text-sm text-muted-foreground">Loading activity…</p>}
        {isError && <p className="text-sm text-muted-foreground">Could not load activity.</p>}
        {data?.items.map((e) => (
          <div key={e.id} className="rounded-md border p-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="font-medium">{e.event_type}</span>
              <Badge className={STATUS_STYLE[e.status] ?? ""}>{e.status}</Badge>
            </div>
            {e.blocked_tool && (
              <div className="mt-1 text-xs text-red-700">Blocked tool: {e.blocked_tool}</div>
            )}
            {e.rationale && <div className="mt-1 text-xs text-muted-foreground">{e.rationale}</div>}
            {e.response_summary && (
              <div className="mt-1 text-xs text-muted-foreground">{e.response_summary}</div>
            )}
            <div className="mt-1 flex gap-3 text-xs text-muted-foreground">
              {e.confidence != null && <span>confidence {e.confidence}</span>}
              {e.entity_type && <span>{e.entity_type}</span>}
            </div>
          </div>
        ))}
        {data?.items.length === 0 && (
          <p className="text-sm text-muted-foreground">No agent activity yet.</p>
        )}
      </CardContent>
    </Card>
  );
}
