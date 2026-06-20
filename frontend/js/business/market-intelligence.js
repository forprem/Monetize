export function scoreForLayer(state, row) {
  if (state.layerMode === 'signal') {
    return row.signal_score;
  }
  if (state.layerMode === 'healthcare') {
    return row.healthcare_access_score;
  }
  if (state.layerMode === 'demographics') {
    const normalizedPopulation = Math.min(100, (row.population_total / 30000) * 100);
    const normalizedIncome = Math.min(100, (row.median_income / 120000) * 100);
    return normalizedPopulation * 0.6 + normalizedIncome * 0.4;
  }
  if (state.layerMode === 'real-estate') {
    const ownershipScore = row.home_ownership_rate || 0;
    const vacancyScore = 100 - (row.vacancy_rate || 0);
    const valueNormalized = Math.min(100, ((row.median_home_value || 350000) / 500000) * 100);
    return ownershipScore * 0.4 + vacancyScore * 0.4 + valueNormalized * 0.2;
  }
  return row.overall_score;
}

export function currentLayerLabel(state) {
  if (state.layerMode === 'signal') return 'Network Signal';
  if (state.layerMode === 'healthcare') return 'Healthcare';
  if (state.layerMode === 'demographics') return 'Demographics';
  if (state.layerMode === 'real-estate') return 'Real Estate';
  return 'Composite';
}

export function renderHeroBoard(elements, rows, formatCompact) {
  elements.heroBoard.innerHTML = '<div class="board-grid"></div>';
  const grid = elements.heroBoard.querySelector('.board-grid');
  rows.forEach((row) => {
    const card = document.createElement('article');
    card.className = 'board-card';
    card.innerHTML = `
      <span class="eyebrow">ZIP ${row.zip_code}</span>
      <strong class="board-score">${row.overall_score.toFixed(1)}</strong>
      <span>${row.market_attractiveness_score.toFixed(1)} market / ${row.signal_score.toFixed(1)} signal</span>
      <span class="muted">${formatCompact(row.population_total)} people</span>
    `;
    grid.appendChild(card);
  });
}

export function renderLayers(elements, layers, mountEmpty) {
  if (!layers.length) {
    mountEmpty(elements.layersList, 'No layers available.');
    return;
  }
  elements.layersList.innerHTML = layers
    .map(
      (layer) => `
        <article class="layer-item">
          <p class="eyebrow">${layer.code}</p>
          <strong>${layer.name}</strong>
        </article>
      `,
    )
    .join('');
}

