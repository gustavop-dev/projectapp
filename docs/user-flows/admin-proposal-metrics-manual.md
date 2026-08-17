### FLOW: `admin-proposal-metrics-manual`

- **Module:** admin
- **Role:** admin
- **Priority:** P3
- **Routes:** `/panel/proposals/`
- **Description:** Floating "?" button opens a slide-over panel (MetricsManual component) with searchable definitions of all metrics: conversion rate, engagement score, heat score, time-to-first-view, win rate, zombie proposals, late returns, seller inactivity, etc.
- **Steps:**
  1. Admin clicks the floating "?" button (bottom-right corner).
  2. MetricsManual slide-over opens with search bar and 16 metric definitions.
  3. Admin types in search bar → results filter in real-time.
  4. Each metric shows name, description, calculation method, and recommended action.
  5. Admin clicks outside or ✕ to close.
- **Coverage:** ✅ Covered — `frontend/e2e/admin/admin-proposal-metrics-manual.spec.js`
