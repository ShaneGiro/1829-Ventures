import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import { useCompanies } from "@/api/companies";
import { useArchiveDeal, useDeals, useDealStatuses, useMoveDeal } from "@/api/deals";
import type { Deal } from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { StateNotice } from "@/components/ui/state";
import { cn } from "@/lib/utils";

const UNASSIGNED = "__unassigned__";

/** Short, human-readable date for a deal's most recent change. */
function formatLastActivity(updatedAt: string | null | undefined): string {
  if (!updatedAt) return "—";
  const date = new Date(updatedAt);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

interface StageArrowProps {
  direction: "left" | "right";
  visibleClass: string;
  disabled: boolean;
  onMove: () => void;
}

/** Small chevron button that moves a card to an adjacent pipeline stage. */
function StageArrow({ direction, visibleClass, disabled, onMove }: StageArrowProps) {
  const Icon = direction === "left" ? ChevronLeft : ChevronRight;
  return (
    <button
      type="button"
      aria-label={direction === "left" ? "Move to previous stage" : "Move to next stage"}
      disabled={disabled}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onMove();
      }}
      className={cn(
        "flex w-5 shrink-0 items-center justify-center rounded text-muted-foreground transition hover:bg-accent hover:text-foreground disabled:opacity-40",
        visibleClass,
      )}
    >
      <Icon className="h-4 w-4" />
    </button>
  );
}

