import { useState } from "react";
import { useCompleteTask, useCreateTask, useTasks } from "@/api/tasks";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { StateNotice } from "@/components/ui/state";

export function TaskList() {
  const { data, isLoading, isError } = useTasks({ limit: 50 });
  const create = useCreateTask();
  const complete = useCompleteTask();
  const [title, setTitle] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    create.mutate(
      { title: title.trim(), priority: "medium" },
      { onSuccess: () => setTitle("") },
    );
  };

  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-xl font-semibold">Tasks</h1>

      <Card>
        <CardHeader>
          <CardTitle>New task</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="flex flex-col gap-2 sm:flex-row">
            <Input
              placeholder="Task title…"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <Button type="submit" disabled={create.isPending}>
              Add
            </Button>
          </form>
        </CardContent>
      </Card>

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
          <div
            key={t.id}
            className="flex flex-col gap-3 rounded-md border bg-background p-3 text-sm sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="min-w-0">
              <span className="font-medium">{t.title}</span>{" "}
              <Badge>{t.status}</Badge> <Badge>{t.priority}</Badge>
            </div>
            {t.status !== "completed" && t.status !== "cancelled" && (
              <Button size="sm" variant="outline" onClick={() => complete.mutate(t.id)}>
                Complete
              </Button>
            )}
          </div>
        ))}
        {data?.items.length === 0 && (
          <p className="text-sm text-muted-foreground">No tasks yet.</p>
        )}
      </div>
    </div>
  );
}
