import { useEffect, useState } from "react";
import { Plus, X } from "lucide-react";
import { useCompanies } from "@/api/companies";
import { useCreateTask, useUpdateTask } from "@/api/tasks";
import type { Task, TaskCreate } from "@/api/types";
import { useUsers } from "@/api/users";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";

interface TaskCreateDialogProps {
  open: boolean;
  onClose: () => void;
  /** Pre-selected company (e.g. when opened from a company page). */
  defaultCompanyId?: string;
  /** When provided, the dialog edits this task instead of creating a new one. */
  task?: Task;
}

const isoToDateInput = (iso: string | null | undefined): string =>
  iso ? new Date(iso).toISOString().slice(0, 10) : "";

const selectClass =
  "h-9 w-full rounded-md border border-border bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2";

export function TaskCreateDialog({ open, onClose, defaultCompanyId, task }: TaskCreateDialogProps) {
  const { data: companies } = useCompanies({ limit: 200 });
  const { data: users } = useUsers({ limit: 200 });
  const create = useCreateTask();
  const update = useUpdateTask();
  const isEdit = !!task;
  const pending = create.isPending || update.isPending;

  const [title, setTitle] = useState("");
  const [companyId, setCompanyId] = useState(defaultCompanyId ?? "");
  const [description, setDescription] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [ownerId, setOwnerId] = useState("");
  const [checklist, setChecklist] = useState<string[]>([]);

  // Reset/prefill the form whenever the dialog (re)opens.
  useEffect(() => {
    if (!open) return;
    setTitle(task?.title ?? "");
    setCompanyId(task?.company_id ?? defaultCompanyId ?? "");
    setDescription(task?.description ?? "");
    setDueDate(isoToDateInput(task?.due_date));
    setOwnerId(task?.owner_id ?? "");
    setChecklist((task?.checklist ?? []).map((c) => c.text));
  }, [open, defaultCompanyId, task]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const canSubmit = title.trim().length > 0 && !!companyId && !pending;

  const submit = () => {
    if (!canSubmit) return;
    const original = task?.checklist ?? [];
    const checklistItems = checklist
      .map((text, idx) => ({ text: text.trim(), idx }))
      .filter((c) => c.text)
      // Preserve a checked item's state when its text is unchanged.
      .map(({ text, idx }) => ({
        text,
        done: original[idx]?.text === text ? original[idx].done : false,
      }));
    const payload: TaskCreate = {
      title: title.trim(),
      company_id: companyId,
      priority: task?.priority ?? "medium",
      description: description.trim() || null,
      due_date: dueDate ? new Date(`${dueDate}T00:00:00`).toISOString() : null,
      owner_id: ownerId || null,
      checklist: checklistItems,
    };
    if (isEdit && task) {
      update.mutate({ id: task.id, body: payload }, { onSuccess: onClose });
    } else {
      create.mutate(payload, { onSuccess: onClose });
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="task-dialog-title"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border bg-background p-5 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="task-dialog-title" className="text-base font-semibold">
          {isEdit ? "Edit task" : "New task"}
        </h2>

        <div className="mt-4 space-y-4">
          <Field label="Task name" required>
            <Input
              autoFocus
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What needs to be done?"
            />
          </Field>

          <Field label="Company" required>
            <select
              className={selectClass}
              value={companyId}
              onChange={(e) => setCompanyId(e.target.value)}
            >
              <option value="">Select company…</option>
              {companies?.items.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Description">
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add context, notes, or links."
            />
          </Field>

          <Field label="Checklist">
            <div className="space-y-2">
              {checklist.map((item, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <Input
                    value={item}
                    onChange={(e) =>
                      setChecklist((prev) => prev.map((v, i) => (i === idx ? e.target.value : v)))
                    }
                    placeholder={`Todo ${idx + 1}`}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label="Remove checklist item"
                    onClick={() => setChecklist((prev) => prev.filter((_, i) => i !== idx))}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setChecklist((prev) => [...prev, ""])}
              >
                <Plus className="h-4 w-4" />
                Add checklist item
              </Button>
            </div>
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Due date">
              <Input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
            </Field>
            <Field label="Assign to">
              <select
                className={selectClass}
                value={ownerId}
                onChange={(e) => setOwnerId(e.target.value)}
              >
                <option value="">Unassigned</option>
                {users?.items.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name || u.email}
                  </option>
                ))}
              </select>
            </Field>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={pending}>
            Cancel
          </Button>
          <Button size="sm" onClick={submit} disabled={!canSubmit}>
            {pending ? "Saving..." : isEdit ? "Save changes" : "Create task"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function Field({
  label,
  required = false,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium">
        {label}
        {required && <span className="text-destructive"> *</span>}
      </span>
      {children}
    </label>
  );
}