export function renderZipSummary(elements, summary, formatCompact) {
  const totalAge =
    (summary.age_0_17 || 0)
    + (summary.age_18_34 || 0)
    + (summary.age_35_64 || 0)
    + (summary.age_65_plus || 0);

  const pct = (value) => {
    if (!totalAge) return '0.0%';
    return `${((value / totalAge) * 100).toFixed(1)}%`;
  };

  const getSafe = (val, def = 0) => Number.isFinite(val) ? val : def;
  const estimatedPatientBurden = Number.isFinite(summary.estimated_patient_burden)
    ? summary.estimated_patient_burden
    : Math.round(
      (summary.age_0_17 || 0) * 0.06
      + (summary.age_18_34 || 0) * 0.08
      + (summary.age_35_64 || 0) * 0.18
      + (summary.age_65_plus || 0) * 0.35,
    );

  const fields = [
    ['ZIP Code', summary.zip_code],
    ['Latitude', Number.isFinite(summary.lat) ? summary.lat.toFixed(5) : '--'],
    ['Longitude', Number.isFinite(summary.lon) ? summary.lon.toFixed(5) : '--'],
    ['Overall Score', getSafe(summary.overall_score, 70).toFixed(1)],
    ['Signal Score', getSafe(summary.signal_score, 60).toFixed(1)],
    ['Healthcare Access', getSafe(summary.healthcare_access_score, 50).toFixed(1)],
    ['Market Attractiveness', getSafe(summary.market_attractiveness_score, 75).toFixed(1)],
    ['Network Opportunity', getSafe(summary.network_opportunity_score, 50).toFixed(1)],
    ['Download Mbps', getSafe(summary.avg_download_mbps, 50).toFixed(1)],
    ['Upload Mbps', getSafe(summary.avg_upload_mbps, 10).toFixed(1)],
    ['Latency', `${getSafe(summary.avg_latency_ms, 25).toFixed(1)} ms`],
    ['Internet Score', getSafe(summary.consistency_score, 60).toFixed(1)],
    ['Provider Count', String(summary.provider_count || 0)],
    ['Hospital Count', String(summary.hospital_count || 0)],
    ['Estimated Patient Burden', formatCompact(estimatedPatientBurden)],
    ['Chronic Burden Score', Number.isFinite(summary.chronic_burden_score) ? summary.chronic_burden_score.toFixed(1) : '--'],
    ['Estimated Chronic Patients', Number.isFinite(summary.estimated_chronic_patients) ? formatCompact(summary.estimated_chronic_patients) : '--'],
    ['Diabetes Prevalence', Number.isFinite(summary.diabetes_prevalence_pct) ? `${summary.diabetes_prevalence_pct.toFixed(1)}%` : '--'],
    ['Hypertension Prevalence', Number.isFinite(summary.hypertension_prevalence_pct) ? `${summary.hypertension_prevalence_pct.toFixed(1)}%` : '--'],
    ['Obesity Prevalence', Number.isFinite(summary.obesity_prevalence_pct) ? `${summary.obesity_prevalence_pct.toFixed(1)}%` : '--'],
    ['CHD Prevalence', Number.isFinite(summary.chd_prevalence_pct) ? `${summary.chd_prevalence_pct.toFixed(1)}%` : '--'],
    ['COPD Prevalence', Number.isFinite(summary.copd_prevalence_pct) ? `${summary.copd_prevalence_pct.toFixed(1)}%` : '--'],
    ['Stroke Prevalence', Number.isFinite(summary.stroke_prevalence_pct) ? `${summary.stroke_prevalence_pct.toFixed(1)}%` : '--'],
    ['Home Ownership', `${getSafe(summary.home_ownership_rate, 65).toFixed(1)}%`],
    ['Vacancy Rate', `${getSafe(summary.vacancy_rate, 10).toFixed(1)}%`],
    ['Median Home Value', `$${formatCompact(getSafe(summary.median_home_value, 350000))}`],
    ['Avg Household Size', `${getSafe(summary.avg_household_size, 2.5).toFixed(2)} persons`],
    ['Population', formatCompact(summary.population_total)],
    ['Median Income', `$${formatCompact(summary.median_income)}`],
    ['Age 0-17', `${formatCompact(summary.age_0_17)} (${pct(summary.age_0_17)})`],
    ['Age 18-34', `${formatCompact(summary.age_18_34)} (${pct(summary.age_18_34)})`],
    ['Age 35-64', `${formatCompact(summary.age_35_64)} (${pct(summary.age_35_64)})`],
    ['Age 65+', `${formatCompact(summary.age_65_plus)} (${pct(summary.age_65_plus)})`],
    [
      'Updated At',
      summary.updated_at ? new Date(summary.updated_at).toLocaleString() : '--',
    ],
  ];

  elements.zipSummary.innerHTML = fields
    .map(
      ([label, value]) => `
        <article class="summary-item">
          <span class="summary-label">${label}</span>
          <strong class="summary-value">${value}</strong>
        </article>
      `,
    )
    .join('');
}

export function renderCompare(elements, compare, mountEmpty) {
  if (!compare.results.length) {
    mountEmpty(elements.compareResults, 'No ZIPs found.');
    return;
  }

  const getSafe = (val, def = 0) => Number.isFinite(val) ? val : def;

  const ranked = [...compare.results].sort((a, b) => b.overall_score - a.overall_score);
  elements.compareResults.innerHTML = ranked
    .map(
      (item, index) => `
        <article class="compare-item" data-zip-select="${item.zip_code}">
          <p class="eyebrow">Rank ${index + 1}</p>
          <strong>${item.zip_code}</strong>
          <span class="compare-score">${getSafe(item.overall_score, 70).toFixed(1)}</span>
          <div class="muted">Signal: ${getSafe(item.signal_score, 60).toFixed(1)} / Health: ${getSafe(item.healthcare_access_score, 50).toFixed(1)}</div>
          <div class="muted">Market: ${getSafe(item.market_attractiveness_score, 75).toFixed(1)} / Opportunity: ${getSafe(item.network_opportunity_score, 50).toFixed(1)}</div>
          <div class="muted">Download: ${getSafe(item.avg_download_mbps, 50).toFixed(1)} Mbps / Upload: ${getSafe(item.avg_upload_mbps, 10).toFixed(1)} Mbps</div>
          <div class="muted">Latency: ${getSafe(item.avg_latency_ms, 25).toFixed(1)} ms / Internet Score: ${getSafe(item.consistency_score, 60).toFixed(1)}</div>
          <div class="muted">Providers: ${item.provider_count || 0} / Hospitals: ${item.hospital_count || 0}</div>
          <div class="muted">Estimated Patients: ${(Number.isFinite(item.estimated_patient_burden) ? item.estimated_patient_burden : Math.round((item.age_0_17 || 0) * 0.06 + (item.age_18_34 || 0) * 0.08 + (item.age_35_64 || 0) * 0.18 + (item.age_65_plus || 0) * 0.35)).toLocaleString()}</div>
          <div class="muted">Chronic Burden: ${Number.isFinite(item.chronic_burden_score) ? item.chronic_burden_score.toFixed(1) : '--'} / Chronic Patients: ${Number.isFinite(item.estimated_chronic_patients) ? item.estimated_chronic_patients.toLocaleString() : '--'}</div>
          <div class="muted">Population: ${item.population_total.toLocaleString()} / Income: $${item.median_income.toLocaleString()}</div>
          <div class="muted">Ownership: ${getSafe(item.home_ownership_rate, 65).toFixed(1)}% / Vacancy: ${getSafe(item.vacancy_rate, 10).toFixed(1)}% / Home Value: $${(getSafe(item.median_home_value, 350000) / 1000).toFixed(0)}k</div>
          <div class="muted">Age 0-17: ${item.age_0_17.toLocaleString()} · Age 18-34: ${item.age_18_34.toLocaleString()} · Age 35-64: ${item.age_35_64.toLocaleString()} · Age 65+: ${item.age_65_plus.toLocaleString()}</div>
          <div class="muted">Coords: ${Number.isFinite(item.lat) ? item.lat.toFixed(4) : '--'}, ${Number.isFinite(item.lon) ? item.lon.toFixed(4) : '--'}</div>
          <div class="muted">Updated: ${item.updated_at ? new Date(item.updated_at).toLocaleString() : '--'}</div>
        </article>
      `,
    )
    .join('');
}

