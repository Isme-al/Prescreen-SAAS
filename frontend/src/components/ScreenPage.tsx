import { useState, useEffect } from "react";
import { getProtocols, screenPatient, redactText } from "../services/api";
import type { ProtocolListItem, ScreenResponse } from "../types";
import ScreenResults from "./ScreenResults";

export default function ScreenPage() {
  const [protocols, setProtocols] = useState<ProtocolListItem[]>([]);
  const [selectedProtocol, setSelectedProtocol] = useState<number | "">("");
  const [medicalText, setMedicalText] = useState("");
  const [result, setResult] = useState<ScreenResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getProtocols().then(setProtocols).catch(() => {});
  }, []);

  const handleScreen = async () => {
    if (!selectedProtocol || !medicalText.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await screenPatient(medicalText, selectedProtocol as number);
      setResult(res);
    } catch (e: any) {
      setError(e.message || "Screening failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRedactOnly = async () => {
    if (!medicalText.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await redactText(medicalText);
      setMedicalText(res.redacted_text);
    } catch (e: any) {
      setError(e.message || "Redaction failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Patient Prescreening</h2>

      {error && <div className="error">{error}</div>}

      <div className="screen-layout">
        {/* Left: Input */}
        <div>
          <div className="form-group">
            <label>Select Protocol</label>
            <select
              value={selectedProtocol}
              onChange={(e) => setSelectedProtocol(e.target.value ? Number(e.target.value) : "")}
            >
              <option value="">-- Select a protocol --</option>
              {protocols.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.protocol_number} - {p.name} ({p.criteria_count} criteria)
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Paste Medical History / Progress Note</label>
            <textarea
              className="paste-area"
              placeholder={"Paste the patient's medical history, progress note, or H&P here...\n\nAll PHI will be automatically redacted before screening."}
              value={medicalText}
              onChange={(e) => setMedicalText(e.target.value)}
            />
          </div>

          <div className="flex gap-1">
            <button
              className="btn-primary"
              onClick={handleScreen}
              disabled={loading || !selectedProtocol || !medicalText.trim()}
            >
              {loading ? "Screening..." : "Screen Patient"}
            </button>
            <button
              onClick={handleRedactOnly}
              disabled={loading || !medicalText.trim()}
            >
              Redact PHI Only
            </button>
            <button
              onClick={() => { setMedicalText(""); setResult(null); setError(""); }}
              disabled={loading}
            >
              Clear
            </button>
          </div>
        </div>

        {/* Right: Results */}
        <div>
          {loading && <div className="loading">Screening in progress...</div>}
          {result && <ScreenResults result={result} />}
          {!result && !loading && (
            <div className="card">
              <p className="text-muted text-sm">
                Paste a patient's medical history on the left, select a protocol, and click
                "Screen Patient" to check eligibility against inclusion/exclusion criteria.
              </p>
              <p className="text-muted text-sm mt-1">
                All PHI is automatically redacted locally before any analysis.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
