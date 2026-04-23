from __future__ import annotations

import importlib
import os
import sys
import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


FORBIDDEN_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
}
FORBIDDEN_SUFFIXES = {
    ".db",
    ".sqlite",
    ".pyc",
}
FORBIDDEN_FILES = {
    ".env",
    "secrets.toml",
}


def fail(message: str) -> None:
    raise SystemExit(f"pre-deploy check failed: {message}")


def load_app(target_root: Path, db_path: Path):
    target_root = target_root.resolve()
    sys.path = [str(target_root), *[entry for entry in sys.path if Path(entry).resolve() != target_root]]
    os.environ["PETMATE_DB_PATH"] = str(db_path)
    importlib.invalidate_caches()
    for module_name in [name for name in sys.modules if name == "app" or name.startswith("app.")]:
        sys.modules.pop(module_name, None)

    module = importlib.import_module("app.main")
    module_path = Path(module.__file__).resolve()
    expected_path = (target_root / "app" / "main.py").resolve()
    if module_path != expected_path:
        fail(f"imported wrong app.main: {module_path} != {expected_path}")
    return module.app


def check_project_tree(root: Path, strict_generated_files: bool) -> None:
    required = [
        "streamlit_app.py",
        "requirements.txt",
        ".streamlit/config.toml",
        "app/main.py",
        "app/database.py",
        "static/icon.svg",
        "static/manifest.webmanifest",
    ]
    for relative in required:
        if not (root / relative).exists():
            fail(f"missing {relative}")

    for path in root.rglob("*"):
        if strict_generated_files and any(part in FORBIDDEN_NAMES for part in path.parts):
            fail(f"forbidden cache/env directory included: {path}")
        if path.name in FORBIDDEN_FILES:
            fail(f"forbidden secret/env file included: {path}")
        if strict_generated_files and path.suffix in FORBIDDEN_SUFFIXES:
            fail(f"forbidden generated data file included: {path}")


def check_api_smoke(root: Path) -> None:
    db_path = Path(tempfile.gettempdir()) / f"petmate_predeploy_{abs(hash(str(root.resolve())))}.db"
    if db_path.exists():
        db_path.unlink()
    app = load_app(root, db_path)
    try:
        with TestClient(app) as client:
            response = client.get("/health")
            if response.status_code != 200 or response.json().get("status") != "ok":
                fail("/health did not return ok")

            child = client.post(
                "/api/child/create",
                json={"name": "部署检查", "age": 8, "guardian_name": "家长"},
            )
            if child.status_code >= 400:
                fail(f"child create failed: {child.text}")
            child_id = child.json()["child"]["id"]

            pet = client.post("/api/pet/create", json={"child_id": child_id, "name": "豆豆"})
            if pet.status_code >= 400:
                fail(f"pet create failed: {pet.text}")

            adventure = client.get("/api/adventure/today", params={"child_id": child_id})
            if adventure.status_code >= 400:
                fail(f"today adventure failed: {adventure.text}")

            settings = client.get("/api/parent/settings", params={"child_id": child_id})
            if settings.status_code >= 400:
                fail(f"parent settings failed: {settings.text}")
    finally:
        os.environ.pop("PETMATE_DB_PATH", None)
        if db_path.exists():
            for _ in range(5):
                try:
                    db_path.unlink()
                    break
                except PermissionError:
                    time.sleep(0.2)


def main() -> None:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT
    strict_generated_files = root != ROOT
    check_project_tree(root, strict_generated_files)
    check_api_smoke(root)
    print(f"pre-deploy check passed: {root}")


if __name__ == "__main__":
    main()
