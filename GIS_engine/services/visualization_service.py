import os
import json
from typing import Any, Dict, Optional

MAC_TERMINAL_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>GIS launchpad — SANJEEVANI</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  
  <!-- MapLibre GL JS v3.6.2 -->
  <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
  <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
  
  <!-- Uber H3-JS v4.1.0 -->
  <script src="https://unpkg.com/h3-js@4.1.0/dist/h3-js.umd.js"></script>

  <style>
    :root {
      --mac-bg: rgba(22, 27, 34, 0.94);
      --mac-titlebar: #161b22;
      --mac-border: rgba(255, 255, 255, 0.14);
      --mac-text: #e6edf3;
      --mac-muted: #8b949e;
      --mac-cyan: #58a6ff;
      --mac-green: #3fb950;
      --mac-yellow: #d29922;
      --mac-red: #f85149;
      --mac-purple: #bc8cff;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "SF Mono", Menlo, Monaco, "Courier New", monospace;
      background: #0d1117;
      color: var(--mac-text);
      overflow: hidden;
      width: 100vw;
      height: 100vh;
    }

    #map {
      position: absolute;
      top: 0;
      bottom: 0;
      width: 100%;
      height: 100%;
      background: #090d16;
    }

    /* Floating Mac Terminal: Standard 80 cols x 24 rows character size */
    .mac-terminal {
      position: absolute;
      top: 24px;
      left: 24px;
      width: 560px;
      max-height: 520px;
      background: var(--mac-bg);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border: 1px solid var(--mac-border);
      border-radius: 10px;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.75), 0 0 0 1px rgba(255, 255, 255, 0.05);
      z-index: 10;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.2s ease;
    }

    .mac-terminal.minimised {
      transform: scale(0.01) translate(-200px, 200px);
      opacity: 0;
      pointer-events: none;
    }

    /* Mac Title Bar */
    .mac-titlebar {
      background: var(--mac-titlebar);
      border-bottom: 1px solid var(--mac-border);
      height: 34px;
      padding: 0 12px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      user-select: none;
    }

    .mac-traffic-lights {
      display: flex;
      gap: 7px;
      align-items: center;
    }
    .mac-light {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 8px;
      color: transparent;
      transition: all 0.15s;
    }
    .mac-traffic-lights:hover .mac-light {
      color: rgba(0, 0, 0, 0.6);
    }
    .light-close { background: #ff5f56; border: 1px solid #e0443e; }
    .light-min { background: #ffbd2e; border: 1px solid #dea123; }
    .light-max { background: #27c93f; border: 1px solid #1aab29; }

    .mac-title {
      font-size: 11.5px;
      font-weight: 600;
      color: var(--mac-muted);
      letter-spacing: 0.3px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    /* Terminal Body */
    .mac-body {
      flex: 1;
      padding: 12px 14px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 10px;
      font-size: 11px;
      line-height: 1.45;
    }
    .mac-body::-webkit-scrollbar { width: 4px; }
    .mac-body::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }

    .term-prompt {
      color: var(--mac-green);
      font-weight: 600;
    }
    .term-cmd { color: #f0f6fc; font-weight: 500; }

    /* Source Facility Display */
    .source-panel {
      background: rgba(88, 166, 255, 0.08);
      border: 1px solid rgba(88, 166, 255, 0.25);
      border-radius: 6px;
      padding: 8px 10px;
    }
    .source-head {
      font-size: 10px;
      font-weight: 700;
      color: var(--mac-cyan);
      letter-spacing: 0.5px;
      text-transform: uppercase;
      margin-bottom: 2px;
    }
    .source-name {
      font-size: 12.5px;
      font-weight: 700;
      color: #fff;
    }
    .source-details {
      font-size: 10.5px;
      color: var(--mac-muted);
      margin-top: 2px;
      display: flex;
      gap: 10px;
    }

    /* Collapsible Stage Accordions */
    .stage-item {
      border: 1px solid var(--mac-border);
      border-radius: 6px;
      background: rgba(0, 0, 0, 0.2);
      overflow: hidden;
    }
    .stage-header {
      padding: 7px 10px;
      background: rgba(255, 255, 255, 0.02);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: space-between;
      user-select: none;
      font-weight: 600;
      transition: background 0.15s;
    }
    .stage-header:hover {
      background: rgba(255, 255, 255, 0.05);
    }
    .stage-title {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .stage-icon {
      font-size: 9px;
      transition: transform 0.2s;
    }
    .stage-item.open .stage-icon {
      transform: rotate(90deg);
    }
    .stage-badge {
      font-size: 9.5px;
      padding: 1px 5px;
      border-radius: 3px;
      font-weight: 700;
    }
    .badge-s1 { background: rgba(88, 166, 255, 0.15); color: #58a6ff; }
    .badge-s2 { background: rgba(63, 185, 80, 0.15); color: #3fb950; }
    .badge-s3 { background: rgba(188, 140, 255, 0.15); color: #bc8cff; }

    .stage-content {
      display: none;
      padding: 8px 10px;
      border-top: 1px solid var(--mac-border);
      background: rgba(0, 0, 0, 0.15);
      max-height: 140px;
      overflow-y: auto;
      font-size: 10.5px;
    }
    .stage-item.open .stage-content {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    /* Target Corridor Rows */
    .corridor-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 4px 6px;
      border-radius: 4px;
      cursor: pointer;
      transition: background 0.15s;
    }
    .corridor-row:hover {
      background: rgba(88, 166, 255, 0.12);
    }
    .corridor-row.active {
      background: rgba(88, 166, 255, 0.25);
      border-left: 2px solid #58a6ff;
    }
    .corridor-rank {
      font-size: 9px;
      font-weight: 800;
      padding: 1px 5px;
      border-radius: 3px;
      color: #041324;
    }

    /* Minimal Toggles Bar */
    .minimal-toggles {
      display: flex;
      gap: 6px;
    }
    .min-toggle-btn {
      flex: 1;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--mac-border);
      color: #c9d1d9;
      padding: 5px 8px;
      border-radius: 4px;
      font-family: inherit;
      font-size: 10.5px;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: space-between;
      transition: all 0.15s;
    }
    .min-toggle-btn:hover { background: rgba(255, 255, 255, 0.08); }
    .min-toggle-btn.active {
      background: rgba(88, 166, 255, 0.2);
      border-color: #58a6ff;
      color: #fff;
    }
    .min-toggle-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #484f58;
    }
    .min-toggle-btn.active .min-toggle-dot {
      background: #58a6ff;
      box-shadow: 0 0 5px #58a6ff;
    }

    /* Best 5 Color Legend */
    .mac-legend {
      background: rgba(0, 0, 0, 0.25);
      border: 1px solid var(--mac-border);
      border-radius: 4px;
      padding: 6px 8px;
      font-size: 9.5px;
    }
    .legend-row {
      display: flex;
      justify-content: space-between;
      margin-top: 3px;
    }
    .legend-chip {
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .legend-color {
      width: 8px;
      height: 8px;
      border-radius: 2px;
    }

    /* Minimised Dock Icon */
    .mac-dock-icon {
      position: absolute;
      bottom: 24px;
      left: 24px;
      background: var(--mac-bg);
      border: 1px solid var(--mac-border);
      border-radius: 8px;
      padding: 8px 14px;
      font-size: 11px;
      font-weight: 700;
      color: var(--mac-cyan);
      display: none;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
      z-index: 10;
      transition: transform 0.15s;
    }
    .mac-dock-icon:hover {
      transform: scale(1.05);
    }
    .mac-dock-icon.visible {
      display: flex;
    }

    /* Basemap Switcher (Bottom Right) */
    .mac-style-bar {
      position: absolute;
      bottom: 24px;
      right: 24px;
      background: var(--mac-bg);
      backdrop-filter: blur(20px);
      border: 1px solid var(--mac-border);
      border-radius: 8px;
      padding: 5px;
      display: flex;
      gap: 5px;
      z-index: 10;
    }
    .mac-style-btn {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: var(--mac-muted);
      padding: 5px 10px;
      border-radius: 4px;
      font-family: inherit;
      font-size: 10.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }
    .mac-style-btn:hover { color: #fff; background: rgba(255, 255, 255, 0.1); }
    .mac-style-btn.active {
      background: #1f6feb;
      border-color: #58a6ff;
      color: #fff;
    }

    /* Hover Coordinate Tooltip */
    .hover-hud {
      position: absolute;
      bottom: 68px;
      right: 24px;
      background: var(--mac-bg);
      border: 1px solid var(--mac-border);
      border-radius: 6px;
      padding: 5px 10px;
      font-size: 10px;
      color: #c9d1d9;
      display: flex;
      align-items: center;
      gap: 10px;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.2s;
      z-index: 10;
    }
    .hover-hud.visible { opacity: 1; }

    /* Custom Markers */
    .marker-pin {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 10px rgba(0, 0, 0, 0.8);
      border: 2px solid #fff;
      cursor: pointer;
      transition: transform 0.15s;
    }
    .marker-pin:hover { transform: scale(1.25); }
    .pin-source {
      background: #f85149;
      box-shadow: 0 0 16px rgba(248, 81, 73, 0.9);
      animation: sourcePulse 1.5s infinite;
    }
    .pin-rank1 { background: #3fb950; }
    .pin-rank2 { background: #58a6ff; }
    .pin-rank3 { background: #bc8cff; }
    .pin-rank4 { background: #d29922; }
    .pin-rank5 { background: #f85149; }
    .pin-other { background: #6e7681; opacity: 0.55; }

    @keyframes sourcePulse {
      0%, 100% { box-shadow: 0 0 6px rgba(248, 81, 73, 0.6); }
      50% { box-shadow: 0 0 18px rgba(248, 81, 73, 1); }
    }

    .maplibregl-popup-content {
      background: #161b22 !important;
      border: 1px solid #30363d !important;
      border-radius: 6px !important;
      color: #e6edf3 !important;
      padding: 8px 10px !important;
      font-family: inherit !important;
      font-size: 10.5px !important;
    }
    .maplibregl-popup-close-button { color: #8b949e !important; }
  </style>
</head>
<body>
  <div id="map"></div>

  <!-- Floating Mac Terminal: GIS launchpad -->
  <div class="mac-terminal" id="mac-terminal-window">
    <!-- Mac Title Bar -->
    <div class="mac-titlebar">
      <div class="mac-traffic-lights">
        <span class="mac-light light-close" onclick="resetTerminalView()" title="Reset">✕</span>
        <span class="mac-light light-min" onclick="toggleMinimiseTerminal()" title="Minimise">−</span>
        <span class="mac-light light-max" onclick="toggleExpandTerminal()" title="Expand">＋</span>
      </div>
      <div class="mac-title">
        <span>📁</span> GIS launchpad
      </div>
      <div style="width: 36px;"></div>
    </div>

    <!-- Terminal Body -->
    <div class="mac-body">
      <!-- Prompt Line -->
      <div>
        <span class="term-prompt">sanjeevani</span> <span style="color:#8b949e">~ %</span> <span class="term-cmd">gis-launchpad --dynamic-cascading</span>
      </div>

      <!-- Source Hospital Box -->
      <div class="source-panel">
        <div class="source-head">[DESIGNATED SOURCE NODE]</div>
        <div class="source-name" id="source-name-display">Querying facility...</div>
        <div class="source-details">
          <span>HFR: <b style="color:#fff" id="source-hfr-display">--</b></span>
          <span>Hex: <b style="color:#58a6ff" id="source-hex-display">--</b></span>
          <span>Coords: <b style="color:#fff" id="source-coords-display">--</b></span>
        </div>
      </div>

      <!-- Stage 1: PostGIS Discovery Dropdown -->
      <div class="stage-item open" id="stage-1-item">
        <div class="stage-header" onclick="toggleStageAccordion('stage-1-item')">
          <div class="stage-title">
            <span class="stage-icon">▶</span>
            <span>Stage 1: PostGIS Spatial Discovery</span>
          </div>
          <span class="stage-badge badge-s1" id="stage-1-badge">-- ROI nodes</span>
        </div>
        <div class="stage-content" id="stage-1-content">
          <div style="color:#8b949e;">Executing 60km spatial radius query on PostgreSQL DB...</div>
        </div>
      </div>

      <!-- Stage 2: H3 Hex Cluster Dropdown -->
      <div class="stage-item open" id="stage-2-item">
        <div class="stage-header" onclick="toggleStageAccordion('stage-2-item')">
          <div class="stage-title">
            <span class="stage-icon">▶</span>
            <span>Stage 2: Uber H3 Spatial Clustering</span>
          </div>
          <span class="stage-badge badge-s2" id="stage-2-badge">-- clustered</span>
        </div>
        <div class="stage-content" id="stage-2-content">
          <div style="color:#8b949e;">Clustering at resolution 7 with dynamic expansion...</div>
        </div>
      </div>

      <!-- Stage 3: OSRM Road Networks (95% Opacity) Dropdown -->
      <div class="stage-item open" id="stage-3-item">
        <div class="stage-header" onclick="toggleStageAccordion('stage-3-item')">
          <div class="stage-title">
            <span class="stage-icon">▶</span>
            <span>Stage 3: OSRM Road Networks (95% Opacity)</span>
          </div>
          <span class="stage-badge badge-s3" id="stage-3-badge">Best 5</span>
        </div>
        <div class="stage-content" id="stage-3-content">
          <div style="color:#8b949e;">Mapping turn-by-turn road pathways...</div>
        </div>
      </div>

      <!-- Minimal Toggles Bar -->
      <div class="minimal-toggles">
        <button class="min-toggle-btn active" id="toggle-roads-btn" onclick="toggleMapFeature('roads')">
          <span>Roads (95%)</span>
          <span class="min-toggle-dot"></span>
        </button>
        <button class="min-toggle-btn active" id="toggle-h3-btn" onclick="toggleMapFeature('h3')">
          <span>H3 Cluster</span>
          <span class="min-toggle-dot"></span>
        </button>
        <button class="min-toggle-btn active" id="toggle-hover-btn" onclick="toggleMapFeature('hover')">
          <span>Adjoint Hover</span>
          <span class="min-toggle-dot"></span>
        </button>
      </div>

      <!-- Best 5 Color Legend -->
      <div class="mac-legend">
        <div style="color:#8b949e; font-weight:700; text-transform:uppercase;">Best 5 Networks &bull; Color Index</div>
        <div class="legend-row">
          <div class="legend-chip"><div class="legend-color" style="background:#3fb950"></div><span>#1 Primary</span></div>
          <div class="legend-chip"><div class="legend-color" style="background:#58a6ff"></div><span>#2 Secondary</span></div>
          <div class="legend-chip"><div class="legend-color" style="background:#bc8cff"></div><span>#3 Tertiary</span></div>
          <div class="legend-chip"><div class="legend-color" style="background:#d29922"></div><span>#4 Alternate</span></div>
          <div class="legend-chip"><div class="legend-color" style="background:#f85149"></div><span>#5 Auxiliary</span></div>
          <div class="legend-chip"><div class="legend-color" style="background:#6e7681"></div><span>Outer</span></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Minimised Dock Icon -->
  <div class="mac-dock-icon" id="mac-dock-icon" onclick="toggleMinimiseTerminal()">
    <span>⌘</span> GIS launchpad
  </div>

  <!-- Basemap Switcher (Bottom Right) -->
  <div class="mac-style-bar">
    <button class="mac-style-btn active" id="btn-style-satellite" onclick="switchBaseStyle('satellite')">🛰️ Satellite 3D</button>
    <button class="mac-style-btn" id="btn-style-street" onclick="switchBaseStyle('street')">🗺️ Vector Street</button>
    <button class="mac-style-btn" id="btn-style-dark" onclick="switchBaseStyle('dark')">🎯 Tactical Dark</button>
  </div>

  <!-- Hover HUD Tooltip -->
  <div class="hover-hud" id="hover-hud">
    <div>HEX: <span style="color:#58a6ff; font-weight:700;" id="hud-hex">--</span></div>
    <div>RINGS: <span style="color:#58a6ff; font-weight:700;" id="hud-rings">--</span></div>
    <div>COORDS: <span style="color:#fff;" id="hud-coords">--</span></div>
  </div>

  <script>
    // Embedded Pipeline Data from Backend Generator
    const EMBEDDED_PIPELINE_DATA = __PIPELINE_DATA__;

    // URL Query Parameters (Overrides Embedded Data if Provided)
    const urlParams = new URLSearchParams(window.location.search);
    const hasUrlParams = urlParams.has('lat') && urlParams.has('lon');

    let dynamicSource = {
      hospital_id: urlParams.get('id') || (EMBEDDED_PIPELINE_DATA ? EMBEDDED_PIPELINE_DATA.source.hospital_id : 'HFR_MOCK_000124'),
      hospital_name: urlParams.get('name') || (EMBEDDED_PIPELINE_DATA ? EMBEDDED_PIPELINE_DATA.source.hospital_name : 'Vani Priya Hospital'),
      mvp_hfr_id: urlParams.get('hfr') || (EMBEDDED_PIPELINE_DATA ? EMBEDDED_PIPELINE_DATA.source.mvp_hfr_id : 'HFR_MOCK_000124'),
      latitude: hasUrlParams ? parseFloat(urlParams.get('lat')) : (EMBEDDED_PIPELINE_DATA ? EMBEDDED_PIPELINE_DATA.source.latitude : 22.5657131),
      longitude: hasUrlParams ? parseFloat(urlParams.get('lon')) : (EMBEDDED_PIPELINE_DATA ? EMBEDDED_PIPELINE_DATA.source.longitude : 88.3557301)
    };

    // State
    let map;
    let mapLoaded = false;
    let currentBaseStyle = 'satellite';
    let pipelineData = EMBEDDED_PIPELINE_DATA || null;
    let markers = [];
    let focusedHospitalId = null;

    const mapOptions = {
      roads: true,
      h3: true,
      hover: true
    };

    const STYLES = {
      satellite: {
        version: 8,
        sources: {
          'esri-satellite': {
            type: 'raster',
            tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
            tileSize: 256,
            attribution: 'Esri World Imagery'
          }
        },
        layers: [
          { id: 'satellite-layer', type: 'raster', source: 'esri-satellite' }
        ]
      },
      street: 'https://tiles.openfreemap.org/styles/liberty',
      dark: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json'
    };

    // Initialize MapLibre GL
    map = new maplibregl.Map({
      container: 'map',
      style: STYLES.satellite,
      center: [dynamicSource.longitude, dynamicSource.latitude],
      zoom: 13.2,
      pitch: 55,
      bearing: -15,
      antialias: true,
      attributionControl: false
    });

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');

    map.on('load', async () => {
      mapLoaded = true;
      initMapSourcesAndLayers();
      setupHoverEngine();

      if (pipelineData && !hasUrlParams) {
        renderLoadedPipelineData();
      } else {
        await runCascadingPipeline();
      }
    });

    // Re-Attach All Sources & Layers (Fixes Vector Street & Tactical Dark Road Persistence)
    function initMapSourcesAndLayers() {
      // 1. Hover Hexagons
      if (!map.getSource('hover-hex-src')) {
        map.addSource('hover-hex-src', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] }
        });
        map.addLayer({
          id: 'hover-hex-fill',
          type: 'fill',
          source: 'hover-hex-src',
          paint: {
            'fill-color': ['match', ['get', 'ring'], 0, '#58a6ff', 1, '#1f6feb', 2, '#bc8cff', '#58a6ff'],
            'fill-opacity': ['match', ['get', 'ring'], 0, 0.25, 1, 0.15, 2, 0.10, 0.12]
          }
        });
        map.addLayer({
          id: 'hover-hex-line',
          type: 'line',
          source: 'hover-hex-src',
          paint: {
            'line-color': '#58a6ff',
            'line-width': ['match', ['get', 'ring'], 0, 2.5, 1.5],
            'line-opacity': 0.85,
            'line-dasharray': [2, 2]
          }
        });
      }

      // 2. Reachability H3 Cluster Outline
      if (!map.getSource('reachability-cluster-src')) {
        map.addSource('reachability-cluster-src', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] }
        });
        map.addLayer({
          id: 'reachability-cluster-line',
          type: 'line',
          source: 'reachability-cluster-src',
          paint: {
            'line-color': '#3fb950',
            'line-width': 2,
            'line-dasharray': [3, 2],
            'line-opacity': 0.8
          }
        });
      }

      // 3. Road Pathways (95% Core Opacity + Outer Glow)
      if (!map.getSource('road-pathways-src')) {
        map.addSource('road-pathways-src', {
          type: 'geojson',
          data: { type: 'FeatureCollection', features: [] }
        });

        map.addLayer({
          id: 'road-pathways-glow',
          type: 'line',
          source: 'road-pathways-src',
          paint: {
            'line-color': ['get', 'color'],
            'line-width': 8,
            'line-opacity': 0.45,
            'line-blur': 4
          }
        });

        map.addLayer({
          id: 'road-pathways-core',
          type: 'line',
          source: 'road-pathways-src',
          paint: {
            'line-color': ['get', 'color'],
            'line-width': ['case', ['boolean', ['get', 'is_focused'], false], 5.5, 4.0],
            'line-opacity': 0.95 // Exact 95% opacity
          }
        });
      }

      syncVisibilities();
    }

    // Execute Sequential Cascading Pipeline
    async function runCascadingPipeline() {
      // Display Source Info
      document.getElementById('source-name-display').innerText = dynamicSource.hospital_name;
      document.getElementById('source-hfr-display').innerText = dynamicSource.mvp_hfr_id;
      document.getElementById('source-coords-display').innerText = `${dynamicSource.latitude.toFixed(4)}, ${dynamicSource.longitude.toFixed(4)}`;

      try {
        const res = await fetch('/gis/pathways', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            source: dynamicSource,
            radius_km: 60.0,
            initial_k_ring: 2,
            max_k_ring: 5,
            candidate_limit: 50,
            h3_resolution: 7
          })
        });

        pipelineData = await res.json();

        if (pipelineData.status === 'SUCCESS') {
          renderLoadedPipelineData();
        } else {
          document.getElementById('stage-1-content').innerHTML = `<div style="color:#f85149">${pipelineData.message || 'No hospital nearby.'}</div>`;
        }
      } catch (err) {
        console.error('Cascading pipeline execution error:', err);
      }
    }

    function renderLoadedPipelineData() {
      if (!pipelineData || pipelineData.status !== 'SUCCESS') return;

      dynamicSource = {
        hospital_id: pipelineData.source.hospital_id,
        hospital_name: pipelineData.source.hospital_name,
        mvp_hfr_id: pipelineData.source.mvp_hfr_id,
        latitude: pipelineData.source.latitude,
        longitude: pipelineData.source.longitude
      };

      document.getElementById('source-name-display').innerText = dynamicSource.hospital_name;
      document.getElementById('source-hfr-display').innerText = dynamicSource.mvp_hfr_id;
      document.getElementById('source-coords-display').innerText = `${dynamicSource.latitude.toFixed(4)}, ${dynamicSource.longitude.toFixed(4)}`;
      document.getElementById('source-hex-display').innerText = pipelineData.source.h3_cell;

      // Stage 1 Summary
      document.getElementById('stage-1-badge').innerText = `${pipelineData.stage_1_postgis.total_candidates_found} nodes`;
      renderStage1Content();

      // Stage 2 Summary
      document.getElementById('stage-2-badge').innerText = `${pipelineData.stage_2_h3_cluster.clustered_count} clustered (k=${pipelineData.stage_2_h3_cluster.expanded_k_ring})`;
      renderStage2Content();

      // Stage 3 Summary
      document.getElementById('stage-3-badge').innerText = `${pipelineData.stage_3_road_matrix.best_5_networks.length} Best Corridors`;
      renderStage3Content();

      // Fly to source
      map.flyTo({
        center: [dynamicSource.longitude, dynamicSource.latitude],
        zoom: 13.2,
        pitch: 55,
        speed: 1.2
      });

      // Render Map Layers
      updateMapData();
      renderMarkers();
    }

    function renderStage1Content() {
      const all = pipelineData.stage_3_road_matrix.all_pathways || [];
      const cont = document.getElementById('stage-1-content');
      cont.innerHTML = `
        <div style="color:#8b949e; margin-bottom:4px;">PostGIS Bounding Radius (60km) &bull; Total ${all.length} authentic facilities:</div>
        ${all.map(c => `
          <div style="display:flex; justify-content:space-between; padding:2px 0;">
            <span style="color:#f0f6fc; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:320px;">${c.hospital_name}</span>
            <span style="color:#58a6ff;">${c.mvp_hfr_id}</span>
          </div>
        `).join('')}
      `;
    }

    function renderStage2Content() {
      const clustered = (pipelineData.stage_3_road_matrix.all_pathways || []).filter(p => p.in_h3_cluster);
      const cont = document.getElementById('stage-2-content');
      cont.innerHTML = `
        <div style="color:#8b949e; margin-bottom:4px;">Uber H3 (Resolution 7, Level k=${pipelineData.stage_2_h3_cluster.expanded_k_ring}) &bull; ${clustered.length} clustered:</div>
        ${clustered.map(c => `
          <div style="display:flex; justify-content:space-between; padding:2px 0;">
            <span style="color:#f0f6fc;">${c.hospital_name}</span>
            <span style="color:#3fb950;">Hex: ${c.h3_cell} (Ring ${c.h3_grid_distance})</span>
          </div>
        `).join('')}
      `;
    }

    function renderStage3Content() {
      const best5 = pipelineData.stage_3_road_matrix.best_5_networks || [];
      const cont = document.getElementById('stage-3-content');
      cont.innerHTML = `
        <div style="color:#8b949e; margin-bottom:4px;">Best 5 Feasible Road Corridors:</div>
        ${best5.map(c => {
          const isFoc = (focusedHospitalId === c.hospital_id);
          return `
            <div class="corridor-row ${isFoc ? 'active' : ''}" onclick="focusCorridor('${c.hospital_id}')">
              <div style="display:flex; align-items:center; gap:6px;">
                <span class="corridor-rank" style="background:${c.color}">#${c.rank}</span>
                <span style="color:#f0f6fc; font-weight:600;">${c.hospital_name}</span>
              </div>
              <div style="display:flex; gap:8px;">
                <span style="color:#58a6ff;">⏱️ ${c.duration_minutes}m</span>
                <span style="color:#c9d1d9;">📍 ${c.distance_km}km</span>
              </div>
            </div>
          `;
        }).join('')}
      `;
    }

    function updateMapData() {
      if (!mapLoaded || !pipelineData) return;

      // 1. H3 Cluster Footprint Outline
      if (pipelineData.stage_2_h3_cluster.h3_cluster_footprint && map.getSource('reachability-cluster-src')) {
        map.getSource('reachability-cluster-src').setData(pipelineData.stage_2_h3_cluster.h3_cluster_footprint);
      }

      // 2. Road Pathways Features
      const pathways = pipelineData.stage_3_road_matrix.all_pathways || [];
      const features = [];

      pathways.forEach(p => {
        if (mapOptions.h3 && !p.in_h3_cluster) return;

        const isFocused = (focusedHospitalId === p.hospital_id);
        if (p.route_geometry && p.route_geometry.coordinates) {
          features.push({
            type: 'Feature',
            properties: {
              hospital_id: p.hospital_id,
              rank: p.rank,
              color: p.color,
              distance_km: p.distance_km,
              duration_minutes: p.duration_minutes,
              is_focused: isFocused
            },
            geometry: p.route_geometry
          });
        }
      });

      if (map.getSource('road-pathways-src')) {
        map.getSource('road-pathways-src').setData({
          type: 'FeatureCollection',
          features: features
        });
      }
    }

    function renderMarkers() {
      markers.forEach(m => m.remove());
      markers = [];

      // Source Marker
      const srcEl = document.createElement('div');
      srcEl.className = 'marker-pin pin-source';
      srcEl.innerHTML = `<svg width="10" height="10" fill="#fff" viewBox="0 0 24 24"><path d="M19 10.5h-5.5V5h-3v5.5H5v3h5.5V19h3v-5.5H19v-3z"/></svg>`;
      
      const srcMarker = new maplibregl.Marker({ element: srcEl })
        .setLngLat([dynamicSource.longitude, dynamicSource.latitude])
        .setPopup(new maplibregl.Popup({ offset: 14 }).setHTML(`
          <b>[SOURCE NODE]</b><br>
          ${dynamicSource.hospital_name}<br>
          HFR: ${dynamicSource.mvp_hfr_id}
        `))
        .addTo(map);
      markers.push(srcMarker);

      // Candidate Markers
      const pathways = pipelineData.stage_3_road_matrix.all_pathways || [];
      pathways.forEach(p => {
        if (mapOptions.h3 && !p.in_h3_cluster) return;

        const el = document.createElement('div');
        const pinClass = p.rank <= 5 ? `pin-rank${p.rank}` : 'pin-other';
        el.className = `marker-pin ${pinClass}`;
        el.innerHTML = `<svg width="9" height="9" fill="#fff" viewBox="0 0 24 24"><path d="M19 10.5h-5.5V5h-3v5.5H5v3h5.5V19h3v-5.5H19v-3z"/></svg>`;

        const marker = new maplibregl.Marker({ element: el })
          .setLngLat([p.coordinates.lon, p.coordinates.lat])
          .setPopup(new maplibregl.Popup({ offset: 14 }).setHTML(`
            <b>#${p.rank} ${p.hospital_name}</b><br>
            Distance: ${p.distance_km} km<br>
            Duration: ${p.duration_minutes} min<br>
            Hex: ${p.h3_cell} (Ring ${p.h3_grid_distance})
          `))
          .addTo(map);

        el.onclick = () => focusCorridor(p.hospital_id);
        markers.push(marker);
      });
    }

    function focusCorridor(hospitalId) {
      focusedHospitalId = hospitalId;
      const all = pipelineData.stage_3_road_matrix.all_pathways || [];
      const match = all.find(p => p.hospital_id === hospitalId);

      updateMapData();
      renderStage3Content();

      if (match) {
        map.flyTo({
          center: [match.coordinates.lon, match.coordinates.lat],
          zoom: 14,
          pitch: 58,
          speed: 1.2
        });
      }
    }

    // Toggle Map Features
    function toggleMapFeature(type) {
      mapOptions[type] = !mapOptions[type];
      const btn = document.getElementById(`toggle-${type}-btn`);
      if (btn) btn.classList.toggle('active', mapOptions[type]);

      if (type === 'h3') {
        updateMapData();
        renderMarkers();
      } else {
        syncVisibilities();
      }
    }

    function syncVisibilities() {
      // 1. Roads (95% Opacity)
      const roadVis = mapOptions.roads ? 'visible' : 'none';
      if (map.getLayer('road-pathways-core')) map.setLayoutProperty('road-pathways-core', 'visibility', roadVis);
      if (map.getLayer('road-pathways-glow')) map.setLayoutProperty('road-pathways-glow', 'visibility', roadVis);

      // 2. H3 Cluster Outline
      const h3Vis = mapOptions.h3 ? 'visible' : 'none';
      if (map.getLayer('reachability-cluster-line')) map.setLayoutProperty('reachability-cluster-line', 'visibility', h3Vis);

      // 3. Hover Hexagons
      const hoverVis = mapOptions.hover ? 'visible' : 'none';
      if (map.getLayer('hover-hex-fill')) map.setLayoutProperty('hover-hex-fill', 'visibility', hoverVis);
      if (map.getLayer('hover-hex-line')) map.setLayoutProperty('hover-hex-line', 'visibility', hoverVis);
    }

    // Switch Base Map Style (Re-Attaches Layers Seamlessly Across Styles)
    function switchBaseStyle(type) {
      if (type === currentBaseStyle) return;
      currentBaseStyle = type;

      document.querySelectorAll('.mac-style-btn').forEach(b => b.classList.remove('active'));
      document.getElementById(`btn-style-${type}`).classList.add('active');

      map.setStyle(STYLES[type]);

      map.once('style.load', () => {
        initMapSourcesAndLayers();
        updateMapData();
        renderMarkers();
      });
    }

    // Accordion Toggle
    function toggleStageAccordion(stageId) {
      const item = document.getElementById(stageId);
      if (item) item.classList.toggle('open');
    }

    // Terminal Window Controls (Minimise to Dock Icon)
    function toggleMinimiseTerminal() {
      const win = document.getElementById('mac-terminal-window');
      const dock = document.getElementById('mac-dock-icon');
      win.classList.toggle('minimised');
      dock.classList.toggle('visible', win.classList.contains('minimised'));
    }

    function toggleExpandTerminal() {
      const win = document.getElementById('mac-terminal-window');
      if (win.style.maxHeight === '90vh') {
        win.style.maxHeight = '520px';
        win.style.width = '560px';
      } else {
        win.style.maxHeight = '90vh';
        win.style.width = '680px';
      }
    }

    function resetTerminalView() {
      focusedHospitalId = null;
      map.flyTo({
        center: [dynamicSource.longitude, dynamicSource.latitude],
        zoom: 13.2,
        pitch: 55,
        bearing: -15,
        speed: 1.2
      });
      updateMapData();
      renderStage3Content();
    }

    // Hover Engine
    function setupHoverEngine() {
      let lastHex = null;
      const hoverHud = document.getElementById('hover-hud');

      map.on('mousemove', (e) => {
        if (!mapOptions.hover) {
          hoverHud.classList.remove('visible');
          return;
        }

        const lat = e.lngLat.lat;
        const lon = e.lngLat.lng;

        if (typeof h3 === 'undefined') return;

        const currentHex = h3.latLngToCell(lat, lon, 7);

        if (currentHex !== lastHex) {
          lastHex = currentHex;
          const diskCells = h3.gridDisk(currentHex, 2);
          const features = [];

          for (const cell of diskCells) {
            const ringDist = h3.gridDistance(currentHex, cell);
            const boundary = h3.cellToBoundary(cell);
            const coords = boundary.map(pt => [pt[1], pt[0]]);
            if (coords.length > 0) coords.push(coords[0]);

            features.push({
              type: 'Feature',
              properties: {
                h3_index: cell,
                ring: ringDist,
                is_center: (cell == currentHex)
              },
              geometry: {
                type: 'Polygon',
                coordinates: [coords]
              }
            });
          }

          if (map.getSource('hover-hex-src')) {
            map.getSource('hover-hex-src').setData({
              type: 'FeatureCollection',
              features: features
            });
          }

          document.getElementById('hud-hex').innerText = currentHex;
          document.getElementById('hud-rings').innerText = `k=0..2 (${features.length} cells)`;
          document.getElementById('hud-coords').innerText = `${lat.toFixed(4)}, ${lon.toFixed(4)}`;
          hoverHud.classList.add('visible');
        }
      });

      map.on('mouseout', () => {
        hoverHud.classList.remove('visible');
      });
    }
  </script>
</body>
</html>
"""

def generate_route_map_html(pipeline_data: Dict[str, Any] | None = None) -> str:
    """
    Generates standalone Mac Terminal GIS launchpad HTML with embedded pipeline data.
    """
    html = MAC_TERMINAL_TEMPLATE
    data_json = json.dumps(pipeline_data) if pipeline_data else "null"
    return html.replace("__PIPELINE_DATA__", data_json)

def save_route_map_file(pipeline_data: Dict[str, Any] | None = None, file_path: Optional[str] = None) -> str:
    """
    Writes the dynamically generated route map HTML to disk.
    """
    if not file_path:
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "route_map.html")
    html_content = generate_route_map_html(pipeline_data)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    return file_path