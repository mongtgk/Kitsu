# RBAC UI Write Actions (P1.5 audit)

- **Authentication**
  - `src/components/login-popover-button.tsx` — Login and Signup buttons (`POST /auth/login`, `POST /auth/register`). Always visible to guests; no RBAC gating beyond form validation.
  - `src/components/navbar-avatar.tsx` — Logout action (`POST /auth/logout`) inside the avatar popover. Visible when authenticated; no RBAC gating.

- **Profile**
  - `src/app/profile/[username]/page.tsx` + `src/app/profile/[username]/components/anilist-import.tsx` — Anilist import dialog (Continue fetches Anilist lists, Import posts to `/api/import/anilist` and creates favorites). Visibility gated by `write:profile`.

- **Favorites / Content**
  - `src/app/anime/[slug]/page.tsx` — Favorites toggle button (POST/DELETE `/favorites`). Visibility gated by `write:content`.
  - `src/app/anime/watch/layout.tsx` — Favorites toggle button (POST/DELETE `/favorites`). Visibility gated by `write:content`.
  - `src/hooks/use-get-bookmark.tsx` — `createOrUpdateBookMark` helper (POST `/favorites`) used by player/import flows; authentication required, no RBAC visibility gating.
  - `src/components/kitsune-player.tsx` — Playback auto bookmark creation plus watch-progress sync queue (triggers `createOrUpdateBookMark` and local progress storage) for logged-in users; no RBAC visibility gating.
