/** Stub page for sections built out by Agents 21/22. */
export function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="space-y-2">
      <h1 className="text-xl font-semibold">{title}</h1>
      <p className="text-sm text-muted-foreground">Coming soon.</p>
    </div>
  );
}

export function NotFoundPage() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2">
      <h1 className="text-2xl font-semibold">404</h1>
      <p className="text-sm text-muted-foreground">Page not found.</p>
    </div>
  );
}
