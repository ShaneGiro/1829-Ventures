import { AgentAuditLog } from "@/components/agent/AgentAuditLog";
import { PolicyPanel } from "@/components/agent/PolicyPanel";

export function RitchiePage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Ritchie</h1>
      <div className="grid gap-6 lg:grid-cols-2">
        <AgentAuditLog />
        <PolicyPanel />
      </div>
    </div>
  );
}
