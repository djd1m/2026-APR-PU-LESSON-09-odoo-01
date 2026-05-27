# Feature Specification: Drill-Down Dashboard

> **Feature ID:** drill-down-dashboard
> **Date:** 2026-05-27
> **Priority:** P0
> **Complexity:** High (+11)

## Overview

Interactive dashboard for renovation project monitoring with drill-down capability:
- **Level 1 (Project):** Overall progress, budget, timeline with delay prediction
- **Level 2 (Stage):** Per-stage plan vs actual with delay indicators (green/yellow/red)
- **Level 3 (Snapshots):** Photos for selected stage with AI analysis, confidence, explanations
- **AI Summary:** Cloud.ru vLLM generates natural language project status summary

## User Stories

### US-DD-01: Project Overview Dashboard

**As a** homeowner or contractor,
**I want to** see a project dashboard with overall progress, budget status, and timeline,
**So that** I understand the current state of my renovation at a glance.

**Acceptance Criteria:**
| # | Criterion |
|---|-----------|
| 1 | Dashboard shows: project name, address, area, overall progress bar |
| 2 | Budget card: estimate vs actual, remaining, % consumed with color (green ≤80%, yellow 80-100%, red >100%) |
| 3 | Timeline: planned end date, predicted end date (from AI), delay in days |
| 4 | Stage summary table: 8 stages with status, progress %, planned/actual dates |
| 5 | Color coding per stage: green (on time), yellow (≤3 days delay), red (>3 days delay) |

### US-DD-02: Stage Drill-Down

**As a** homeowner,
**I want to** click on a stage to see its photos and AI analysis,
**So that** I can verify what work was done and understand delays.

**Acceptance Criteria:**
| # | Criterion |
|---|-----------|
| 1 | Click stage row → shows filtered list of snapshots for that stage |
| 2 | Each snapshot shows: thumbnail, date, CV confidence, AI explanation |
| 3 | Back button returns to project dashboard |

### US-DD-03: AI Project Summary (Cloud.ru vLLM)

**As a** homeowner,
**I want to** see an AI-generated text summary of my renovation status,
**So that** I get a human-readable overview without interpreting charts.

**Acceptance Criteria:**
| # | Criterion |
|---|-----------|
| 1 | Button "Сгенерировать AI отчёт" on project dashboard |
| 2 | Sends project data (stages, progress, budget, delays) to Cloud.ru vLLM |
| 3 | Displays 3-5 sentence summary in Russian |
| 4 | Summary includes: current stage, delays, budget status, predicted completion |
| 5 | Summary cached for 1 hour (avoid repeated API calls) |

## Architecture

```
Odoo Views (XML)
├── project_dashboard_view.xml    ← Kanban/form with dashboard widgets
├── stage_drilldown_action.xml    ← Action to filter snapshots by stage
└── project_ai_summary.py        ← Controller calling Cloud.ru API

Cloud.ru API (vLLM)
└── Text completion (not vision) for generating project summary
    Model: Qwen/Qwen3.5-397B-A17B or GigaChat/GigaChat-2-Max
```

## Data Model Changes

| Model | Field | Type | Description |
|-------|-------|------|-------------|
| remont.project | ai_summary | Text | Cached AI-generated summary |
| remont.project | ai_summary_date | Datetime | When summary was last generated |
| remont.project | delay_days | Integer(computed) | Total delay in days vs plan |
| remont.stage | delay_days | Integer(computed) | Delay for this stage |
| remont.stage | delay_status | Selection(computed) | green/yellow/red |
