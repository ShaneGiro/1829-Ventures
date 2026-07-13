import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Company, Page } from "@/api/types";

export interface CandidateCompany extends Company {
  alumni_founder_status: "active" | "unclear" | "inactive" | "not_found" | "unverified";
  alumni_founder_confidence?: number | null;
  operational_status: "operational" | "unclear" | "not_operational" | "unverified";
  operational_confidence?: number | null;
  rubric_fit_score?: number | null;
  thesis_alignment_score?: number | null;
  fit_score_reasons: string[];
}

export interface OutreachCandidate {
  company: CandidateCompany;
  score: number;
  score_version: string;
  breakdown: Record<string, number>;
  why_this_company: string;
  warnings: string[];
  last_outreach_at?: string | null;
  follow_up_needed: boolean;
}

export function useOutreachCandidates(includeRecentlyContacted = false) {
  return useQuery({
    queryKey: ["outreach-candidates", includeRecentlyContacted],
    queryFn: () =>
      api.get<Page<OutreachCandidate>>("/outreach-candidates", {
        limit: 200,
        include_recently_contacted: includeRecentlyContacted,
      }),
  });
}
