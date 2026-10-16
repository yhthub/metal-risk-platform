# Shared website access entry — 2026-10-11

Scope: `app/app.vue`, `app/composables/useApi.ts`, new `app/utils/systemAccess.ts`, and offline tests.

- Initial GET system-information probe must succeed before any Nuxt page mounts. Local API without a key enters directly; protected API uses one simple password-masked shared-key dialog.
- All existing `useApi` callers share the same module-memory Bearer key. It is not written to browser storage, a URL, public runtime configuration, or logs. Only a successfully validated candidate replaces the current key.
- Later HTTP 401 opens settings without unmounting the current page or automatically replaying a POST/upload/chat. Failed API or network responses do not become successful checks.
- `/zhiwei/` coexistence is supported by configuring the existing `public.apiBase=/zhiwei`; the access entry never fetches a hardcoded root endpoint directly. No existing web-server configuration or port was changed.
- `agent/index.vue` and other feature pages were not edited by this task. Existing feature-level error handling remains in place.

Verification command from `D:/gradstu/gard1/vite+vue3/my-nuxt-app`:

```text
D:/node/node.exe --test tests/system-access.test.cjs tests/rag-frontend.test.cjs
```

Result: 16 new offline access checks and 36 existing offline RAG checks passed (2 Node test files, 0 failures). SFC/template/TypeScript syntax/scoped CSS compilation is included.

Limits: no live HTTP, browser interaction/screenshot, real model request, development-server start, or remote deployment was performed. A parent-task production build and live deployment verification remain separate.
