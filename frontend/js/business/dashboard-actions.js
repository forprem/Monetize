// Action handlers: form submissions and row-level admin actions (exports, API keys, compare selection).
import {
  applyExportAction,
  createExport,
  processPendingExports,
} from './services/delivery-operations-service.js';
import {
  applyApiKeyAction,
  createAuthUser,
  createApiKey,
  disableAuthUser,
  resetAuthUserPassword,
} from './services/access-management-service.js';

export function createDashboardActions(context) {
  const {
    elements,
    state,
    apiFetch,
    setStatus,
    showToast,
    mountEmpty,
    copyToClipboard,
    loaders,
    pagination,
    map,
  } = context;

  async function handleExportActionClick(event) {
    const copyButton = event.target.closest('button[data-copy-value]');
    if (copyButton) {
      await copyToClipboard(copyButton.dataset.copyValue || '', copyButton.dataset.copyLabel || 'value');
      return;
    }

    const downloadButton = event.target.closest('button[data-export-download]');
    if (downloadButton) {
      const uri = downloadButton.dataset.exportDownload;
      if (!uri) {
        showToast('No artifact URI available', 'error');
        return;
      }
      window.open(uri, '_blank', 'noopener,noreferrer');
      showToast('Opened export artifact link', 'ok');
      return;
    }

    const button = event.target.closest('button[data-export-action]');
    if (!button) return;

    const action = button.dataset.exportAction;
    const jobId = button.dataset.jobId;
    try {
      await applyExportAction(apiFetch, action, jobId);
      await loaders.loadExports();
      setStatus('ok', `Export ${action} ok`);
      showToast(`Export ${action} completed`, 'ok');
    } catch (error) {
      setStatus('error', 'Admin denied');
      showToast(error.message, 'error');
      mountEmpty(elements.exportsList, error.message);
    }
  }

  async function handleApiKeyActionClick(event) {
    const copyButton = event.target.closest('button[data-copy-value]');
    if (copyButton) {
      await copyToClipboard(copyButton.dataset.copyValue || '', copyButton.dataset.copyLabel || 'value');
      return;
    }

    const button = event.target.closest('button[data-key-action]');
    if (!button) return;

    const action = button.dataset.keyAction;
    const apiKey = button.dataset.apiKey;

    try {
      if (action === 'revoke') {
        await applyApiKeyAction(apiFetch, action, apiKey, null);
      } else if (action === 'rotate') {
        const input = window.prompt('Rotate key expiry in seconds (empty for no expiry)', '3600');
        if (input === null) return;
        const payload = input.trim() === '' ? { expires_in_seconds: null } : { expires_in_seconds: Number(input) };
        await applyApiKeyAction(apiFetch, action, apiKey, payload);
      }

      await loaders.loadApiKeys();
      setStatus('ok', `Key ${action} ok`);
      showToast(`Key ${action} completed`, 'ok');
    } catch (error) {
      setStatus('error', 'Admin denied');
      showToast(error.message, 'error');
      mountEmpty(elements.apiKeysList, error.message);
    }
  }

  async function handleCompareCardClick(event) {
    const card = event.target.closest('[data-zip-select]');
    if (!card) return;

    const zip = card.dataset.zipSelect;
    elements.zipInput.value = zip;
    state.focusedZip = zip;
    map.renderMap(state.compareResults, state.focusedZip);

    try {
      const summary = await loaders.loadZipSummary(zip);
      map.renderMap(state.compareResults, state.focusedZip);
      if (typeof map.showZipSummaryOnMap === 'function') {
        map.showZipSummaryOnMap(summary);
      }
      setStatus('ok', `ZIP ${zip}`);
    } catch (_) {
      setStatus('error', 'Error');
    }
  }

  async function handleUserActionClick(event) {
    const copyButton = event.target.closest('button[data-copy-value]');
    if (copyButton) {
      await copyToClipboard(copyButton.dataset.copyValue || '', copyButton.dataset.copyLabel || 'value');
      return;
    }

    const button = event.target.closest('button[data-user-action]');
    if (!button) return;

    const action = button.dataset.userAction;
    const email = button.dataset.userEmail;
    if (!email) return;

    try {
      if (action === 'disable') {
        await disableAuthUser(apiFetch, email);
      } else if (action === 'password') {
        const password = window.prompt('New password (min 6 chars)');
        if (password === null) return;
        if (password.trim().length < 6) {
          showToast('Password must be at least 6 characters', 'error');
          return;
        }
        await resetAuthUserPassword(apiFetch, email, password.trim());
      }
      await loaders.loadAuthUsers();
      setStatus('ok', `User ${action} ok`);
      showToast(`User ${action} completed`, 'ok');
    } catch (error) {
      setStatus('error', 'Admin denied');
      showToast(error.message, 'error');
      mountEmpty(elements.authUsersList, error.message);
    }
  }

  async function handleZipSubmit(event) {
    event.preventDefault();
    try {
      const zip = elements.zipInput.value.trim();
      if (!zip) return;
      state.focusedZip = zip;

      if (state.compareResults.length) {
        map.renderMap(state.compareResults, state.focusedZip);
      }

      const summary = await loaders.loadZipSummary(zip);
      map.renderMap(state.compareResults, state.focusedZip);
      if (typeof map.showZipSummaryOnMap === 'function') {
        map.showZipSummaryOnMap(summary);
      }
      setStatus('ok', 'Connected');
    } catch (error) {
      setStatus('error', 'Error');
      showToast(error.message, 'error');
      mountEmpty(elements.zipSummary, error.message);
    }
  }

  async function handleCompareSubmit(event) {
    event.preventDefault();
    const zips = elements.compareInput.value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
    try {
      state.focusedZip = zips[0] || null;
      await loaders.loadComparison(zips);
      setStatus('ok', 'Connected');
    } catch (error) {
      setStatus('error', 'Error');
      showToast(error.message, 'error');
      mountEmpty(elements.compareResults, error.message);
    }
  }

  async function handleExportSubmit(event) {
    event.preventDefault();
    try {
      await createExport(apiFetch, elements.datasetInput.value.trim());
      pagination.resetExportsPagination();
      await loaders.loadExports();
      setStatus('ok', 'Export queued');
      showToast('Export queued', 'ok');
    } catch (error) {
      setStatus('error', 'Export blocked');
      showToast(error.message, 'error');
      mountEmpty(elements.exportsList, error.message);
    }
  }

  async function handleCreateApiKey(event) {
    event.preventDefault();
    const expiresValue = elements.expiryInput.value.trim();
    const payload = {
      tenant_id: elements.tenantIdInput.value.trim(),
      plan: elements.planInput.value,
    };
    if (expiresValue !== '') {
      payload.expires_in_seconds = Number(expiresValue);
    }

    try {
      await createApiKey(apiFetch, payload);
      await loaders.loadApiKeys();
      setStatus('ok', 'Key created');
      showToast('API key created', 'ok');
    } catch (error) {
      setStatus('error', 'Admin denied');
      showToast(error.message, 'error');
      mountEmpty(elements.apiKeysList, error.message);
    }
  }

  async function handleProcessPending() {
    try {
      await processPendingExports(apiFetch);
      await loaders.loadExports();
      setStatus('ok', 'Pending processed');
      showToast('Pending exports processed', 'ok');
    } catch (error) {
      setStatus('error', 'Admin denied');
      showToast(error.message, 'error');
      mountEmpty(elements.exportsList, error.message);
    }
  }

  async function handleCreateAuthUser(event) {
    event.preventDefault();
    const payload = {
      email: elements.authUserEmail.value.trim(),
      password: elements.authUserPassword.value,
      tenant_id: elements.authUserTenant.value.trim(),
      plan: elements.authUserPlan.value,
    };

    try {
      await createAuthUser(apiFetch, payload);
      elements.authUserPassword.value = '';
      await loaders.loadAuthUsers();
      setStatus('ok', 'User created');
      showToast('User created', 'ok');
    } catch (error) {
      setStatus('error', 'Admin denied');
      showToast(error.message, 'error');
      mountEmpty(elements.authUsersList, error.message);
    }
  }

  return {
    handleExportActionClick,
    handleApiKeyActionClick,
    handleCompareCardClick,
    handleUserActionClick,
    handleZipSubmit,
    handleCompareSubmit,
    handleExportSubmit,
    handleCreateApiKey,
    handleProcessPending,
    handleCreateAuthUser,
  };
}
