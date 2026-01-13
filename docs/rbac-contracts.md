# RBAC Contract (P1.6)

This document locks the RBAC contract between the backend API, permissions, and the current frontend visibility-only gating. Behavior is unchanged in P1; P2 will switch the marked items to strict deny.

## Backend write endpoints

| Method | Path | Required permission | Enforcement phase (P1) | Notes / P2 intent |
| --- | --- | --- | --- | --- |
| POST | /auth/register | public (auth flow) | Open (no RBAC check) | User signup, stays public in P2. |
| POST | /auth/login | public (auth flow) | Open (no RBAC check) | User login, stays public in P2. |
| POST | /auth/refresh | public (auth flow) | Open (no RBAC check) | Session refresh, stays public in P2. |
| POST | /auth/logout | public (auth flow) | Open (no RBAC check) | Session revoke, stays public in P2. |
| POST | /users | public (system placeholder) | Open (no RBAC check) | Stubbed create-user endpoint; UI does not call it yet. |
| PATCH | /users/me | write:profile | Enforced (P1 backend) | Will be strict-deny in P2 for callers without write:profile. |
| POST | /favorites | write:content | Enforced (P1 backend) | Strict deny in P2 for missing write:content. |
| DELETE | /favorites/{anime_id} | write:content | Enforced (P1 backend) | Strict deny in P2 for missing write:content. |
| POST | /watch/progress | write:content | Enforced (P1 backend) | No UI caller yet; strict deny in P2 for missing write:content. |
| POST | /collections | TBD (system/internal) | Open (no RBAC check) | Placeholder; to be classified before P2. |
| POST | /views | TBD (system/internal) | Open (no RBAC check) | Placeholder; to be classified before P2. |

## Frontend write actions

| UI action | Component / file | API endpoint(s) | Required permission | Current mode (P1) |
| --- | --- | --- | --- | --- |
| Login submit | `src/components/login-popover-button.tsx` | POST /auth/login | public | Always visible; form-level validation only. |
| Signup submit | `src/components/login-popover-button.tsx` | POST /auth/register | public | Always visible; form-level validation only. |
| Logout button | `src/components/navbar-avatar.tsx` | POST /auth/logout | public | Shown when authenticated; no RBAC gating. |
| Session refresh effect | `src/components/navbar.tsx` | POST /auth/refresh | public | Background call when a refresh token exists; visibility-only trigger. |
| Add/remove favorites (detail page) | `src/app/anime/[slug]/page.tsx` | POST /favorites, DELETE /favorites/{anime_id} | write:content | Button visibility-only (hidden without write:content). |
| Add/remove favorites (watch layout) | `src/app/anime/watch/layout.tsx` | POST /favorites, DELETE /favorites/{anime_id} | write:content | Button visibility-only (hidden without write:content). |
| Anilist import dialog | `src/app/profile/[username]/components/anilist-import.tsx` | POST /api/import/anilist → POST /favorites | write:profile for visibility, backend requires write:content | Dialog is visibility-only behind write:profile; backend favorites calls still need write:content. |
| Auto bookmark from player (inactive component) | `src/components/kitsune-player.tsx` | POST /favorites | write:content | Component is currently not mounted; when enabled it uses background POST with no additional gating. |

## Consistency check

- Mapped backend → frontend: `/favorites` (add/remove favorites, import dialog, player helper), auth endpoints (login/register/refresh/logout).
- Backend endpoints without a UI action: `/watch/progress` (player queues locally today), `/users` (stub), `/collections` (stub), `/views` (stub). These are marked system/internal until wired.
- Frontend write actions all point to an existing backend endpoint; import dialog ultimately calls `/favorites`.

## P2 strict-mode plan (no code changes now)

- `write:content`: POST/DELETE `/favorites` and POST `/watch/progress` will hard-deny when the permission is missing. UI plan — keep favorites buttons hidden for unauthorized roles and block any background player auto-bookmark/progress sync when re-enabled.
- `write:profile`: PATCH `/users/me` and the profile import entry point will hard-deny when missing `write:profile`. UI plan — keep Anilist import hidden/disabled without the permission and disable any profile editing affordances before calling the API.
- Auth endpoints remain public. System/internal stubs (`/collections`, `/views`, `/users`) need classification before enabling strict checks.