export function PipelineBoard() {
  const { data: statuses } = useDealStatuses();
  const { data: deals, isLoading, isError } = useDeals({ limit: 200 });
  const { data: companies } = useCompanies({ limit: 200 });
  const archiveDeal = useArchiveDeal();
  const moveDeal = useMoveDeal();

  const [selectMode, setSelectMode] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirmOpen, setConfirmOpen] = useState(false);

  const companyName = useMemo(() => {
    const map = new Map<string, string>();
    companies?.items.forEach((c) => map.set(c.id, c.name));
    return map;
  }, [companies]);

  const dealById = useMemo(() => {
    const map = new Map<string, Deal>();
    deals?.items.forEach((d) => map.set(d.id, d));
    return map;
  }, [deals]);

  // Real pipeline stages in order (excludes the synthetic "Unassigned" column).
  const orderedStatuses = useMemo(
    () => [...(statuses?.items ?? [])].sort((a, b) => a.sort_order - b.sort_order),
    [statuses],
  );

  const columns = useMemo(
    () => [...orderedStatuses, { id: UNASSIGNED, name: "Unassigned", sort_order: 999 }],
    [orderedStatuses],
  );

  const byStatus = useMemo(() => {
    const groups = new Map<string, Deal[]>();
    deals?.items.forEach((d) => {
      const key = d.deal_status_id ?? UNASSIGNED;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(d);
    });
    return groups;
  }, [deals]);

  // Adjacent-stage ids for a deal. Initial Review (first) has no previous;
  // Closed/Invested (last) has no next. Unassigned deals can move into stage 1.
  const neighbors = (deal: Deal): { prevId: string | null; nextId: string | null } => {
    if (!deal.deal_status_id) {
      return { prevId: null, nextId: orderedStatuses[0]?.id ?? null };
    }
    const i = orderedStatuses.findIndex((s) => s.id === deal.deal_status_id);
    if (i < 0) return { prevId: null, nextId: null };
    return {
      prevId: i > 0 ? orderedStatuses[i - 1].id : null,
      nextId: i < orderedStatuses.length - 1 ? orderedStatuses[i + 1].id : null,
    };
  };

  // Board order (column order, then top-to-bottom within a column) so the
  // "top" selected card can anchor the shared arrows.
  const orderedDealIds = useMemo(() => {
    const ids: string[] = [];
    columns.forEach((col) => (byStatus.get(col.id) ?? []).forEach((d) => ids.push(d.id)));
    return ids;
  }, [columns, byStatus]);

  const anchorId = useMemo(
    () => orderedDealIds.find((id) => selected.has(id)) ?? null,
    [orderedDealIds, selected],
  );

  // Whether any selected card can shift left/right — drives the shared arrows.
  let canMoveLeft = false;
  let canMoveRight = false;
  selected.forEach((id) => {
    const d = dealById.get(id);
    if (!d) return;
    const { prevId, nextId } = neighbors(d);
    if (prevId) canMoveLeft = true;
    if (nextId) canMoveRight = true;
  });

  const moveSelected = (direction: "left" | "right") => {
    selected.forEach((id) => {
      const d = dealById.get(id);
      if (!d) return;
      const { prevId, nextId } = neighbors(d);
      const target = direction === "left" ? prevId : nextId;
      if (target) moveDeal.mutate({ id, dealStatusId: target });
    });
  };

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const exitSelectMode = () => {
    setSelectMode(false);
    setSelected(new Set());
  };

  const handleDelete = async () => {
    const ids = [...selected];
    await Promise.all(ids.map((id) => archiveDeal.mutateAsync(id)));
    setConfirmOpen(false);
    exitSelectMode();
  };

  const selectedCount = selected.size;
  const spacer = <span className="w-5 shrink-0" aria-hidden />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">Pipeline</h1>
        <div className="flex items-center gap-2">
          {selectMode && selectedCount > 0 && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setConfirmOpen(true)}
              disabled={archiveDeal.isPending}
            >
              Delete {selectedCount} from pipeline
            </Button>
          )}
          {selectMode ? (
            <Button variant="outline" size="sm" onClick={exitSelectMode}>
              Cancel
            </Button>
          ) : (
            <Button variant="outline" size="sm" onClick={() => setSelectMode(true)}>
              Select
            </Button>
          )}
        </div>
      </div>

      {isLoading && <StateNotice title="Loading pipeline" />}
      {isError && (
        <StateNotice
          title="Could not load pipeline"
          description="Refresh the page or check the API connection."
          variant="error"
        />
      )}
      <div className="flex gap-4 overflow-x-auto pb-4">
        {columns.map((col) => {
          const items = byStatus.get(col.id) ?? [];
          return (
            <div key={col.id} className="w-72 shrink-0">
              <div className="mb-2 flex items-center justify-between px-1">
                <span className="text-sm font-medium">{col.name}</span>
                <Badge>{items.length}</Badge>
              </div>
              <div className="space-y-2">
                {items.map((d) => {
                  const label = companyName.get(d.company_id) || d.name || "Untitled company";
                  const activity = `Last activity ${formatLastActivity(d.updated_at)}`;
                  const isSelected = selected.has(d.id);
                  const { prevId, nextId } = neighbors(d);

                  // Select mode: only the top selected card ("anchor") shows
                  // arrows, and they move the whole selection. Otherwise arrows
                  // reveal on hover and move just this card.
                  let leftArrow = spacer;
                  let rightArrow = spacer;
                  if (selectMode) {
                    if (d.id === anchorId) {
                      leftArrow = canMoveLeft ? (
                        <StageArrow
                          direction="left"
                          visibleClass="opacity-100"
                          disabled={moveDeal.isPending}
                          onMove={() => moveSelected("left")}
                        />
                      ) : (
                        spacer
                      );
                      rightArrow = canMoveRight ? (
                        <StageArrow
                          direction="right"
                          visibleClass="opacity-100"
                          disabled={moveDeal.isPending}
                          onMove={() => moveSelected("right")}
                        />
                      ) : (
                        spacer
                      );
                    }
                  } else {
                    const hoverClass = "opacity-0 group-hover:opacity-100 focus-visible:opacity-100";
                    leftArrow = prevId ? (
                      <StageArrow
                        direction="left"
                        visibleClass={hoverClass}
                        disabled={moveDeal.isPending}
                        onMove={() => moveDeal.mutate({ id: d.id, dealStatusId: prevId })}
                      />
                    ) : (
                      spacer
                    );
                    rightArrow = nextId ? (
                      <StageArrow
                        direction="right"
                        visibleClass={hoverClass}
                        disabled={moveDeal.isPending}
                        onMove={() => moveDeal.mutate({ id: d.id, dealStatusId: nextId })}
                      />
                    ) : (
                      spacer
                    );
                  }

                  return (
                    <div key={d.id} className="group flex items-stretch gap-1">
                      {leftArrow}
                      {selectMode ? (
                        <label
                          className={cn(
                            "flex flex-1 cursor-pointer items-start gap-2 rounded-md border bg-background p-3 text-sm hover:bg-accent/40",
                            isSelected && "ring-2 ring-primary",
                          )}
                        >
                          <input
                            type="checkbox"
                            className="mt-0.5 h-4 w-4 shrink-0"
                            checked={isSelected}
                            onChange={() => toggle(d.id)}
                            aria-label={`Select ${label}`}
                          />
                          <span className="min-w-0">
                            <span className="block font-medium">{label}</span>
                            <span className="mt-1 block text-xs text-muted-foreground">
                              {activity}
                            </span>
                          </span>
                        </label>
                      ) : (
                        <Link
                          to={`/companies/${d.company_id}`}
                          className="flex-1 rounded-md border bg-background p-3 text-sm hover:bg-accent/40"
                        >
                          <div className="font-medium">{label}</div>
                          <div className="mt-1 text-xs text-muted-foreground">{activity}</div>
                        </Link>
                      )}
                      {rightArrow}
                    </div>
                  );
                })}
                {items.length === 0 && (
                  <div className="rounded-md border border-dashed p-3 text-center text-xs text-muted-foreground">
                    Empty
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <ConfirmDialog
        open={confirmOpen}
        destructive
        title={`Delete ${selectedCount} ${selectedCount === 1 ? "company" : "companies"} from the pipeline?`}
        description="This removes the selected deals from the pipeline. The companies themselves are kept, and the deals can be restored from the archive."
        confirmLabel="Delete"
        busy={archiveDeal.isPending}
        onConfirm={handleDelete}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  );
}
