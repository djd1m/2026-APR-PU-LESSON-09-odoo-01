# Pseudocode: Client Portal (client-portal)

## Routes
```python
GET /my/projects → list user's projects (filter owner_id = current_user)
GET /my/projects/<id> → project detail: timeline, stages, budget, timelapse
GET /share/<token> → public timelapse page (no auth)
```

## Portal Controller
```python
class PortalController(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        # Add project count to portal home
        values['project_count'] = env['remont.project'].search_count(
            [('owner_id', '=', request.uid)])
        return values

    @route('/my/projects')
    def portal_my_projects(self):
        projects = env['remont.project'].search([('owner_id', '=', request.uid)])
        return request.render('remont_portal.portal_my_projects', {'projects': projects})

    @route('/my/projects/<int:project_id>')
    def portal_project_detail(self, project_id):
        project = env['remont.project'].browse(project_id)
        # ACL: verify current user is owner
        if project.owner_id.id != request.uid:
            raise AccessError("Access denied")
        return request.render('remont_portal.portal_project_detail', {'project': project})

    @route('/share/<string:token>')
    def portal_share(self, token):
        timelapse = env['remont.timelapse'].sudo().search(
            [('share_token', '=', token)], limit=1)
        if not timelapse:
            raise NotFound()
        return request.render('remont_portal.portal_share', {'timelapse': timelapse})
```
