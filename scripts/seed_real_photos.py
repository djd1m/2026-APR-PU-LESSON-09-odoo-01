"""Seed remont.snapshot records from /tmp/test_photos via ir.attachment.

Each photo becomes a public ir.attachment served at /web/image/<id>,
and a remont.snapshot is created pointing at that URL with realistic
diagnostic fields per stage.
"""
import os
import base64
from datetime import datetime, timedelta

import odoo
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

DBNAME = "remont_erp"
PHOTOS_ROOT = "/tmp/test_photos"

DIAGNOSTICS = {
    "demolition": {
        "conf": 0.92, "backend": "yolo", "mv": "yolov8n-v1.2",
        "expl": None,
    },
    "electrical": {
        "conf": 0.81, "backend": "vllm", "mv": "qwen2.5-vl-7b",
        "expl": "Видна разводка электропроводки в штробах. Кабели уложены, "
                "розеточные коробки установлены, штрабы готовы к заделке.",
    },
    "plumbing": {
        "conf": 0.55, "backend": "yolo", "mv": "yolov8n-v1.2",
        "expl": None,
    },
    "plaster": {
        "conf": 0.88, "backend": "vllm", "mv": "qwen2.5-vl-7b",
        "expl": "Стены оштукатурены, поверхность серая, свежая. "
                "Электрические провода уже скрыты в штробах. Готово к шпаклёвке.",
    },
    "screed": {
        "conf": 0.79, "backend": "yolo", "mv": "yolov8n-v1.2",
        "expl": None,
    },
    "tiles": {
        "conf": 0.94, "backend": "vllm", "mv": "qwen2.5-vl-7b",
        "expl": "Уложена керамическая плитка. Видны крестики для выравнивания швов, "
                "затирка ещё не выполнена.",
    },
    "painting": {
        "conf": 0.41, "backend": "yolo", "mv": "yolov8n-v1.2",
        "expl": None,
    },
    "finishing": {
        "conf": 0.96, "backend": "vllm", "mv": "qwen2.5-vl-7b",
        "expl": "Финишная отделка завершена: уложен ламинат, установлен плинтус, "
                "поклеены обои, смонтированы розетки и выключатели.",
    },
}

STAGE_ORDER = [
    "demolition", "electrical", "plumbing", "plaster",
    "screed", "tiles", "painting", "finishing",
]


def main():
    registry = odoo.modules.registry.Registry(DBNAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        project = env["remont.project"].search([], limit=1)
        if not project:
            print("ERROR: no remont.project found, create one first")
            return

        old_snaps = env["remont.snapshot"].search([])
        old_count = len(old_snaps)
        old_attach_names = ["snapshot_" + s + "_" for s in STAGE_ORDER]
        old_attachments = env["ir.attachment"].search([
            "|", ("name", "=like", "snapshot\\_%"),
            ("name", "=like", "snapshot_%.jpg"),
        ])
        old_snaps.unlink()
        old_attachments.unlink()
        print(f"Cleared {old_count} old snapshots and "
              f"{len(old_attachments)} old attachments")

        now = datetime.now()
        created = 0
        idx = 0
        for stage in STAGE_ORDER:
            stage_dir = os.path.join(PHOTOS_ROOT, stage)
            if not os.path.isdir(stage_dir):
                continue
            files = sorted(
                f for f in os.listdir(stage_dir)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            )
            d = DIAGNOSTICS.get(stage, {"conf": 0.0, "backend": "", "mv": "", "expl": None})

            for fname in files:
                fpath = os.path.join(stage_dir, fname)
                with open(fpath, "rb") as fp:
                    raw = fp.read()
                b64 = base64.b64encode(raw)

                mimetype = "image/jpeg" if fname.lower().endswith((".jpg", ".jpeg")) else "image/png"
                attachment = env["ir.attachment"].create({
                    "name": f"snapshot_{stage}_{fname}",
                    "datas": b64,
                    "mimetype": mimetype,
                    "public": True,
                    "res_model": "remont.snapshot",
                    "type": "binary",
                })
                # res_id will be set after snapshot create

                image_url = f"/web/image/{attachment.id}"
                thumb_url = f"/web/image/{attachment.id}?width=240&height=180"

                captured = now - timedelta(hours=idx * 5)
                snap = env["remont.snapshot"].create({
                    "project_id": project.id,
                    "image_url": image_url,
                    "thumbnail_url": thumb_url,
                    "captured_at": captured,
                    "stage_detected": stage,
                    "cv_confidence": d["conf"],
                    "cv_backend": d["backend"] or False,
                    "model_version": d["mv"] or False,
                    "cv_explanation": d["expl"] or False,
                })
                attachment.write({"res_id": snap.id})
                created += 1
                idx += 1

        cr.commit()
        print(f"OK — created {created} snapshots from real photos in {PHOTOS_ROOT}")


if __name__ == "__main__":
    main()
