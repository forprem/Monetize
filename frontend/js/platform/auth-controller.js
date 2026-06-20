import { apiFetch as platformApiFetch } from './api-client.js';

const TOKEN_KEY = 'monetize-access-token';
const USER_KEY = 'monetize-user';

export function createAuthController({ elements, configController, setStatus, showToast }) {
  function setOverlayVisible(visible) {
    if (!elements.authOverlay) return;
    elements.authOverlay.classList.toggle('hidden', !visible);
    if (visible) {
      elements.authOverlay.removeAttribute('hidden');
      elements.authOverlay.style.display = '';
    } else {
      elements.authOverlay.setAttribute('hidden', 'hidden');
      elements.authOverlay.style.display = 'none';
    }
    document.body.classList.toggle('unauthenticated', visible);
    document.body.classList.toggle('authenticated', !visible);
    if (elements.pageShell) {
      elements.pageShell.classList.toggle('hidden', visible);
      if (visible) {
        elements.pageShell.setAttribute('hidden', 'hidden');
        elements.pageShell.style.display = 'none';
      } else {
        elements.pageShell.removeAttribute('hidden');
        elements.pageShell.style.display = '';
      }
    }
  }

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function saveSession(payload) {
    localStorage.setItem(TOKEN_KEY, payload.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify({
      email: payload.email,
      tenant_id: payload.tenant_id,
      plan: payload.plan,
    }));
  }

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  async function fetchMe(token) {
    const { baseUrl } = configController.getConfig();
    return platformApiFetch(baseUrl, '', '/auth/me', {}, token);
  }

  async function tryResumeSession() {
    // Always show login first; dashboard opens only after explicit sign-in.
    setOverlayVisible(true);
    return false;
  }

  function bindLogin(onLoginSuccess) {
    if (!elements.loginForm) return;

    elements.loginForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const email = elements.loginEmail?.value?.trim() || '';
      const password = elements.loginPassword?.value || '';

      try {
        const { baseUrl } = configController.getConfig();
        const payload = await platformApiFetch(baseUrl, '', '/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        });
        saveSession(payload);
        if (elements.loginError) {
          elements.loginError.textContent = '';
          elements.loginError.classList.add('hidden');
        }
        setOverlayVisible(false);
        setStatus('ok', 'Connected');
        showToast('Login successful', 'ok');
        onLoginSuccess();
      } catch (error) {
        if (elements.loginError) {
          elements.loginError.textContent = error.message || 'Login failed';
          elements.loginError.classList.remove('hidden');
        }
        setStatus('error', 'Login failed');
      }
    });
  }

  return {
    bindLogin,
    tryResumeSession,
    clearSession,
    setOverlayVisible,
  };
}
