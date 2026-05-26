# Feature Specification: Client Portal (client-portal)

> **Version:** 1.0
> **Date:** 2026-05-26
> **Status:** Approved
> **Epic:** Epic 4 — Client Portal (US-CP-01, US-CP-02, US-TL-02)

---

## 1. Overview

The Client Portal provides homeowners with a web-based interface built on
Odoo's portal framework. It surfaces renovation project data -- timeline with
photos, stage progress, budget overview, and timelapse videos -- through
authenticated portal pages. A public share page allows unauthenticated viewers
to watch timelapse videos via token-based URLs.

## 2. User Stories Covered

| ID | Title | Priority |
|----|-------|----------|
| US-CP-01 | Renovation Timeline with Photos | Must Have |
| US-CP-02 | Budget Visibility in Portal | Must Have |
| US-TL-02 | Timelapse Sharing (public page) | Could Have |

## 3. Functional Requirements

### 3.1 Project List (/my/projects)

- Authenticated portal users see only projects where `owner_id = current user`
- Card grid layout: project name, address, status badge, start date
- Status badges: draft (secondary), in_progress (primary), completed (success), cancelled (danger)
- Counter in portal sidebar ("My Renovations" link with project count)

### 3.2 Project Detail (/my/projects/<id>)

- Ownership check: if `project.owner_id != current_user`, redirect to /my/projects
- **Timeline section:** snapshots grouped by day, filterable by detected stage, lazy-loaded (20 per batch)
- **Stage progress section:** progress bars per stage with percentage labels, color-coded by status
- **Budget card:**
  - Fields: Estimate, Spent, Remaining, Variance %
  - Color coding: green (<=80% consumed), yellow (80-100%), red (>100%)
  - All values formatted as RUB with 2 decimal places
  - Read-only for portal users (no edit controls)
- **Timelapse embed:** latest timelapse video with HTML5 player

### 3.3 Public Timelapse Share (/share/<token>)

- No authentication required (`auth="public"`)
- Looks up `remont.timelapse` by `share_token` field
- Renders minimal page: project name, video player, "Get RemontERP" CTA button
- Returns 404 if token not found or timelapse not available

### 3.4 Portal Sidebar Menu

- "My Renovations" entry in Odoo portal home via `portal.portal_my_home` inheritance
- Shows project count badge

## 4. Security Requirements

### 4.1 Data Isolation (CRITICAL)

- Portal users MUST only see projects where `owner_id` matches `request.env.user.id`
- Enforced via Odoo record rules (ir.rule) at the ORM level, not just controller filtering
- Record rules cover: `remont.project`, `remont.stage`, `remont.snapshot`, `remont.timelapse`
- Portal users get read-only access (perm_read=1, all others=0)

### 4.2 Budget Display

- All monetary values use `fields.Monetary` (backed by NUMERIC(12,2))
- No float arithmetic in templates -- values computed server-side
- Display formatting only in QWeb (no JS calculations)

### 4.3 Public Share Page

- Uses `sudo()` to bypass record rules (public users have no user record)
- Only exposes: project name, project address, video URL
- No budget, no owner info, no detailed snapshots on public page

## 5. Technical Architecture

### 5.1 Module Dependencies

```
remont_portal
  depends: base, website, portal, remont_core, remont_camera
```

### 5.2 Files Modified/Created

| File | Action | Purpose |
|------|--------|---------|
| `controllers/portal.py` | Enhance | Complete routes with budget color logic, ownership checks |
| `views/portal_templates.xml` | Enhance | Full QWeb templates with progress bars, budget card, timelapse |
| `views/portal_menus.xml` | Enhance | Fix portal sidebar icon reference |
| `static/src/css/portal.css` | Enhance | Responsive styles for mobile (375px+) |
| `security/ir.model.access.csv` | Enhance | Portal group read access for timelapse, budget models |
| `security/portal_rules.xml` | Create | Record rules restricting portal users to own projects |
| `__manifest__.py` | Update | Add security/portal_rules.xml to data list |

### 5.3 Record Rules

```xml
<!-- Portal users see only their own projects -->
<record id="rule_portal_project_owner" model="ir.rule">
    <field name="name">Portal: own projects only</field>
    <field name="model_id" ref="remont_core.model_remont_project"/>
    <field name="groups" eval="[(4, ref('base.group_portal'))]"/>
    <field name="domain_force">[('owner_id', '=', user.id)]</field>
</record>
```

Similar rules for stage, snapshot, timelapse linked via `project_id.owner_id`.

## 6. UI/UX

### 6.1 Responsive Breakpoints

- Mobile: 375px+ (single column cards, stacked budget)
- Tablet: 768px+ (2-column grid)
- Desktop: 992px+ (3-column grid, side-by-side budget)

### 6.2 Budget Color Coding

| Consumption | Color | CSS Class |
|-------------|-------|-----------|
| <= 80% | Green | `text-success` / `bg-success` |
| 80-100% | Yellow | `text-warning` / `bg-warning` |
| > 100% | Red | `text-danger` / `bg-danger` |

## 7. Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | Portal user sees only projects where they are owner |
| AC-2 | Project list renders card grid with name, address, status badge |
| AC-3 | Project detail shows stage progress bars with percentages |
| AC-4 | Budget card shows estimate/spent/remaining with correct color coding |
| AC-5 | Budget values displayed as RUB with 2 decimal places |
| AC-6 | Public share page loads timelapse without authentication |
| AC-7 | Invalid share token returns 404 |
| AC-8 | Mobile viewport (375px) renders without horizontal scroll |
| AC-9 | Record rules prevent portal users from accessing other users' projects via ORM |
| AC-10 | Portal sidebar shows "My Renovations" with project count |

---

*End of Specification.*
