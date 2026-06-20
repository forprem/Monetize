import { renderMap as bizRenderMap } from './market-intelligence.js';
import { colorForScore, getCoord } from '../platform/runtime-state.js';

// Cache ZIP boundary payloads fetched from backend endpoint.
const ZIP_BOUNDARIES = new Map();

async function loadBoundaryForZip(apiFetch, zipCode) {
  if (!apiFetch || !zipCode) return null;
  if (ZIP_BOUNDARIES.has(zipCode)) {
    return ZIP_BOUNDARIES.get(zipCode);
  }

  try {
    const payload = await apiFetch(`/map/boundary/${zipCode}`);
    const boundary = payload?.type === 'FeatureCollection' ? payload : null;
    ZIP_BOUNDARIES.set(zipCode, boundary);
    return boundary;
  } catch (err) {
    ZIP_BOUNDARIES.set(zipCode, null);
    return null;
  }
}


function resolveCoord(record, getCoordFallback) {
  if (record && Number.isFinite(record.lat) && Number.isFinite(record.lon)) {
    return { lat: record.lat, lon: record.lon };
  }
  return getCoordFallback(record?.zip_code || '');
}

function demographicScore(summary) {
  const normalizedPopulation = Math.min(100, (summary.population_total / 30000) * 100);
  const normalizedIncome = Math.min(100, (summary.median_income / 120000) * 100);
  return normalizedPopulation * 0.6 + normalizedIncome * 0.4;
}

function activeLayerMode(elements, state) {
  return state.layerMode || document.querySelector('#layer-mode-chips .chip.active')?.dataset?.layerMode || 'composite';
}

function clearLegacyMapAnnotations(leafletMap) {
  const panes = leafletMap.getPanes?.();
  if (panes?.tooltipPane) panes.tooltipPane.innerHTML = '';
  if (panes?.popupPane) panes.popupPane.innerHTML = '';

  const mapRoot = leafletMap.getContainer();
  mapRoot.querySelectorAll('.leaflet-tooltip, .leaflet-popup, .zip-map-popup, .zip-map-popup-card').forEach((node) => node.remove());
}

