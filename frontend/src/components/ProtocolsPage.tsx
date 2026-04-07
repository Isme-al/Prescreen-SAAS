import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getProtocols, createProtocol, deleteProtocol } from "../services/api";
import type { ProtocolListItem } from "../types";

export default function ProtocolsPage() {
  const [protocols, setProtocols] = useState<ProtocolListItem[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    name: "", protocol_number: "", sponsor: "", indication: "", phase: "", description: "",
  });
  const [error, setError] = useState("");

  const load = () => getProtocols().then(setProtocols).catch(() => {});
  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!form.name || !form.protocol_number) {
      setError("Name and protocol number are required");
      return;
    }
    setError("");
    try {
      await createProtocol(form);
      setForm({ name: "", protocol_number: "", sponsor: "", indication: "", phase: "", description: "" });
      setShowForm(false);
      load();
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this protocol and all its criteria?")) return;
    await deleteProtocol(id);
    load();
  };

  return (
    <div>
      <div className="flex-between">
        <h2>Protocols</h2>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "+ New Protocol"}
        </button>
      </div>

      {error && <div className="error mt-1">{error}</div>}

      {showForm && (
        <div className="card mt-1">
          <div className="form-row">
            <div className="form-group">
              <label>Protocol Name *</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. KEYNOTE-522" />
            </div>
            <div className="form-group">
              <label>Protocol Number *</label>
              <input value={form.protocol_number} onChange={(e) => setForm({ ...form, protocol_number: e.target.value })} placeholder="e.g. MK-3475-522" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Sponsor</label>
              <input value={form.sponsor} onChange={(e) => setForm({ ...form, sponsor: e.target.value })} placeholder="e.g. Merck" />
            </div>
            <div className="form-group">
              <label>Indication</label>
              <input value={form.indication} onChange={(e) => setForm({ ...form, indication: e.target.value })} placeholder="e.g. Triple-Negative Breast Cancer" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Phase</label>
              <select value={form.phase} onChange={(e) => setForm({ ...form, phase: e.target.value })}>
                <option value="">Select</option>
                <option>Phase 1</option>
                <option>Phase 1/2</option>
                <option>Phase 2</option>
                <option>Phase 2/3</option>
                <option>Phase 3</option>
                <option>Phase 4</option>
              </select>
            </div>
            <div className="form-group">
              <label>Description</label>
              <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Brief description" />
            </div>
          </div>
          <button className="btn-primary" onClick={handleCreate}>Create Protocol</button>
        </div>
      )}

      <table className="mt-2">
        <thead>
          <tr>
            <th>Protocol</th>
            <th>Sponsor</th>
            <th>Indication</th>
            <th>Phase</th>
            <th>Criteria</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {protocols.length === 0 && (
            <tr><td colSpan={6} className="text-muted text-sm" style={{ textAlign: "center", padding: "2rem" }}>No protocols yet. Create one to get started.</td></tr>
          )}
          {protocols.map((p) => (
            <tr key={p.id}>
              <td><Link to={`/protocols/${p.id}`}><strong>{p.protocol_number}</strong> — {p.name}</Link></td>
              <td>{p.sponsor}</td>
              <td>{p.indication}</td>
              <td>{p.phase}</td>
              <td>{p.criteria_count}</td>
              <td><button className="btn-danger btn-sm" onClick={() => handleDelete(p.id)}>Delete</button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
