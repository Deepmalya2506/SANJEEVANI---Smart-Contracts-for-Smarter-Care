import { useState, useEffect, useCallback } from "react";
import {
  Building2,
  ShieldCheck,
  Package,
  MapPin,
  Compass,
  CreditCard,
  Check,
  Mail,
  RefreshCw,
  Zap,
  Activity,
  ArrowRight,
  Clock3,
  AlertCircle,
  Filter,
  Sparkles,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import {
  registerHospitalAdmin,
  registerEquipmentAsset,
  getNearbyHospitals,
  sanctionTransaction,
  getNotifications,
  verifyPayment,
  getHospitals,
  getEquipmentAssets,
  searchFacilities,
  NearbyHospitalItem,
  NotificationItem,
} from "@/lib/api";

type RazorpayCheckout = {
  open: () => void;
};

type RazorpayConstructor = new (options: {
  key: string;
  amount: number;
  currency: string;
  name: string;
  description: string;
  order_id: string;
  handler: (payment: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  }) => void;
  modal: { ondismiss: () => void };
}) => RazorpayCheckout;

declare global {
  interface Window {
    Razorpay?: RazorpayConstructor;
  }
}

let razorpayScriptPromise: Promise<void> | undefined;

function loadRazorpayCheckout() {
  if (typeof window === "undefined") return Promise.resolve();
  if (window.Razorpay) return Promise.resolve();
  if (!razorpayScriptPromise) {
    razorpayScriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve();
      script.onerror = () => reject(new Error("Razorpay Checkout could not load"));
      document.body.appendChild(script);
    });
  }
  return razorpayScriptPromise;
}

