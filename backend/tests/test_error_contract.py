import ast
from pathlib import Path

from app import errors
from app.transport import error_mapper

PROJECT_ROOT = Path(__file__).resolve().parents[1] / "app"


def _collect_imports(file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text())
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_domain_errors_infra_free() -> None:
    domain_errors_file = PROJECT_ROOT / "errors" / "domain.py"
    imports = _collect_imports(domain_errors_file)
    forbidden_prefixes = ("fastapi", "sqlalchemy", "httpx", "app.")
    assert not any(imp.startswith(forbidden_prefixes) for imp in imports)


def test_use_cases_do_not_import_app_error() -> None:
    use_cases_dir = PROJECT_ROOT / "use_cases"
    for file_path in use_cases_dir.rglob("*.py"):
        tree = ast.parse(file_path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and any(
                alias.name == "AppError" for alias in node.names
            ):
                assert False, f"{file_path} imports AppError"
            if isinstance(node, ast.Import) and any(alias.name.endswith("AppError") for alias in node.names):
                assert False, f"{file_path} imports AppError"


def test_routers_do_not_import_domain_errors() -> None:
    routers_dir = PROJECT_ROOT / "routers"
    for file_path in routers_dir.rglob("*.py"):
        imports = _collect_imports(file_path)
        assert not any("errors.domain" in imp for imp in imports), f"{file_path} imports domain errors"


def test_error_mapper_covers_public_errors() -> None:
    handled = set(error_mapper.HANDLED_EXCEPTION_TYPES)
    public = set(errors.PUBLIC_ERRORS)
    missing = {err for err in public if err not in handled}
    assert not missing, f"Mapper does not cover: {missing}"
