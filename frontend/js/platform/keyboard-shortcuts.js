export function registerKeyboardShortcuts(documentRef, elements, actions, notify) {
  const handler = (event) => {
    const tag = event.target?.tagName?.toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') {
      return;
    }

    const key = event.key.toLowerCase();
    if (key === 'r') {
      event.preventDefault();
      actions.refreshDashboard();
    } else if (key === 'p') {
      event.preventDefault();
      actions.processPending();
    } else if (key === 'e') {
      event.preventDefault();
      elements.exportsSearch.focus();
      notify('Focused exports search', 'ok');
    } else if (key === 'a') {
      event.preventDefault();
      elements.activitySearch.focus();
      notify('Focused activity search', 'ok');
    }
  };

  documentRef.addEventListener('keydown', handler);
  return () => documentRef.removeEventListener('keydown', handler);
}
