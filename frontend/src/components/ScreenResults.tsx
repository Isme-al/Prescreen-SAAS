import type { ScreenResponse, CriterionMatchResult } from "../types";

const STATUS_LABELS: Record<string, string> = {
  eligible: "Potentially Eligible",
  not_eligible: "Screen Fail",
  needs_review: "Needs Review",
};

const MATCH_LABELS: Record<string, string> = {
  met: "Met",
  not_met: "Not Met",
  uncertain: "Uncertain",
  not_evaluated: "Not Evaluated",
};

function ConfidenceBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color =
    confidence >= 0.7 ? "var(--success)" : confidence >= 0.5 ? "var(--warning)" : "var(--text-muted)";
  return (
    <div className="confidence-bar">
      <div className="fill" style={{ width: `${pct}%`, background: color }} />
    </div>
  );
}

function CriterionCard({ r }: { r: CriterionMatchResult }) {
  const typeLabel = r.criterion_type === "inclusion" ? "INC" : "EXC";
  return (
    <div className="criterion-card">
      <div className="header">
        <span>
          <strong>{typeLabel} #{r.criterion_number}</strong>
        </span>
        <span className={`status-badge status-${r.status}`}>
          {MATCH_LABELS[r.status]}
        </span>
      </div>
      <div className="description">{r.description}</div>
      <div className="reasoning">{r.reasoning}</div>
      <ConfidenceBar confidence={r.confidence} />
      {r.evidence.length > 0 && (
        <div className="evidence">
          <strong>Evidence:</strong>
          {r.evidence.map((e, i) => (
            <div key={i} style={{ marginTop: "0.25rem" }}>
              {e}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ScreenResults({ result }: { result: ScreenResponse }) {
  const inclusion = result.results.filter((r) => r.criterion_type === "inclusion");
  const exclusion = result.results.filter((r) => r.criterion_type === "exclusion");

  return (
    <div>
      <div className="card">
        <div className="flex-between mb-1">
          <h3>Screening Result</h3>
          <span className={`status-badge status-${result.overall_status}`}>
            {STATUS_LABELS[result.overall_status]}
          </span>
        </div>
        <pre className="text-sm text-muted" style={{ whiteSpace: "pre-wrap" }}>
          {result.summary}
        </pre>
      </div>

      {inclusion.length > 0 && (
        <>
          <h4 className="mb-1">Inclusion Criteria</h4>
          {inclusion.map((r) => (
            <CriterionCard key={r.criterion_id} r={r} />
          ))}
        </>
      )}

      {exclusion.length > 0 && (
        <>
          <h4 className="mb-1 mt-2">Exclusion Criteria</h4>
          {exclusion.map((r) => (
            <CriterionCard key={r.criterion_id} r={r} />
          ))}
        </>
      )}

      <details className="mt-2">
        <summary className="text-muted text-sm" style={{ cursor: "pointer" }}>
          View Redacted Text
        </summary>
        <div className="redacted-text mt-1">{result.redacted_text}</div>
      </details>
    </div>
  );
}
