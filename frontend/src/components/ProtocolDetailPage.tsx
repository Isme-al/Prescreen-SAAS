import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { getProtocol, addCriterion, updateCriterion, deleteCriterion } from "../services/api";
import type { Protocol, Criterion } from "../types";

const EMPTY_CRITERION: Omit<Criterion, "id"> = {
  criterion_type: "inclusion",
  number: 1,
  description: "",
  keywords: "",
  category: "",
};

export default function ProtocolDetailPage() {
  const { id } = useParams();
  const [protocol, setProtocol] = useState<Protocol | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<Omit<Criterion, "id">>(EMPTY_CRITERION);
  const [error, setError] = useState("");

  const load = () => {
    if (id) getProtocol(Number(id)).then(setProtocol).catch(() => {});
  };
  useEffect(() => { load(); }, [id]);

  const resetForm = () => {
    setForm(EMPTY_CRITERION);
    setShowForm(false);
    setEditingId(null);
    setError("");
  };

  const handleSave = async () => {
    if (!form.description) { setError("Description is required"); return; }
    setError("");
    try {
      if (editingId) {
        await updateCriterion(Number(id), editingId, form);
      } else {
        await addCriterion(Number(id), form);
      }
      resetForm();
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleEdit = (c: Criterion) => {
    setForm({
      criterion_type: c.criterion_type,
      number: c.number,
      description: c.description,
      keywords: c.keywords,
      category: c.category,
    });
    setEditingId(c.id!);
    setShowForm(true);
  };

  const handleDelete = async (criterionId: number) => {
    if (!confirm("Delete this criterion?")) return;
    await deleteCriterion(Number(id), criterionId);
    load();
  };

  if (!protocol) return <div className="loading">Loading...</div>;

  const inclusion = protocol.criteria.filter((c) => c.criterion_type === "inclusion");
  const exclusion = protocol.criteria.filter((c) => c.criterion_type === "exclusion");

  return (
    <div>
      <Link to="/protocols" className="text-sm">&larr; Back to Protocols</Link>

      <div className="flex-between mt-1">
        <div>
          <h2>{protocol.protocol_number} — {protocol.name}</h2>
          <p className="text-muted text-sm">
            {protocol.sponsor} | {protocol.indication} | {protocol.phase}
          </p>
        </div>
        <button className="btn-primary" onClick={() => { resetForm(); setShowForm(!showForm); }}>
          {showForm ? "Cancel" : "+ Add Criterion"}
        </button>
      </div>

      {error && <div className="error mt-1">{error}</div>}

      {showForm && (
        <div className="card mt-1">
          <h4 className="mb-1">{editingId ? "Edit" : "Add"} Criterion</h4>
          <div className="form-row">
            <div className="form-group">
              <label>Type</label>
              <select value={form.criterion_type} onChange={(e) => setForm({ ...form, criterion_type: e.target.value as any })}>
                <option value="inclusion">Inclusion</option>
                <option value="exclusion">Exclusion</option>
              </select>
            </div>
            <div className="form-group">
              <label>Number</label>
              <input type="number" value={form.number} onChange={(e) => setForm({ ...form, number: Number(e.target.value) })} />
            </div>
          </div>
          <div className="form-group">
            <label>Description</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="e.g. Patient must have documented diagnosis of Type 2 Diabetes Mellitus" />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Keywords (comma-separated)</label>
              <input value={form.keywords} onChange={(e) => setForm({ ...form, keywords: e.target.value })}
                placeholder="e.g. diabetes, dm2, type 2 diabetes, t2dm, hba1c" />
            </div>
            <div className="form-group">
              <label>Category</label>
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                <option value="">Select</option>
                <option value="demographics">Demographics</option>
                <option value="diagnosis">Diagnosis</option>
                <option value="labs">Labs</option>
                <option value="medications">Medications</option>
                <option value="procedures">Procedures</option>
                <option value="vitals">Vitals</option>
                <option value="history">History</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <button className="btn-primary" onClick={handleSave}>
            {editingId ? "Update" : "Add"} Criterion
          </button>
        </div>
      )}

      {/* Inclusion Criteria */}
      <h3 className="mt-2 mb-1">Inclusion Criteria ({inclusion.length})</h3>
      {inclusion.length === 0 && <p className="text-muted text-sm">No inclusion criteria yet.</p>}
      {inclusion.sort((a, b) => a.number - b.number).map((c) => (
        <div key={c.id} className="criterion-card">
          <div className="header">
            <span><strong>#{c.number}</strong> <span className="text-muted text-sm">[{c.category || "uncategorized"}]</span></span>
            <div className="flex gap-1">
              <button className="btn-sm" onClick={() => handleEdit(c)}>Edit</button>
              <button className="btn-sm btn-danger" onClick={() => handleDelete(c.id!)}>Delete</button>
            </div>
          </div>
          <div className="description">{c.description}</div>
          {c.keywords && <div className="text-muted text-sm mt-1">Keywords: {c.keywords}</div>}
        </div>
      ))}

      {/* Exclusion Criteria */}
      <h3 className="mt-2 mb-1">Exclusion Criteria ({exclusion.length})</h3>
      {exclusion.length === 0 && <p className="text-muted text-sm">No exclusion criteria yet.</p>}
      {exclusion.sort((a, b) => a.number - b.number).map((c) => (
        <div key={c.id} className="criterion-card">
          <div className="header">
            <span><strong>#{c.number}</strong> <span className="text-muted text-sm">[{c.category || "uncategorized"}]</span></span>
            <div className="flex gap-1">
              <button className="btn-sm" onClick={() => handleEdit(c)}>Edit</button>
              <button className="btn-sm btn-danger" onClick={() => handleDelete(c.id!)}>Delete</button>
            </div>
          </div>
          <div className="description">{c.description}</div>
          {c.keywords && <div className="text-muted text-sm mt-1">Keywords: {c.keywords}</div>}
        </div>
      ))}
    </div>
  );
}
