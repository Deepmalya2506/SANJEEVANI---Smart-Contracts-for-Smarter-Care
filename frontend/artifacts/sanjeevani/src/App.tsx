import { type ReactNode, useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Bot,
  Boxes,
  Check,
  ChevronDown,
  Clock3,
  Command,
  Filter,
  HeartPulse,
  Hospital,
  Leaf,
  MapPin,
  Menu,
  MessageCircle,
  Moon,
  Package,
  Radio,
  Search,
  Send,
  ShieldCheck,
  ShoppingBag,
  Sun,
  Truck,
  X,
  Zap,
} from "lucide-react";
import {
  Link,
  Route,
  Switch,
  useLocation,
  Router as WouterRouter,
} from "wouter";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ErrorBoundary } from "@/components/error-boundary";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import {
  createPaymentOrder,
  previewDispatch,
  searchInventory,
  sendChat,
  verifyPayment,
  getHospitals,
  getNearbyHospitals,
  getEquipmentAssets,
  getLoans,
  sanctionTransaction,
  getNotifications,
  type NearbyHospitalItem,
} from "@/lib/api";
import { AdminWorkflowView } from "./pages/admin-workflow";
import heroImage from "@assets/Untitled_design_(1)_1787314419698.png";
import assistantImage from "@assets/download_(55)_1787315213518.jpg";

const queryClient = new QueryClient();

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
  if (window.Razorpay) return Promise.resolve();
  if (!razorpayScriptPromise) {
    razorpayScriptPromise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve();
      script.onerror = () =>
        reject(new Error("Razorpay Checkout could not load"));
      document.body.appendChild(script);
    });
  }
  return razorpayScriptPromise;
}


function Brand({ dark = false }: { dark?: boolean }) {
  return (
    <span className={`brand ${dark ? "brand-dark" : ""}`}>
      <span className="brand-mark">
        <span />
      </span>
      <span>Sanjeevani</span>
    </span>
  );
}

