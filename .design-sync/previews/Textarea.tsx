import { Textarea } from "ventures-crm-frontend";

export function Default() {
  return (
    <div style={{ maxWidth: 420 }}>
      <Textarea
        rows={4}
        defaultValue={
          "Met the founders at the demo day. Clear product vision and strong early traction with two design partners. Want to revisit after the next cohort of customers lands."
        }
      />
    </div>
  );
}

export function Labeled() {
  return (
    <label style={{ display: "block", maxWidth: 420 }}>
      <span style={{ display: "block", fontSize: 13, fontWeight: 500, marginBottom: 6 }}>
        Outreach message
      </span>
      <Textarea rows={5} placeholder="Write a note to the founder…" />
    </label>
  );
}
