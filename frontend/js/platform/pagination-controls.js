export function updatePagerUi(elements, pagination, kind) {
  const { offset, limit, returned } = pagination[kind];
  const page = Math.floor(offset / limit) + 1;
  const hasNext = returned >= limit;
  const hasPrev = offset > 0;

  if (kind === 'exports') {
    elements.exportsPageInfo.textContent = `Page ${page}`;
    elements.exportsPrev.disabled = !hasPrev;
    elements.exportsNext.disabled = !hasNext;
    return;
  }

  elements.auditPageInfo.textContent = `Page ${page}`;
  elements.auditPrev.disabled = !hasPrev;
  elements.auditNext.disabled = !hasNext;
}

export function resetPager(pageState) {
  pageState.offset = 0;
}

export function movePagerPrev(pageState) {
  pageState.offset = Math.max(0, pageState.offset - pageState.limit);
}

export function movePagerNext(pageState) {
  if (pageState.returned < pageState.limit) {
    return false;
  }

  pageState.offset += pageState.limit;
  return true;
}
