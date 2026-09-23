import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

export type MapCoordinate = {
  lat: number;
  lon: number;
  label?: string;
};

export type HospitalNode = {
  hospital_id: string;
  hospital_name: string;
  latitude: number;
  longitude: number;
  distance_km?: number;
  eta_min?: number;
  available_count?: number;
  total_assets?: number;
  traffic_status?: string;
  traffic_color?: string;
  h3_cell?: string;
  wallet_address?: string;
  upi_id?: string;
};

export type MapLibreViewProps = {
  origin?: MapCoordinate;
  destination?: MapCoordinate;
  routeGeometry?: {
    type: string;
    coordinates: number[][];
  } | null;
  trafficStatus?: string;
  trafficColor?: string;
  candidates?: HospitalNode[];
  h3Footprint?: any;
  selectedHospitalId?: string;
  onSelectHospital?: (hospital: HospitalNode) => void;
  className?: string;
  interactive?: boolean;
  center?: [number, number]; // [lon, lat]
  zoom?: number;
};

const OPEN_FREE_MAP_STYLE = "https://tiles.openfreemap.org/styles/liberty";
const CARTO_POSITRON_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";

export function MapLibreView({
  origin,
  destination,
  routeGeometry,
  trafficStatus = "NORMAL",
  trafficColor = "#10B981",
  candidates = [],
  h3Footprint,
  selectedHospitalId,
  onSelectHospital,
  className = "w-full h-full min-h-[300px] rounded-lg",
  interactive = true,
  center = [88.3639, 22.5726], // Default Kolkata center [lon, lat]
  zoom = 12,
}: MapLibreViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Initialize MapLibre
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const initialCenter = origin
      ? [origin.lon, origin.lat]
      : center;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: OPEN_FREE_MAP_STYLE,
      center: initialCenter as [number, number],
      zoom: zoom,
      interactive: interactive,
      attributionControl: false,
    });

    if (interactive) {
      map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-right");
      map.addControl(
        new maplibregl.AttributionControl({
          compact: true,
          customAttribution: "OpenFreeMap · OpenStreetMap",
        }),
        "bottom-right"
      );
    }

    map.on("load", () => {
      setMapLoaded(true);
      // Trigger a resize to handle flex/modal layout animations
      setTimeout(() => map.resize(), 100);
    });

    map.on("error", (e) => {
      // Fallback to CARTO Positron if OpenFreeMap is blocked or unreachable
      if (map.getStyle()?.sources === undefined) {
        map.setStyle(CARTO_POSITRON_STYLE);
      }
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update Route Polyline and H3 Footprint layers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    // --- H3 Footprint Hexagons ---
    if (map.getSource("h3-footprint")) {
      (map.getSource("h3-footprint") as maplibregl.GeoJSONSource).setData(
        h3Footprint || { type: "FeatureCollection", features: [] }
      );
    } else if (h3Footprint) {
      map.addSource("h3-footprint", {
        type: "geojson",
        data: h3Footprint,
      });

      map.addLayer({
        id: "h3-footprint-fill",
        type: "fill",
        source: "h3-footprint",
        paint: {
          "fill-color": "#6366f1",
          "fill-opacity": 0.12,
        },
      });

      map.addLayer({
        id: "h3-footprint-line",
        type: "line",
        source: "h3-footprint",
        paint: {
          "line-color": "#818cf8",
          "line-width": 1.5,
          "line-dasharray": [2, 1],
          "line-opacity": 0.6,
        },
      });
    }

    // --- Route Polyline with Traffic Glow and Traffic Color ---
    const routeData = routeGeometry
      ? {
          type: "Feature",
          properties: { trafficStatus },
          geometry: routeGeometry,
        }
      : { type: "FeatureCollection", features: [] };

    if (map.getSource("route-source")) {
      (map.getSource("route-source") as maplibregl.GeoJSONSource).setData(routeData as any);
      if (map.getLayer("route-line-core")) {
        map.setPaintProperty("route-line-core", "line-color", trafficColor);
      }
    } else if (routeGeometry) {
      map.addSource("route-source", {
        type: "geojson",
        data: routeData as any,
      });

      // Outer glow / casing
      map.addLayer({
        id: "route-line-casing",
        type: "line",
        source: "route-source",
        layout: {
          "line-join": "round",
          "line-cap": "round",
        },
        paint: {
          "line-color": "#0f172a",
          "line-width": 8,
          "line-opacity": 0.4,
        },
      });

      // Core route with traffic status color
      map.addLayer({
        id: "route-line-core",
        type: "line",
        source: "route-source",
        layout: {
          "line-join": "round",
          "line-cap": "round",
        },
        paint: {
          "line-color": trafficColor,
          "line-width": 4.5,
          "line-opacity": 0.95,
        },
      });
    }

    // Auto-fit bounds if we have coordinates
    const bounds = new maplibregl.LngLatBounds();
    let hasPoints = false;

    if (origin) {
      bounds.extend([origin.lon, origin.lat]);
      hasPoints = true;
    }
    if (destination) {
      bounds.extend([destination.lon, destination.lat]);
      hasPoints = true;
    }
    if (routeGeometry?.coordinates) {
      routeGeometry.coordinates.forEach((coord) => {
        bounds.extend([coord[0], coord[1]]);
        hasPoints = true;
      });
    }

    if (hasPoints && map.getContainer().offsetWidth > 0) {
      map.fitBounds(bounds, {
        padding: { top: 40, bottom: 40, left: 40, right: 40 },
        maxZoom: 15,
        duration: 800,
      });
    }
  }, [mapLoaded, routeGeometry, trafficColor, trafficStatus, h3Footprint, origin, destination]);

  // Update Markers (Origin, Destination, Candidates)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    // Clear existing markers
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // Origin Marker (Pulse ring animation)
    if (origin) {
      const el = document.createElement("div");
      el.className = "origin-map-marker";
      el.innerHTML = `
        <div style="position: relative; display: flex; align-items: center; justify-content: center; width: 26px; height: 26px;">
          <div style="position: absolute; width: 26px; height: 26px; border-radius: 50%; background: rgba(59, 130, 246, 0.35); animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
          <div style="width: 14px; height: 14px; border-radius: 50%; background: #2563eb; border: 2.5px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.35);"></div>
        </div>
      `;

      const popup = new maplibregl.Popup({ offset: 14, closeButton: false }).setHTML(`
        <div style="padding: 4px 6px; font-family: sans-serif; font-size: 12px; font-weight: 600; color: #1e293b;">
          🏥 ${origin.label || "Origin (Receiving Hospital)"}
        </div>
      `);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([origin.lon, origin.lat])
        .setPopup(popup)
        .addTo(map);

      markersRef.current.push(marker);
    }

    // Destination / Selected Donor Marker
    if (destination) {
      const el = document.createElement("div");
      el.className = "dest-map-marker";
      el.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; width: 26px; height: 26px;">
          <div style="width: 16px; height: 16px; border-radius: 50%; background: #10b981; border: 2.5px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.4);"></div>
        </div>
      `;

      const popup = new maplibregl.Popup({ offset: 14, closeButton: false }).setHTML(`
        <div style="padding: 4px 6px; font-family: sans-serif; font-size: 12px; font-weight: 600; color: #065f46;">
          🎯 ${destination.label || "Donor Hospital"}
        </div>
      `);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([destination.lon, destination.lat])
        .setPopup(popup)
        .addTo(map);

      markersRef.current.push(marker);
    }

    // Candidate Network Hospitals Markers
    candidates.forEach((cand) => {
      // Don't duplicate if this is the origin or destination
      if (
        (origin && Math.abs(cand.longitude - origin.lon) < 0.0001 && Math.abs(cand.latitude - origin.lat) < 0.0001) ||
        (destination && Math.abs(cand.longitude - destination.lon) < 0.0001 && Math.abs(cand.latitude - destination.lat) < 0.0001)
      ) {
        return;
      }

      const isSelected = selectedHospitalId === cand.hospital_id;
      const el = document.createElement("div");
      el.className = "candidate-node-marker";
      el.style.cursor = "pointer";
      el.innerHTML = `
        <div style="display: flex; flex-direction: column; align-items: center; transition: transform 0.2s;">
          <div style="
            width: ${isSelected ? "18px" : "13px"};
            height: ${isSelected ? "18px" : "13px"};
            border-radius: 50%;
            background: ${isSelected ? "#6366f1" : "#475569"};
            border: 2px solid white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
          "></div>
        </div>
      `;

      const popupHtml = `
        <div style="padding: 6px 8px; font-family: sans-serif; font-size: 12px; color: #1e293b; max-width: 220px;">
          <div style="font-weight: 700; font-size: 13px; margin-bottom: 3px;">${cand.hospital_name}</div>
          ${cand.h3_cell ? `<div style="font-size: 11px; color: #64748b;">H3 Hex: <code>${cand.h3_cell.slice(0, 9)}...</code></div>` : ""}
          ${cand.available_count !== undefined ? `<div style="margin-top: 3px; font-weight: 600; color: #0284c7;">${cand.available_count} units available</div>` : ""}
          ${cand.eta_min !== undefined ? `<div style="color: #10b981; font-weight: 600;">ETA: ${cand.eta_min} min · ${cand.distance_km || 0} km</div>` : ""}
          ${cand.traffic_status ? `<div style="font-size: 11px; color: #64748b;">Traffic: <b>${cand.traffic_status}</b></div>` : ""}
        </div>
      `;

      const popup = new maplibregl.Popup({ offset: 12 }).setHTML(popupHtml);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([cand.longitude, cand.latitude])
        .setPopup(popup)
        .addTo(map);

      el.addEventListener("click", () => {
        if (onSelectHospital) onSelectHospital(cand);
      });

      markersRef.current.push(marker);
    });
  }, [mapLoaded, origin, destination, candidates, selectedHospitalId]);

  return (
    <div className={`relative overflow-hidden ${className}`}>
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
}
