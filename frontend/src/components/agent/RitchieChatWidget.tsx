import { FormEvent, useMemo, useState } from "react";
import { Bot, CheckCircle2, Loader2, MessageSquare, Send, X } from "lucide-react";
import { useAgentEvents, useChatWithRitchie } from "@/api/agentApi";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type ChatMessage = {
  id: string;
  role: "user" | "ritchie";
  text: string;
};

const STATUS_STYLE: Record<string, string> = {
  pending: "border-blue-500 text-blue-700",
  processing: "border-blue-500 text-blue-700",
  processed: "border-green-500 text-green-700",
  policy_blocked: "border-red-500 text-red-700",
  agent_unavailable: "border-amber-500 text-amber-700",
  failed: "border-red-500 text-red-700",
};

function eventLabel(eventType: string, status: string) {
  if (eventType === "human_prompt" && status === "processing") return "queued";
  if (eventType === "human_prompt" && status === "processed") return "delivered";
  return status.replaceAll("_", " ");
}

function initialMessages(): ChatMessage[] {
  return [
    {
      id: "welcome",
      role: "ritchie",
      text: "What should I work on?",
    },
  ];
}

export function RitchieChatWidget() {
  const [open, setOpen] = useState(false);
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const chat = useChatWithRitchie();
  const events = useAgentEvents({ limit: 5 });

  const latestStatus = useMemo(() => events.data?.items[0], [events.data?.items]);

  const submit = (event?: FormEvent) => {
    event?.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed || chat.isPending) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: trimmed,
    };
    setMessages((current) => [...current, userMessage]);
    setPrompt("");

    chat.mutate(
      { prompt: trimmed },
      {
        onSuccess: (response) => {
          setMessages((current) => [
            ...current,
            {
              id: crypto.randomUUID(),
              role: "ritchie",
              text: response.message,
            },
          ]);
        },
        onError: () => {
          setMessages((current) => [
            ...current,
            {
              id: crypto.randomUUID(),
              role: "ritchie",
              text: "I could not reach Ritchie for chat.",
            },
          ]);
        },
      },
    );
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 flex max-w-[calc(100vw-2rem)] flex-col items-end gap-3">
      {open && (
        <section className="flex h-[min(34rem,calc(100vh-6rem))] w-[min(26rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-lg border bg-background shadow-xl">
          <header className="flex min-h-12 items-center justify-between gap-3 border-b px-3">
            <div className="flex min-w-0 items-center gap-2">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <Bot className="h-4 w-4" />
              </span>
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold">Ritchie</div>
                {latestStatus ? (
                  <div className="truncate text-xs text-muted-foreground">
                    Latest: {latestStatus.event_type.replaceAll("_", " ")}
                  </div>
                ) : (
                  <div className="truncate text-xs text-muted-foreground">Ready</div>
                )}
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Close Ritchie chat"
              onClick={() => setOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </header>

          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex",
                  message.role === "user" ? "justify-end" : "justify-start",
                )}
              >
                <div
                  className={cn(
                    "max-w-[85%] rounded-lg px-3 py-2 text-sm leading-5",
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "border bg-muted/40",
                  )}
                >
                  {message.text}
                </div>
              </div>
            ))}
            {chat.isPending && (
              <div className="flex justify-start">
                <div className="inline-flex items-center gap-2 rounded-lg border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Thinking
                </div>
              </div>
            )}
          </div>

          <div className="border-t p-3">
            {latestStatus && (
              <div className="mb-2 flex min-w-0 items-center justify-between gap-2 text-xs">
                <span className="truncate text-muted-foreground">
                  {latestStatus.event_type.replaceAll("_", " ")}
                </span>
                <Badge className={STATUS_STYLE[latestStatus.status] ?? ""}>
                  {eventLabel(latestStatus.event_type, latestStatus.status)}
                </Badge>
              </div>
            )}
            <form className="space-y-2" onSubmit={submit}>
              <Textarea
                value={prompt}
                onChange={(event) => setPrompt(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) submit(event);
                }}
                placeholder="Message Ritchie..."
                className="max-h-32 min-h-20 resize-none"
              />
              <div className="flex justify-end">
                <Button type="submit" disabled={!prompt.trim() || chat.isPending}>
                  <Send className="h-4 w-4" />
                  Send
                </Button>
              </div>
            </form>
          </div>
        </section>
      )}

      <Button
        type="button"
        size="lg"
        className="h-12 rounded-full px-4 shadow-lg"
        aria-label={open ? "Hide Ritchie chat" : "Open Ritchie chat"}
        onClick={() => setOpen((current) => !current)}
      >
        {open ? <CheckCircle2 className="h-5 w-5" /> : <MessageSquare className="h-5 w-5" />}
        Ritchie
      </Button>
    </div>
  );
}
