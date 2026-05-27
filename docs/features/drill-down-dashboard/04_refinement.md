# Refinement: Drill-Down Dashboard
## Edge Cases
| Edge Case | Handling |
|-----------|----------|
| No stages yet | Show "Этапы не созданы" message |
| All stages planned (no actual dates) | delay_days = 0, all green |
| API timeout for AI summary | Show error toast, keep old summary |
| Budget = 0 | Skip budget card, show "Бюджет не указан" |
| No snapshots for a stage | Show "Нет снимков" in drill-down |
