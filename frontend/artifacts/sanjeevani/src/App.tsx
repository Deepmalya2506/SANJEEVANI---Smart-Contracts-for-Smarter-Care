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
import { previewDispatch, searchInventory, sendChat } from "@/lib/api";
import heroImage from "@assets/Untitled_design_(1)_1787314419698.png";
import assistantImage from "@assets/download_(55)_1787315213518.jpg";

const queryClient = new QueryClient();

type Lender = {
  id: number;
  name: string;
  type: string;
  eta: string;
  price: string;
  stock: string;
  distance: string;
  rating: string;
};

const lenders: Lender[] = [
  {
    id: 1,
    name: "Aster Medisource",
    type: "Oxygen concentrator",
    eta: "12 min",
    price: "₹1,850 / day",
    stock: "4 available",
    distance: "2.4 km",
    rating: "4.9",
  },
  {
    id: 2,
    name: "CareBridge Network",
    type: "Portable ventilator",
    eta: "18 min",
    price: "₹3,200 / day",
    stock: "2 available",
    distance: "4.1 km",
    rating: "4.8",
  },
  {
    id: 3,
    name: "Northstar Health",
    type: "Oxygen concentrator",
    eta: "24 min",
    price: "₹1,600 / day",
    stock: "7 available",
    distance: "7.8 km",
    rating: "4.7",
  },
];
const equipment = [
  {
    id: "oxygen-1",
    name: "OxyFlow 5L Concentrator",
    category: "Oxygen",
    lender: "Aster Medisource",
    price: "₹1,850",
    unit: "per day",
    distance: "2.4 km",
    available: 4,
    accent: "violet",
  },
  {
    id: "vent-2",
    name: "BreatheSafe V-40",
    category: "Ventilator",
    lender: "CareBridge Network",
    price: "₹3,200",
    unit: "per day",
    distance: "4.1 km",
    available: 2,
    accent: "rose",
  },
  {
    id: "monitor-3",
    name: "PulseTrack M7",
    category: "Patient monitor",
    lender: "Northstar Health",
    price: "₹940",
    unit: "per day",
    distance: "7.8 km",
    available: 7,
    accent: "slate",
  },
  {
    id: "oxygen-4",
    name: "OxyFlow 10L Station",
    category: "Oxygen",
    lender: "Swasthya Collective",
    price: "₹2,450",
    unit: "per day",
    distance: "9.2 km",
    available: 3,
    accent: "violet",
  },
];

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
          <span className="home-stat-value">146</span>
          <span className="home-stat-label">trusted lenders</span>
        </div>
        <div>
          <span className="home-stat-value">18,420</span>
          <span className="home-stat-label">fulfilled requests</span>
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
  const [hospital, setHospital] = useState("St. Martha Medical Centre");
  const [requested, setRequested] = useState(false);
  const [selected, setSelected] = useState(1);
  const requestEquipment = async () => {
    const equipmentTypeId =
      [
        "Oxygen concentrator",
        "Portable ventilator",
        "Patient monitor",
        "Infusion pump",
      ].indexOf(equipmentType) + 1;
    await previewDispatch({
      equipment_type: equipmentTypeId,
      quantity: 1,
      location: {
        lat: Number(import.meta.env.VITE_ORIGIN_LAT ?? 22.5726),
        lon: Number(import.meta.env.VITE_ORIGIN_LON ?? 88.3639),
      },
      hospital_id: hospital,
      skip_blockchain: true,
    });
    setRequested(true);
  };
  return (
    <Shell dark={dark} onToggle={onToggle}>
      <div className="workspace">
        <SectionHeader
          eyebrow="LIVE DISPATCH / 09:41 IST"
          title="Hospital network control room."
          description="One live request is being coordinated across the care network."
          action={
            <div className="header-status">
              <span className="live-dot" /> Network healthy{" "}
              <span className="header-divider" /> <Clock3 size={14} /> Updated
              16 sec ago
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
              Receiving hospital
            </label>
            <div className="select-wrap">
              <Hospital size={15} />
              <select
                id="hospital"
                value={hospital}
                onChange={(e) => setHospital(e.target.value)}
                data-testid="select-hospital"
              >
                <option>St. Martha Medical Centre</option>
                <option>Howrah General Hospital</option>
                <option>Lakeview Institute of Care</option>
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
              <span>NEARBY LENDERS</span>
              <span>3 available</span>
            </div>
            <div className="lender-list">
              {lenders.map((lender) => (
                <button
                  type="button"
                  key={lender.id}
                  className={`lender-row ${selected === lender.id ? "selected" : ""}`}
                  onClick={() => setSelected(lender.id)}
                  data-testid={`button-lender-${lender.id}`}
                >
                  <span className="lender-avatar">
                    {lender.name
                      .split(" ")
                      .map((part) => part[0])
                      .join("")
                      .slice(0, 2)}
                  </span>
                  <span className="lender-main">
                    <strong>{lender.name}</strong>
                    <small>
                      {lender.stock} · {lender.distance}
                    </small>
                  </span>
                  <span className="lender-eta">
                    <b>{lender.eta}</b>
                    <small>{lender.price}</small>
                  </span>
                </button>
              ))}
            </div>
            <button
              type="button"
              className="primary-button full"
              onClick={() => void requestEquipment()}
              data-testid="button-request-now"
            >
              {requested ? (
                <>
                  <Check size={16} /> Request queued
                </>
              ) : (
                <>
                  <Zap size={16} /> Request now
                </>
              )}
            </button>
            {requested && (
              <div className="success-note page-enter">
                <Check size={14} /> Preview locked for {hospital}. A lender will
                confirm in under 2 minutes.
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
              <div className="map-label label-one">SALT LAKE</div>
              <div className="map-label label-two">PARK STREET</div>
              <div className="map-label label-three">HOWRAH</div>
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
                <span className="pulse-dot" /> St. Martha · receiving
              </div>
              <div className="node-callout lender">
                <span /> Aster Medisource · 12 min
              </div>
              <div className="map-scale">
                <span>15 min reach</span>
                <span>0</span>
                <span>2 km</span>
              </div>
            </div>
            <div className="map-footer">
              <span>
                <MapPin size={14} /> Kolkata network · 12 active nodes
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
                <h2>Request {requested ? "queued" : "in transit"}</h2>
              </div>
              <span className="status-badge">
                <span /> {requested ? "PREVIEW" : "IN_TRANSIT"}
              </span>
            </div>
            <div className="status-card">
              <div className="status-icon">
                <Truck size={20} />
              </div>
              <div>
                <strong>
                  {requested
                    ? "Dispatch preview ready"
                    : "OxyFlow 5L Concentrator"}
                </strong>
                <span>
                  {requested
                    ? "Awaiting lender confirmation"
                    : "Aster Medisource · Vehicle MH 04"}
                </span>
              </div>
            </div>
            <div className="timeline">
              {[
                "Request verified by St. Martha",
                "Lender accepted the handoff",
                "Courier en route to receiving hospital",
              ].map((item, i) => (
                <div
                  className={`timeline-item ${i < (requested ? 1 : 3) ? "done" : ""}`}
                  key={item}
                >
                  <span className="timeline-dot">
                    {i < (requested ? 1 : 3) && <Check size={10} />}
                  </span>
                  <div>
                    <strong>{item}</strong>
                    <small>
                      {i === 0
                        ? "09:26 · system verified"
                        : i === 1
                          ? "09:29 · 3 min ago"
                          : "ETA 09:53 · 12 min remaining"}
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
                <strong>₹1,850</strong>
              </div>
              <code>0x7f2a…c91e · settlement held</code>
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
  const filtered = useMemo(
    () =>
      equipment.filter(
        (item) =>
          (category === "All equipment" || item.category === category) &&
          `${item.name} ${item.lender}`
            .toLowerCase()
            .includes(query.toLowerCase()),
      ),
    [category, query],
  );
  const syncInventory = async () => {
    const equipmentType =
      category === "Oxygen"
        ? 1
        : category === "Ventilator"
          ? 2
          : category === "Patient monitor"
            ? 3
            : 1;
    await searchInventory({ equipmentType, quantity: 1 });
    setNotice("Inventory synced just now.");
  };
  return (
    <Shell dark={dark} onToggle={onToggle}>
      <div className="workspace">
        <SectionHeader
          eyebrow="TRUSTED SUPPLY NETWORK"
          title="Marketplace"
          description="Browse verified medical equipment available for immediate dispatch."
          action={
            <button
              type="button"
              className="secondary-button"
              onClick={() => void syncInventory()}
              data-testid="button-sync-inventory"
            >
              <Activity size={15} /> Sync inventory
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
              placeholder="Search equipment or lender"
              aria-label="Search equipment or lender"
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
          <span className="result-count">{filtered.length} listings</span>
        </div>
        <div className="market-grid">
          {filtered.map((item) => (
            <article
              className="equipment-card soft-rise"
              key={item.id}
              data-testid={`card-equipment-${item.id}`}
            >
              <div className={`equipment-visual ${item.accent}`}>
                <Package size={35} strokeWidth={1.2} />
                <span>VERIFIED ASSET</span>
              </div>
              <div className="equipment-body">
                <div className="card-kicker">
                  <span>{item.category}</span>
                  <span className="availability">
                    <span /> {item.available} available
                  </span>
                </div>
                <h2>{item.name}</h2>
                <p>
                  {item.lender} <span>·</span> {item.distance} away
                </p>
                <div className="card-footer">
                  <div>
                    <strong>{item.price}</strong>
                    <small>{item.unit}</small>
                  </div>
                  <Link
                    href="/dashboard"
                    className="outline-button"
                    onClick={() =>
                      setNotice(`${item.name} selected for dispatch.`)
                    }
                    data-testid={`link-request-${item.id}`}
                  >
                    Request <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
        {filtered.length === 0 && (
          <div className="empty-state">
            <Boxes size={24} />
            <h2>No matching equipment</h2>
            <p>Try another equipment type or clear your search.</p>
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
  return (
    <Shell dark={dark} onToggle={onToggle}>
      <div className="workspace analytics-workspace">
        <SectionHeader
          eyebrow="NETWORK INTELLIGENCE / LAST 30 DAYS"
          title="Analytics console"
          description="A quiet view of the moments that move through Sanjeevani."
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
              <span className="live-dot" /> SANJEEVANI / OBSERVATORY
            </span>
            <span>
              DATA REFRESHED 09:40 IST · <Command size={12} /> K
            </span>
          </div>
          <div className="console-screen">
            <div className="metric-strip">
              <div>
                <span>Requests fulfilled</span>
                <strong>2,486</strong>
                <small className="positive">+12.4% vs last month</small>
              </div>
              <div>
                <span>Median response</span>
                <strong>04:12</strong>
                <small className="positive">−38 sec improvement</small>
              </div>
              <div>
                <span>Network fulfilment</span>
                <strong>94.8%</strong>
                <small>Target 92%</small>
              </div>
              <div>
                <span>Active lenders</span>
                <strong>146</strong>
                <small>Across 18 cities</small>
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
                      94.8<span>%</span>
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
                {[
                  ["Oxygen", 68, "violet"],
                  ["Ventilation", 46, "rose"],
                  ["Monitoring", 31, "slate"],
                  ["Infusion", 19, "muted"],
                ].map(([name, value, tone]) => (
                  <div className="demand-row" key={name as string}>
                    <span>{name}</span>
                    <div>
                      <i
                        className={tone as string}
                        style={{ width: `${value}%` }}
                      />
                    </div>
                    <b>{value}</b>
                  </div>
                ))}
              </Panel>
              <Panel className="chart-panel leaderboard">
                <span className="eyebrow">HOSPITAL LEADERBOARD</span>
                <h2>Fastest to confirm</h2>
                {[
                  "St. Martha Medical Centre",
                  "Lakeview Institute of Care",
                  "Howrah General Hospital",
                ].map((name, i) => (
                  <div className="leader-row" key={name}>
                    <b>0{i + 1}</b>
                    <span>{name}</span>
                    <strong>{["02:18", "03:04", "03:46"][i]}</strong>
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
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string>();
  const [messages, setMessages] = useState<ChatItem[]>([
    {
      role: "assistant",
      text: "Good morning. I have a clear view of the Kolkata care network. What should we solve first?",
      time: "09:41",
    },
  ]);
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
      <Route component={NotFound} />
    </Switch>
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
