import { movePagerNext, movePagerPrev, resetPager } from '../platform/pagination-controls.js';

export function createDashboardPagination(context) {
  const { state, loaders } = context;

  function resetExportsPagination() {
    resetPager(state.pagination.exports);
  }

  function resetAuditPagination() {
    resetPager(state.pagination.audit);
  }

  async function handleExportsPrev() {
    movePagerPrev(state.pagination.exports);
    await loaders.loadExports();
  }

  async function handleExportsNext() {
    if (!movePagerNext(state.pagination.exports)) return;
    await loaders.loadExports();
  }

  async function handleAuditPrev() {
    movePagerPrev(state.pagination.audit);
    await loaders.loadAudit();
  }

  async function handleAuditNext() {
    if (!movePagerNext(state.pagination.audit)) return;
    await loaders.loadAudit();
  }

  return {
    resetExportsPagination,
    resetAuditPagination,
    handleExportsPrev,
    handleExportsNext,
    handleAuditPrev,
    handleAuditNext,
  };
}
