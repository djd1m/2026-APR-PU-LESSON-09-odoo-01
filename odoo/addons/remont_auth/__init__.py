from . import models
from . import controllers
from .controllers.startup_validation import validate_environment


def _post_init_validate_env(env):
    """Post-init hook: validate required environment variables.

    Called when the module is installed. Crashes if security-critical
    env vars are missing — NO silent fallbacks.
    """
    validate_environment()
