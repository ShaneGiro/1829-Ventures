import { cn } from "@/lib/utils";

type StateNoticeVariant = "muted" | "error";

export function StateNotice({
  title,
  description,
  variant = "muted",
  className,
}: {
  title: string;
  description?: string;
  variant?: StateNoticeVariant;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-md border border-dashed p-4 text-sm",
        variant === "error"
          ? "border-red-200 bg-red-50 text-red-800"
          : "bg-muted/20 text-muted-foreground",
        className,
      )}
    >
      <div className={cn("font-medium", variant === "error" ? "text-red-900" : "text-foreground")}>
        {title}
      </div>
      {description && <div className="mt-1">{description}</div>}
    </div>
  );
}
