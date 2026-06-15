import { useAgentEvents } from "@/api/agentApi";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StateNotice } from "@/components/ui/state";

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
        {isLoading && <StateNotice title="Loading activity" />}
        {isError && <StateNotice title="Could not load activity" variant="error" />}
        {data?.items.map((e) => (
          <div key={e.id} className="rounded-md border p-3 text-sm">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <span className="break-words font-medium">{e.event_type}</span>
              <Badge className={STATUS_STYLE[e.status] ?? ""}>{e.status}</Badge>
            </div>
            {e.blocked_tool && (
              <div className="mt-1 text-xs text-red-700">Blocked tool: {e.blocked_tool}</div>
            )}
            {e.rationale && <div className="mt-1 text-xs text-muted-foreground">{e.rationale}</div>}
            {e.response_summary && (
              <div className="mt-1 text-xs text-muted-foreground">{e.response_summary}</div>
            )}
            <div className="mt-1 flex flex-wrap gap-3 text-xs text-muted-foreground">
              {e.confidence != null && <span>confidence {e.confidence}</span>}
              {e.entity_type && <span>{e.entity_type}</span>}
            </div>
          </div>
        ))}
        {data?.items.length === 0 && (
          <StateNotice title="No agent activity yet" />
        )}
      </CardContent>
    </Card>
  );
}
