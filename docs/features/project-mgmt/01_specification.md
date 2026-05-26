# Feature Specification: Project Management Module (project-mgmt)

> **Version:** 1.0
> **Date:** 2026-05-26
> **Status:** Approved
> **Epic:** Epic 5 — Project Management
> **Module:** `remont_core` (Odoo addon)

---

## 1. Overview

The Project Management Module customizes Odoo's project framework for apartment renovation workflows. It provides 8 renovation-specific stages (demolition through finishing), a Gantt view for scheduling, checklist-based stage completion, a multi-project Kanban dashboard for contractors, and stage dependency tracking.

This feature enhances the existing `remont_core` addon skeleton with the full data model defined in Architecture.md and Specification.md (US-PM-01, US-PM-02, US-PM-03).

---

## 2. User Stories

### US-PM-01: Gantt Chart Scheduling

**As a** contractor,
**I want** a Gantt chart for renovation scheduling,
**So that** I can plan and visualize the project timeline.

**Acceptance Criteria:**

| # | Criterion |
|---|-----------|
| AC-12.1 | Given a project with 8 stages, when the Gantt view loads, all 8 stages render as horizontal bars with correct date spans |
| AC-12.2 | Given a contractor drags a stage bar to new dates, the stage's planned_start and planned_end update in the database |
| AC-12.3 | Given CV detects a stage transition, the Gantt chart marks the previous stage as complete (100%) automatically |
| AC-12.4 | Given "Export PDF" is clicked, a PDF containing the Gantt chart downloads within 10 seconds |

### US-PM-02: Multi-Project Management

**As a** contractor,
**I want to** manage multiple renovation projects simultaneously,
**So that** I can run my business efficiently.

**Acceptance Criteria:**

| # | Criterion |
|---|-----------|
| AC-13.1 | Given a contractor with 5 active projects, the dashboard shows all 5 project cards with status badges |
| AC-13.2 | Given a filter by "in_progress" status, only projects with that status are displayed |
| AC-13.3 | Given two projects have overlapping crew assignments, the resource allocation view highlights the conflict |

### US-PM-03: Checklist-Based Stage Completion

**As a** contractor,
**I want** checklist-based stage completion tracking,
**So that** I can verify work quality before moving to the next stage.

**Acceptance Criteria:**

| # | Criterion |
|---|-----------|
| AC-14.1 | Given a stage "electrical" with 4 checklist items, when 3 are checked, the stage shows 75% checklist completion |
| AC-14.2 | Given a stage with unchecked items, when a contractor tries to mark the stage complete, the system rejects with "Complete all checklist items first" |
| AC-14.3 | Given a checklist item, when a contractor attaches a photo, the photo is stored and linked to the checklist item record |

---

## 3. Data Model

### 3.1 remont.project (extends project.project)

| Field | Type | Description | Constraint |
|-------|------|-------------|------------|
| name | Char | Project name | Required (inherited) |
| address | Char | Apartment address | -- |
| area_sqm | Float | Area in square meters | >= 0 |
| type | Selection | `new` / `renovation` | Default: `renovation` |
| currency_id | Many2one(res.currency) | Currency for monetary fields | Default: company currency |
| budget_estimate | Monetary | Estimated budget | NUMERIC(12,2), >= 0 |
| budget_actual | Monetary | Actual spend | NUMERIC(12,2), >= 0 |
| start_date | Date | Project start date | -- |
| end_date_plan | Date | Planned end date | Must be >= start_date |
| end_date_predict | Date | AI-predicted end date | -- |
| status | Selection | `draft`, `planning`, `in_progress`, `completed`, `on_hold`, `cancelled` | Default: `draft`, tracking |
| owner_id | Many2one(res.users) | Homeowner | Tracking |
| contractor_id | Many2one(res.users) | Contractor | Tracking |
| stage_ids | One2many(remont.stage) | Renovation stages | -- |
| overall_progress | Float (computed) | Weighted average of stage progress | Stored, 0-100 |

### 3.2 remont.stage

