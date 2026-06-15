import { useAgentPolicies, useSetPolicy } from "@/api/agentApi";
import type { AgentPolicy } from "@/api/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Binary authorization toggles per Ritchie tool/field. Flipping a row applies
 * immediately via PUT /agent/policies. There is no proposal/approval queue —
 * governance is strictly authorized/blocked.
 */
export function PolicyPanel() {
  const { data: policies, isLoading } = useAgentPolicies();
  const setPolicy = useSetPolicy();

  const toggle = (p: AgentPolicy) =>
    setPolicy.mutate({
      tool: p.tool,
      field_name: p.field_name,
      state: p.state === "authorized" ? "blocked" : "authorized",
    });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Authorization policy</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {isLoading && <p className="text-sm text-muted-foreground">Loading policy…</p>}
        {policies?.map((p) => (
          <div
            key={`${p.tool}:${p.field_name ?? "*"}`}
            className="flex items-center justify-between rounded-md border p-3 text-sm"
          >
            <div>
              <span className="font-medium">{p.tool}</span>
              {p.field_name && <span className="text-muted-foreground">.{p.field_name}</span>}
            </div>
            <div className="flex items-center gap-3">
              <Badge
                className={
                  p.state === "authorized"
                    ? "border-green-500 text-green-700"
                    : "border-red-500 text-red-700"
                }
              >
                {p.state}
              </Badge>
              <Button
                size="sm"
                variant="outline"
                onClick={() => toggle(p)}
                disabled={setPolicy.isPending}
              >
                {p.state === "authorized" ? "Block" : "Authorize"}
              </Button>
            </div>
          </div>
        ))}
        {policies?.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No policy rows yet. Seed defaults from the backend to populate tool toggles.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
