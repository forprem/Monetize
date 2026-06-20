export function createConfigController(elements, storageKey) {
  function getConfig() {
    return {
      baseUrl: elements.baseUrl.value.replace(/\/$/, ''),
      apiKey: elements.apiKey.value.trim(),
    };
  }

  function loadSavedConfig() {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw);
      if (parsed.baseUrl) elements.baseUrl.value = parsed.baseUrl;
      if (parsed.apiKey) elements.apiKey.value = parsed.apiKey;
    } catch (_) {
      // Ignore malformed local storage payload.
    }
  }

  function saveConfigIfEnabled() {
    if (!elements.rememberConfig.checked) {
      localStorage.removeItem(storageKey);
      return;
    }
    localStorage.setItem(storageKey, JSON.stringify(getConfig()));
  }

  return {
    getConfig,
    loadSavedConfig,
    saveConfigIfEnabled,
  };
}
