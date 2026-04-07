export interface Criterion {
  id?: number;
  criterion_type: "inclusion" | "exclusion";
  number: number;
  description: string;
  keywords: string;
  category: string;
}

export interface Protocol {
  id: number;
  name: string;
  protocol_number: string;
  sponsor: string;
  indication: string;
  phase: string;
  description: string;
  created_at: string;
  criteria: Criterion[];
}

export interface ProtocolListItem {
  id: number;
  name: string;
  protocol_number: string;
  sponsor: string;
  indication: string;
  phase: string;
  criteria_count: number;
}

export interface CriterionMatchResult {
  criterion_id: number;
  criterion_type: string;
  criterion_number: number;
  description: string;
  status: "met" | "not_met" | "uncertain" | "not_evaluated";
  confidence: number;
  evidence: string[];
  reasoning: string;
}

export interface ScreenResponse {
  id: number | null;
  overall_status: "eligible" | "not_eligible" | "needs_review";
  summary: string;
  redacted_text: string;
  results: CriterionMatchResult[];
}

export interface RedactResponse {
  redacted_text: string;
  entity_count: number;
  entities_found: { type: string; original_length: number }[];
}