function buildLayerOverlay(summary, layerMode) {
  // Safe getters with defaults
  const getSafeNumber = (val, def = 0) => Number.isFinite(val) ? val : def;
  
  const layerHeadline =
    layerMode === 'signal'
      ? `Network Signal: ${getSafeNumber(summary.signal_score, 60).toFixed(1)}`
      : layerMode === 'healthcare'
        ? `Healthcare: ${getSafeNumber(summary.healthcare_access_score, 50).toFixed(1)}`
        : layerMode === 'demographics'
          ? `Demographics: ${demographicScore(summary).toFixed(1)}`
          : layerMode === 'real-estate'
            ? `Real Estate: ${(getSafeNumber(summary.home_ownership_rate, 65) + getSafeNumber(summary.median_home_value, 350000) / 100000).toFixed(1)}`
            : `Composite: ${getSafeNumber(summary.overall_score, 70).toFixed(1)}`;

  const formatInt = (value) => Number(value || 0).toLocaleString();
  const formatCurrency = (value) => `$${Number(value || 0).toLocaleString()}`;
  const estimatedPatientBurden = Number.isFinite(summary.estimated_patient_burden)
    ? summary.estimated_patient_burden
    : Math.round(
      (summary.age_0_17 || 0) * 0.06
      + (summary.age_18_34 || 0) * 0.08
      + (summary.age_35_64 || 0) * 0.18
      + (summary.age_65_plus || 0) * 0.35,
    );

  let rows = [];
  if (layerMode === 'signal') {
    rows = [
      `Internet Score: ${getSafeNumber(summary.consistency_score, 60).toFixed(1)}`,
      `Signal Score: ${getSafeNumber(summary.signal_score, 60).toFixed(1)}`,
      `Download: ${getSafeNumber(summary.avg_download_mbps, 50).toFixed(1)} Mbps`,
      `Upload: ${getSafeNumber(summary.avg_upload_mbps, 10).toFixed(1)} Mbps`,
      `Latency: ${getSafeNumber(summary.avg_latency_ms, 25).toFixed(1)} ms`,
      `Providers: ${summary.provider_count || 0}`,
    ];
  } else if (layerMode === 'healthcare') {
    rows = [
      `Healthcare Score: ${getSafeNumber(summary.healthcare_access_score, 50).toFixed(1)}`,
      `Hospitals: ${summary.hospital_count || 0}`,
      `Estimated Patients: ${formatInt(estimatedPatientBurden)}`,
      `Chronic Burden: ${Number.isFinite(summary.chronic_burden_score) ? summary.chronic_burden_score.toFixed(1) : '--'}`,
      `Chronic Patients: ${Number.isFinite(summary.estimated_chronic_patients) ? formatInt(summary.estimated_chronic_patients) : '--'}`,
      `Diabetes: ${Number.isFinite(summary.diabetes_prevalence_pct) ? `${summary.diabetes_prevalence_pct.toFixed(1)}%` : '--'}`,
      `Hypertension: ${Number.isFinite(summary.hypertension_prevalence_pct) ? `${summary.hypertension_prevalence_pct.toFixed(1)}%` : '--'}`,
      `Population: ${formatInt(summary.population_total)}`,
      `Age 65+: ${formatInt(summary.age_65_plus)}`,
    ];
  } else if (layerMode === 'demographics') {
    rows = [
      `Population: ${formatInt(summary.population_total)}`,
      `Median Income: ${formatCurrency(summary.median_income)}`,
      `Age 0-17: ${formatInt(summary.age_0_17)}`,
      `Age 18-34: ${formatInt(summary.age_18_34)}`,
      `Age 35-64: ${formatInt(summary.age_35_64)}`,
      `Age 65+: ${formatInt(summary.age_65_plus)}`,
    ];
  } else if (layerMode === 'real-estate') {
    rows = [
      `Home Ownership: ${getSafeNumber(summary.home_ownership_rate, 65).toFixed(1)}%`,
      `Vacancy Rate: ${getSafeNumber(summary.vacancy_rate, 10).toFixed(1)}%`,
      `Median Home Value: ${formatCurrency(getSafeNumber(summary.median_home_value, 350000))}`,
      `Avg Household Size: ${getSafeNumber(summary.avg_household_size, 2.5).toFixed(2)} persons`,
      `Population: ${formatInt(summary.population_total)}`,
      `Median Income: ${formatCurrency(summary.median_income)}`,
    ];
  } else {
    rows = [
      `Overall: ${getSafeNumber(summary.overall_score, 70).toFixed(1)}`,
      `Market: ${getSafeNumber(summary.market_attractiveness_score, 75).toFixed(1)}`,
      `Opportunity: ${getSafeNumber(summary.network_opportunity_score, 50).toFixed(1)}`,
      `Internet Score: ${getSafeNumber(summary.consistency_score, 60).toFixed(1)}`,
      `Healthcare: ${getSafeNumber(summary.healthcare_access_score, 50).toFixed(1)}`,
      `Population: ${formatInt(summary.population_total)}`,
    ];
  }

  return `
    <div class="zip-map-data-panel">
      <div class="zip-map-data-head">
        <strong>${summary.zip_code}</strong>
        <span>${layerHeadline}</span>
      </div>
      <div class="zip-map-data-grid">
        ${rows.map((row) => `<span>${row}</span>`).join('')}
      </div>
    </div>
  `;
}

