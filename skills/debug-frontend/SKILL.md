---
name: debug-frontend
description: Debug frontend UI and behavior end to end with agent-browser, starting the app locally when needed and validating relevant states thoroughly.
---

Assume the current directory is the scope unless the user specifies a path, package, app, route, branch diff, ticket, or URL.

## Execution Principles

- Use `agent-browser` directly for browser work. Validate the actual UI and behavior instead of relying only on code inspection, screenshots, or assumptions.
- Start up the necessary local packages and services yourself when the app is not already reachable. Discover the package manager and scripts from the repo (`package.json`, workspace files, lockfiles, README, env examples, Docker or compose files) and use the smallest command set that gets the relevant frontend running.
- Prefer repo-native patterns for routing, state, styling, components, tests, mocks, fixtures, and authentication helpers.
- Be thorough where user impact is plausible: layout, loading, empty, error, disabled, unauthorized, free-tier, logged-out, logged-in, normal-user, admin, permission-restricted, filtered, paginated, searched, sorted, mobile, tablet, and desktop states.
- Match validation depth to risk. A tiny visual fix may need a narrow browser pass; auth, navigation, forms, filters, or shared components need broader state and regression checks.

## Browser Debugging

- Start from the affected route or workflow, then test adjacent behavior likely to share the same code.
- Use `agent-browser snapshot -i` to inspect structure and target elements, `screenshot` for visual/layout checks, and interactions such as `click`, `fill`, `press`, `select`, navigation, and reloads to exercise behavior.
- Check browser console output and page errors during and after interactions. Treat hydration warnings, failed requests, unhandled promise rejections, accessibility-breaking focus traps, and repeated network failures as real signals.
- Validate responsiveness deliberately. Resize the browser or viewport when the tool supports it, and cover narrow mobile, a mid-size/tablet width when layout changes around breakpoints, and a desktop width. Look for clipping, overlap, hidden controls, broken sticky/fixed elements, scroll traps, and text that no longer fits.
- Validate meaningful state combinations, not just the happy path. Examples: free user versus paid user, logged-out versus logged-in, admin versus normal user, empty versus populated data, loading versus loaded, network/API error, permission denied, applied filters, no filter results, long labels, long lists, pagination boundaries, disabled controls, and form validation failures.
- For filters, search, sorting, tabs, and menus, verify both the visible UI state and the resulting data or URL/query state when applicable.

## Fixing

- Reproduce or observe the issue before changing code whenever feasible.
- Make the smallest idiomatic fix that addresses the observed behavior and nearby regressions. Avoid speculative redesigns unless the current structure is the root cause.
- Add or update tests when they would catch the bug without excessive setup. Browser validation is still required for user-visible behavior.
- After editing, reload or restart as needed and repeat the relevant browser checks. Do not assume hot reload applied cleanly.

## Completion

- Kill processes you started where reasonable

Summarize the work in concrete terms:

- What was broken or risky.
- What code changed and why.
- What commands or servers were run.
- Which routes, roles, states, filters, interactions, and viewport sizes were validated with `agent-browser`.
- Any console errors, failed requests, skipped states, missing credentials, unavailable services, or residual risks.

High-quality execution leaves the app running only when it is useful for the user to inspect, provides the URL when available, and clearly distinguishes verified behavior from inferred behavior.
