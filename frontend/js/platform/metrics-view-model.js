function metricCard(template, label, value, note) {
  const fragment = template.content.cloneNode(true);
  fragment.querySelector('.metric-label').textContent = label;
  fragment.querySelector('.metric-value').textContent = value;
  fragment.querySelector('.metric-note').textContent = note;
  return fragment;
}

export function renderDashboardMetrics(elements, metricTemplate, payload, formatCompact) {
  const { usage, exportsPage, auditPage, compare } = payload;

  elements.metricCards.innerHTML = '';
  elements.metricCards.appendChild(
    metricCard(
      metricTemplate,
      'Requests',
      usage ? String(formatCompact(usage.requests_this_month)) : '--',
      'This month'
    )
  );
  elements.metricCards.appendChild(
    metricCard(
      metricTemplate,
      'Exports',
      usage ? String(formatCompact(usage.exports_this_month)) : '--',
      'This month'
    )
  );
  elements.metricCards.appendChild(
    metricCard(
      metricTemplate,
      'Queued Jobs',
      exportsPage ? String(exportsPage.items.filter((item) => item.status === 'queued').length) : '--',
      'Awaiting processing'
    )
  );
  elements.metricCards.appendChild(
    metricCard(metricTemplate, 'Audit Events', auditPage ? String(auditPage.returned) : '--', 'Latest page')
  );

  if (compare?.results?.length) {
    const top = [...compare.results].sort((a, b) => b.overall_score - a.overall_score)[0];
    elements.metricCards.appendChild(
      metricCard(metricTemplate, 'Top ZIP', top.zip_code, `${top.overall_score.toFixed(1)} overall`)
    );
  }
}
