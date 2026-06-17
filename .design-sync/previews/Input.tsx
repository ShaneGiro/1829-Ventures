import { Input } from "ventures-crm-frontend";

export function Default() {
  return (
    <div style={{ maxWidth: 320 }}>
      <Input placeholder="Search companies…" defaultValue="Northwind" />
    </div>
  );
}

export function Labeled() {
  return (
    <label style={{ display: "block", maxWidth: 320 }}>
      <span style={{ display: "block", fontSize: 13, fontWeight: 500, marginBottom: 6 }}>
        Company website
      </span>
      <Input type="url" placeholder="https://example.com" />
    </label>
  );
}

export function Disabled() {
  return (
    <div style={{ maxWidth: 320 }}>
      <Input placeholder="Read only" defaultValue="acme.com" disabled />
    </div>
  );
}
