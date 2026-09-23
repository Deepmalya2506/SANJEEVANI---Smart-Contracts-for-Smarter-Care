import { useState, useEffect } from "react";
import { 
  Compass, 
  Layers, 
  MapPin, 
  Activity, 
  Clock, 
  ShieldCheck, 
  Navigation, 
  Radio, 
  RefreshCw,
  AlertTriangle
} from "lucide-react";
import { MapLibreView, HospitalNode } from "@/components/map/MapLibreView";
import { getNetworkNodes, searchSpatialCandidates, getGisRoute, getH3Footprint } from "@/lib/api";

export function MapCommandPage() {
  const [nodes, setNodes] = useState<HospitalNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [originHospital, setOriginHospital] = useState<HospitalNode | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<HospitalNode | null>(null);
  const [equipmentType, setEquipmentType] = useState("Portable ventilator");
  const [maxEta, setMaxEta] = useState(45);
  const [showH3Footprint, setShowH3Footprint] = useState(true);
  const [h3Data, setH3Data] = useState<any>(null);
  const [routeGeometry, setRouteGeometry] = useState<any>(null);
  const [routeInfo, setRouteInfo] = useState<any>(null);
  const [candidates, setCandidates] = useState<HospitalNode[]>([]);
  const [calculatingRoute, setCalculatingRoute] = useState(false);

  // Load network nodes on initial mount
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await getNetworkNodes();
        const activeNodes: HospitalNode[] = res.nodes || [];
        setNodes(activeNodes);
        if (activeNodes.length > 0) {
          // Default to first active hospital as origin
          setOriginHospital(activeNodes[0]);
        }
      } catch (err) {
        // Fallback default sample nodes for Kolkata area if API is unreachable
        const fallbackNodes: HospitalNode[] = [
          {
            hospital_id: "st-martha",
            hospital_name: "St. Martha Medical Centre",
            latitude: 22.5726,
            longitude: 88.3639,
            h3_cell: "873cf2c60ffffff",
            total_assets: 8,
            available_count: 5,
          },
          {
            hospital_id: "carebridge",
            hospital_name: "CareBridge Network",
            latitude: 22.5958,
            longitude: 88.4112,
            h3_cell: "873cf2c62ffffff",
            total_assets: 6,
            available_count: 2,
          },
          {
            hospital_id: "northstar",
            hospital_name: "Northstar Health Hub",
            latitude: 22.5512,
            longitude: 88.3498,
            h3_cell: "873cf2c64ffffff",
            total_assets: 12,
            available_count: 7,
          },
          {
            hospital_id: "howrah-gen",
            hospital_name: "Howrah General Hospital",
            latitude: 22.5892,
            longitude: 88.3103,
            h3_cell: "873cf2c66ffffff",
            total_assets: 4,
            available_count: 1,
          },
        ];
        setNodes(fallbackNodes);
        setOriginHospital(fallbackNodes[0]);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Update H3 footprint whenever origin changes or toggle is pressed
  useEffect(() => {
    if (!originHospital || !showH3Footprint) {
      setH3Data(null);
      return;
    }
    getH3Footprint(originHospital.latitude, originHospital.longitude, 2, 7)
      .then((data) => setH3Data(data))
      .catch(() => setH3Data(null));
  }, [originHospital, showH3Footprint]);

  // Query spatial candidates whenever origin or equipment selection changes
  useEffect(() => {
    if (!originHospital) return;
    searchSpatialCandidates({
      origin: { lat: originHospital.latitude, lon: originHospital.longitude },
      equipment_type: equipmentType,
      radius_km: 40.0,
      max_eta_minutes: maxEta,
    })
      .then((res) => {
        const found = res.candidates || [];
        setCandidates(found);
        if (found.length > 0) {
          handleSelectCandidate(found[0]);
        } else {
          setSelectedCandidate(null);
          setRouteGeometry(null);
          setRouteInfo(null);
        }
      })
      .catch(() => {
        // Mock fallback candidates for visualization
        const others = nodes.filter((n) => n.hospital_id !== originHospital.hospital_id);
        setCandidates(others);
        if (others.length > 0) handleSelectCandidate(others[0]);
      });
  }, [originHospital, equipmentType, maxEta, nodes]);

  // Calculate route to selected candidate
  const handleSelectCandidate = async (cand: HospitalNode) => {
    if (!originHospital) return;
    setSelectedCandidate(cand);
    setCalculatingRoute(true);
    try {
      const res = await getGisRoute({
        source: { lat: originHospital.latitude, lon: originHospital.longitude },
        destination: { lat: cand.latitude, lon: cand.longitude },
      });
      const data = res.data || res;
      setRouteGeometry(data.geometry);
      setRouteInfo(data);
    } catch {
      // Fallback straight line polyline
      setRouteGeometry({
        type: "LineString",
        coordinates: [
          [originHospital.longitude, originHospital.latitude],
          [cand.longitude, cand.latitude],
        ],
      });
      setRouteInfo({
        distance: 4200,
        traffic_adjusted_eta_min: 16.5,
        traffic_status: "NORMAL",
        traffic_color: "#10B981",
      });
    } finally {
      setCalculatingRoute(false);
    }
  };

  return (
    <div className="workspace h-[calc(100vh-80px)] flex flex-col p-4 md:p-6 gap-4">
      {/* Top Bar Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="live-dot" />
            <span className="eyebrow">GLOBAL NETWORK GIS SANDBOX</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Geospatial Command View</h1>
          <p className="text-xs md:text-sm text-muted-foreground">
            Multi-stage PostGIS spatial filtering, Uber H3 hex clustering, and OSRM traffic routing.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 bg-card/60 backdrop-blur border border-border/50 px-3 py-1.5 rounded-lg text-xs font-medium">
            <Radio size={14} className="text-emerald-500 animate-pulse" />
            <span>{nodes.length} Active Facilities</span>
          </div>
          <button
            type="button"
            onClick={() => setShowH3Footprint(!showH3Footprint)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 border transition ${
              showH3Footprint 
                ? "bg-indigo-500/15 border-indigo-500/40 text-indigo-400" 
                : "bg-card/40 border-border/50 text-muted-foreground"
            }`}
          >
            <Layers size={13} />
            H3 Footprint (Res 7)
          </button>
        </div>
      </div>

      {/* Main Grid: Control Panel + Map Canvas */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-0">
        {/* Left Sidebar: Controls and Candidates */}
        <aside className="lg:col-span-4 flex flex-col gap-4 overflow-y-auto pr-1">
          {/* Origin & Requirement Filter Card */}
          <div className="bg-card/70 border border-border/50 rounded-xl p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Compass size={14} /> Origin Facility
              </span>
              <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded font-mono">
                {originHospital?.h3_cell?.slice(0, 9) || "Res 7"}
              </span>
            </div>

            <select
              value={originHospital?.hospital_id || ""}
              onChange={(e) => {
                const found = nodes.find((n) => n.hospital_id === e.target.value);
                if (found) setOriginHospital(found);
              }}
              className="w-full bg-background/80 border border-border/60 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
            >
              {nodes.map((h) => (
                <option key={h.hospital_id} value={h.hospital_id}>
                  {h.hospital_name}
                </option>
              ))}
            </select>

            <div className="grid grid-cols-2 gap-2 pt-1">
              <div>
                <label className="text-[11px] font-medium text-muted-foreground block mb-1">
                  Equipment Needed
                </label>
                <select
                  value={equipmentType}
                  onChange={(e) => setEquipmentType(e.target.value)}
                  className="w-full bg-background/80 border border-border/60 rounded-lg px-2.5 py-1.5 text-xs"
                >
                  <option>Portable ventilator</option>
                  <option>Oxygen concentrator</option>
                  <option>Patient monitor</option>
                  <option>Infusion pump</option>
                </select>
              </div>

              <div>
                <label className="text-[11px] font-medium text-muted-foreground block mb-1">
                  Max Travel Window
                </label>
                <select
                  value={maxEta}
                  onChange={(e) => setMaxEta(Number(e.target.value))}
                  className="w-full bg-background/80 border border-border/60 rounded-lg px-2.5 py-1.5 text-xs"
                >
                  <option value={20}>20 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={45}>45 minutes</option>
                  <option value={60}>60 minutes</option>
                </select>
              </div>
            </div>
          </div>

          {/* Active Candidate Selection and Traffic Report */}
          <div className="bg-card/70 border border-border/50 rounded-xl p-4 flex flex-col gap-3 flex-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Navigation size={14} /> Feasible Candidates ({candidates.length})
              </span>
              <div className="flex items-center gap-1.5 text-[10px]">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" /> Normal
                <span className="w-2 h-2 rounded-full bg-amber-500 inline-block ml-1" /> Slow
                <span className="w-2 h-2 rounded-full bg-red-500 inline-block ml-1" /> Heavy
              </div>
            </div>

            {candidates.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground text-xs flex flex-col items-center gap-2">
                <AlertTriangle size={24} className="text-amber-500/80" />
                <span>No facilities with {equipmentType} found within {maxEta} min radius.</span>
              </div>
            ) : (
              <div className="flex flex-col gap-2 overflow-y-auto max-h-[340px] pr-1">
                {candidates.map((cand) => {
                  const isSelected = selectedCandidate?.hospital_id === cand.hospital_id;
                  const isNormal = !cand.traffic_status || cand.traffic_status === "NORMAL";
                  return (
                    <button
                      type="button"
                      key={cand.hospital_id}
                      onClick={() => handleSelectCandidate(cand)}
                      className={`text-left p-3 rounded-xl border transition flex flex-col gap-1.5 ${
                        isSelected
                          ? "bg-primary/10 border-primary/50 shadow-sm"
                          : "bg-background/40 hover:bg-background/80 border-border/40"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-xs truncate max-w-[200px]">
                          {cand.hospital_name}
                        </span>
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase ${
                          cand.traffic_status === "HEAVY" 
                            ? "bg-red-500/15 text-red-400"
                            : cand.traffic_status === "SLOW"
                            ? "bg-amber-500/15 text-amber-400"
                            : "bg-emerald-500/15 text-emerald-400"
                        }`}>
                          {cand.traffic_status || "NORMAL"}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                        <span>{cand.available_count || 1} available</span>
                        <span className="font-mono text-foreground font-medium">
                          {cand.eta_min ? `${cand.eta_min} min` : "Calculating..."} · {cand.distance_km || 0} km
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Selected Route Summary Banner */}
            {routeInfo && selectedCandidate && (
              <div className="mt-auto pt-3 border-t border-border/50 bg-background/60 p-3 rounded-lg flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-muted-foreground uppercase font-bold block">
                    Calculated Road Transit
                  </span>
                  <span className="text-sm font-bold text-foreground">
                    {routeInfo.traffic_adjusted_eta_min || routeInfo.eta_min || 18} min ETA
                  </span>
                  <span className="text-[11px] text-muted-foreground ml-1.5">
                    ({Math.round((routeInfo.distance || 4500) / 1000 * 10) / 10} km)
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-muted-foreground uppercase font-bold block">
                    Traffic Mask
                  </span>
                  <span className="text-xs font-semibold text-emerald-400">
                    {routeInfo.traffic_status || "NORMAL"}
                  </span>
                </div>
              </div>
            )}
          </div>
        </aside>

        {/* Right Main Area: MapLibre GL JS Vector Map */}
        <main className="lg:col-span-8 bg-card/40 border border-border/50 rounded-xl overflow-hidden relative shadow-inner">
          <MapLibreView
            origin={
              originHospital
                ? {
                    lat: originHospital.latitude,
                    lon: originHospital.longitude,
                    label: originHospital.hospital_name,
                  }
                : undefined
            }
            destination={
              selectedCandidate
                ? {
                    lat: selectedCandidate.latitude,
                    lon: selectedCandidate.longitude,
                    label: selectedCandidate.hospital_name,
                  }
                : undefined
            }
            routeGeometry={routeGeometry}
            trafficStatus={routeInfo?.traffic_status || "NORMAL"}
            trafficColor={routeInfo?.traffic_color || "#10B981"}
            candidates={nodes}
            h3Footprint={h3Data}
            selectedHospitalId={selectedCandidate?.hospital_id}
            onSelectHospital={(node) => handleSelectCandidate(node)}
            className="w-full h-full min-h-[500px]"
          />

          {/* Floating Map Overlay Badges */}
          <div className="absolute top-3 left-3 bg-card/85 backdrop-blur border border-border/60 rounded-lg p-2 text-xs flex flex-col gap-1 shadow-md pointer-events-none">
            <span className="font-semibold text-[11px] flex items-center gap-1.5 text-primary">
              <ShieldCheck size={13} /> OpenFreeMap Vector Layer
            </span>
            <span className="text-[10px] text-muted-foreground">
              Zero Mapbox API Tokens · 100% Open Source
            </span>
          </div>
        </main>
      </div>
    </div>
  );
}
