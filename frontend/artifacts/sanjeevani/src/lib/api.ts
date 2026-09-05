const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");
const GIS_BASE_URL = (
  import.meta.env.VITE_GIS_API_BASE_URL ?? API_BASE_URL
).replace(/\/$/, "");
const MCP_BASE_URL = (
  import.meta.env.VITE_MCP_API_BASE_URL ?? API_BASE_URL
).replace(/\/$/, "");

export const USE_MOCKS = (import.meta.env.VITE_USE_MOCKS ?? "false") === "true";

type RequestOptions = RequestInit & { baseUrl?: string };

async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { baseUrl = API_BASE_URL, ...init } = options;
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      ...(init.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...init.headers,
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

const post = <T>(path: string, body: unknown, baseUrl = API_BASE_URL) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body), baseUrl });

export type DispatchPreview = {
  id: string;
  status?: "PREVIEW" | "IN_TRANSIT" | "DELIVERED";
  etaMinutes?: number;
  lender?: string;
  amount?: number;
  selected_hospital?: Record<string, unknown>;
  loan?: Record<string, unknown> | null;
  error?: string;
};

export async function previewDispatch(
  input: Record<string, unknown>,
): Promise<DispatchPreview> {
  if (USE_MOCKS) return { id: `preview-${Date.now()}`, status: "PREVIEW" };
  return post<DispatchPreview>("/dispatch/preview", input);
}

export async function createDispatch(
  input: Record<string, unknown>,
): Promise<DispatchPreview> {
  return post<DispatchPreview>("/dispatch", input);
}

export async function getHospitals() {
  return request<Array<Record<string, unknown>>>("/hospitals");
}

export async function getHospital(id: string) {
  return request<Record<string, unknown> | null>(
    `/hospitals/${encodeURIComponent(id)}`,
  );
}

export async function createHospital(input: Record<string, unknown>) {
  return post<{ message: string }>("/hospitals", input);
}

export async function uploadInventory(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return request<{ message: string }>("/inventory/upload", {
    method: "POST",
    body: formData,
  });
}

export async function getInventory(hospitalId: string) {
  return request<Array<Record<string, unknown>>>(
    `/inventory/${encodeURIComponent(hospitalId)}`,
  );
}

export async function searchInventory(query: {
  equipmentType: number;
  quantity: number;
}) {
  const params = new URLSearchParams({
    equipment_type: String(query.equipmentType),
    quantity: String(query.quantity),
  });
  return request<Array<Record<string, unknown>>>(`/inventory/search?${params}`);
}

export type ChatResponse = {
  session_id?: string;
  reply?: string;
  response?: string;
  approval_required?: boolean;
  tx_hash?: string;
  loan_id?: number;
  [key: string]: unknown;
};

export async function sendChat(
  message: string,
  hospitalId?: string,
  sessionId?: string,
) {
  if (USE_MOCKS)
    return {
      response:
        "I found the best available option and prepared the next safe step.",
    };
  return post<ChatResponse>(
    "/chat",
    {
      query: message,
      ...(hospitalId ? { hospital_id: hospitalId } : {}),
      ...(sessionId ? { session_id: sessionId } : {}),
    },
    MCP_BASE_URL,
  );
}

export async function bestOption(input: unknown) {
  return post("/gis/best-option", input, GIS_BASE_URL);
}

export async function getRoute(input: unknown) {
  return post("/gis/route", input, GIS_BASE_URL);
}

export async function getRouteMap(input: unknown) {
  return post("/gis/route-map", input, GIS_BASE_URL);
}

export async function getIsochrone(input: unknown) {
  return post("/gis/isochrone", input, GIS_BASE_URL);
}

export async function getIsochroneMap(input: unknown) {
  return post("/gis/isochrone-map", input, GIS_BASE_URL);
}

export async function emitLoanCreated(input: Record<string, unknown>) {
  return post("/events/loan-created", input);
}

export async function emitDeliveryConfirmed(input: Record<string, unknown>) {
  return post("/events/delivery-confirmed", input);
}

export async function emitLoanSettled(input: Record<string, unknown>) {
  return post("/events/loan-settled", input);
}
