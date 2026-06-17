# 1829 Ventures CRM UI — conventions

A small Tailwind-based component kit (shadcn-style) for the 1829 Ventures CRM. Use these real components for controls and surfaces; style your own layout glue with the design tokens below.

## Setup — no provider needed

Components are plain and self-styled. There is **no** theme provider, context, or root wrapper to mount — just import and render. Tokens are global CSS custom properties defined on `:root` in `styles.css`, so they apply everywhere automatically. Light theme only.

```jsx
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from "ventures-crm-frontend";

<Card>
  <CardHeader><CardTitle>Northwind Analytics</CardTitle></CardHeader>
  <CardContent>
    <p style={{ color: "hsl(var(--muted-foreground))" }}>Series A · Fintech · SF</p>
    <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
      <Badge>High priority</Badge>
      <Button size="sm">Open</Button>
    </div>
  </CardContent>
</Card>
```

## Styling idiom — use the design tokens

The brand palette lives in CSS custom properties as HSL triplets, consumed as `hsl(var(--token))`. These are **always defined** and are the reliable way to stay on-brand:

| Token | Use |
|---|---|
| `--primary` / `--primary-foreground` | brand navy actions, primary buttons |
| `--background` / `--foreground` | surface and default text |
| `--muted` / `--muted-foreground` | subtle fills, secondary text |
| `--accent` / `--accent-foreground` | hover/selected surfaces |
| `--destructive` / `--destructive-foreground` | dangerous actions, errors |
| `--border` | hairline borders/dividers |

Example: `style={{ background: "hsl(var(--primary))", color: "hsl(var(--primary-foreground))" }}`.

**Important — the stylesheet is a compiled snapshot.** `styles.css` (which `@import`s `_ds_bundle.css`) contains only the Tailwind utility classes the components themselves use (`bg-primary`, `text-muted-foreground`, `border-border`, `rounded-md`, `rounded-lg`, …). It is **not** a full Tailwind build, so an arbitrary new utility class you invent (e.g. `bg-accent`, `grid-cols-3`, `p-6`) will likely have no CSS and render unstyled. For custom layout and spacing, prefer inline styles / your own CSS using the `hsl(var(--token))` variables above, rather than reaching for utility classes that may not exist.

## Components

- **Button** — `variant`: `default | outline | ghost | destructive`; `size`: `default | sm | lg | icon`. Accepts native button props.
- **Badge** — small rounded pill for tags / pipeline stages. Pass text as children.
- **Card / CardHeader / CardTitle / CardContent** — compose in that order; `CardHeader` adds a bottom divider.
- **Input / Textarea** — full-width form fields; standard input/textarea props.
- **ConfirmDialog** — controlled modal (`open`, `title`, `description`, `onConfirm`, `onCancel`, `destructive`). Renders a full-screen overlay; renders nothing when `open` is false.
- **StateNotice** — empty/error/loading panel; `variant`: `muted | error`, with `title` and optional `description`.

## Where the truth lives

- `styles.css` → `_ds_bundle.css` for the token definitions and compiled classes.
- Each component's `<Name>.d.ts` (the prop contract) and `<Name>.prompt.md` (usage) under `components/general/<Name>/`.