export function createDashboardMapController(context) {
  const { elements, state, mountEmpty, apiFetch } = context;

  let leafletMap = null;
  let markersGroup = null;
  let detailMarker = null;
  let detailOverlay = null;
  let boundaryLayer = null;
  let lastSummary = null;

  if (window.L && elements.mapContainer) {
    leafletMap = window.L.map(elements.mapContainer, {
      center: [39.5, -98.35],
      zoom: 4,
      zoomControl: true,
      scrollWheelZoom: true,
    });

    window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(leafletMap);

    markersGroup = window.L.layerGroup().addTo(leafletMap);
  }

  const mapDeps = { mountEmpty, colorForScore, getCoord, leafletMap, markersGroup };

  function syncLeafletSize() {
    if (!leafletMap) return;
    // If map booted while container was hidden, Leaflet keeps stale dimensions
    // until invalidateSize() is called after the container is visible.
    requestAnimationFrame(() => {
      leafletMap.invalidateSize(false);
      setTimeout(() => leafletMap.invalidateSize(false), 120);
    });
  }

  function showZipSummaryOnMap(summary) {
    if (!leafletMap || !markersGroup || !summary) return;
    lastSummary = summary;

    // Ensure stale Leaflet tooltips/popups do not overlap the custom chip overlay.
    clearLegacyMapAnnotations(leafletMap);
    leafletMap.getContainer().querySelectorAll('.zip-inline-card').forEach((node) => {
      if (node !== detailOverlay) node.remove();
    });

    const coord = resolveCoord(summary, getCoord);

    loadBoundaryForZip(apiFetch, summary.zip_code).then((boundary) => {
      if (!leafletMap) return;
      if (boundaryLayer && leafletMap.hasLayer(boundaryLayer)) {
        leafletMap.removeLayer(boundaryLayer);
      }

      if (boundary) {
        boundaryLayer = window.L.geoJSON(boundary, {
          style: {
            color: '#2f80ed',
            weight: 2,
            opacity: 0.8,
            fillOpacity: 0,
          },
        }).addTo(leafletMap);
      } else {
        boundaryLayer = null;
      }
    });

    const popupHtml = buildLayerOverlay(summary, activeLayerMode(elements, state));

    if (detailMarker && markersGroup.hasLayer(detailMarker)) {
      markersGroup.removeLayer(detailMarker);
    }

    detailMarker = window.L.circleMarker([coord.lat, coord.lon], {
      radius: 13,
      fillColor: '#2f80ed',
      color: '#ffffff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.95,
    }).addTo(markersGroup);

    if (!detailOverlay) {
      detailOverlay = document.createElement('div');
      detailOverlay.className = 'zip-inline-card';
      leafletMap.getContainer().appendChild(detailOverlay);
    }

    detailOverlay.innerHTML = popupHtml;
    detailOverlay.classList.remove('hidden');

    const positionOverlay = (point) => {
      detailOverlay.style.left = `${Math.round(point.x)}px`;
      detailOverlay.style.top = `${Math.round(point.y)}px`;
    };

    const point = leafletMap.latLngToContainerPoint([coord.lat, coord.lon]);
    positionOverlay(point);

    leafletMap.panTo([coord.lat, coord.lon], { animate: true });

    const syncOverlayPosition = () => {
      if (!detailOverlay) return;
      const p = leafletMap.latLngToContainerPoint([coord.lat, coord.lon]);
      positionOverlay(p);
    };

    leafletMap.off('move', syncOverlayPosition);
    leafletMap.on('move', syncOverlayPosition);
  }

  function renderMap(compareResults, focusedZip) {
    mapDeps.leafletMap = leafletMap;
    mapDeps.markersGroup = markersGroup;
    syncLeafletSize();
    bizRenderMap(elements, state, compareResults, focusedZip, mapDeps);

    // Keep the focused ZIP overlay in sync with layer switches and map redraws.
    if (lastSummary && (!focusedZip || lastSummary.zip_code === focusedZip)) {
      showZipSummaryOnMap(lastSummary);
    }
  }

  function zoomToZip(zip) {
    if (!leafletMap) return;
    syncLeafletSize();
    const coord = getCoord(zip);
    leafletMap.setView([coord.lat, coord.lon], 12, { animate: true });
  }

  return {
    renderMap,
    zoomToZip,
    showZipSummaryOnMap,
    mapDeps,
    leafletMap,
    markersGroup,
    state,
  };
}
