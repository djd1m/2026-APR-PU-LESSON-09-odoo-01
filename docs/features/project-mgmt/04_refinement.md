# Refinement: Project Management (project-mgmt)

## Edge Cases
| Edge Case | Handling |
|-----------|----------|
| Project created without stages | Auto-create 8 default stages |
| Stage progress set > 100 | Clamp to 100 |
| All stages complete | Auto-set project status to 'completed' |
| Stage regression (progress decreases) | Allow — CV may re-detect earlier stage |
| Budget fields use float | BLOCKED — must use Monetary/Decimal |

## Tests
| Test | Validates |
|------|-----------|
| test_project_creates_8_stages | Auto-creation of stages |
| test_stage_progress_clamp | progress_pct clamped at 100 |
| test_project_auto_complete | All stages done → project completed |
| test_budget_monetary_field | Budget uses Monetary type |
