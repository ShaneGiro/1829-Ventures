import { AgentAuditLog } from "@/components/agent/AgentAuditLog";
import { PolicyPanel } from "@/components/agent/PolicyPanel";

export function RitchiePage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Ritchie</h1>
      <div className="grid grid-cols-2 gap-6">
        <AgentAuditLog />
        <PolicyPanel />
      </div>
    </div>
  );
}
