"""Basic tests that do not require Django."""

import os
import unittest

import toml

from nautobot_dns_models import __version__ as project_version


class TestVersion(unittest.TestCase):
    """Test Version is the same."""

    def test_version(self):
        """Verify that pyproject.toml version is same as version specified in the package."""
        parent_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        poetry_version = toml.load(os.path.join(parent_path, "pyproject.toml"))["tool"]["poetry"]["version"]
        self.assertEqual(project_version, poetry_version)


class TestDocsPackaging(unittest.TestCase):
    """Test Version in doc requirements is the same pyproject."""

    def test_version(self):
        """Verify that pyproject.toml dev dependencies have the same versions as in the docs requirements.txt."""
        parent_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
        poetry_path = os.path.join(parent_path, "pyproject.toml")
        poetry_details = toml.load(poetry_path)["tool"]["poetry"]["group"]["dev"]["dependencies"]
        with open(f"{parent_path}/docs/requirements.txt", "r", encoding="utf-8") as file:
            requirements = [line for line in file.read().splitlines() if (len(line) > 0 and not line.startswith("#"))]
        for pkg in requirements:
            package_name = pkg
            if len(pkg.split("==")) == 2:  # noqa: PLR2004
                package_name, version = pkg.split("==")
            else:
                version = "*"
            self.assertEqual(poetry_details[package_name], version)
