// Composition root: build dependency graph, wire features, then bootstrap startup.
import { createDashboardDependencies } from './dashboard-dependencies.js';
import { createDashboardFeatureWiring } from './dashboard-feature-wiring.js';
import { createAuthController } from '../platform/auth-controller.js';

export function startDashboardApp(documentRef = document) {
  const dependencies = createDashboardDependencies(documentRef);
  const features = createDashboardFeatureWiring(dependencies);
  const { configController, runtime, elements } = dependencies;

  configController.loadSavedConfig();
  features.attachEvents();

  const auth = createAuthController({
    elements,
    configController,
    setStatus: runtime.setStatus,
    showToast: runtime.showToast,
  });

  auth.bindLogin(features.refreshDashboard);
  auth.tryResumeSession().then((hasSession) => {
    if (hasSession) {
      features.refreshDashboard();
    } else {
      runtime.setStatus('idle', 'Sign in required');
    }
  });
}
