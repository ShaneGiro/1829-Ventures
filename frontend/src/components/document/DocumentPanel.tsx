import { useRef, useState } from "react";
import { Archive, Download, UploadCloud } from "lucide-react";
import {
  downloadDocument,
  useArchiveDocument,
  useDocuments,
  useUploadDocument,
} from "@/api/documents";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const ACCEPTED_EXTENSIONS =
  ".pdf,.md,.markdown,.txt,.doc,.docx,.xls,.xlsx,.csv,.png,.jpg,.jpeg";

interface DocumentPanelProps {
  companyId?: string;
  personId?: string;
}

export function DocumentPanel({ companyId, personId }: DocumentPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const documents = useDocuments({ company_id: companyId, person_id: personId, limit: 50 });
  const upload = useUploadDocument();
  const archive = useArchiveDocument();

  async function uploadFiles(files: FileList | File[]) {
    for (const file of Array.from(files)) {
      await upload.mutateAsync({ file, company_id: companyId, person_id: personId });
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Documents</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <button
          type="button"
          className={`flex w-full flex-col items-center gap-2 rounded-md border border-dashed p-5 text-sm transition-colors ${
            isDragging ? "border-primary bg-primary/5" : "border-border hover:bg-muted/40"
          }`}
          onClick={() => inputRef.current?.click()}
          onDragEnter={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragOver={(event) => event.preventDefault()}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            void uploadFiles(event.dataTransfer.files);
          }}
          disabled={upload.isPending}
        >
          <UploadCloud className="h-5 w-5" />
          {upload.isPending ? "Uploading…" : "Drop files here or choose files"}
        </button>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_EXTENSIONS}
          className="hidden"
          onChange={(event) => {
            if (event.target.files) void uploadFiles(event.target.files);
            event.target.value = "";
          }}
        />
        {upload.error && <p className="text-sm text-destructive">{upload.error.message}</p>}

        <div className="space-y-2">
          {documents.data?.items.length ? (
            documents.data.items.map((document) => (
              <div key={document.id} className="flex items-center gap-2 rounded-md border p-2">
                <span className="min-w-0 flex-1 truncate text-sm">{document.filename}</span>
                {document.storage_key && (
                  <Button
                    variant="ghost"
                    size="sm"
                    aria-label={`Download ${document.filename}`}
                    onClick={() => void downloadDocument(document.id)}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label={`Archive ${document.filename}`}
                  onClick={() => archive.mutate(document.id)}
                  disabled={archive.isPending}
                >
                  <Archive className="h-4 w-4" />
                </Button>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No documents.</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
