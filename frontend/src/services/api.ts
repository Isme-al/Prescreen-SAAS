import type { Protocol, ProtocolListItem, ScreenResponse, RedactResponse } from "../types";

const BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// Protocols
export const getProtocols = () => request<ProtocolListItem[]>("/protocols");
export const getProtocol = (id: number) => request<Protocol>(`/protocols/${id}`);
export const createProtocol = (data: Partial<Protocol>) =>
  request<Protocol>("/protocols", { method: "POST", body: JSON.stringify(data) });
export const deleteProtocol = (id: number) =>
  request<void>(`/protocols/${id}`, { method: "DELETE" });

// Criteria
export const addCriterion = (protocolId: number, data: any) =>
  request(`/protocols/${protocolId}/criteria`, { method: "POST", body: JSON.stringify(data) });
export const updateCriterion = (protocolId: number, criterionId: number, data: any) =>
  request(`/protocols/${protocolId}/criteria/${criterionId}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteCriterion = (protocolId: number, criterionId: number) =>
  request<void>(`/protocols/${protocolId}/criteria/${criterionId}`, { method: "DELETE" });

// Screening
export const screenPatient = (medicalText: string, protocolId: number) =>
  request<ScreenResponse>("/screening/screen", {
    method: "POST",
    body: JSON.stringify({ medical_text: medicalText, protocol_id: protocolId }),
  });

export const redactText = (text: string) =>
  request<RedactResponse>("/screening/redact", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
