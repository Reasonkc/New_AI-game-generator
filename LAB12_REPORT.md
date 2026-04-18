# Lab 12 — Performance / UX Improvement Report

**Project:** AI Game Generator
**Branch:** `perf/lab12-ux-improvements`
**Date:** 2026-04-17
**Author:** Rijan Khatri

## Objective

Improve application responsiveness and usability by identifying concrete
perf/UX issues, applying AI-assisted optimizations, and validating the
changes with the existing build + test suite.

## Methodology

1. Audited the React frontend (`frontend/src`) and Flask backend
   (`backend/`) for common perf/UX smells: re-render triggers on every
   keystroke, eagerly-loaded images, non-descriptive alt text,
   inaccessible clickable `div`s, and uncached disk reads on hot paths.
2. Asked Claude (Opus 4.7) to rank findings by "high impact + low risk"
   and to suggest targeted fixes scoped small enough to land in a single
   PR.
3. Implemented the top four improvements, then validated with
   `npm run build` (frontend) and `pytest` (backend).

## Issues Identified

| # | Area | File(s) | Problem | Severity |
|---|------|---------|---------|----------|
| 1 | Rendering | `HomePage.jsx:111-116`, `Gallery.jsx:26-30` | Search filter re-runs on every keystroke — list re-filters 10+× per second while typing. | Medium |
| 2 | Assets / a11y | `HomePage.jsx:212-218` | 6 thumbnails load eagerly, non-descriptive `alt="Game Thumbnail"`, no width/height → layout shift risk. | Medium |
| 3 | Accessibility | `HomePage.jsx:205-210` | Game cards are `<div onClick>` — keyboard users cannot activate, screen readers get no role/label. | High |
| 4 | Backend I/O | `backend.py:570-577` | `/list_games` scans `games/` and reads every `metadata.json` on every request — O(N) disk reads per call, fired on every page load. | Medium |

## Changes Applied

### 1. Debounced search inputs (`useDebouncedValue` hook)

**New file:** `frontend/src/useDebouncedValue.js`

```js
export default function useDebouncedValue(value, delay = 250) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}
```

Wired into `HomePage.jsx` and `Gallery.jsx`. The input still updates
instantly (controlled input), but the expensive `.filter()` only runs
250 ms after typing stops. `useMemo` caches the filtered list between
keystrokes.

**Before:** Filter runs on every keystroke. Typing "jungle" (6 chars)
→ 6 filter passes + 6 re-renders of the cards grid.
**After:** One filter pass, one re-render after the user pauses.

### 2. Lazy-loaded thumbnails + descriptive alt text

```jsx
<img
  src={game.thumbnail}
  alt={`${game.title} — ${game.category} game thumbnail`}
  loading="lazy"
  decoding="async"
  width="400"
  height="192"
  ...
/>
```

- `loading="lazy"` defers off-screen thumbnails until scroll.
- `decoding="async"` lets the browser decode off the main thread.
- Explicit `width`/`height` reserves layout space → removes CLS
  (Cumulative Layout Shift).
- Alt text now names the specific game + category instead of the generic
  "Game Thumbnail" string repeated 6×.
- Guarded `onError` against infinite fallback loops
  (`e.target.onerror = null`).

### 3. Keyboard-accessible game cards

Added `role="link"`, `tabIndex={0}`, `aria-label`, `onKeyDown` handler
(Enter / Space), and a visible `focus:ring` to the card `<div>` in
`HomePage.jsx`. Tab order now reaches every card and activation works
without a mouse. Also upgraded the hero search to `type="search"` with
an `aria-label`.

### 4. TTL cache for `GET /list_games`

```python
_LIST_GAMES_CACHE = {"expires_at": 0.0, "games": None}
_LIST_GAMES_TTL_S = 30.0

def _invalidate_list_games_cache() -> None:
    _LIST_GAMES_CACHE["expires_at"] = 0.0
    _LIST_GAMES_CACHE["games"] = None
```

The endpoint now serves a 30 s in-memory snapshot instead of scanning
`games/` and parsing every `metadata.json` on every request. The cache
is invalidated immediately after `save_new_game()` in `/generate_game`,
so a freshly created game appears in the gallery without any staleness.
`/update_game` and `/report_broken_game` only overwrite HTML (metadata
list is unchanged), so they intentionally do not invalidate.

## Validation

- **Backend:** `pytest` — **72 / 72 passed** in 0.94 s.
- **Frontend:** `npm run build` succeeds, bundle 431 KB JS / 131 KB
  gzipped (no regression).
- **Manual:** Searched on Home + Gallery — cards update smoothly after
  typing pauses; tabbing through the Home grid now highlights each card
  with a visible focus ring and Enter activates it; thumbnails load
  progressively on scroll.

## Measured / Expected Impact

| Metric | Before | After |
|---|---|---|
| Filter passes while typing "jungle" | 6 | 1 |
| Eager image requests on Home mount | 6 | ~2 (above-the-fold) |
| `/list_games` disk reads on repeat hit (within 30 s) | O(N) | 0 |
| Keyboard-accessible cards | No | Yes |
| Distinct alt text per thumbnail | No | Yes |

## Files Changed

- `frontend/src/useDebouncedValue.js` (new)
- `frontend/src/HomePage.jsx`
- `frontend/src/Gallery.jsx`
- `backend/backend.py`

## Follow-ups (not in this PR)

- Split `Create.jsx` (807 lines) into step components + `React.memo`.
- Delete dead `Create_new.jsx`.
- Add `Cache-Control` header to `/list_games` for browser-side caching.
- Extract the `HomePage` game card into a memoized `<GameCard>`
  component.
