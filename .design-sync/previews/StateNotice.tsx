import { StateNotice } from "ventures-crm-frontend";

export function Empty() {
  return (
    <div style={{ maxWidth: 420 }}>
      <StateNotice
        title="No companies yet"
        description="Companies you source or import will show up here."
      />
    </div>
  );
}

export function Error() {
  return (
    <div style={{ maxWidth: 420 }}>
      <StateNotice
        variant="error"
        title="Couldn’t load pipeline"
        description="The request timed out. Check your connection and try again."
      />
    </div>
  );
}

export function TitleOnly() {
  return (
    <div style={{ maxWidth: 420 }}>
      <StateNotice title="Loading deals…" />
    </div>
  );
}
