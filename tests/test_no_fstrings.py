
def test_no_fstrings():
    from pathlib import Path
    import ast
    pkg_path = Path(__file__).absolute().parent.parent
    py_paths = list((pkg_path / 'kpa').rglob('*.py')) + list(pkg_path.glob('*.py'))
    for py_path in py_paths:
        parsed = ast.parse(py_path.read_text())
        for node in ast.walk(parsed):
            assert not isinstance(node, ast.FormattedValue), (py_path, node.lineno)
