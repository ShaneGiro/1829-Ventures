import { useState } from "react";
import { useTasks } from "@/api/tasks";
import { Button } from "@/components/ui/button";
import { StateNotice } from "@/components/ui/state";
import { TaskCreateDialog } from "@/components/task/TaskCreateDialog";
import { TaskItem } from "@/components/task/TaskItem";

export function TaskList() {
  const { data, isLoading, isError } = useTasks({ limit: 50 });
  const [dialogOpen, setDialogOpen] = useState(false);

  return (
    <div className="max-w-2xl space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Tasks</h1>
        <Button onClick={() => setDialogOpen(true)}>Add task</Button>
      </div>

      {isLoading && <StateNotice title="Loading tasks" />}
      {isError && (
        <StateNotice
          title="Could not load tasks"
          description="Refresh the page or check the API connection."
          variant="error"
        />
      )}
      <div className="space-y-2">
        {data?.items.map((t) => (
          <TaskItem key={t.id} task={t} />
        ))}
        {data?.items.length === 0 && <p className="text-sm text-muted-foreground">No tasks yet.</p>}
      </div>

      <TaskCreateDialog open={dialogOpen} onClose={() => setDialogOpen(false)} />
    </div>
  );
}