export function AdminWorkflowView() {
  const [activeTab, setActiveTab] = useState<"register" | "equipment" | "nearby" | "sanction" | "notifications">("register");

  // ABDM Registry facilities list loaded dynamically from Supabase
  const [abdmFacilities, setAbdmFacilities] = useState<
    Array<{ mvp_hfr_id: string; hospital_name: string; latitude: number; longitude: number; address?: string }>
  >([]);

  // State 1: Hospital Admin Registration
  const [adminName, setAdminName] = useState("Dr. Arindam Sen");
  const [adminEmail, setAdminEmail] = useState("admin@sanjeevani.health");
  const [hospitalName, setHospitalName] = useState("");
  const [hfrId, setHfrId] = useState("");
  const [adminLat, setAdminLat] = useState(11.6358);
  const [adminLon, setAdminLon] = useState(92.7121);
  const [registering, setRegistering] = useState(false);
  const [registeredOrg, setRegisteredOrg] = useState<{
    hospital_id: string;
    hospital_name: string;
    admin_name: string;
    admin_email: string;
    mvp_hfr_id: string;
  } | null>(() => {
    const saved = localStorage.getItem("sanjeevani_registered_org");
    return saved ? JSON.parse(saved) : null;
  });
  const [regSuccessMsg, setRegSuccessMsg] = useState("");

  // State 2: Equipment Registration
  const [eqType, setEqType] = useState("Oxygen concentrator");
  const [eqModel, setEqModel] = useState("Philips EverFlo 5L Concentrator");
  const [eqSerial, setEqSerial] = useState("SN-OX-9941");
  const [eqCondition, setEqCondition] = useState("OPERATIONAL");
  const [eqDailyRate, setEqDailyRate] = useState(1850);
  const [registeringEq, setRegisteringEq] = useState(false);
  const [registeredAssets, setRegisteredAssets] = useState<Array<Record<string, unknown>>>([]);
  const [eqSuccessMsg, setEqSuccessMsg] = useState("");

  // State 3: Nearby Hospitals Discovery (ABDM Geo-Search)
  const [searchLat, setSearchLat] = useState(11.6358);
  const [searchLon, setSearchLon] = useState(92.7121);
  const [radiusKm, setRadiusKm] = useState(100);
  const [filterEq, setFilterEq] = useState("");
  const [searchingNearby, setSearchingNearby] = useState(false);
  const [nearbyHospitals, setNearbyHospitals] = useState<NearbyHospitalItem[]>([]);

  // State 4: Sanction Transaction & Payment
  const [selectedHospitalForLoan, setSelectedHospitalForLoan] = useState<NearbyHospitalItem | null>(null);
  const [loanEqType, setLoanEqType] = useState("Oxygen concentrator");
  const [loanDays, setLoanDays] = useState(3);
  const [dailyRateInr, setDailyRateInr] = useState(1850);
  const [borrowerEmail, setBorrowerEmail] = useState("borrower-admin@sanjeevani.health");
  const [sanctioning, setSanctioning] = useState(false);
  const [sanctionStatus, setSanctionStatus] = useState("");
  const [paymentReceipt, setPaymentReceipt] = useState<{
    loan_id?: string;
    payment_id?: string;
    order_id?: string;
    amount?: number;
  } | null>(null);

  // Notifications
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loadingNotifs, setLoadingNotifs] = useState(false);

  // Load ABDM facilities, registered hospitals, and registered assets from Supabase on mount
  useEffect(() => {
    void (async () => {
      try {
        const [facilities, existingHosps, existingAssets] = await Promise.all([
          searchFacilities("", 50),
          getHospitals(),
          getEquipmentAssets(),
        ]);
        if (facilities.length > 0) {
          setAbdmFacilities(facilities);
          if (!hospitalName) {
            setHospitalName(facilities[0].hospital_name);
            setHfrId(facilities[0].mvp_hfr_id);
            setAdminLat(facilities[0].latitude);
            setAdminLon(facilities[0].longitude);
            setSearchLat(facilities[0].latitude);
            setSearchLon(facilities[0].longitude);
          }
        }
        if (existingHosps.length > 0 && !registeredOrg) {
          const firstHosp = existingHosps[0] as Record<string, unknown>;
          const autoOrg = {
            hospital_id: String(firstHosp.hospital_id ?? firstHosp.id),
            hospital_name: String(firstHosp.hospital_name ?? firstHosp.name),
            admin_name: "Network Admin",
            admin_email: "admin@sanjeevani.health",
            mvp_hfr_id: String(firstHosp.mvp_hfr_id ?? ""),
          };
          setRegisteredOrg(autoOrg);
          localStorage.setItem("sanjeevani_registered_org", JSON.stringify(autoOrg));
          if (firstHosp.location && typeof firstHosp.location === "object") {
            const loc = firstHosp.location as { lat?: number; lon?: number };
            if (loc.lat && loc.lon) {
              setSearchLat(loc.lat);
              setSearchLon(loc.lon);
              setAdminLat(loc.lat);
              setAdminLon(loc.lon);
            }
          }
        }
        if (existingAssets.length > 0) {
          setRegisteredAssets(existingAssets);
        }
      } catch (err) {
        console.warn("Error initializing ABDM & Supabase data:", err);
      }
    })();
  }, []);

  const fetchNotificationLedger = useCallback(async () => {
    setLoadingNotifs(true);
    try {
      const data = await getNotifications(20);
      setNotifications(data);
    } catch {
      // Graceful fallback
    } finally {
      setLoadingNotifs(false);
    }
  }, []);

  useEffect(() => {
    void fetchNotificationLedger();
    const timer = setInterval(() => void fetchNotificationLedger(), 8000);
    return () => clearInterval(timer);
  }, [fetchNotificationLedger]);

  // Handle ABDM Mock selection
  const handleAbdmSelect = (id: string) => {
    setHfrId(id);
    const found = abdmFacilities.find((h) => h.mvp_hfr_id === id);
    if (found) {
      setHospitalName(found.hospital_name);
      setAdminLat(found.latitude);
      setAdminLon(found.longitude);
      setSearchLat(found.latitude);
      setSearchLon(found.longitude);
    }
  };

  // 1. Submit Hospital Admin Registration
  const handleRegisterAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegistering(true);
    setRegSuccessMsg("");
    try {
      const res = await registerHospitalAdmin({
        admin_name: adminName,
        email: adminEmail,
        hospital_name: hospitalName,
        mvp_hfr_id: hfrId,
        latitude: adminLat,
        longitude: adminLon,
      });
      const orgData = {
        hospital_id: res.hospital_id,
        hospital_name: res.hospital_name,
        admin_name: res.admin_name,
        admin_email: res.admin_email,
        mvp_hfr_id: res.mvp_hfr_id,
      };
      setRegisteredOrg(orgData);
      localStorage.setItem("sanjeevani_registered_org", JSON.stringify(orgData));
      setBorrowerEmail(res.admin_email);
      setRegSuccessMsg(`Hospital "${res.hospital_name}" and Admin "${res.admin_name}" registered! Welcome email dispatched.`);
      void fetchNotificationLedger();
      setActiveTab("equipment");
    } catch (err) {
      setRegSuccessMsg(err instanceof Error ? err.message : "Failed to register hospital admin.");
    } finally {
      setRegistering(false);
    }
  };

  // 2. Submit Equipment Registration
  const handleRegisterEquipment = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegisteringEq(true);
    setEqSuccessMsg("");
    try {
      const res = await registerEquipmentAsset({
        hospital_id: registeredOrg?.hospital_id,
        equipment_type: eqType,
        name: eqModel,
        serial_number: eqSerial,
        condition_status: eqCondition,
        hourly_rate: Math.round(eqDailyRate / 24),
        shareable: true,
        metadata: {
          daily_rate_inr: eqDailyRate,
          registered_by: registeredOrg?.admin_name ?? "Admin",
        },
      });
      setRegisteredAssets((prev) => [res, ...prev]);
      setEqSuccessMsg(`Equipment "${eqModel}" added to equipment_assets! Confirmation email dispatched.`);
      void fetchNotificationLedger();
      setActiveTab("nearby");
    } catch (err) {
      setEqSuccessMsg(err instanceof Error ? err.message : "Failed to register equipment asset.");
    } finally {
      setRegisteringEq(false);
    }
  };

  // 3. Search Nearby Hospitals from ABDM Mock HFR
  const handleSearchNearby = async () => {
    setSearchingNearby(true);
    try {
      const results = await getNearbyHospitals({
        lat: searchLat,
        lon: searchLon,
        radiusKm,
        equipmentType: filterEq || undefined,
      });
      setNearbyHospitals(results);
    } catch {
      // Fallback
    } finally {
      setSearchingNearby(false);
    }
  };

  // Run initial search
  useEffect(() => {
    void handleSearchNearby();
  }, [searchLat, searchLon, radiusKm, filterEq]);

  // 4. Sanction Transaction & Trigger Razorpay Test Payment
  const handleSanctionAndPay = async () => {
    if (!registeredOrg?.hospital_id) {
      setSanctionStatus("Please register or select an active borrowing hospital organization first.");
      return;
    }
    if (!selectedHospitalForLoan) {
      setSanctionStatus("Please select a nearby lender hospital from ABDM discovery first.");
      return;
    }
    const lenderHid = selectedHospitalForLoan.hospital_id || selectedHospitalForLoan.mvp_hfr_id;
    if (
      !lenderHid ||
      lenderHid === registeredOrg.hospital_id ||
      (selectedHospitalForLoan.mvp_hfr_id && selectedHospitalForLoan.mvp_hfr_id === registeredOrg.mvp_hfr_id)
    ) {
      setSanctionStatus("Please select a different ABDM hospital as lender. A hospital cannot sanction an inter-hospital loan to itself.");
      return;
    }
    setSanctioning(true);
    setSanctionStatus("Sanctioning loan and locking equipment asset in Supabase...");
    const totalRupees = dailyRateInr * loanDays;

    try {
      const sanctionRes = await sanctionTransaction({
        borrower_hospital_id: registeredOrg.hospital_id,
        lender_hospital_id: lenderHid,
        equipment_type: loanEqType,
        borrower_admin_email: borrowerEmail,
        duration_hours: loanDays * 24,
        amount_rupees: totalRupees,
        notes: {
          lender_hospital: selectedHospitalForLoan.hospital_name,
          borrower_hospital: registeredOrg.hospital_name,
          days: loanDays,
        },
      });

      setSanctionStatus("Transaction sanctioned! Notification email sent. Loading Razorpay checkout...");
      void fetchNotificationLedger();

      await loadRazorpayCheckout();
      if (!window.Razorpay) throw new Error("Razorpay Checkout library could not be loaded.");

      const order = sanctionRes.payment_order;
      const razorpay = new window.Razorpay({
        key: order.key_id,
        amount: order.amount_paise,
        currency: order.currency,
        name: "SANJEEVANI Care Network",
        description: `Sanctioned Loan: ${loanEqType} (${loanDays} days)`,
        order_id: order.order_id,
        modal: {
          ondismiss: () => setSanctionStatus("Payment flow paused. You can resume anytime."),
        },
        handler: (paymentResponse) => {
          void (async () => {
            try {
              setSanctionStatus("Verifying cryptographic signature on backend...");
              await verifyPayment(paymentResponse);
              setSanctionStatus("Payment confirmed! Asset marked ON_LOAN and dispatch clearance granted.");
              setPaymentReceipt({
                loan_id: sanctionRes.loan_id,
                payment_id: paymentResponse.razorpay_payment_id,
                order_id: paymentResponse.razorpay_order_id,
                amount: totalRupees,
              });
              void fetchNotificationLedger();
            } catch (err) {
              setSanctionStatus(err instanceof Error ? err.message : "Payment verification failed.");
            }
          })();
        },
      });

      razorpay.open();
    } catch (err) {
      setSanctionStatus(err instanceof Error ? err.message : "Sanction failed.");
    } finally {
      setSanctioning(false);
    }
  };

  return (
    <div className="workspace">
      {/* Header */}
      <div className="section-header">
        <div>
          <span className="eyebrow">SMART PROTOCOL / ABDM & SUPABASE WORKFLOW</span>
          <h1>Admin Portal & Care Network Workflow</h1>
          <p>
            Complete end-to-end lifecycle: Register hospital admin &amp; equipment assets in Supabase, discover
            verified ABDM care centers by GPS, sanction equipment transactions with exact Razorpay paise checkout,
            and monitor transactional email notifications.
          </p>
        </div>
        <div className="header-status">
          <span className="live-dot" /> Live Ledger Connected{" "}
          <span className="header-divider" /> <Clock3 size={14} /> {notifications.length} Emails Sent
        </div>
      </div>

      {/* Stepper Navigation */}
      <nav className="workflow-nav" aria-label="Workflow Navigation">
        <button
          type="button"
          className={`workflow-step-btn ${activeTab === "register" ? "active" : registeredOrg ? "completed" : ""}`}
          onClick={() => setActiveTab("register")}
        >
          <span className="workflow-step-num">1</span>
          <span>Admin &amp; Hospital Signup</span>
          {registeredOrg && <Check size={14} />}
        </button>

        <button
          type="button"
          className={`workflow-step-btn ${activeTab === "equipment" ? "active" : registeredAssets.length > 0 ? "completed" : ""}`}
          onClick={() => setActiveTab("equipment")}
        >
          <span className="workflow-step-num">2</span>
          <span>Register Equipment</span>
          {registeredAssets.length > 0 && <Check size={14} />}
        </button>

        <button
          type="button"
          className={`workflow-step-btn ${activeTab === "nearby" ? "active" : nearbyHospitals.length > 0 ? "completed" : ""}`}
          onClick={() => setActiveTab("nearby")}
        >
          <span className="workflow-step-num">3</span>
          <span>Nearby Hospitals (ABDM)</span>
        </button>

        <button
          type="button"
          className={`workflow-step-btn ${activeTab === "sanction" ? "active" : paymentReceipt ? "completed" : ""}`}
          onClick={() => setActiveTab("sanction")}
        >
          <span className="workflow-step-num">4</span>
          <span>Sanction &amp; Razorpay Pay</span>
          {paymentReceipt && <Check size={14} />}
        </button>

        <button
          type="button"
          className={`workflow-step-btn ${activeTab === "notifications" ? "active" : ""}`}
          onClick={() => setActiveTab("notifications")}
        >
          <span className="workflow-step-num">5</span>
          <span>Email &amp; Notification Ledger</span>
          <span className="status-badge" style={{ padding: "2px 6px", fontSize: 10 }}>{notifications.length}</span>
        </button>
      </nav>

      {/* STEP 1: Hospital Admin Registration */}
      {activeTab === "register" && (
        <div className="workflow-grid">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">STEP 01 / ONBOARDING</span>
                <h2>Register Hospital Administrator</h2>
              </div>
              <span className="round-icon">
                <Building2 size={16} />
              </span>
            </div>

            {regSuccessMsg && (
              <div className="success-note page-enter" style={{ marginBottom: 16 }}>
                <Check size={14} /> {regSuccessMsg}
              </div>
            )}

            <form onSubmit={handleRegisterAdmin}>
              <label className="field-label" htmlFor="admin-name">Administrator Full Name</label>
              <div className="input-wrap">
                <input
                  id="admin-name"
                  value={adminName}
                  onChange={(e) => setAdminName(e.target.value)}
                  placeholder="e.g. Dr. Arindam Sen"
                  required
                />
              </div>

              <label className="field-label" htmlFor="admin-email">Administrator Official Email (Receives Welcome Mail)</label>
              <div className="input-wrap">
                <Mail size={15} />
                <input
                  id="admin-email"
                  type="email"
                  value={adminEmail}
                  onChange={(e) => setAdminEmail(e.target.value)}
                  placeholder="admin@mch-kolkata.org"
                  required
                />
              </div>

              <label className="field-label" htmlFor="abdm-preset">Verified ABDM Directory Match (from public.abdm_mock_hfr)</label>
              <div className="select-wrap">
                <ShieldCheck size={15} />
                <select
                  id="abdm-preset"
                  value={hfrId}
                  onChange={(e) => handleAbdmSelect(e.target.value)}
                >
                  {abdmFacilities.map((opt) => (
                    <option key={opt.mvp_hfr_id} value={opt.mvp_hfr_id}>
                      {opt.mvp_hfr_id} — {opt.hospital_name}
                    </option>
                  ))}
                  {abdmFacilities.length === 0 && (
                    <option value="">Loading facilities from Supabase...</option>
                  )}
                </select>
              </div>

              <label className="field-label" htmlFor="hosp-name">Hospital / Facility Legal Name</label>
              <div className="input-wrap">
                <input
                  id="hosp-name"
                  value={hospitalName}
                  onChange={(e) => setHospitalName(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <label className="field-label" htmlFor="admin-lat">Latitude</label>
                  <div className="input-wrap">
                    <input
                      id="admin-lat"
                      type="number"
                      step="any"
                      value={adminLat}
                      onChange={(e) => setAdminLat(parseFloat(e.target.value))}
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="field-label" htmlFor="admin-lon">Longitude</label>
                  <div className="input-wrap">
                    <input
                      id="admin-lon"
                      type="number"
                      step="any"
                      value={adminLon}
                      onChange={(e) => setAdminLon(parseFloat(e.target.value))}
                      required
                    />
                  </div>
                </div>
              </div>

              <button
                type="submit"
                className="primary-button full"
                style={{ marginTop: 24 }}
                disabled={registering}
              >
                {registering ? (
                  <>
                    <Activity size={16} className="animate-spin" /> Registering in Supabase...
                  </>
                ) : (
                  <>
                    <Building2 size={16} /> Register Admin &amp; Hospital Organization
                  </>
                )}
              </button>
            </form>
          </section>

          {/* Org Profile Summary */}
          <section className="panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">VERIFIED IDENTITY</span>
                <h2>Active Organization State</h2>
              </div>
              <span className="abdm-badge">
                <ShieldCheck size={11} /> ABDM HFR
              </span>
            </div>

            {registeredOrg ? (
              <div style={{ display: "grid", gap: 14 }}>
                <div className="status-card">
                  <div className="status-icon">
                    <Building2 size={20} />
                  </div>
                  <div>
                    <strong>{registeredOrg.hospital_name}</strong>
                    <span>HFR ID: {registeredOrg.mvp_hfr_id}</span>
                  </div>
                </div>
                <p style={{ fontSize: 13, color: "hsl(var(--muted-foreground))" }}>
                  <strong>Admin:</strong> {registeredOrg.admin_name} ({registeredOrg.admin_email})
                </p>
                <p style={{ fontSize: 13, color: "hsl(var(--muted-foreground))" }}>
                  <strong>Supabase UUID:</strong> <code style={{ fontSize: 11 }}>{registeredOrg.hospital_id}</code>
                </p>
                <div className="success-note">
                  <Check size={14} /> Organization verified. You can now register equipments into public.equipment_assets.
                </div>
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setActiveTab("equipment")}
                >
                  Proceed to Equipment Registration <ArrowRight size={14} />
                </button>
              </div>
            ) : (
              <div className="empty-state">
                <Building2 size={32} />
                <h3>No Organization Registered Yet</h3>
                <p>Fill out the registration form to create the hospital identity in Supabase PostgreSQL.</p>
              </div>
            )}
          </section>
        </div>
      )}

      {/* STEP 2: Equipment Registration */}
      {activeTab === "equipment" && (
        <div className="workflow-grid">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">STEP 02 / ASSET INTAKE</span>
                <h2>Register Equipment in equipment_assets</h2>
              </div>
              <span className="round-icon">
                <Package size={16} />
              </span>
            </div>

            {eqSuccessMsg && (
              <div className="success-note page-enter" style={{ marginBottom: 16 }}>
                <Check size={14} /> {eqSuccessMsg}
              </div>
            )}

            <form onSubmit={handleRegisterEquipment}>
              <label className="field-label" htmlFor="eq-hosp">Owning Hospital</label>
              <div className="input-wrap">
                <input
                  id="eq-hosp"
                  value={registeredOrg?.hospital_name ?? "Medical College Hospital Kolkata"}
                  disabled
                />
              </div>

              <label className="field-label" htmlFor="eq-type">Equipment Category</label>
              <div className="select-wrap">
                <Package size={15} />
                <select
                  id="eq-type"
                  value={eqType}
                  onChange={(e) => setEqType(e.target.value)}
                >
                  <option>Oxygen concentrator</option>
                  <option>Portable ventilator</option>
                  <option>Patient monitor</option>
                  <option>Infusion pump</option>
                  <option>ICU Bed</option>
                  <option>Defibrillator</option>
                </select>
              </div>

              <label className="field-label" htmlFor="eq-model">Equipment Model &amp; Make</label>
              <div className="input-wrap">
                <input
                  id="eq-model"
                  value={eqModel}
                  onChange={(e) => setEqModel(e.target.value)}
                  placeholder="e.g. Philips EverFlo 5L Concentrator"
                  required
                />
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <label className="field-label" htmlFor="eq-serial">Serial Number</label>
                  <div className="input-wrap">
                    <input
                      id="eq-serial"
                      value={eqSerial}
                      onChange={(e) => setEqSerial(e.target.value)}
                      placeholder="SN-OX-9941"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="field-label" htmlFor="eq-condition">Condition Status</label>
                  <div className="select-wrap">
                    <select
                      id="eq-condition"
                      value={eqCondition}
                      onChange={(e) => setEqCondition(e.target.value)}
                    >
                      <option value="OPERATIONAL">OPERATIONAL</option>
                      <option value="EXCELLENT">EXCELLENT</option>
                      <option value="GOOD">GOOD</option>
                    </select>
                  </div>
                </div>
              </div>

              <label className="field-label" htmlFor="eq-rate">Daily Lending Rate (₹ INR)</label>
              <div className="input-wrap">
                <input
                  id="eq-rate"
                  type="number"
                  value={eqDailyRate}
                  onChange={(e) => setEqDailyRate(parseFloat(e.target.value))}
                  min={100}
                  step={50}
                  required
                />
              </div>

              <button
                type="submit"
                className="primary-button full"
                style={{ marginTop: 24 }}
                disabled={registeringEq}
              >
                {registeringEq ? (
                  <>
                    <Activity size={16} className="animate-spin" /> Adding to equipment_assets...
                  </>
                ) : (
                  <>
                    <Package size={16} /> Register Equipment into Care Network
                  </>
                )}
              </button>
            </form>
          </section>

          {/* Registered Assets Preview */}
          <section className="panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">NETWORK INVENTORY</span>
                <h2>Registered Assets ({registeredAssets.length})</h2>
              </div>
              <span className="status-badge">
                <Check size={12} /> AVAILABLE
              </span>
            </div>

            {registeredAssets.length > 0 ? (
              <div style={{ display: "grid", gap: 12 }}>
                {registeredAssets.map((asset, idx) => (
                  <div key={idx} className="nearby-card">
                    <div className="nearby-header">
                      <div>
                        <strong style={{ fontSize: 15 }}>{String(asset.name ?? eqModel)}</strong>
                        <div style={{ fontSize: 12, color: "hsl(var(--muted-foreground))" }}>
                          {String(asset.equipment_type ?? eqType)} · SN: {String(asset.serial_number ?? eqSerial)}
                        </div>
                      </div>
                      <span className="abdm-badge">
                        <Check size={10} /> AVAILABLE
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
                      <span style={{ fontSize: 13, fontWeight: 700 }}>₹{eqDailyRate} / day</span>
                      <span style={{ fontSize: 11, color: "hsl(var(--muted-foreground))" }}>
                        Asset ID: {String(asset.asset_id ?? "").slice(0, 8)}...
                      </span>
                    </div>
                  </div>
                ))}
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setActiveTab("nearby")}
                >
                  Explore Nearby Hospitals <ArrowRight size={14} />
                </button>
              </div>
            ) : (
              <div className="empty-state">
                <Package size={32} />
                <h3>No Equipment Registered Yet</h3>
                <p>Submit the form to add equipment to public.equipment_assets and trigger the confirmation email.</p>
              </div>
            )}
          </section>
        </div>
      )}

      {/* STEP 3: Nearby Hospitals Discovery (ABDM Mock HFR) */}
      {activeTab === "nearby" && (
        <div>
          <section className="panel" style={{ marginBottom: 20 }}>
            <div className="panel-heading">
              <div>
                <span className="eyebrow">STEP 03 / ABDM MOCK GEO-SEARCH</span>
                <h2>Discover Nearby Hospitals from public.abdm_mock_hfr</h2>
              </div>
              <button
                type="button"
                className="secondary-button"
                onClick={() => void handleSearchNearby()}
                disabled={searchingNearby}
              >
                <RefreshCw size={14} className={searchingNearby ? "animate-spin" : ""} /> Refresh
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 14 }}>
              <div>
                <label className="field-label" htmlFor="search-lat">Latitude</label>
                <div className="input-wrap">
                  <MapPin size={15} />
                  <input
                    id="search-lat"
                    type="number"
                    step="any"
                    value={searchLat}
                    onChange={(e) => setSearchLat(parseFloat(e.target.value))}
                  />
                </div>
              </div>

              <div>
                <label className="field-label" htmlFor="search-lon">Longitude</label>
                <div className="input-wrap">
                  <Compass size={15} />
                  <input
                    id="search-lon"
                    type="number"
                    step="any"
                    value={searchLon}
                    onChange={(e) => setSearchLon(parseFloat(e.target.value))}
                  />
                </div>
              </div>

              <div>
                <label className="field-label" htmlFor="search-radius">Radius (km)</label>
                <div className="select-wrap">
                  <select
                    id="search-radius"
                    value={radiusKm}
                    onChange={(e) => setRadiusKm(parseInt(e.target.value, 10))}
                  >
                    <option value={10}>10 km</option>
                    <option value={25}>25 km</option>
                    <option value={50}>50 km</option>
                    <option value={100}>100 km</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="field-label" htmlFor="filter-eq">Equipment Filter</label>
                <div className="select-wrap">
                  <Filter size={15} />
                  <select
                    id="filter-eq"
                    value={filterEq}
                    onChange={(e) => setFilterEq(e.target.value)}
                  >
                    <option value="">All Equipments</option>
                    <option value="Oxygen concentrator">Oxygen concentrator</option>
                    <option value="Portable ventilator">Portable ventilator</option>
                    <option value="Patient monitor">Patient monitor</option>
                    <option value="Infusion pump">Infusion pump</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Quick Location Presets */}
            <div style={{ display: "flex", gap: 8, marginTop: 16, flexWrap: "wrap" }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: "hsl(var(--muted-foreground))", alignSelf: "center" }}>
                ABDM PRESETS:
              </span>
              {abdmFacilities.slice(0, 4).map((opt) => (
                <button
                  type="button"
                  key={opt.mvp_hfr_id}
                  className="outline-button"
                  style={{ fontSize: 11, padding: "4px 10px" }}
                  onClick={() => {
                    setSearchLat(opt.latitude);
                    setSearchLon(opt.longitude);
                  }}
                >
                  {opt.hospital_name.split(" ")[0]} ({opt.latitude.toFixed(2)}, {opt.longitude.toFixed(2)})
                </button>
              ))}
            </div>
          </section>

          {/* Results Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
            {nearbyHospitals.map((hosp) => (
              <div key={hosp.mvp_hfr_id} className="nearby-card">
                <div className="nearby-header">
                  <div>
                    <strong style={{ fontSize: 16 }}>{hosp.hospital_name}</strong>
                    <div style={{ fontSize: 12, color: "hsl(var(--muted-foreground))" }}>
                      HFR: {hosp.mvp_hfr_id}
                    </div>
                  </div>
                  <span className="nearby-distance">
                    <MapPin size={11} /> {hosp.distance_km.toFixed(1)} km
                  </span>
                </div>

                <p style={{ fontSize: 12, color: "hsl(var(--muted-foreground))", marginBottom: 12 }}>
                  {hosp.address || "Kolkata Care Network Corridor"}
                </p>

                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderTop: "1px solid hsl(var(--border) / 0.5)", paddingTop: 12 }}>
                  <span className="abdm-badge">
                    <ShieldCheck size={11} /> ABDM VERIFIED
                  </span>
                  {registeredOrg?.hospital_id && hosp.hospital_id === registeredOrg.hospital_id ? (
                    <span style={{ fontSize: 11, color: "hsl(var(--muted-foreground))", fontWeight: 600 }}>
                      Current Organization
                    </span>
                  ) : (
                    <button
                      type="button"
                      className="primary-button"
                      style={{ fontSize: 12, padding: "6px 14px" }}
                      onClick={() => {
                        setSelectedHospitalForLoan(hosp);
                        setActiveTab("sanction");
                      }}
                    >
                      Sanction Equipment Loan <ArrowRight size={13} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* STEP 4: Sanction Transaction & Razorpay Payment */}
      {activeTab === "sanction" && (
        <div className="workflow-grid">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">STEP 04 / SANCTION &amp; CHECKOUT</span>
                <h2>Sanction Equipment Transaction</h2>
              </div>
              <span className="round-icon">
                <CreditCard size={16} />
              </span>
            </div>

            {sanctionStatus && (
              <div className="toast-note page-enter" style={{ marginBottom: 16 }}>
                <Activity size={14} /> {sanctionStatus}
              </div>
            )}

            <div style={{ display: "grid", gap: 16 }}>
              <div>
                <label className="field-label" htmlFor="lender-hosp">Lender Hospital (from ABDM Registry)</label>
                <div className="input-wrap">
                  <input
                    id="lender-hosp"
                    value={selectedHospitalForLoan?.hospital_name ?? "Select lender in Step 3"}
                    disabled
                  />
                </div>
              </div>

              <div>
                <label className="field-label" htmlFor="borrower-hosp">Borrowing Hospital (Registered in Supabase)</label>
                <div className="input-wrap">
                  <input
                    id="borrower-hosp"
                    value={registeredOrg?.hospital_name ?? "Register in Step 1"}
                    disabled
                  />
                </div>
              </div>

              <div>
                <label className="field-label" htmlFor="borrower-email">Notification Recipient Email</label>
                <div className="input-wrap">
                  <Mail size={15} />
                  <input
                    id="borrower-email"
                    type="email"
                    value={borrowerEmail}
                    onChange={(e) => setBorrowerEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <div>
                  <label className="field-label" htmlFor="loan-eq">Equipment Type</label>
                  <div className="select-wrap">
                    <select
                      id="loan-eq"
                      value={loanEqType}
                      onChange={(e) => setLoanEqType(e.target.value)}
                    >
                      <option>Oxygen concentrator</option>
                      <option>Portable ventilator</option>
                      <option>Patient monitor</option>
                      <option>Infusion pump</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="field-label" htmlFor="loan-days">Duration (Days)</label>
                  <div className="input-wrap">
                    <input
                      id="loan-days"
                      type="number"
                      min={1}
                      max={30}
                      value={loanDays}
                      onChange={(e) => setLoanDays(parseInt(e.target.value, 10) || 1)}
                    />
                  </div>
                </div>
              </div>

              <div className="status-card" style={{ marginTop: 8 }}>
                <div className="status-icon">
                  <Zap size={20} />
                </div>
                <div>
                  <strong>Total Transaction Value: ₹{(dailyRateInr * loanDays).toLocaleString()}</strong>
                  <span>Razorpay Conversion: {(dailyRateInr * loanDays * 100).toLocaleString()} Paise (Exact 100x INR conversion)</span>
                </div>
              </div>

              <button
                type="button"
                className="primary-button full"
                onClick={() => void handleSanctionAndPay()}
                disabled={sanctioning}
              >
                {sanctioning ? (
                  <>
                    <Activity size={16} className="animate-spin" /> Sanctioning &amp; Opening Razorpay...
                  </>
                ) : (
                  <>
                    <CreditCard size={16} /> Sanction Transaction &amp; Pay ₹{(dailyRateInr * loanDays).toLocaleString()}
                  </>
                )}
              </button>
            </div>
          </section>

          {/* Payment Receipt / Verification Status */}
          <section className="panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">PAYMENT AUDIT</span>
                <h2>Transaction Receipt</h2>
              </div>
              {paymentReceipt ? (
                <span className="status-badge" style={{ background: "hsl(152 69% 45% / 0.15)", color: "hsl(152 69% 45%)" }}>
                  <Check size={12} /> PAID
                </span>
              ) : (
                <span className="status-badge">
                  <Clock3 size={12} /> PENDING
                </span>
              )}
            </div>

            {paymentReceipt ? (
              <div style={{ display: "grid", gap: 14 }}>
                <div className="status-card">
                  <div className="status-icon" style={{ background: "hsl(152 69% 45% / 0.15)", color: "hsl(152 69% 45%)" }}>
                    <ShieldCheck size={20} />
                  </div>
                  <div>
                    <strong>Payment Confirmed &amp; Asset Dispatched!</strong>
                    <span>Loan ID: {paymentReceipt.loan_id}</span>
                  </div>
                </div>

                <div style={{ fontSize: 13, display: "grid", gap: 6, color: "hsl(var(--muted-foreground))" }}>
                  <div><strong>Razorpay Payment ID:</strong> <code>{paymentReceipt.payment_id}</code></div>
                  <div><strong>Razorpay Order ID:</strong> <code>{paymentReceipt.order_id}</code></div>
                  <div><strong>Amount Settled:</strong> ₹{paymentReceipt.amount?.toLocaleString()}</div>
                  <div><strong>Asset State:</strong> ON_LOAN (Reserved in Supabase)</div>
                </div>

                <div className="success-note">
                  <Check size={14} /> Transactional payment receipt email dispatched to {borrowerEmail}.
                </div>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setActiveTab("notifications")}
                >
                  View Notification Ledger <ArrowRight size={14} />
                </button>
              </div>
            ) : (
              <div className="empty-state">
                <CreditCard size={32} />
                <h3>No Active Transaction Sanctioned</h3>
                <p>Click "Sanction Transaction" to lock the equipment asset and launch the Razorpay test payment modal.</p>
              </div>
            )}
          </section>
        </div>
      )}

      {/* STEP 5: Real-Time Email Notification Ledger */}
      {activeTab === "notifications" && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">AUDIT LEDGER / SMTP &amp; SUPABASE</span>
              <h2>Transactional Email Notification Ledger</h2>
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={() => void fetchNotificationLedger()}
              disabled={loadingNotifs}
            >
              <RefreshCw size={14} className={loadingNotifs ? "animate-spin" : ""} /> Refresh Ledger
            </button>
          </div>

          <p style={{ fontSize: 13, color: "hsl(var(--muted-foreground))", marginBottom: 16 }}>
            Every critical lifecycle milestone triggers a transactional email notification recorded into{" "}
            <code>public.notifications</code> in Supabase.
          </p>

          {notifications.length > 0 ? (
            <div className="notifications-table-wrap">
              <table className="notifications-table">
                <thead>
                  <tr>
                    <th>Event Type</th>
                    <th>Recipient</th>
                    <th>Subject</th>
                    <th>Status</th>
                    <th>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {notifications.map((notif) => (
                    <tr key={notif.notification_id}>
                      <td>
                        <span className={`event-tag ${notif.event_type}`}>
                          {notif.event_type}
                        </span>
                      </td>
                      <td style={{ fontFamily: "var(--app-font-mono)", fontSize: 11 }}>
                        {notif.recipient_email || "hospital-admin@sanjeevani.health"}
                      </td>
                      <td>{notif.subject || `Notification ${notif.event_type}`}</td>
                      <td>
                        <span className="status-badge" style={{ fontSize: 10 }}>
                          <Check size={10} /> {notif.status}
                        </span>
                      </td>
                      <td style={{ color: "hsl(var(--muted-foreground))", fontSize: 11 }}>
                        {new Date(notif.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <Mail size={32} />
              <h3>No Notifications Logged Yet</h3>
              <p>Execute Step 1, 2, or 4 to trigger transactional notifications.</p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
