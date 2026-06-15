/** Convenience aliases over the generated OpenAPI types. Never hand-edit shapes. */
import type { components } from "@/types/api";

export type Schemas = components["schemas"];

export type Company = Schemas["CompanyRead"];
export type CompanyCreate = Schemas["CompanyCreate"];
export type CompanyUpdate = Schemas["CompanyUpdate"];
export type CompanyCompleteness = Schemas["CompanyCompleteness"];
export type Person = Schemas["PersonRead"];
export type Affiliation = Schemas["AffiliationRead"];
export type Deal = Schemas["DealRead"];
export type DealStatus = Schemas["DealStatusRead"];
export type Rubric = Schemas["RubricRead"];
export type RubricUpdate = Schemas["RubricUpdate"];
export type Interaction = Schemas["InteractionRead"];
export type Task = Schemas["TaskRead"];
export type TaskCreate = Schemas["TaskCreate"];
export type DocumentMeta = Schemas["DocumentRead"];
// Agent 22: imports, Ritchie governance, portfolio.
export type ImportBatch = Schemas["ImportBatchRead"];
export type ImportRow = Schemas["ImportRowRead"];
export type AgentEvent = Schemas["AgentEventLogRead"];
export type AgentPolicy = Schemas["AgentPolicyRead"];
export type PolicyState = Schemas["PolicyState"];
export type Fund = Schemas["FundRead"];
export type Investment = Schemas["InvestmentRead"];
export type PortfolioMetric = Schemas["PortfolioMetricRead"];
export type PortfolioSummary = Schemas["PortfolioSummary"];
export type AgentActivitySummary = Schemas["AgentActivitySummary"];

/** All PaginatedResponse_X_ share this shape. */
export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