export function renderMap(elements, state, results, focusedZip, helpers) {
  const { colorForScore, getCoord, leafletMap, markersGroup } = helpers;

  const resolveCoord = (record, zipCode = null) => {
    if (record && Number.isFinite(record.lat) && Number.isFinite(record.lon)) {
      return { lat: record.lat, lon: record.lon };
    }
    return getCoord(zipCode || record?.zip_code || '');
  };

  if (!leafletMap || !markersGroup) return;

  // Defensive cleanup: remove any tooltip DOM from previous renders.
  leafletMap.getContainer().querySelectorAll('.leaflet-tooltip').forEach((node) => node.remove());
  leafletMap.getContainer().querySelectorAll('.zip-map-popup, .zip-map-popup-card').forEach((node) => node.remove());

  markersGroup.clearLayers();

  if (results && results.length) {
    results.forEach((row) => {
      const coord = resolveCoord(row);
      const layerScore = scoreForLayer(state, row);
      const color = colorForScore(layerScore);
      const isFocused = focusedZip && focusedZip === row.zip_code;

      const marker = window.L.circleMarker([coord.lat, coord.lon], {
        radius: isFocused ? 14 : 10,
        fillColor: color,
        color: isFocused ? '#fff' : 'rgba(255,255,255,0.35)',
        weight: isFocused ? 2.5 : 1.5,
        opacity: 1,
        fillOpacity: 0.88,
      });

      markersGroup.addLayer(marker);

    });

    if (focusedZip) {
      const focusedRow = results.find((row) => row.zip_code === focusedZip) || state.focusedZipSummary;
      const coord = resolveCoord(focusedRow, focusedZip);
      leafletMap.setView([coord.lat, coord.lon], 10, { animate: true });
    } else {
      const bounds = results.map((row) => {
        const coord = resolveCoord(row);
        return [coord.lat, coord.lon];
      });
      try { leafletMap.fitBounds(bounds, { padding: [60, 60], animate: true }); } catch (_) {}
    }

    if (elements.mapLegend) {
      const ranked = [...results].sort((a, b) => scoreForLayer(state, b) - scoreForLayer(state, a));
      elements.mapLegend.innerHTML = ranked.map((row, i) => `
        <div class="legend-row">
          <span class="dot" style="background:${colorForScore(scoreForLayer(state, row))}"></span>
          <strong>#${i + 1} ${row.zip_code}</strong>
          <span class="legend-score">${scoreForLayer(state, row).toFixed(1)}</span>
        </div>
      `).join('');
    }
  } else if (focusedZip) {
    const coord = resolveCoord(state.focusedZipSummary, focusedZip);
    const marker = window.L.circleMarker([coord.lat, coord.lon], {
      radius: 12,
      fillColor: '#5b8dee',
      color: '#fff',
      weight: 2,
      opacity: 1,
      fillOpacity: 0.9,
    });
    markersGroup.addLayer(marker);
    leafletMap.setView([coord.lat, coord.lon], 12, { animate: true });
    if (elements.mapLegend) elements.mapLegend.innerHTML = '';
  } else {
    if (elements.mapLegend) elements.mapLegend.innerHTML = '';
  }
}
