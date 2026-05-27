"""JSON-RPC client for communicating with Odoo."""

import logging
import xmlrpc.client

logger = logging.getLogger(__name__)


class OdooClient:
    """Communicate with Odoo via XML-RPC."""

    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self._uid = None

    @property
    def uid(self):
        if self._uid is None:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self._uid = common.authenticate(self.db, self.username, self.password, {})
            if not self._uid:
                raise ConnectionError(f"Failed to authenticate with Odoo at {self.url}")
            logger.info(f"Authenticated with Odoo as uid={self._uid}")
        return self._uid

    @property
    def models(self):
        return xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

    def execute(self, model: str, method: str, *args, **kwargs):
        return self.models.execute_kw(
            self.db, self.uid, self.password,
            model, method, list(args), kwargs
        )

    def update_snapshot(self, snapshot_id: int, stage: str, confidence: float,
                        model_version: str = None, explanation: str = None):
        """Update snapshot with CV detection result."""
        vals = {
            'stage_detected': stage,
            'cv_confidence': confidence,
        }
        if model_version:
            vals['model_version'] = model_version
        if explanation:
            vals['cv_explanation'] = explanation
        self.execute('remont.snapshot', 'write', [snapshot_id], vals)
        logger.info(
            "Updated snapshot %s: stage=%s, confidence=%.2f, backend=%s",
            snapshot_id, stage, confidence, model_version or "N/A",
        )

    def update_stage_progress(self, project_id: int, detected_stage: str):
        """Update project stage progress based on detection."""
        # Find the stage record
        stage_ids = self.execute('remont.stage', 'search', [
            ('project_id', '=', project_id),
            ('name', '=', detected_stage),
        ])

        if not stage_ids:
            logger.warning(f"No stage record for project={project_id}, stage={detected_stage}")
            return

        # Get recent snapshots for progress calculation
        recent = self.execute('remont.snapshot', 'search_read', [
            ('project_id', '=', project_id),
            ('cv_confidence', '>=', 0.7),
        ], {'limit': 20, 'order': 'captured_at desc', 'fields': ['stage_detected']})

        if not recent:
            return

        # Count dominant stage
        stage_counts = {}
        for snap in recent:
            s = snap['stage_detected']
            stage_counts[s] = stage_counts.get(s, 0) + 1

        dominant = max(stage_counts, key=stage_counts.get)
        progress = (stage_counts.get(dominant, 0) / len(recent)) * 100

        if dominant == detected_stage:
            update_vals = {
                'progress_pct': min(progress, 100),
                'status': 'done' if progress >= 95 else 'in_progress',
            }
            self.execute('remont.stage', 'write', stage_ids, update_vals)
            logger.info(f"Updated stage {detected_stage}: progress={progress:.0f}%")
