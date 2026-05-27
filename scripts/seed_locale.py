"""Activate ru_RU language and set as default for admin + DB.

Runs inside Odoo container as: python3 /tmp/seed_locale.py

Steps:
  1. Activate ru_RU via res.lang._activate_lang
  2. Set admin user lang to ru_RU
  3. Reload .po translations for all remont_* modules
  4. Set ru_RU as the default language for new users (ir.default)
"""
import odoo
import odoo.modules.registry
from odoo import api, SUPERUSER_ID

DBNAME = "remont_erp"
TARGET_LANG = "ru_RU"
REMONT_MODULES = [
    "remont_core", "remont_auth", "remont_camera", "remont_portal",
    "remont_cv", "remont_timelapse", "remont_alerts", "remont_billing",
    "remont_referral",
]


def main():
    registry = odoo.modules.registry.Registry(DBNAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # 1. Activate ru_RU
        Lang = env["res.lang"]
        ru = Lang.with_context(active_test=False).search(
            [("code", "=", TARGET_LANG)], limit=1
        )
        if not ru:
            print(f"Loading language {TARGET_LANG}")
            Lang._activate_lang(TARGET_LANG)
            ru = Lang.with_context(active_test=False).search(
                [("code", "=", TARGET_LANG)], limit=1
            )
        elif not ru.active:
            print(f"Activating language {TARGET_LANG}")
            ru.write({"active": True})
        else:
            print(f"Language {TARGET_LANG} already active (id={ru.id})")

        # 2. Set admin lang
        admin = env.ref("base.user_admin")
        admin.write({"lang": TARGET_LANG})
        print(f"Admin user lang set to {TARGET_LANG}")

        # 3. Reload .po translations for remont_* modules
        installed = env["ir.module.module"].search([
            ("name", "in", REMONT_MODULES),
            ("state", "=", "installed"),
        ])
        for module in installed:
            print(f"Loading translations for {module.name}")
            module._update_translations(filter_lang=[TARGET_LANG])

        # 4. Default lang for new users (via res.users default)
        IrDefault = env["ir.default"]
        IrDefault.set("res.users", "lang", TARGET_LANG)
        print(f"Default user lang set to {TARGET_LANG}")

        cr.commit()
        print("OK — ru_RU activated and translations loaded")


if __name__ == "__main__":
    main()
