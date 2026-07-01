import { useEffect, useState } from "react";
import { useUpdateDeal } from "@/api/deals";
import { useCreateInvestment, useFunds } from "@/api/portfolioApi";
import { ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input, Textarea } from "@/components/ui/input";

interface CloseInvestmentDialogProps {
  open: boolean;
  companyId: string;
  companyName: string;
  dealId: string;
  /** deal_status_id of the "Closed/Invested" column the deal is moving into. */
  targetStatusId: string;
  /** Deal's current decision_notes, so a new note is appended rather than overwriting history. */
  existingNotes: string | null;
  onClose: () => void;
}

const selectClass =
  "h-9 w-full rounded-md border border-border bg-background px-3 text-sm focus-visible:outline-none focus-visible:ring-2";

const today = (): string => new Date().toISOString().slice(0, 10);

/** Captures closing details and records the exact moment a deal is marked invested. */
export function CloseInvestmentDialog({
  open,
  companyId,
  companyName,
  dealId,
  targetStatusId,
  existingNotes,
  onClose,
}: CloseInvestmentDialogProps) {
  const { data: funds } = useFunds();
  const createInvestment = useCreateInvestment();
  const updateDeal = useUpdateDeal(dealId);
  const pending = createInvestment.isPending || updateDeal.isPending;

  const [fundId, setFundId] = useState("");
  const [investmentDate, setInvestmentDate] = useState(today());
  const [amount, setAmount] = useState("");
  const [valuation, setValuation] = useState("");
  const [instrument, setInstrument] = useState("");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Reset/prefill the form whenever the dialog (re)opens.
  useEffect(() => {
    if (!open) return;
    setFundId(funds?.items[0]?.id ?? "");
    setInvestmentDate(today());
    setAmount("");
    setValuation("");
    setInstrument("");
    setNotes("");
    setError(null);
  }, [open, funds]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const canSubmit = !!fundId && !!investmentDate && !pending;

  const submit = async () => {
    if (!canSubmit) return;
    setError(null);
    try {
      await createInvestment.mutateAsync({
        fund_id: fundId,
        company_id: companyId,
        deal_id: dealId,
        currency: "USD",
        investment_date: investmentDate,
        amount: amount || null,
        post_money_valuation: valuation || null,
        instrument: instrument.trim() || null,
      });
      const trimmedNotes = notes.trim();
      await updateDeal.mutateAsync({
        deal_status_id: targetStatusId,
        investment_status: "invested",
        ...(trimmedNotes
          ? { decision_notes: existingNotes ? `${existingNotes}\n${trimmedNotes}` : trimmedNotes }
          : {}),
      });
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Try again.");
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="close-investment-dialog-title"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md rounded-lg border bg-background p-5 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="close-investment-dialog-title" className="text-base font-semibold">
          Close investment — {companyName}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">
          This records the investment and moves the deal to Closed/Invested.
        </p>

        <div className="mt-4 space-y-4">
          <Field label="Fund" required>
            <select className={selectClass} value={fundId} onChange={(e) => setFundId(e.target.value)}>
              <option value="">Select fund…</option>
              {funds?.items.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Investment date" required>
            <Input
              type="date"
              value={investmentDate}
              onChange={(e) => setInvestmentDate(e.target.value)}
            />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Amount invested">
              <Input
                type="number"
                min="0"
                step="0.01"
                placeholder="$"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
              />
            </Field>
            <Field label="Post-money valuation">
              <Input
                type="number"
                min="0"
                step="0.01"
                placeholder="$"
                value={valuation}
                onChange={(e) => setValuation(e.target.value)}
              />
            </Field>
          </div>

          <Field label="Instrument">
            <Input
              placeholder="e.g. SAFE, Series A Preferred"
              value={instrument}
              onChange={(e) => setInstrument(e.target.value)}
            />
          </Field>

          <Field label="Notes">
            <Textarea
              placeholder="Anything worth recording about how this closed…"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </Field>
        </div>

        {error && <p className="mt-4 text-sm text-destructive">{error}</p>}

        <div className="mt-6 flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={pending}>
            Cancel
          </Button>
          <Button size="sm" onClick={submit} disabled={!canSubmit}>
            {pending ? "Saving..." : "Close investment"}
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
