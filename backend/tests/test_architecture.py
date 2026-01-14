import ast
from pathlib import Path

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


def test_use_cases_do_not_import_crud() -> None:
    use_cases_dir = PROJECT_ROOT / "use_cases"
    for file_path in use_cases_dir.rglob("*.py"):
        imports = _collect_imports(file_path)
        forbidden = [
            imp
            for imp in imports
            if imp.startswith("app.crud") or imp.startswith(".crud") or imp.startswith("..crud")
        ]
        assert not forbidden, f"{file_path} imports infrastructure modules: {forbidden}"


def test_domain_has_no_infrastructure_dependencies() -> None:
    domain_dir = PROJECT_ROOT / "domain"
    forbidden_prefixes = (
        "fastapi",
        "sqlalchemy",
        "httpx",
        "app.crud",
        "app.routers",
        "app.database",
        "app.dependencies",
    )
    for file_path in domain_dir.rglob("*.py"):
        imports = _collect_imports(file_path)
        offending = [
            imp for imp in imports
            if any(imp.startswith(prefix) for prefix in forbidden_prefixes)
        ]
        assert not offending, f"{file_path} depends on infrastructure: {offending}"