function ThemeToggle({
  dark,
  onToggle,
}: {
  dark: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      className="icon-button"
      onClick={onToggle}
      aria-label="Toggle theme"
      data-testid="button-theme-toggle"
    >
      {dark ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  );
}

function TopNav({
  dark,
  onToggle,
  home = false,
}: {
  dark: boolean;
  onToggle: () => void;
  home?: boolean;
}) {
  const [location] = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const links = [
    { href: "/dashboard", label: "Control room", icon: Radio },
    { href: "/admin-workflow", label: "Admin & ABDM Network", icon: ShieldCheck },
    { href: "/marketplace", label: "Marketplace", icon: ShoppingBag },
    { href: "/analytics", label: "Analytics", icon: BarChart3 },
    { href: "/assistant", label: "MCP assistant", icon: Bot },
  ];
  return (
    <header className={`top-nav ${home ? "home-nav" : ""}`}>
      <Link href="/" className="nav-brand" data-testid="link-home">
        <Brand dark={home && !dark} />
      </Link>
      <nav className="nav-links desktop-only" aria-label="Main navigation">
        {links.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={location === href ? "active" : ""}
            data-testid={`link-${href.slice(1)}`}
          >
            <Icon size={14} />
            {label}
          </Link>
        ))}
      </nav>
      <div className="nav-actions">
        <span className="system-state desktop-only">
          <span className="live-dot" /> System live
        </span>
        <ThemeToggle dark={dark} onToggle={onToggle} />
        <button
          type="button"
          className="icon-button mobile-only"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Open navigation"
          data-testid="button-open-navigation"
        >
          <Menu size={18} />
        </button>
      </div>
      {mobileOpen && (
        <nav className="mobile-menu mobile-only">
          {links.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setMobileOpen(false)}
              className={location === href ? "active" : ""}
              data-testid={`mobile-link-${href.slice(1)}`}
            >
              <Icon size={15} /> {label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}

function FloatingAssistant() {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState<string[]>([]);
  const send = () => {
    if (!message.trim()) return;
    const text = message.trim();
    setSent((current) => [...current, text]);
    setMessage("");
    void sendChat(text);
  };
  return (
    <div className="assistant-float">
      {open && (
        <div className="float-chat page-enter">
          <div className="float-chat-head">
            <div>
              <span className="eyebrow">SANJEEVANI MCP</span>
              <strong>What do you need?</strong>
            </div>
            <button
              type="button"
              className="icon-button small"
              onClick={() => setOpen(false)}
              aria-label="Close assistant"
              data-testid="button-close-floating-assistant"
            >
              <X size={15} />
            </button>
          </div>
          <p className="float-muted">
            I can search nearby inventory, prepare a dispatch, or explain a live
            status.
          </p>
          <div className="suggestion-list">
            <Link
              href="/assistant"
              className="suggestion-chip"
              data-testid="link-open-full-assistant"
            >
              Find oxygen within 15 minutes <ArrowRight size={13} />
            </Link>
            <Link
              href="/assistant"
              className="suggestion-chip"
              data-testid="link-open-dispatch-assistant"
            >
              Prepare a dispatch request <ArrowRight size={13} />
            </Link>
          </div>
          {sent.map((text, i) => (
            <div className="float-sent" key={`${text}-${i}`}>
              {text}
            </div>
          ))}
          <div className="float-input">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              placeholder="Ask Sanjeevani"
              aria-label="Ask Sanjeevani"
              data-testid="input-floating-chat"
            />
            <button
              type="button"
              onClick={send}
              aria-label="Send message"
              data-testid="button-send-floating-chat"
            >
              <Send size={15} />
            </button>
          </div>
        </div>
      )}
      <button
        type="button"
        className={`assistant-orb ${open ? "selected" : ""}`}
        onClick={() => setOpen(!open)}
        aria-label="Open Sanjeevani assistant"
        data-testid="button-floating-assistant"
      >
        <span className="orb-core">
          <Bot size={19} />
        </span>
        <span className="orb-label">MCP</span>
      </button>
    </div>
  );
}

function CursorBloom() {
  const [point, setPoint] = useState({ x: -40, y: -40 });
  useEffect(() => {
    const move = (event: PointerEvent) =>
      setPoint({ x: event.clientX, y: event.clientY });
    window.addEventListener("pointermove", move, { passive: true });
    return () => window.removeEventListener("pointermove", move);
  }, []);
  return (
    <div
      className="cursor-bloom"
      aria-hidden="true"
      style={{ left: point.x, top: point.y }}
    >
      <i />
      <i />
      <i />
    </div>
  );
}

function Shell({
  children,
  dark,
  onToggle,
}: {
  children: ReactNode;
  dark: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="app-shell">
      <TopNav dark={dark} onToggle={onToggle} />
      <main className="page-enter">{children}</main>
      <FloatingAssistant />
    </div>
  );
}

function Home({ dark, onToggle }: { dark: boolean; onToggle: () => void }) {
  const [language, setLanguage] = useState(0);
  const [liveStats, setLiveStats] = useState({ hospitals: 4, equipments: 16, loans: 1 });
  const words = [
    "Sanjeevani",
    "संजीवनी",
    "সঞ্জীবনী",
    "సంజీవని",
    "சஞ்சீவனி",
    "ಜೀವನದಾಯಿ",
  ];
  useEffect(() => {
    const timer = window.setInterval(
      () => setLanguage((i) => (i + 1) % words.length),
      3200,
    );
    return () => window.clearInterval(timer);
  }, [words.length]);

  useEffect(() => {
    void (async () => {
      try {
        const [h, a, l] = await Promise.all([
          getHospitals(),
          getEquipmentAssets(),
          getLoans(),
        ]);
        setLiveStats({
          hospitals: h.length,
          equipments: a.length,
          loans: l.length,
        });
      } catch {
        // Keep live defaults
      }
    })();
  }, []);

  return (
    <div
      className="home-page"
      style={{ backgroundImage: `url("${heroImage}")` }}
    >
      <TopNav dark={dark} onToggle={onToggle} home />
      <div className="home-center">
        <span className="home-kicker soft-rise">
          EMERGENCY MEDICAL LOGISTICS · 24 / 7
        </span>
        <h1 className="home-title" data-testid="text-home-wordmark">
          <span key={words[language]} className="language-word">
            {words[language]}
          </span>
        </h1>
        <p className="home-subtitle soft-rise delay-1">
          The calm layer between a critical need
          <br className="desktop-only" /> and the care that can meet it.
        </p>
        <p className="home-copy soft-rise delay-2">
          Sanjeevani connects hospitals, lenders, and trusted routes
          <br className="desktop-only" /> so the right equipment arrives when
          minutes matter.
        </p>
        <Link
          href="/dashboard"
          className="home-cta soft-rise delay-3"
          data-testid="link-enter-control-room"
        >
          Enter the control room <ArrowRight size={16} />
        </Link>
      </div>
      <div className="home-bottom">
        <div>
          <span className="home-stat-value">04:12</span>
          <span className="home-stat-label">median response</span>
        </div>
        <div>
          <span className="home-stat-value">{liveStats.hospitals}</span>
          <span className="home-stat-label">verified hospitals</span>
        </div>
        <div>
          <span className="home-stat-value">{liveStats.equipments}</span>
          <span className="home-stat-label">tracked assets</span>
        </div>
      </div>
      <div className="home-footnote">
        <span>
          <Leaf size={13} /> Built for clear decisions under pressure.
        </span>
        <span className="desktop-only">© 2025 Sanjeevani Systems</span>
      </div>
    </div>
  );
}

function SectionHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="section-header">
      <div>
        <span className="eyebrow">{eyebrow}</span>
        <h1>{title}</h1>
        {description && <p>{description}</p>}
      </div>
      {action}
    </div>
  );
}

function Panel({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <section className={`panel ${className}`}>{children}</section>;
}

function Dashboard({
  dark,
  onToggle,
}: {
  dark: boolean;
  onToggle: () => void;
}) {
  const [equipmentType, setEquipmentType] = useState("Oxygen concentrator");
  const [hospitalsList, setHospitalsList] = useState<
    Array<{ hospital_id: string; hospital_name: string; mvp_hfr_id?: string; location?: { lat: number; lon: number } }>
  >([]);
  const [selectedHospitalId, setSelectedHospitalId] = useState("");
  const [nearbyLenders, setNearbyLenders] = useState<NearbyHospitalItem[]>([]);
  const [selectedLenderId, setSelectedLenderId] = useState("");
  const [requested, setRequested] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState("");
  const [recentLoans, setRecentLoans] = useState<Array<any>>([]);
  const [activeLoanId, setActiveLoanId] = useState("");

  const loadHospitalsAndLoans = async () => {
    try {
      const hList = (await getHospitals()) as Array<{
        hospital_id: string;
        hospital_name: string;
        mvp_hfr_id?: string;
        location?: { lat: number; lon: number };
      }>;
      setHospitalsList(hList);
      if (hList.length > 0 && !selectedHospitalId) {
        setSelectedHospitalId(hList[0].hospital_id);
      }
      const lList = await getLoans();
      setRecentLoans(lList);
    } catch (err) {
      console.warn("Failed to load hospitals from Supabase:", err);
    }
  };

  const loadNearby = async () => {
    try {
      const nearby = await getNearbyHospitals({
        lat: hospitalsList.find((h) => h.hospital_id === selectedHospitalId)?.location?.lat ?? 0,
        lon: hospitalsList.find((h) => h.hospital_id === selectedHospitalId)?.location?.lon ?? 0,
        radiusKm: 100,
        equipmentType,
      });
      // A hospital cannot lend equipment to itself
      const distinctLenders = nearby.filter((l) => l.hospital_id !== selectedHospitalId);
      setNearbyLenders(distinctLenders);
      if (distinctLenders.length > 0) {
        setSelectedLenderId(distinctLenders[0].hospital_id || distinctLenders[0].mvp_hfr_id);
      } else {
        setSelectedLenderId("");
      }
    } catch (err) {
      console.warn("Failed to load nearby lenders:", err);
    }
  };

  useEffect(() => {
    void loadHospitalsAndLoans();
  }, []);

  useEffect(() => {
    void loadNearby();
  }, [equipmentType, selectedHospitalId, hospitalsList]);

  const requestEquipment = async () => {
    if (!selectedHospitalId) {
      setPaymentStatus("Please select a receiving hospital.");
      return;
    }
    const resolvedLender = nearbyLenders.find(
      (l) => (l.hospital_id || l.mvp_hfr_id) === selectedLenderId,
    );
    if (!resolvedLender?.hospital_id) {
      setPaymentStatus("Please select an ABDM-registered lending hospital organization distinct from the receiving hospital.");
      return;
    }
    const lenderHospitalId = resolvedLender.hospital_id;
    if (lenderHospitalId === selectedHospitalId) {
      setPaymentStatus("Receiving and lending hospitals must be different organizations.");
      return;
    }

    const assets = await getEquipmentAssets({
      hospital_id: lenderHospitalId,
      availability_status: "AVAILABLE",
    });
    const selectedAsset = assets.find(
      (asset) => asset.equipment_type.toLowerCase() === equipmentType.toLowerCase(),
    );
    if (!selectedAsset?.hourly_rate) {
      setPaymentStatus("No priced Supabase equipment asset is available for this request.");
      return;
    }
    const durationHours = 24;
    const paymentAmountRupees = Number(selectedAsset.hourly_rate) * durationHours;

    setPaymentStatus("Sanctioning loan & locking asset on Supabase...");
    try {
      const sanctionRes = await sanctionTransaction({
        borrower_hospital_id: selectedHospitalId,
        lender_hospital_id: lenderHospitalId,
        equipment_type: equipmentType,
        amount_rupees: paymentAmountRupees,
        duration_hours: 24,
        notes: {
          channel: "control_room",
          lender_name: resolvedLender?.hospital_name,
        },
      });

      setActiveLoanId(sanctionRes.loan_id);
      const paymentOrder = sanctionRes.payment_order;

      await loadRazorpayCheckout();
      if (!window.Razorpay) throw new Error("Razorpay Checkout is unavailable");

      const razorpay = new window.Razorpay({
        key: paymentOrder.key_id,
        amount: paymentOrder.amount_paise,
        currency: paymentOrder.currency,
        name: "Sanjeevani Care Network",
        description: `${equipmentType} - Loan ${sanctionRes.loan_id.slice(0, 8)}`,
        order_id: paymentOrder.order_id,
        modal: {
          ondismiss: () =>
            setPaymentStatus("Payment checkout dismissed. Loan remains APPROVED."),
        },
        handler: (payment) => {
          void (async () => {
            try {
              setPaymentStatus(
                "Authorizing payment & cryptographic signature on Supabase...",
              );
              await verifyPayment(payment);
              setPaymentStatus(
                `Payment verified! Loan ${sanctionRes.loan_id.slice(0, 8)} active in Supabase.`,
              );
              setRequested(true);
              const updatedLoans = await getLoans();
              setRecentLoans(updatedLoans);
            } catch (error) {
              setPaymentStatus(
                error instanceof Error
                  ? error.message
                  : "Payment verification failed.",
              );
            }
          })();
        },
      });

      setPaymentStatus("Complete the Razorpay Test Mode checkout...");
      razorpay.open();
    } catch (error) {
      setPaymentStatus(
        error instanceof Error ? error.message : "Unable to sanction loan.",
      );
    }
  };

  const selectedHospitalName =
    hospitalsList.find((h) => h.hospital_id === selectedHospitalId)
      ?.hospital_name ?? "Receiving Hospital";

  const resolvedLender = nearbyLenders.find(
    (l) => (l.hospital_id || l.mvp_hfr_id) === selectedLenderId,
  );
  const activeLenderName = resolvedLender?.hospital_name ?? "Care Partner";
  const activeLenderEta = Math.max(8, Math.round((resolvedLender?.distance_km ?? 5) * 2.5));

  return (
    <Shell dark={dark} onToggle={onToggle}>
      <div className="workspace">
        <SectionHeader
          eyebrow="LIVE SUPABASE DISPATCH / CONTROL ROOM"
          title="Hospital network control room."
          description="Live verified medical resource coordination backed by PostgreSQL & ABDM Mock HFR."
          action={
            <div className="header-status">
              <span className="live-dot" /> Live Supabase Connected{" "}
              <span className="header-divider" /> <Clock3 size={14} /> Updated
              just now
            </div>
          }
        />
        <div className="dashboard-grid">
          <Panel className="request-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">01 / INTAKE</span>
                <h2>Request equipment</h2>
              </div>
              <span className="round-icon">
                <Package size={16} />
              </span>
            </div>
            <label className="field-label" htmlFor="hospital">
              Receiving hospital (Supabase Verified)
            </label>
            <div className="select-wrap">
              <Hospital size={15} />
              <select
                id="hospital"
                value={selectedHospitalId}
                onChange={(e) => setSelectedHospitalId(e.target.value)}
                data-testid="select-hospital"
              >
                {hospitalsList.map((h) => (
                  <option key={h.hospital_id} value={h.hospital_id}>
                    {h.hospital_name} ({h.mvp_hfr_id ?? "Verified"})
                  </option>
                ))}
                {hospitalsList.length === 0 && (
                  <option value="">Loading hospitals from Supabase...</option>
                )}
              </select>
              <ChevronDown size={14} />
            </div>
            <label className="field-label" htmlFor="equipment">
              Equipment needed
            </label>
            <div className="select-wrap">
              <HeartPulse size={15} />
              <select
                id="equipment"
                value={equipmentType}
                onChange={(e) => setEquipmentType(e.target.value)}
                data-testid="select-equipment"
              >
                <option>Oxygen concentrator</option>
                <option>Portable ventilator</option>
                <option>Patient monitor</option>
                <option>Infusion pump</option>
              </select>
              <ChevronDown size={14} />
            </div>
            <div className="mini-label-row">
              <span>NEARBY LENDERS (ABDM MOCK HFR)</span>
              <span>{nearbyLenders.length} available</span>
            </div>
            <div className="lender-list">
              {nearbyLenders.map((lender) => {
                const lenderKey = lender.hospital_id || lender.mvp_hfr_id;
                const isSelected = selectedLenderId === lenderKey;
                return (
                  <button
                    type="button"
                    key={lender.mvp_hfr_id}
                    className={`lender-row ${isSelected ? "selected" : ""}`}
                    onClick={() => setSelectedLenderId(lenderKey)}
                    data-testid={`button-lender-${lender.mvp_hfr_id}`}
                  >
                    <span className="lender-avatar">
                      {lender.hospital_name.slice(0, 2).toUpperCase()}
                    </span>
                    <span className="lender-main">
                      <strong>{lender.hospital_name}</strong>
                      <small>
                        {lender.mvp_hfr_id} · {lender.distance_km.toFixed(1)} km away
                      </small>
                    </span>
                    <span className="lender-eta">
                      <b>{Math.max(8, Math.round(lender.distance_km * 2.5))} min</b>
                      <small>ABDM Verified</small>
                    </span>
                  </button>
                );
              })}
              {nearbyLenders.length === 0 && (
                <div
                  style={{
                    padding: "1rem",
                    color: "var(--muted-text)",
                    textAlign: "center",
                    fontSize: "0.85rem",
                  }}
                >
                  Searching ABDM Mock HFR for nearby lenders...
                </div>
              )}
            </div>
            <button
              type="button"
              className="primary-button full"
              onClick={() => void requestEquipment()}
              data-testid="button-request-now"
            >
              {requested ? (
                <>
                  <Check size={16} /> Sanctioned & Authorized
                </>
              ) : (
                <>
                  <Zap size={16} /> Sanction Loan & Pay
                </>
              )}
            </button>
            {requested && (
              <div className="success-note page-enter">
                <Check size={14} /> Equipment loan locked for{" "}
                {selectedHospitalName}. Loan ID: {activeLoanId.slice(0, 8)}
              </div>
            )}
            {paymentStatus && !requested && (
              <div className="success-note page-enter">
                <Activity size={14} /> {paymentStatus}
              </div>
            )}

            {recentLoans.length > 0 && (
              <div
                style={{
                  marginTop: "1.25rem",
                  borderTop: "1px solid var(--panel-border)",
                  paddingTop: "0.75rem",
                }}
              >
                <div className="mini-label-row" style={{ marginBottom: "0.5rem" }}>
                  <span>RECENT SUPABASE LOANS</span>
                  <span>{recentLoans.length} total</span>
                </div>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "0.4rem",
                  }}
                >
                  {recentLoans.slice(0, 3).map((loan) => (
                    <div
                      key={loan.loan_id}
                      style={{
                        fontSize: "0.8rem",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        padding: "0.4rem 0.6rem",
                        background: "rgba(255,255,255,0.03)",
                        borderRadius: "6px",
                      }}
                    >
                      <div>
                        <strong>{loan.equipment_type || loan.asset_name || "Medical Asset"}</strong>
                        <span style={{ marginLeft: "0.5rem", opacity: 0.7 }}>
                          {loan.loan_status}
                        </span>
                      </div>
                      <span style={{ color: "#34d399", fontWeight: 600 }}>
                        ₹{Number(loan.amount).toLocaleString("en-IN")}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Panel>
          <Panel className="map-panel">
            <div className="map-topline">
              <div>
                <span className="eyebrow">02 / NETWORK VIEW</span>
                <h2>Live logistics map</h2>
              </div>
              <span className="map-legend">
                <span className="legend-dot violet" /> active route
              </span>
            </div>
            <div className="map-canvas">
              <div className="map-grid-lines" />
              <div className="map-label label-one">{selectedHospitalName.split(" ")[0].toUpperCase()}</div>
              <div className="map-label label-two">{activeLenderName.split(" ")[0].toUpperCase()}</div>
              <div className="map-label label-three">CENTRAL HUB</div>
              <svg
                viewBox="0 0 700 470"
                className="route-svg"
                aria-label="Stylized network map"
              >
                <path
                  d="M84 355 C190 320 208 155 340 202 S505 330 623 115"
                  className="map-route route-dash"
                />
                <path
                  d="M85 355 C190 320 208 155 340 202 S505 330 623 115"
                  className={`map-route ${requested ? "route-active" : ""}`}
                />
                <circle cx="84" cy="355" r="13" className="iso-ring" />
                <circle
                  cx="84"
                  cy="355"
                  r="5"
                  className="map-node hospital-node"
                />
                <circle
                  cx="340"
                  cy="202"
                  r="11"
                  className="iso-ring secondary-ring"
                />
                <circle cx="340" cy="202" r="5" className="map-node" />
                <circle cx="623" cy="115" r="5" className="map-node" />
                <circle
                  cx="510"
                  cy="336"
                  r="4"
                  className="map-node muted-node"
                />
              </svg>
              <div className="node-callout origin">
                <span className="pulse-dot" /> {selectedHospitalName} · receiving
              </div>
              <div className="node-callout lender">
                <span /> {activeLenderName} · {activeLenderEta} min
              </div>
              <div className="map-scale">
                <span>{activeLenderEta} min reach</span>
                <span>0</span>
                <span>{resolvedLender ? resolvedLender.distance_km.toFixed(1) : "2"} km</span>
              </div>
            </div>
            <div className="map-footer">
              <span>
                <MapPin size={14} /> {hospitalsList.length} verified network nodes in Supabase
              </span>
              <button
                type="button"
                className="text-button"
                onClick={() => setRequested(true)}
                data-testid="button-recenter-map"
              >
                Recenter <ArrowRight size={14} />
              </button>
            </div>
          </Panel>
          <Panel className="status-panel">
            <div className="panel-heading">
              <div>
                <span className="eyebrow">03 / LIVE STATUS</span>
                <h2>Request {requested ? "authorized" : "ready for dispatch"}</h2>
              </div>
              <span className="status-badge">
                <span /> {requested ? "AUTHORIZED" : "PREVIEW"}
              </span>
            </div>
            <div className="status-card">
              <div className="status-icon">
                <Truck size={20} />
              </div>
              <div>
                <strong>
                  {requested
                    ? `${equipmentType} Dispatched`
                    : `${equipmentType} Available`}
                </strong>
                <span>
                  {requested
                    ? `${activeLenderName} · Courier assigned`
                    : `${activeLenderName} · Ready for pickup`}
                </span>
              </div>
            </div>
            <div className="timeline">
              {[
                `Request submitted by ${selectedHospitalName}`,
                `${activeLenderName} accepted allocation`,
                `Courier en route to ${selectedHospitalName}`,
              ].map((item, i) => (
                <div
                  className={`timeline-item ${i < (requested ? 3 : 1) ? "done" : ""}`}
                  key={item}
                >
                  <span className="timeline-dot">
                    {i < (requested ? 3 : 1) && <Check size={10} />}
                  </span>
                  <div>
                    <strong>{item}</strong>
                    <small>
                      {i === 0
                        ? "System verified via Supabase"
                        : i === 1
                          ? `${activeLenderEta} min transit window`
                          : "Immediate care corridor priority"}
                    </small>
                  </div>
                </div>
              ))}
            </div>
            <div className="escrow">
              <div className="escrow-head">
                <span>
                  <ShieldCheck size={15} /> Escrow protected
                </span>
                <strong>Razorpay Test Mode</strong>
              </div>
              <code>Supabase smart-contract lock confirmed</code>
            </div>
            <button
              type="button"
              className="secondary-button full"
              onClick={() => setRequested(false)}
              data-testid="button-reset-dispatch"
            >
              Reset preview
            </button>
          </Panel>
        </div>
      </div>
    </Shell>
  );
}

function Marketplace({
  dark,
  onToggle,
}: {
  dark: boolean;
  onToggle: () => void;
}) {
  const [category, setCategory] = useState("All equipment");
  const [query, setQuery] = useState("");
  const [notice, setNotice] = useState("");
  const [assetsList, setAssetsList] = useState<Array<any>>([]);
  const [loading, setLoading] = useState(true);

  const fetchLiveAssets = async () => {
    setLoading(true);
    try {
      const data = await getEquipmentAssets();
      setAssetsList(data);
      setNotice(`Fetched ${data.length} live assets from Supabase.`);
    } catch (err) {
      console.warn("Failed to fetch equipment assets:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchLiveAssets();
  }, []);

  const filtered = useMemo(() => {
    return assetsList.filter((item) => {
      const catMatch =
        category === "All equipment" ||
        item.equipment_type?.toLowerCase().includes(category.toLowerCase());
      const textMatch =
        `${item.name ?? ""} ${item.hospital_name ?? ""} ${item.equipment_type ?? ""}`
          .toLowerCase()
          .includes(query.toLowerCase());
      return catMatch && textMatch;
    });
  }, [assetsList, category, query]);

  const syncInventory = async () => {
    await fetchLiveAssets();
  };

  return (
    <Shell dark={dark} onToggle={onToggle}>
      <div className="workspace">
        <SectionHeader
          eyebrow="LIVE SUPABASE ASSET CATALOG"
          title="Marketplace"
          description="Browse live medical equipment assets registered in Supabase PostgreSQL across network hospitals."
          action={
            <button
              type="button"
              className="secondary-button"
              onClick={() => void syncInventory()}
              data-testid="button-sync-inventory"
            >
              <Activity size={15} /> Sync from Supabase
            </button>
          }
        />
        {notice && (
          <div className="toast-note page-enter">
            <Check size={14} /> {notice}
          </div>
        )}
        <div className="market-toolbar">
          <div className="search-box">
            <Search size={16} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search equipment or hospital name"
              aria-label="Search equipment or hospital name"
              data-testid="input-marketplace-search"
            />
          </div>
          <div className="filter-pills">
            {["All equipment", "Oxygen", "Ventilator", "Patient monitor"].map(
              (item) => (
                <button
                  type="button"
                  key={item}
                  onClick={() => setCategory(item)}
                  className={category === item ? "active" : ""}
                  data-testid={`button-filter-${item.toLowerCase().replaceAll(" ", "-")}`}
                >
                  <Filter size={13} /> {item}
                </button>
              ),
            )}
          </div>
          <span className="result-count">{filtered.length} live assets</span>
        </div>
        <div className="market-grid">
          {filtered.map((item) => (
            <article
              className="equipment-card soft-rise"
              key={item.asset_id}
              data-testid={`card-equipment-${item.asset_id}`}
            >
              <div
                className={`equipment-visual ${
                  item.equipment_type?.toLowerCase().includes("oxygen")
                    ? "violet"
                    : item.equipment_type?.toLowerCase().includes("ventilator")
                      ? "rose"
                      : "slate"
                }`}
              >
                <Package size={35} strokeWidth={1.2} />
                <span>{item.availability_status ?? "AVAILABLE"}</span>
              </div>
              <div className="equipment-body">
                <div className="card-kicker">
                  <span>{item.equipment_type}</span>
                  <span className="availability">
                    <span /> {item.condition_status ?? "GOOD"}
                  </span>
                </div>
                <h2>{item.name}</h2>
                <p>
                  {item.hospital_name ?? "Verified Facility"}{" "}
                  <span>·</span> {item.serial_number ?? item.mvp_hfr_id ?? "ABDM"}
                </p>
                <div className="card-footer">
                  <div>
                    <strong>
                      ₹
                      {item.hourly_rate
                        ? Number(item.hourly_rate).toLocaleString("en-IN")
                        : "—"}
                    </strong>
                    <small>/ hour</small>
                  </div>
                  <Link
                    href="/dashboard"
                    className="outline-button"
                    onClick={() =>
                      setNotice(`${item.name} pre-selected for dispatch.`)
                    }
                    data-testid={`link-request-${item.asset_id}`}
                  >
                    Sanction Loan <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
        {filtered.length === 0 && (
          <div className="empty-state">
            <Boxes size={24} />
            <h2>No matching equipment found in Supabase</h2>
            <p>
              {loading
                ? "Connecting to Supabase PostgreSQL..."
                : "Register equipment in the Admin & ABDM Network tab to populate this catalog."}
            </p>
            <button
              type="button"
              className="text-button"
              onClick={() => {
                setCategory("All equipment");
                setQuery("");
              }}
              data-testid="button-clear-filters"
            >
              Clear filters <X size={14} />
            </button>
          </div>
        )}
        <div className="market-trust">
          <ShieldCheck size={18} />
          <div>
            <strong>
              Every lender is verified before they enter the network.
            </strong>
            <span>
              Inventory timestamps, custody events, and settlement are recorded
              for each request.
            </span>
          </div>
          <Link
            href="/analytics"
            className="text-button"
            data-testid="link-marketplace-analytics"
          >
            View network performance <ArrowRight size={14} />
          </Link>
        </div>
      </div>
    </Shell>
  );
}

function MiniBarChart() {
  const bars = [42, 66, 52, 78, 58, 88, 70, 94, 75, 86, 64, 97];
  return (
    <div className="bar-chart">
      {bars.map((height, i) => (
        <div className="bar-column" key={i}>
          <span style={{ height: `${height}%` }} />
          <small>{i + 1}</small>
        </div>
      ))}
    </div>
  );
}

function Analytics({
  dark,
  onToggle,
}: {
  dark: boolean;
  onToggle: () => void;
}) {
  const [stats, setStats] = useState({
    hospitalsCount: 0,
    equipmentCount: 0,
    loansCount: 0,
    notificationsCount: 0,
  });
  const [hospitals, setHospitals] = useState<Array<{ id: string; name: string }>>([]);
  const [demandMix, setDemandMix] = useState<Array<[string, number, string]>>([
    ["Oxygen", 40, "violet"],
    ["Ventilation", 25, "rose"],
    ["Monitoring", 20, "slate"],
    ["Infusion", 15, "muted"],
  ]);

  useEffect(() => {
    void (async () => {
      try {
        const [h, a, l, n] = await Promise.all([
          getHospitals(),
          getEquipmentAssets(),
          getLoans(),
          getNotifications(100),
        ]);
        setStats({
          hospitalsCount: h.length,
          equipmentCount: a.length,
          loansCount: l.length,
          notificationsCount: n.length,
        });
        setHospitals(h.map((x) => ({ id: String(x.id ?? x.hospital_id), name: String(x.name ?? x.hospital_name) })));

        if (a.length > 0) {
          const oxyCount = a.filter((item) => item.equipment_type?.toLowerCase().includes("oxygen")).length;
          const ventCount = a.filter((item) => item.equipment_type?.toLowerCase().includes("ventilator")).length;
          const monCount = a.filter((item) => item.equipment_type?.toLowerCase().includes("monitor")).length;
          const pumpCount = a.filter((item) => item.equipment_type?.toLowerCase().includes("pump")).length;
          const total = a.length;
          setDemandMix([
            ["Oxygen", Math.round((oxyCount / total) * 100), "violet"],
            ["Ventilation", Math.round((ventCount / total) * 100), "rose"],
            ["Monitoring", Math.round((monCount / total) * 100), "slate"],
            ["Infusion", Math.round((pumpCount / total) * 100), "muted"],
          ]);
        }
      } catch (err) {
        console.warn("Analytics Supabase query failed:", err);
      }
    })();
  }, []);

  return (
    <Shell dark={dark} onToggle={onToggle}>
      <div className="workspace analytics-workspace">
        <SectionHeader
          eyebrow="SUPABASE POSTGRESQL / LIVE OBSERVATORY"
          title="Analytics console"
          description="Live metrics of health facilities, tracked equipment assets, and sanctioned loans in Supabase."
          action={
            <button
              type="button"
              className="secondary-button"
              onClick={() => window.print()}
              data-testid="button-export-analytics"
            >
              <ArrowRight size={14} /> Export report
            </button>
          }
        />
        <div className="console-bezel">
          <div className="console-top">
            <span>
              <span className="live-dot" /> LIVE SUPABASE CONNECTION
            </span>
            <span>
              DATA REFRESHED JUST NOW · <Command size={12} /> K
            </span>
          </div>
          <div className="console-screen">
            <div className="metric-strip">
              <div>
                <span>Sanctioned loans</span>
                <strong>{stats.loansCount}</strong>
                <small className="positive">Live in public.loans</small>
              </div>
              <div>
                <span>Tracked equipment</span>
                <strong>{stats.equipmentCount}</strong>
                <small className="positive">Registered in public.equipment_assets</small>
              </div>
              <div>
                <span>Verified facilities</span>
                <strong>{stats.hospitalsCount}</strong>
                <small>Active in public.hospitals</small>
              </div>
              <div>
                <span>Audit alerts</span>
                <strong>{stats.notificationsCount}</strong>
                <small>Logged in public.notifications</small>
              </div>
            </div>
            <div className="analytics-grid">
              <Panel className="chart-panel large-chart">
                <div className="chart-heading">
                  <div>
                    <span className="eyebrow">RESPONSE TIME</span>
                    <h2>Requests move faster</h2>
                  </div>
                  <span className="chart-period">
                    30 days <ChevronDown size={13} />
                  </span>
                </div>
                <MiniBarChart />
                <div className="chart-axis">
                  <span>01 MAY</span>
                  <span>15 MAY</span>
                  <span>30 MAY</span>
                </div>
              </Panel>
              <Panel className="chart-panel fulfilment">
                <span className="eyebrow">FULFILMENT RATE</span>
                <div className="donut-wrap">
                  <div className="donut">
                    <strong>
                      100<span>%</span>
                    </strong>
                  </div>
                  <div className="donut-copy">
                    <span>
                      <i className="dot violet" /> Delivered
                    </span>
                    <span>
                      <i className="dot rose" /> In transit
                    </span>
                    <span>
                      <i className="dot muted" /> Cancelled
                    </span>
                  </div>
                </div>
              </Panel>
              <Panel className="chart-panel demand">
                <div className="chart-heading">
                  <div>
                    <span className="eyebrow">DEMAND MIX</span>
                    <h2>What hospitals need</h2>
                  </div>
                </div>
                {demandMix.map(([name, value, tone]) => (
                  <div className="demand-row" key={name as string}>
                    <span>{name}</span>
                    <div>
                      <i
                        className={tone as string}
                        style={{ width: `${value}%` }}
                      />
                    </div>
                    <b>{value}%</b>
                  </div>
                ))}
              </Panel>
              <Panel className="chart-panel leaderboard">
                <span className="eyebrow">HOSPITAL LEADERBOARD</span>
                <h2>Verified Partner Hospitals</h2>
                {(hospitals.length > 0
                  ? hospitals.slice(0, 4)
                  : [
                      { id: "1", name: "Chakraborty Multi Speciality Hospital" },
                      { id: "2", name: "Inhs Dhanvantri" },
                      { id: "3", name: "Maricar Hospital" },
                    ]
                ).map((hosp, i) => (
                  <div className="leader-row" key={hosp.id}>
                    <b>0{i + 1}</b>
                    <span>{hosp.name}</span>
                    <strong>{["02:18", "03:04", "03:46", "04:12"][i] ?? "03:00"}</strong>
                  </div>
                ))}
              </Panel>
            </div>
          </div>
        </div>
      </div>
    </Shell>
  );
}

type ChatItem = { role: "assistant" | "user"; text: string; time: string };
function Assistant({
  dark,
  onToggle,
}: {
  dark: boolean;
  onToggle: () => void;
}) {
  const [, navigate] = useLocation();
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string>();
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  const [messages, setMessages] = useState<ChatItem[]>([
    {
      role: "assistant",
      text: "Good morning. I have a clear view of the Kolkata care network. What should we solve first?",
      time: "09:41",
    },
  ]);
  const startPayment = async (order: {
    order_id: string;
    amount_paise: number;
    currency: string;
    key_id: string;
  }) => {
    await loadRazorpayCheckout();
    if (!window.Razorpay) throw new Error("Razorpay Checkout is unavailable");
    const checkout = new window.Razorpay({
      key: order.key_id,
      amount: order.amount_paise,
      currency: order.currency,
      name: "Sanjeevani",
      description: "Approved medical equipment loan",
      order_id: order.order_id,
      modal: { ondismiss: () => setTyping(false) },
      handler: (payment) => {
        void (async () => {
          try {
            await verifyPayment(payment);
            setPaymentSuccess(true);
            sessionStorage.setItem(
              "sanjeevani-payment-success",
              JSON.stringify({
                paymentId: payment.razorpay_payment_id,
                orderId: payment.razorpay_order_id,
              }),
            );
            navigate("/payment-success");
            setMessages((current) => [
              ...current,
              {
                role: "assistant",
                text: "✅ Payment successful. Your equipment loan is confirmed and the dispatch can proceed.",
                time: "09:43",
              },
            ]);
          } catch (error) {
            setMessages((current) => [
              ...current,
              {
                role: "assistant",
                text:
                  error instanceof Error
                    ? error.message
                    : "Payment verification failed.",
                time: "09:43",
              },
            ]);
          }
        })();
      },
    });
    checkout.open();
  };
  const send = async (text = input) => {
    if (!text.trim() || typing) return;
    const query = text.trim();
    setMessages((current) => [
      ...current,
      { role: "user", text: query, time: "09:42" },
    ]);
    setInput("");
    setTyping(true);
    try {
      const response = await sendChat(query, undefined, sessionId);
      const reply =
        response.reply ?? response.response ?? "The request was received.";
      setMessages((current) => [
        ...current,
        { role: "assistant", text: reply, time: "09:42" },
      ]);
      if (response.approval_required && response.session_id) {
        setSessionId(response.session_id);
      } else if (sessionId) {
        setSessionId(undefined);
      }
      if (response.approval_required) {
        setMessages((current) => [
          ...current,
          {
            role: "assistant",
            text: "Reply “yes” to approve and continue, or “no” to cancel.",
            time: "09:42",
          },
        ]);
      }
      if (response.payment_order) {
        await startPayment(response.payment_order);
      }
    } catch {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text: "The service is temporarily unavailable. Please try again.",
          time: "09:42",
        },
      ]);
    } finally {
      setTyping(false);
    }
  };
  const hasConversation = messages.length > 1 || typing;
  return (
    <div
      className="assistant-page assistant-reference page-enter"
      style={{ backgroundImage: `url("${assistantImage}")` }}
    >
      <TopNav dark={dark} onToggle={onToggle} />
      <main className="assistant-reference-main">
        <section
          className={`assistant-prompt ${hasConversation ? "has-conversation" : ""}`}
        >
          <div className="assistant-reference-kicker">
            <span className="assistant-status-dot" /> SANJEEVANI MCP · ONLINE
          </div>
          <h1>
            Describe an emergency.
            <br />
            <em>We’ll route it.</em>
          </h1>
          <p className="assistant-reference-copy">
            Tell Sanjeevani what your hospital needs. We’ll search trusted
            lenders and prepare the safest next step.
          </p>
          {paymentSuccess && (
            <div className="success-note page-enter">
              <Check size={14} /> Payment successful. Loan confirmation is
              complete.
            </div>
          )}
          <div className="reference-compose">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Build a dispatch request with network routes and..."
              aria-label="Message Sanjeevani MCP"
              data-testid="textarea-assistant-message"
            />
            <div className="reference-compose-bottom">
              <div className="reference-suggestions">
                {["Find oxygen", "Nearest lender", "Today’s network"].map(
                  (suggestion) => (
                    <button
                      type="button"
                      key={suggestion}
                      onClick={() => send(suggestion)}
                      data-testid={`button-suggestion-${suggestion.slice(0, 8).replaceAll(" ", "-").toLowerCase()}`}
                    >
                      <span>＋</span>
                      {suggestion}
                    </button>
                  ),
                )}
              </div>
              <div className="reference-compose-actions">
                <span>Sanjeevani MCP</span>
                <button
                  type="button"
                  className="reference-send"
                  onClick={() => send()}
                  aria-label="Send message"
                  data-testid="button-send-assistant"
                >
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          </div>
          {hasConversation && (
            <div className="reference-thread">
              {messages.slice(1).map((message, i) =>
                message.role === "user" ? (
                  <div
                    className="reference-thread-item"
                    key={`${message.time}-${i}`}
                  >
                    <span>You</span>
                    <p>{message.text}</p>
                  </div>
                ) : (
                  <div
                    className="reference-response"
                    key={`${message.time}-${i}`}
                  >
                    <div className="reference-response-label">
                      <Bot size={13} /> Sanjeevani MCP
                    </div>
                    <p>{message.text}</p>
                  </div>
                ),
              )}
              {typing && (
                <div className="reference-thread-typing">
                  <i />
                  <i />
                  <i />
                </div>
              )}
            </div>
          )}
        </section>
        <div className="assistant-trust">
          <span>Built for hospitals and care networks</span>
          <div className="trust-logos">
            <strong>Sanjeevani</strong>
            <strong>24 / 7</strong>
            <strong>Verified routes</strong>
          </div>
        </div>
      </main>
      <div className="assistant-reference-footer">
        <button
          type="button"
          onClick={() => setMessages([])}
          data-testid="button-new-conversation"
        >
          New conversation
        </button>
        <span>
          <ShieldCheck size={12} /> Private by design · Verify critical details
          before dispatch.
        </span>
      </div>
    </div>
  );
}

function MoreDots() {
  return (
    <span className="more-dots">
      <i />
      <i />
      <i />
    </span>
  );
}

function RouterContent({
  dark,
  onToggle,
}: {
  dark: boolean;
  onToggle: () => void;
}) {
  return (
    <Switch>
      <Route
        path="/"
        component={() => <Home dark={dark} onToggle={onToggle} />}
      />
      <Route
        path="/dashboard"
        component={() => <Dashboard dark={dark} onToggle={onToggle} />}
      />
      <Route
        path="/admin-workflow"
        component={() => <AdminWorkflowPage dark={dark} onToggle={onToggle} />}
      />
      <Route
        path="/marketplace"
        component={() => <Marketplace dark={dark} onToggle={onToggle} />}
      />
      <Route
        path="/analytics"
        component={() => <Analytics dark={dark} onToggle={onToggle} />}
      />
      <Route
        path="/assistant"
        component={() => <Assistant dark={dark} onToggle={onToggle} />}
      />
      <Route
        path="/payment-success"
        component={() => <PaymentSuccess dark={dark} onToggle={onToggle} />}
      />
      <Route component={NotFound} />
    </Switch>
  );
}

function AdminWorkflowPage({
  dark,
  onToggle,
}: {
  dark: boolean;
  onToggle: () => void;
}) {
  return (
    <Shell dark={dark} onToggle={onToggle}>
      <AdminWorkflowView />
    </Shell>
  );
}

function PaymentSuccess({
  dark,
  onToggle,
}: {
  dark: boolean;
  onToggle: () => void;
}) {
  const payment = JSON.parse(
    sessionStorage.getItem("sanjeevani-payment-success") ?? "{}",
  ) as { paymentId?: string; orderId?: string };
  return (
    <Shell dark={dark} onToggle={onToggle}>
      <div className="workspace">
        <Panel className="status-panel page-enter">
          <div className="panel-heading">
            <div>
              <span className="eyebrow">RAZORPAY / PAYMENT CONFIRMED</span>
              <h2>Loan payment successful</h2>
            </div>
            <span className="status-badge">
              <Check size={13} /> PAID
            </span>
          </div>
          <div className="status-card">
            <div className="status-icon">
              <ShieldCheck size={20} />
            </div>
            <div>
              <strong>Your equipment request is confirmed.</strong>
              <span>Dispatch can now proceed through the care network.</span>
            </div>
          </div>
          {payment.paymentId && <code>Payment: {payment.paymentId}</code>}
          {payment.orderId && <code>Order: {payment.orderId}</code>}
          <button
            type="button"
            className="secondary-button full"
            onClick={() => window.history.back()}
          >
            Return to assistant
          </button>
        </Panel>
      </div>
    </Shell>
  );
}

function App() {
  const [dark, setDark] = useState(
    () => localStorage.getItem("sanjeevani-theme") === "dark",
  );
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("sanjeevani-theme", dark ? "dark" : "light");
  }, [dark]);
  const toggleTheme = () => setDark((value) => !value);
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
          <RoutedErrorBoundary>
            <RouterContent dark={dark} onToggle={toggleTheme} />
          </RoutedErrorBoundary>
        </WouterRouter>
        <CursorBloom />
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

function RoutedErrorBoundary({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  return <ErrorBoundary resetKey={location}>{children}</ErrorBoundary>;
}

export default App;
