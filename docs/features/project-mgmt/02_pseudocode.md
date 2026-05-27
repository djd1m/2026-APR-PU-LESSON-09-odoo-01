# Pseudocode: Project Management (project-mgmt)

## 1. Project Creation

```python
def create_project(owner_id, name, address, area_sqm, type, budget_estimate):
    """Create renovation project with auto-generated stages."""
    project = env['remont.project'].create({
        'name': name,
        'address': address,
        'area_sqm': area_sqm,
        'type': type,  # 'new' or 'renovation'
        'budget_estimate': Decimal(str(budget_estimate)),
        'owner_id': owner_id,
        'status': 'draft',
    })

    # Auto-create 8 renovation stages
    STAGES = [
        ('demolition', 'Demolition', 1),
        ('electrical', 'Electrical', 2),
        ('plumbing', 'Plumbing', 3),
        ('plaster', 'Plaster', 4),
        ('screed', 'Floor Screed', 5),
        ('tiles', 'Tiles', 6),
        ('painting', 'Painting', 7),
        ('finishing', 'Finishing', 8),
    ]
    for stage_name, stage_label, seq in STAGES:
        env['remont.stage'].create({
            'name': stage_name,
            'project_id': project.id,
            'sequence': seq,
            'status': 'planned',
            'progress_pct': 0.0,
        })

    return project
```

## 2. Stage Progress Update

```python
def update_stage_progress(project_id, stage_name, progress_pct):
    """Update stage progress. Called by CV worker or manually."""
    stage = env['remont.stage'].search([
        ('project_id', '=', project_id),
        ('name', '=', stage_name),
    ], limit=1)

    if not stage:
        return

    vals = {'progress_pct': min(progress_pct, 100.0)}

    if progress_pct > 0 and stage.status == 'planned':
        vals['status'] = 'in_progress'
        vals['actual_start'] = fields.Date.today()

    if progress_pct >= 95:
        vals['status'] = 'done'
        vals['actual_end'] = fields.Date.today()

    stage.write(vals)

    # Update overall project progress
    all_stages = env['remont.stage'].search([('project_id', '=', project_id)])
    overall = sum(s.progress_pct for s in all_stages) / len(all_stages)
    env['remont.project'].browse(project_id).write({'progress_pct': overall})
```

## 3. Project Status Workflow

```
draft → in_progress → completed
  ↓                       ↑
  └───→ cancelled         │
                          │
  (auto when all stages done)
```
