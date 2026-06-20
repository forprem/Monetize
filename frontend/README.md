# Frontend MVP

This frontend is a no-build static SPA so it can run even in environments where Node.js is not available yet.

## Run it locally

1. Start the backend on `http://localhost:8000`
2. From the `frontend` directory, serve the files with any static server. For example:

```bash
cd /home/ansible/Monetize/frontend
python3 -m http.server 4173
```

3. Open `http://localhost:4173`

## Features in this slice

- Dashboard overview with request and export metrics
- Layer catalog from the live API
- ZIP summary lookup
- ZIP comparison board
- Export queue viewer and batch processing button
- Admin audit viewer
- API key creation and listing

## Architecture

- See `ARCHITECTURE.md` for module layout, dependency direction, and extension guidelines.
- See `CHANGELOG.md` for implementation milestones and handoff history.

## Doc index

- `README.md`: quick start, local run instructions, and fast edit entry points.
- `ARCHITECTURE.md`: module responsibilities, dependency rules, implementation checklists, and troubleshooting.
- `CHANGELOG.md`: timeline of delivered slices and current module map for handoff context.
- `HANDOFF.md`: fill-in template for end-of-session status transfer, including `Current owner/session` and `Last updated`.

## Doc maintenance rule

- Any architecture-impacting slice must update both `ARCHITECTURE.md` and `CHANGELOG.md`, including their `Last updated` lines.

## Session close checklist

1. Run a workspace error scan for changed files and confirm no new errors.
2. Sync changed frontend files to `C:\D drive\2026\Monetize\frontend`.
3. Verify synced file presence with a quick directory listing.
4. Update `CHANGELOG.md` when a meaningful milestone was completed.
5. For process/governance doc updates, follow the `Governance update template` section in `CHANGELOG.md`.
6. Update `ARCHITECTURE.md` if module responsibilities or flows changed.
7. Update the `Last updated` line in `HANDOFF.md`.
8. Update `HANDOFF.md` -> `Current session snapshot` with final slice state before closeout.
9. Review `HANDOFF.md` section 3 (Validation run - handoff-validation) and section 4 (Delivery sync - handoff-delivery-sync) for completeness.
10. Verify the closeout sync command snippet matches across `README.md`, `ARCHITECTURE.md`, and `HANDOFF.md`.
11. Confirm `CHANGELOG.md` was updated for any process/documentation governance change in this session.
12. Fill `HANDOFF.md` -> `Closeout evidence` with final yes/no outcomes.
13. Fill `HANDOFF.md` closeout attribution fields (`Closeout completed by` and `Closeout completion timestamp`).
14. Mark `HANDOFF.md` section 3 `Closeout attribution check` as yes/no after verifying attribution fields are filled.
15. Mark `HANDOFF.md` section 3 `Governance template evidence check` as yes/no.
16. Mark `HANDOFF.md` -> `Closeout evidence` `Governance template entry logged in CHANGELOG.md when required` as yes/no.
17. Set `Session status` in `HANDOFF.md` from `active` to `closed` before ending the session.

## Session open checklist

1. Set `Session status` in `HANDOFF.md` to `active`.
2. Update `Current owner/session` in `HANDOFF.md` with your name/handle and date.
3. Initialize `HANDOFF.md` -> `Current session snapshot` for this session's objective and first slice.
4. Confirm `Known environment assumptions` still match the active environment.
5. Review `HANDOFF.md` section 5 (Open items) to choose the next slice.

## Known environment assumptions

- Active dev shell uses WSL/Linux workspace path: `/home/ansible/Monetize/frontend`.
- Delivery mirror target is Windows path: `C:\D drive\2026\Monetize\frontend`.
- Frontend runtime mode is static no-build ESM (no Node build pipeline required for run).

## Paths quick copy

```text
WSL workspace: /home/ansible/Monetize/frontend
Windows mirror: C:\D drive\2026\Monetize\frontend
```

## Single-command closeout

Use this in WSL to mirror docs to the Windows delivery path and verify presence:

```bash
cp -f README.md ARCHITECTURE.md CHANGELOG.md HANDOFF.md '/mnt/c/D drive/2026/Monetize/frontend/' && ls -la '/mnt/c/D drive/2026/Monetize/frontend'
```

## Handoff usage rule

- Before ending any session, update `HANDOFF.md` with the latest status, validation, sync details, and next slice.
- Also refresh the `Last updated` line in `HANDOFF.md` at session close.
- Fill in the `Current owner/session` field in `HANDOFF.md` for traceability.
- Set `Session status` in `HANDOFF.md` to `closed` before session end.

## Quick edit paths

- Add or change export/API key row actions: `js/business/dashboard-actions.js`
- Add or change filter/search/local UI behavior: `js/business/dashboard-interactions.js`
- Add or change API-backed data loading/render flow: `js/business/dashboard-loaders.js`
- Change refresh orchestration sequence: `js/business/dashboard-refresh-controller.js`
- Change pager reset/next/prev behavior: `js/business/dashboard-pagination.js`
- Change map render dependency wiring: `js/business/dashboard-map-controller.js`
- Change event-to-handler mapping: `js/business/dashboard-event-wiring.js`
- Add new shared runtime helpers (toast/format/copy/download): `js/platform/dashboard-runtime.js`

## Default test keys

- `dev_demo_key`
- `dev_basic_key`
- `dev_trial_key`
- `dev_admin_key`
