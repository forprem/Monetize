export function getFilteredActivityItems(elements, state) {
  const term = elements.activitySearch.value.trim().toLowerCase();
  return state.activityItems.filter((item) => {
    if (!term) {
      return true;
    }
    const haystack = `${item.action} ${item.endpoint} ${item.tenant_id} ${item.outcome}`.toLowerCase();
    return haystack.includes(term);
  });
}

export function renderAudit(elements, page, mountEmpty, formatDate) {
  if (!page.items.length) {
    mountEmpty(elements.auditList, 'No audit events available for this key.');
    return;
  }

  elements.auditList.innerHTML = page.items
    .map(
      (item) => `
        <article class="table-row">
          <div class="table-topline">
            <strong>${item.action}</strong>
            <span class="badge ${item.outcome}">${item.outcome}</span>
          </div>
          <div class="table-meta">${item.endpoint}</div>
          <div class="table-meta">${item.tenant_id} • ${formatDate(item.created_at)}</div>
          <div class="table-meta">${item.reason || 'No reason captured'}</div>
        </article>
      `,
    )
    .join('');
}

export function renderTenantTrend(elements, items) {
  const canvas = elements.tenantTrend;
  if (!canvas) {
    return;
  }

  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const width = Math.max(320, Math.floor(rect.width || 600));
  const height = 86;
  canvas.width = width * dpr;
  canvas.height = height * dpr;

  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);

  ctx.fillStyle = 'rgba(255, 253, 248, 0.85)';
  ctx.fillRect(0, 0, width, height);

  if (!items.length) {
    ctx.fillStyle = '#6b5b4d';
    ctx.font = '12px "IBM Plex Mono", monospace';
    ctx.fillText('No trend data', 12, 24);
    return;
  }

  const byTenant = new Map();
  items.forEach((item) => {
    byTenant.set(item.tenant_id, (byTenant.get(item.tenant_id) || 0) + 1);
  });
  const points = [...byTenant.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
  const max = Math.max(...points.map((entry) => entry[1]), 1);

  const left = 10;
  const bottom = height - 10;
  const step = (width - 20) / Math.max(points.length, 1);

  ctx.beginPath();
  points.forEach((entry, index) => {
    const x = left + index * step + step / 2;
    const y = bottom - (entry[1] / max) * (height - 26);
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.strokeStyle = '#58725c';
  ctx.lineWidth = 2;
  ctx.stroke();

  points.forEach((entry, index) => {
    const x = left + index * step + step / 2;
    const y = bottom - (entry[1] / max) * (height - 26);
    ctx.beginPath();
    ctx.arc(x, y, 3.2, 0, Math.PI * 2);
    ctx.fillStyle = '#c4862e';
    ctx.fill();
    ctx.fillStyle = '#6b5b4d';
    ctx.font = '10px "IBM Plex Mono", monospace';
    ctx.fillText(entry[0].slice(0, 7), x - 14, height - 2);
  });
}

export function renderActivity(elements, state, items, mountEmpty, formatDate) {
  state.activityItems = items || [];
  const filteredItems = getFilteredActivityItems(elements, state);

  if (!filteredItems.length) {
    mountEmpty(elements.activityList, 'No recent events to show.');
    renderTenantTrend(elements, []);
    return;
  }

  renderTenantTrend(elements, filteredItems);
  elements.activityList.innerHTML = filteredItems
    .slice(0, 10)
    .map(
      (item) => `
        <article class="table-row timeline-row">
          <div class="table-topline">
            <strong>${item.action}</strong>
            <span class="badge ${item.outcome}">${item.outcome}</span>
          </div>
          <div class="table-meta">${item.endpoint}</div>
          <div class="table-meta">${item.tenant_id} • ${formatDate(item.created_at)}</div>
        </article>
      `,
    )
    .join('');
}
