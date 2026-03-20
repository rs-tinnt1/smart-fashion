from copy import deepcopy
from typing import Any

DEFAULT_STARTUP_STATUS = {
    "storage": {"ready": False, "detail": "not initialized"},
    "database": {"ready": False, "detail": "deferred until first database request"},
    "model": {"ready": False, "detail": "not initialized"},
}


def initialize_runtime_state(application: Any) -> None:
    application.state.startup_status = deepcopy(DEFAULT_STARTUP_STATUS)
    application.state.startup_warnings = []


def set_runtime_component(application: Any, component: str, ready: bool, detail: str) -> None:
    startup_status = getattr(application.state, "startup_status", None)
    if startup_status is None:
        startup_status = deepcopy(DEFAULT_STARTUP_STATUS)
        application.state.startup_status = startup_status
    startup_status[component] = {"ready": ready, "detail": detail}


def add_runtime_warning(application: Any, message: str) -> None:
    warnings = getattr(application.state, "startup_warnings", None)
    if warnings is None:
        warnings = []
        application.state.startup_warnings = warnings
    if message not in warnings:
        warnings.append(message)


def get_runtime_snapshot(application: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    startup_status = deepcopy(getattr(application.state, "startup_status", DEFAULT_STARTUP_STATUS))
    startup_warnings = list(getattr(application.state, "startup_warnings", []))
    return startup_status, startup_warnings
