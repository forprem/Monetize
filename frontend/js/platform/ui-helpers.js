export function mountEmpty(container, message) {
  container.innerHTML = `<div class="empty-state">${message}</div>`;
}

export function formatCompact(value) {
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value);
}

export function formatDate(value) {
  return new Date(value).toLocaleString();
}

export function maskApiKey(value, showFull) {
  if (!value || value.length < 10 || showFull) {
    return value;
  }
  return `${value.slice(0, 6)}...${value.slice(-4)}`;
}

export function showToast(toastStack, message, mode = 'ok') {
  const toast = document.createElement('div');
  toast.className = `toast ${mode}`;
  toast.textContent = message;
  toastStack.appendChild(toast);
  setTimeout(() => toast.remove(), 3200);
}

export function downloadCsv(filename, rows) {
  const escapeCell = (value) => {
    const stringValue = String(value ?? '');
    if (/[",\n]/.test(stringValue)) {
      return `"${stringValue.replace(/"/g, '""')}"`;
    }
    return stringValue;
  };

  const csv = rows.map((row) => row.map(escapeCell).join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function copyToClipboard(value) {
  await navigator.clipboard.writeText(value);
}
