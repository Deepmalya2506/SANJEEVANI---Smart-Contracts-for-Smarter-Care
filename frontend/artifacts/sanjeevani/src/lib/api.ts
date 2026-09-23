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

export async function getNetworkNodes() {
  if (USE_MOCKS) {
    return {
      status: "success",
      nodes: [
        {
          hospital_id: "st-martha",
          hospital_name: "St. Martha Medical Centre",
          latitude: 22.5726,
          longitude: 88.3639,
          h3_cell: "873cf2c60ffffff",
          available_count: 5,
          total_assets: 8,
        },
        {
          hospital_id: "carebridge",
          hospital_name: "CareBridge Network",
          latitude: 22.5958,
          longitude: 88.4112,
          h3_cell: "873cf2c62ffffff",
          available_count: 2,
          total_assets: 6,
        },
        {
          hospital_id: "northstar",
          hospital_name: "Northstar Health Hub",
          latitude: 22.5512,
          longitude: 88.3498,
          h3_cell: "873cf2c64ffffff",
          available_count: 7,
          total_assets: 12,
        },
      ],
    };
  }
  return request<{ status: string; count: number; nodes: any[] }>("/api/v1/gis/network-nodes");
}

export async function searchSpatialCandidates(input: {
  origin: { lat: number; lon: number };
  equipment_type: string;
  radius_km?: number;
  max_eta_minutes?: number;
}) {
  return post<{ status: string; count: number; candidates: any[] }>("/api/v1/gis/candidates", input);
}

export async function getGisRoute(input: {
  source: { lat: number; lon: number };
  destination: { lat: number; lon: number };
}) {
  return post<{ status: string; data: any }>("/api/v1/gis/routes", input);
}

export async function getH3Footprint(lat: number, lon: number, k_rings = 2, resolution = 7) {
  const params = new URLSearchParams({
    lat: String(lat),
    lon: String(lon),
    k_rings: String(k_rings),
    resolution: String(resolution),
  });
  const res = await request<{ status: string; data: any }>(`/api/v1/gis/h3-footprint?${params}`);
  return res.data;
}

