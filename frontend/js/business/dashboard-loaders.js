// Loader handlers: API reads + business rendering updates for each dashboard data surface.
import {
  renderCompare,
  renderHeroBoard,
  renderLayers,
  renderMap,
  renderZipSummary,
} from './market-intelligence.js';
import { renderExports } from './delivery-operations.js';
import { renderActivity, renderAudit } from './governance-monitoring.js';
import { renderApiKeys, renderAuthUsers } from './access-management.js';
import {
  fetchComparison,
  fetchLayers,
  fetchZipSummary,
} from './services/market-intelligence-service.js';
import { fetchExportsPage } from './services/delivery-operations-service.js';
import { fetchAuditPage } from './services/governance-monitoring-service.js';
import { fetchApiKeys, fetchAuthUsers } from './services/access-management-service.js';

export function createDashboardLoaders(context) {
  const {
    elements,
    state,
    apiFetch,
    mountEmpty,
    formatCompact,
    formatDate,
    maskApiKey,
    updatePager,
    mapDeps,
  } = context;

  async function loadLayers() {
    const layers = await fetchLayers(apiFetch);
    renderLayers(elements, layers, mountEmpty);
    return layers;
  }

  async function loadZipSummary(zip) {
    const summary = await fetchZipSummary(apiFetch, zip);
    state.focusedZipSummary = summary;
    renderZipSummary(elements, summary, formatCompact);
    return summary;
  }

  async function loadComparison(zips) {
    const compare = await fetchComparison(apiFetch, zips);
    renderCompare(elements, compare, mountEmpty);
    renderHeroBoard(elements, compare.results, formatCompact);
    state.compareResults = compare.results;
    renderMap(elements, state, state.compareResults, state.focusedZip, mapDeps);
    return compare;
  }

  async function loadExports() {
    const page = await fetchExportsPage(apiFetch, elements, state);
    state.pagination.exports.returned = page.returned || 0;
    updatePager('exports');
    renderExports(elements, state, page, mountEmpty, formatDate);
    return page;
  }

  async function loadUsage() {
    return apiFetch('/usage/me');
  }

  async function loadAudit() {
    try {
      const page = await fetchAuditPage(apiFetch, elements, state);
      state.pagination.audit.returned = page.returned || 0;
      updatePager('audit');
      renderAudit(elements, page, mountEmpty, formatDate);
      renderActivity(elements, state, page.items || [], mountEmpty, formatDate);
      return page;
    } catch (error) {
      state.pagination.audit.returned = 0;
      updatePager('audit');
      mountEmpty(elements.auditList, error.message);
      mountEmpty(elements.activityList, error.message);
      return { items: [], returned: 0 };
    }
  }

  async function loadApiKeys() {
    try {
      const items = await fetchApiKeys(apiFetch, elements);
      renderApiKeys(elements, items, mountEmpty, maskApiKey, formatDate);
      return items;
    } catch (error) {
      mountEmpty(elements.apiKeysList, error.message);
      return [];
    }
  }

  async function loadAuthUsers() {
    try {
      const items = await fetchAuthUsers(apiFetch, elements);
      renderAuthUsers(elements, items, mountEmpty);
      return items;
    } catch (error) {
      mountEmpty(elements.authUsersList, error.message);
      return [];
    }
  }

  return {
    loadLayers,
    loadZipSummary,
    loadComparison,
    loadExports,
    loadUsage,
    loadAudit,
    loadApiKeys,
    loadAuthUsers,
  };
}
