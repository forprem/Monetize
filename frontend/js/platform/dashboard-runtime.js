import { apiFetch as platformApiFetch } from './api-client.js';
import {
  copyToClipboard as platformCopyToClipboard,
  downloadCsv as platformDownloadCsv,
  formatCompact as platformFormatCompact,
  formatDate as platformFormatDate,
  maskApiKey as platformMaskApiKey,
  mountEmpty as platformMountEmpty,
  showToast as platformShowToast,
} from './ui-helpers.js';

export function createDashboardRuntime({ documentRef, elements, configController }) {
  function setStatus(mode, label) {
    elements.connectionStatus.className = `status-pill ${mode}`;
    elements.connectionStatus.textContent = label;
  }

  function showToast(message, mode = 'ok') {
    platformShowToast(elements.toastStack, message, mode);
  }

  async function apiFetch(path, options = {}) {
    const { baseUrl, apiKey } = configController.getConfig();
    const accessToken = localStorage.getItem('monetize-access-token');
    return platformApiFetch(baseUrl, apiKey, path, options, accessToken);
  }

  function mountEmpty(container, message) {
    platformMountEmpty(container, message);
  }

  function formatCompact(value) {
    return platformFormatCompact(value);
  }

  function formatDate(value) {
    return platformFormatDate(value);
  }

  function maskApiKey(value) {
    return platformMaskApiKey(value, elements.showFullKeys.checked);
  }

  function downloadCsv(filename, rows) {
    platformDownloadCsv(filename, rows);
  }

  async function copyToClipboard(value, label) {
    if (!value) {
      showToast(`No ${label} to copy`, 'error');
      return;
    }

    try {
      await platformCopyToClipboard(value);
      showToast(`Copied ${label}`, 'ok');
    } catch (_error) {
      const temp = documentRef.createElement('textarea');
      temp.value = value;
      documentRef.body.appendChild(temp);
      temp.select();
      documentRef.execCommand('copy');
      temp.remove();
      showToast(`Copied ${label}`, 'ok');
    }
  }

  return {
    setStatus,
    showToast,
    apiFetch,
    mountEmpty,
    formatCompact,
    formatDate,
    maskApiKey,
    downloadCsv,
    copyToClipboard,
  };
}
