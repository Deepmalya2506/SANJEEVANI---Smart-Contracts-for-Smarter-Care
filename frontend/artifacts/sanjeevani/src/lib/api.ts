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

export type RazorpayOrder = {
  order_id: string;
  amount_paise: number;
  currency: string;
  key_id: string;
  status: string;
};

export type RazorpayPayment = {
  razorpay_order_id: string;
  razorpay_payment_id: string;
  razorpay_signature: string;
};

export async function createPaymentOrder(input: {
  amountRupees: number;
  currency?: string;
  loanReference?: string;
  notes?: Record<string, string>;
}) {
  return post<RazorpayOrder>("/payments/orders", {
    amount_rupees: input.amountRupees,
    currency: input.currency ?? "INR",
    loan_reference: input.loanReference,
    notes: input.notes,
  });
}

export async function verifyPayment(input: RazorpayPayment) {
  return post<{ status: string; payment_id: string }>(
    "/payments/verify",
    input,
  );
}

export async function getHospitals() {
  return request<Array<Record<string, unknown>>>("/hospitals");
}

export async function searchFacilities(query: string = "", limit: number = 20) {
  const params = new URLSearchParams({ query, limit: String(limit) });
  return request<
    Array<{
      mvp_hfr_id: string;
      hospital_name: string;
      address?: string;
      latitude: number;
      longitude: number;
    }>
  >(`/api/v1/facilities/search?${params}`);
}

export async function getHospital(id: string) {
  return request<Record<string, unknown> | null>(
    `/hospitals/${encodeURIComponent(id)}`,
  );
}

export type HospitalRegistrationInput = {
  admin_name: string;
  email: string;
  hospital_name: string;
  mvp_hfr_id?: string;
  latitude?: number;
  longitude?: number;
  phone?: string;
  address?: string;
};

export type EquipmentAssetInput = {
  hospital_id?: string;
  equipment_type: string;
  name: string;
  serial_number?: string;
  condition_status?: string;
  hourly_rate?: number;
  shareable?: boolean;
  metadata?: Record<string, unknown>;
};

export type SanctionTransactionInput = {
  asset_id?: string;
  equipment_type: string;
  borrower_hospital_id: string;
  lender_hospital_id?: string;
  borrower_admin_email?: string;
  duration_hours?: number;
  amount_rupees: number;
  notes?: Record<string, unknown>;
};

export type NearbyHospitalItem = {
  mvp_hfr_id: string;
  hospital_name: string;
  address?: string;
  latitude: number;
  longitude: number;
  hospital_id?: string;
  profile_status?: string;
  verification_status?: string;
  distance_km: number;
  available_equipment?: Array<Record<string, unknown>>;
};

export type NotificationItem = {
  notification_id: string;
  hospital_id?: string;
  loan_id?: string;
  channel: string;
  event_type: string;
  recipient_email?: string;
  subject?: string;
  status: string;
  created_at: string;
  sent_at?: string;
};

export async function registerHospitalAdmin(input: HospitalRegistrationInput) {
  return post<{
    success: boolean;
    hospital_id: string;
    hospital_name: string;
    admin_name: string;
    admin_email: string;
    mvp_hfr_id: string;
    message: string;
  }>("/hospitals", input);
}

export async function registerEquipmentAsset(input: EquipmentAssetInput) {
  return post<Record<string, unknown>>("/equipment/assets", input);
}

export async function getNearbyHospitals(query: {
  lat: number;
  lon: number;
  radiusKm?: number;
  limit?: number;
  equipmentType?: string;
}) {
  const params = new URLSearchParams({
    lat: String(query.lat),
    lon: String(query.lon),
    radius_km: String(query.radiusKm ?? 100),
    limit: String(query.limit ?? 20),
    ...(query.equipmentType ? { equipment_type: query.equipmentType } : {}),
  });
  return request<NearbyHospitalItem[]>(`/hospitals/nearby?${params}`);
}

export async function sanctionTransaction(input: SanctionTransactionInput) {
  return post<{
    status: string;
    loan_id: string;
    order_id: string;
    amount_rupees: number;
    amount_paise: number;
    equipment_type: string;
    asset_id: string;
    lender_hospital_id: string;
    borrower_hospital_id: string;
    loan_status: string;
    asset_status: string;
    payment_order: RazorpayOrder;
    message: string;
  }>("/transactions/sanction", input);
}

export async function getNotifications(limit: number = 25) {
  return request<NotificationItem[]>(`/notifications?limit=${limit}`);
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

export async function getEquipmentAssets(params?: {
  hospital_id?: string;
  availability_status?: string;
}) {
  const query = new URLSearchParams();
  if (params?.hospital_id) query.append("hospital_id", params.hospital_id);
  if (params?.availability_status)
    query.append("availability_status", params.availability_status);
  const qStr = query.toString() ? `?${query.toString()}` : "";
  return request<
    Array<{
      asset_id: string;
      hospital_id: string;
      equipment_type: string;
      name: string;
      serial_number?: string;
      condition_status: string;
      availability_status: string;
      shareable: boolean;
      hourly_rate?: number;
      metadata?: Record<string, unknown>;
      created_at?: string;
      hospital_name?: string;
      mvp_hfr_id?: string;
    }>
  >(`/equipment/assets${qStr}`);
}

export async function getLoans(hospitalId?: string) {
  const qStr = hospitalId ? `?hospital_id=${encodeURIComponent(hospitalId)}` : "";
  return request<
    Array<{
      loan_id: string;
      reservation_id: string;
      asset_id: string;
      borrower_hospital_id: string;
      lender_hospital_id: string;
      loan_status: string;
      amount: number;
      duration_hours: number;
      notes?: Record<string, unknown>;
      created_at: string;
      updated_at: string;
      borrower_hospital_name?: string;
      lender_hospital_name?: string;
      asset_name?: string;
      equipment_type?: string;
    }>
  >(`/loans${qStr}`);
}

export async function searchInventory(query?: {
  equipmentType?: string | number;
  quantity?: number;
}) {
  const params = new URLSearchParams();
  if (query?.equipmentType)
    params.append("equipment_type", String(query.equipmentType));
  if (query?.quantity) params.append("quantity", String(query.quantity));
  const qStr = params.toString() ? `?${params.toString()}` : "";
  return request<Array<Record<string, unknown>>>(`/inventory/search${qStr}`);
}

export type ChatResponse = {
  session_id?: string;
  reply?: string;
  response?: string;
  approval_required?: boolean;
  tx_hash?: string;
  loan_id?: number;
  payment_order?: RazorpayOrder;
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
