import { ConfirmDialog } from "ventures-crm-frontend";

const noop = () => {};

// ConfirmDialog renders a `fixed inset-0` overlay. In the card grid each cell
// has `transform`, which makes `fixed` anchor to the (short) cell box rather
// than the viewport — so the centered modal clips at the top. A flow-height
// spacer grows the cell so the whole dialog (title included) stays in view.
function Stage({ children }: { children: React.ReactNode }) {
  return <div style={{ height: 360 }}>{children}</div>;
}

export function Destructive() {
  return (
    <Stage>
      <ConfirmDialog
        open
        destructive
        title="Delete this deal?"
        description="Northwind Analytics will be removed from your pipeline. This can’t be undone."
        confirmLabel="Delete deal"
        cancelLabel="Keep"
        onConfirm={noop}
        onCancel={noop}
      />
    </Stage>
  );
}

export function Default() {
  return (
    <Stage>
      <ConfirmDialog
        open
        title="Move to Diligence?"
        description="This advances the company to the next pipeline stage."
        confirmLabel="Move stage"
        onConfirm={noop}
        onCancel={noop}
      />
    </Stage>
  );
}
