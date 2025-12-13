"""Test to verify that the package can be built and is ready for PyPI distribution.

This test ensures:
- Package can be built successfully
- Package metadata is correct
- Required files are included
- Package structure is valid
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Handle TOML parsing for different Python versions
try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Python < 3.11
    except ImportError:
        tomllib = None


def test_package_can_be_built():
    """Test that the package can be built using uv build."""
    project_root = Path(__file__).parent.parent

    # Change to project root directory
    original_cwd = os.getcwd()
    try:
        os.chdir(project_root)

        # Run uv build
        result = subprocess.run(
            ["uv", "build"],
            capture_output=True,
            text=True,
            check=False,
        )

        # Check if build was successful
        assert result.returncode == 0, (
            f"uv build failed with return code {result.returncode}.\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}"
        )

        # Verify dist directory was created
        dist_dir = project_root / "dist"
        assert dist_dir.exists(), "dist directory was not created"

        # Verify both wheel and sdist were created
        wheel_files = list(dist_dir.glob("*.whl"))
        sdist_files = list(dist_dir.glob("*.tar.gz"))

        assert len(wheel_files) > 0, "No wheel file was created"
        assert len(sdist_files) > 0, "No source distribution file was created"

    finally:
        os.chdir(original_cwd)


def test_package_metadata_is_correct():
    """Test that package metadata in pyproject.toml is correct."""
    if tomllib is None:
        pytest.skip("tomllib or tomli is required to parse pyproject.toml")

    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    assert pyproject_path.exists(), "pyproject.toml not found"

    # Read and parse pyproject.toml
    with open(pyproject_path, "rb") as f:
        config = tomllib.load(f)

    project_config = config.get("project", {})

    # Verify required fields
    assert "name" in project_config, "Package name is missing"
    assert "version" in project_config, "Package version is missing"
    assert "description" in project_config, "Package description is missing"
    assert "authors" in project_config, "Package authors are missing"
    assert "license" in project_config, "Package license is missing"
    assert "readme" in project_config, "Package readme is missing"

    # Verify name format (should be valid for PyPI)
    # PyPI allows: letters, numbers, hyphens, underscores, and periods
    name = project_config["name"]
    # Remove allowed characters and check if anything remains
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_. ")
    assert all(c in allowed_chars for c in name), (
        f"Package name '{name}' contains invalid characters for PyPI"
    )
    assert len(name) > 0, "Package name cannot be empty"

    # Verify license matches classifier
    license_value = project_config["license"]
    # Handle both string and dict format for license
    if isinstance(license_value, dict):
        license_value = license_value.get("text", "")
    classifiers = project_config.get("classifiers", [])
    license_classifier = f"License :: OSI Approved :: {license_value} License"
    assert license_classifier in classifiers, (
        f"License classifier '{license_classifier}' not found in classifiers. "
        f"Found: {classifiers}"
    )


def test_required_files_are_included():
    """Test that all required files are included in the package."""
    if tomllib is None:
        pytest.skip("tomllib or tomli is required to parse pyproject.toml")

    project_root = Path(__file__).parent.parent

    # Check MANIFEST.in for included files (setuptools uses MANIFEST.in)
    manifest_path = project_root / "MANIFEST"
    if manifest_path.exists():
        with open(manifest_path) as f:
            manifest_content = f.read()

        # Check that required files are mentioned in MANIFEST
        required_files = ["README.md", "LICENSE"]
        for required_file in required_files:
            assert required_file in manifest_content, (
                f"Required file '{required_file}' is not included in MANIFEST"
            )

    # Verify files actually exist
    for required_file in required_files:
        file_path = project_root / required_file
        assert file_path.exists(), f"Required file '{required_file}' does not exist"


def test_package_structure_is_valid():
    """Test that the package structure is valid for PyPI."""
    project_root = Path(__file__).parent.parent

    # Verify main package directory exists
    package_dir = project_root / "sqlalchemy_serializer"
    assert package_dir.exists(), "Main package directory 'sqlalchemy_serializer' not found"
    assert package_dir.is_dir(), "sqlalchemy_serializer is not a directory"

    # Verify __init__.py exists in main package
    init_file = package_dir / "__init__.py"
    assert init_file.exists(), "__init__.py not found in main package"

    # Verify core modules exist
    core_modules = ["serializer.py", "lib"]
    for module in core_modules:
        module_path = package_dir / module
        assert module_path.exists(), f"Core module '{module}' not found"


def test_package_can_be_installed():
    """Test that the built package can be installed in a clean environment."""
    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist"

    # Skip if dist directory doesn't exist (build might not have run)
    if not dist_dir.exists():
        pytest.skip("dist directory not found. Run uv build first.")

    # Find the wheel file
    wheel_files = list(dist_dir.glob("*.whl"))
    if not wheel_files:
        pytest.skip("No wheel file found. Run uv build first.")

    wheel_file = wheel_files[0]

    # Create a temporary virtual environment
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "test_venv"

        # Create virtual environment
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
        )

        # Get pip path
        if sys.platform == "win32":
            pip_path = venv_path / "Scripts" / "pip"
        else:
            pip_path = venv_path / "bin" / "pip"

        # Install the wheel
        result = subprocess.run(
            [str(pip_path), "install", str(wheel_file)],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, (
            f"Package installation failed.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

        # Verify package can be imported
        python_path = (
            venv_path / "bin" / "python"
            if sys.platform != "win32"
            else venv_path / "Scripts" / "python"
        )
        import_result = subprocess.run(
            [str(python_path), "-c", "import sqlalchemy_serializer; print('OK')"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert import_result.returncode == 0, (
            f"Package import failed after installation.\n"
            f"STDOUT: {import_result.stdout}\n"
            f"STDERR: {import_result.stderr}"
        )