| Field | Type | Description | Constraint |
|-------|------|-------------|------------|
| name | Selection | 8 renovation stages | Required |
| project_id | Many2one(remont.project) | Parent project | Required, cascade |
| sequence | Integer | Ordering | Default: 10 |
| status | Selection | `planned`, `in_progress`, `done` | Default: `planned` |
| progress_pct | Float | Progress percentage | 0-100 |
| weight | Float | Weight for overall progress calc | Default: 1.0 |
| planned_start | Date | Planned start date | -- |
| planned_end | Date | Planned end date | Must be >= planned_start |
| actual_start | Date | Actual start date | -- |
| actual_end | Date | Actual end date | -- |
| dependency_ids | Many2many(remont.stage) | Predecessor stages | -- |
| checklist_ids | One2many(remont.checklist.item) | Checklist items | -- |
| checklist_progress | Float (computed) | % of checklist items done | Stored |

### 3.3 remont.checklist.item

| Field | Type | Description | Constraint |
|-------|------|-------------|------------|
| name | Char | Checklist item description | Required |
| stage_id | Many2one(remont.stage) | Parent stage | Required, cascade |
| is_done | Boolean | Completion flag | Default: False |
| completed_by | Many2one(res.users) | Who completed | -- |
| completed_at | Datetime | When completed | -- |
| photo_attachment_id | Many2one(ir.attachment) | Photo evidence | -- |

### 3.4 Stage Name Enum

| Value | Label | Sequence |
|-------|-------|----------|
| demolition | Demolition | 10 |
| electrical | Electrical | 20 |
| plumbing | Plumbing | 30 |
| plaster | Plaster | 40 |
| screed | Screed | 50 |
| tiles | Tiles | 60 |
| painting | Painting | 70 |
| finishing | Finishing | 80 |

---

## 4. Views

### 4.1 Gantt View (US-PM-01)

- Odoo built-in `<gantt>` view on `remont.stage`
- `date_start="planned_start"`, `date_stop="planned_end"`
- Color-coded by stage status (planned=grey, in_progress=blue, done=green)
- Grouped by `project_id` for multi-project visibility
- Drag-and-drop rescheduling via Odoo Gantt

### 4.2 Kanban View (US-PM-02)

- Kanban view on `remont.project`
- Cards show: name, address, status badge, overall_progress bar, owner, contractor
- Grouped by `status` field
- Filter presets: All, In Progress, Completed, On Hold

### 4.3 Stage Form (US-PM-03)

- Enhanced stage form with checklist tab
- Inline editable checklist items with photo attachment support
- "Mark Complete" button with validation (all checklist items must be done)

---

## 5. Business Rules

1. **Stage cannot be marked `done` if any checklist item is unchecked** (AC-14.2)
2. **Overall project progress** = weighted average of stage progress_pct values
3. **Status workflow**: `draft` -> `planning` -> `in_progress` -> `completed` (or `on_hold`/`cancelled` from any state)
4. **Budget fields use `fields.Monetary`** backed by PostgreSQL NUMERIC(12,2)
5. **Python financial calculations use `decimal.Decimal`**, never `float`
6. **Stage dependencies**: a stage cannot start (move to `in_progress`) if any predecessor stage is not `done`

---

## 6. Security & Access

| Model | Group | Read | Write | Create | Delete |
|-------|-------|------|-------|--------|--------|
| remont.project | User | Yes | No | No | No |
| remont.project | Admin | Yes | Yes | Yes | Yes |
| remont.stage | User | Yes | No | No | No |
| remont.stage | Admin | Yes | Yes | Yes | Yes |
| remont.checklist.item | User | Yes | Yes | No | No |
| remont.checklist.item | Admin | Yes | Yes | Yes | Yes |

---

## 7. Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `models/project.py` | Modify | Add status `planning`/`on_hold`, overall_progress computed field |
| `models/stage.py` | Modify | Add weight, dependency_ids, checklist_ids, checklist_progress, stage completion constraint |
| `models/checklist_item.py` | Create | New model for checklist items |
| `models/__init__.py` | Modify | Import checklist_item |
| `views/project_views.xml` | Modify | Add Kanban view |
| `views/stage_views.xml` | Modify | Add Gantt view, enhance form with checklist tab |
| `views/menus.xml` | Modify | Add Gantt/Kanban menu items |
| `security/ir.model.access.csv` | Modify | Add checklist.item ACL |
| `__manifest__.py` | Modify | Add new view files |
| `tests/test_project.py` | Modify | Add tests for new functionality |

---

*End of specification.*
