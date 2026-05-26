# Architecture: Project Management (project-mgmt)

## Module: remont_core

### Models
- `remont.project` — extends `project.project`: address, area_sqm, type, budget (Monetary), dates, owner/contractor, status, progress_pct
- `remont.stage` — 8 renovation stages: name (Selection), progress_pct, planned/actual dates, sequence, status, checklist_ids
- `remont.checklist.item` — per-stage checklist: name, is_done, stage_id

### Views
- Project form with tabs: General, Stages, Budget, Cameras, Alerts
- Project tree with progress bar and status badges
- Project Kanban by status
- Stage inline tree within project form
- Menu: RemontERP → Projects → All Projects

### Security
- Record rules: owner sees own projects, contractor sees assigned, admin sees all
