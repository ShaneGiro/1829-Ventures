import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge conditional class names, de-duplicating Tailwind utilities. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

function parseFiniteNumber(value: string | number | null | undefined): number | null {
  if (value === null || value === undefined) return null;
  const parsed = typeof value === "number" ? value : Number(value.replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : null;
}

export function formatDecimal(value: string | number | null | undefined): string {
  const parsed = parseFiniteNumber(value);
  if (parsed === null) return "—";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(parsed);
}

export function formatCurrency(value: string | number | null | undefined): string {
  const parsed = parseFiniteNumber(value);
  if (parsed === null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(parsed);
}

export function formatPercent(value: string | number | null | undefined): string {
  const parsed = parseFiniteNumber(value);
  if (parsed === null) return "—";
  return `${new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(parsed)}%`;
}

export function formatInteger(value: string | number | null | undefined): string {
  const parsed = parseFiniteNumber(value);
  if (parsed === null) return "—";
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 0,
  }).format(parsed);
}
