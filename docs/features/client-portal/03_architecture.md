# Architecture: Client Portal (client-portal)

## Module: remont_portal
- Extends Odoo Website Portal
- QWeb templates for project list, detail, share pages
- Record rules: portal users see only own projects
- Responsive CSS (mobile 375px+)

## Security
- ACL: portal users get read-only access to their projects
- Record rules in portal_rules.xml
- Share page: public (no auth), but only exposes timelapse video
