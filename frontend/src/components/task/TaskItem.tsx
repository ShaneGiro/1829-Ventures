import { useEffect, useState } from "react";
import { Check, Pencil, Trash2 } from "lucide-react";
import { useArchiveTask, useCompleteTask, useUpdateTask } from "@/api/tasks";
import type { ChecklistItem, Task } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { TaskCreateDialog } from "@/components/task/TaskCreateDialog";
import { cn } from "@/lib/utils";

function formatDue(due: string | null | undefined): string | null {
  if (!due) return null;
  const date = new Date(due);
  if (Number.isNaN(date.getTime())) return null;
  return `Due ${date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  })}`;
}

export function TaskItem({ task }: { task: Task }) {
  const update = useUpdateTask();
  const complete = useCompleteTask();
  const archive = useArchiveTask();

  const [expanded, setExpanded] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [items, setItems] = useState<ChecklistItem[]>(task.checklist ?? []);

  useEffect(() => {
    setItems(task.checklist ?? []);
  }, [task.checklist]);

  const completed = task.status === "completed";
  const dueText = formatDue(task.due_date);
  const doneCount = items.filter((c) => c.done).length;

  const toggleComplete = () => {
    if (completed) update.mutate({ id: task.id, body: { status: "open" } });
    else complete.mutate(task.id);
  };

  const toggleItem = (idx: number) => {
    const next = items.map((c, i) => (i === idx ? { ...c, done: !c.done } : c));
    setItems(next); // optimistic
    update.mutate({ id: task.id, body: { checklist: next } });
  };

  return (
    <div className="rounded-md border bg-background">
      <div className="flex items-center gap-2 p-3">
        <button
          type="button"
          aria-label={completed ? "Mark task open" : "Mark task complete"}
          aria-pressed={completed}
          onClick={toggleComplete}
          className={cn(
            "flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition-colors",
            completed
              ? "border-primary bg-primary text-primary-foreground"
              : "border-border text-transparent hover:text-muted-foreground",
          )}
        >
          <Check className="h-3.5 w-3.5" />
        </button>

        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="min-w-0 flex-1 text-left"
        >
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "truncate text-sm font-medium",
                completed && "text-muted-foreground line-through",
              )}
            >
              {task.title}
            </span>
            {items.length > 0 && (
              <span className="shrink-0 text-xs text-muted-foreground">
                {doneCount}/{items.length}
              </span>
            )}
          </div>
          <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
            <Badge>{task.status}</Badge>
            {dueText && <span>{dueText}</span>}
          </div>
        </button>

        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Edit task"
          onClick={() => setEditOpen(true)}
        >
          <Pencil className="h-4 w-4" />
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label="Delete task"
          onClick={() => setConfirmDelete(true)}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>

      {expanded && (
        <div className="space-y-3 border-t px-3 py-3 text-sm">
          {task.description ? (
            <p className="whitespace-pre-wrap text-muted-foreground">{task.description}</p>
          ) : (
            <p className="text-muted-foreground">No description.</p>
          )}
          {items.length > 0 && (
            <div className="space-y-1.5">
              {items.map((c, idx) => (
                <label key={idx} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    className="h-4 w-4 shrink-0"
                    checked={c.done}
                    onChange={() => toggleItem(idx)}
                  />
                  <span className={cn(c.done && "text-muted-foreground line-through")}>
                    {c.text}
                  </span>
                </label>
              ))}
            </div>
          )}
        </div>
      )}

      <TaskCreateDialog open={editOpen} onClose={() => setEditOpen(false)} task={task} />
      <ConfirmDialog
        open={confirmDelete}
        destructive
        title="Delete this task?"
        description="The task will be removed. This can be restored from the archive."
        confirmLabel="Delete"
        busy={archive.isPending}
        onConfirm={() =>
          archive.mutate(task.id, { onSuccess: () => setConfirmDelete(false) })
        }
        onCancel={() => setConfirmDelete(false)}
      />
    </div>
  );
}
