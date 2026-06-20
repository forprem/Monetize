export async function runDashboardRefresh(context) {
  const {
    configController,
    setStatus,
    loaders,
    renderers,
    state,
    elements,
    showToast,
    mountEmpty,
    mapDeps,
    defaultZips,
  } = context;

  configController.saveConfigIfEnabled();
  setStatus('idle', 'Loading');

  try {
    const { baseUrl } = configController.getConfig();
    const baseLabel = baseUrl || 'no-base-url';

    const compareInputZips = elements.compareInput.value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
    const comparisonZips = compareInputZips.length ? compareInputZips : defaultZips;
    const selectedZip = elements.zipInput.value.trim();

    const comparePromise = comparisonZips.length
      ? loaders.loadComparison(comparisonZips)
      : Promise.resolve({ results: [] });
    const usagePromise = loaders.loadUsage().catch(() => null);
    const exportsPromise = loaders.loadExports().catch(() => ({ items: [] }));
    const auditPromise = loaders.loadAudit();
    const layersPromise = loaders.loadLayers();
    const zipPromise = selectedZip
      ? loaders.loadZipSummary(selectedZip)
      : Promise.resolve(null);
    const keysPromise = loaders.loadApiKeys();
    const usersPromise = loaders.loadAuthUsers();

    const [compare, usage, exportsPage, auditPage] = await Promise.all([
      comparePromise,
      usagePromise,
      exportsPromise,
      auditPromise,
      layersPromise,
      zipPromise,
      keysPromise,
      usersPromise,
    ]);

    renderers.renderMetrics({ usage, exportsPage, auditPage, compare });
    if (!state.focusedZip && compare?.results?.length) {
      state.focusedZip = compare.results[0].zip_code;
    }

    renderers.renderMap(state.compareResults, state.focusedZip, mapDeps);
    setStatus('ok', `Connected: ${baseLabel}`);
    showToast('Dashboard refreshed', 'ok');
  } catch (error) {
    setStatus('error', 'Error');
    showToast(error.message, 'error');
    mountEmpty(elements.metricCards, error.message);
  }
}
