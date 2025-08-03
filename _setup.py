
from __future__ import annotations
import sys

from pathlib import Path
from typing import TYPE_CHECKING, NotRequired, TypedDict

from contextlib import contextmanager

sys.path.append(str(Path(__file__).absolute().parent))
if TYPE_CHECKING:
    import typing

from typing import Any

from setuptools import Command, Distribution, Extension
if TYPE_CHECKING:
    from yarl import URL
    from collections.abc import Mapping

Incomplete =  Any
import setuptools

from util import generate_requirements, get_packages_modules, viz


class BuildInfo(TypedDict):
    sources: list[str] | tuple[str, ...]
    obj_deps: NotRequired[dict[str, list[str] | tuple[str, ...]]]
    macros: NotRequired[list[tuple[str] | tuple[str, str | None]]]
    include_dirs: NotRequired[list[str]]
    cflags: NotRequired[list[str]]

class ExtraKwds(dict):
    """A class to hold extra keyword arguments for setup.py. Ignores None or empty values and any extra key/value pairs not already in class dict."""
    def __init__(
        self,
        *,
        long_description_content_type: str | None = None,
        long_description: str | None = None,
        maintainer: str | None = None,
        maintainer_email: str | None = None,
        url: str | None = None,
        scripts: list[str] | None = None,
        ext_modules: typing.Sequence[Extension] | None = None,
        classifiers: list[str] | None = None,
        distclass: type[Distribution] | None = None,
        script_name: str | None = None,
        script_args: list[str] | None = None,
        options: Mapping[str, Incomplete] | None = None,
        keywords: list[str] | str | None = None,
        platforms: list[str] | str | None = None,
        cmdclass: Mapping[str, type[Command]] | None = None,
        data_files: list[tuple[str, list[str]]] | None = None,
        command_packages: list[str] | None = None,
        command_options: Mapping[str, Mapping[str, tuple[Incomplete, Incomplete]]]
        | None = None,
        package_data: Mapping[str, list[str]] | None = None,
        include_package_data: bool | None = None,
        libraries: list[tuple[str, BuildInfo]] | None = None,
        headers: list[str] | None = None,
        ext_package: str | None = None,
        include_dirs: list[str] | None = None,
        password: str | None = None,
        fullname: str | None = None,
        obsoletes: list[str] | None = None,
        provides: list[str] | None = None,
        package_dir: Mapping[str, str] | None = None,
        **attrs: Any,
    ):
        super().__init__(**attrs)
        # self.kwds = dict(attrs)
        self.long_description_content_type = long_description_content_type
        self.long_description = long_description
        self.maintainer = maintainer
        self.maintainer_email = maintainer_email
        self.url = url
        self.scripts = scripts or None
        self.ext_modules = ext_modules or None
        self.classifiers = classifiers or None
        self.distclass = distclass
        self.script_name = script_name
        self.script_args = script_args or None
        self.options = options or None
        self.keywords = keywords or None
        self.platforms = platforms or None
        self.cmdclass = cmdclass or None
        self.data_files = data_files or None
        self.command_packages = command_packages or None
        self.command_options = command_options or None
        self.package_data = package_data or None
        self.include_package_data = include_package_data
        self.libraries = libraries or None
        self.headers = headers or None
        self.ext_package = ext_package
        self.include_dirs = include_dirs or None
        self.password = password
        self.fullname = fullname
        self.obsoletes = obsoletes or None
        self.provides = provides or None
        self.package_dir = package_dir or None

    def __setattr__(self, name: str, value: Any) -> None:
        """Set an attribute in the dictionary."""
        if name in ExtraKwds.__dict__['__static_attributes__']:
            super().__setattr__(name, value)


    def __getitem__(self, key: str) -> Any:
        """Get an item from the dictionary."""
        return self.__dict__[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item in the dictionary."""
        if key in ExtraKwds.__dict__['__static_attributes__']:
            self.__dict__[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete an item from the dictionary."""
        if key in self:
            del self.__dict__[key]
        else:
            raise KeyError(f"'{key}' not found in ExtraKwds")
    def __contains__(self, key: object) -> bool:
        """Check if a key is in the dictionary."""
        return key in self.__dict__

    def __iter__(self):
        """Iterate over the keys in the dictionary."""
        return iter(self.keys())

    def __len__(self) -> int:
        """Get the number of items in the dictionary."""
        return len(self.keys())

    def __repr__(self) -> str:
        """Return a string representation of the ExtraKwds."""
        # _kwds = {k: v for k, v in self.items() if v not in [None, ""] and len(v) >= 1}
        return f"ExtraKwds({', '.join(f'{k}={v!r}' for k, v in self.__dict__.items() if v not in [None, ''] and len(v) >= 1)})"

    def items(self):
        """Return the items in the dictionary."""
        return self.__dict__.items()

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        """Return the values in the dictionary."""
        return self.__dict__.values()


class SetUp:
    def __init__(
        self,
        *,
        name: str,
        cwd: Path | str | None = None,
        version: str | float | None = "0.1.0",
        description: str | None = "",
        author: str | None = "Steven Kellum",
        author_email: str | None = "sk@perfectatrifecta.com",
        license: str | None = "Proprietary License",
        download_url: str | None = None,
        py_modules: list[str] | None = None,
        requires: list[str] | None = None,
        packages: list[str] | None = None,
        **extra_kwds: ExtraKwds | dict[str, Any] | None,
    ):
        self.cwd = Path(cwd).absolute() if cwd else Path.cwd().absolute()
        packages_modules = get_packages_modules(Path.cwd())
        self.name = name
        self.version = str(version)
        self.description = description
        self.author = author
        self.author_email = author_email
        self.download_url = download_url
        self.py_modules = py_modules or packages_modules.get("modules")
        self.license = license
        self.requires = requires or generate_requirements(Path.cwd())
        self.packages = packages or packages_modules.get("packages")
        self.extra_kwds = extra_kwds or {}

    def setup(self):
        """Run the setup function with the provided parameters."""
        if not self.name:
            raise ValueError("Package name is required.")
        if not self.version:
            raise ValueError("Package version is required.")
        setuptools.setup(
            name=self.name,
            version=self.version,
            author=self.author or "Unknown Author",
            author_email=self.author_email or "sk@perfectatrifecta.com",
            description=self.description or "No description provided.",
            download_url=self.download_url or "",
            py_modules=self.py_modules or [],
            python_requires=f">={sys.version_info.major}.{sys.version_info.minor}",
            requires=self.requires or [],
            **self.extra_kwds if isinstance(self.extra_kwds, ExtraKwds | dict) else {},
        )

    def __enter__(self):
        """Enter the setup context."""
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the setup context."""
        if exc_type is not None:
            viz(f"Error during setup: {exc_value}")
            return False
        return True

    def generate_setup_py(self):
        """Generate a setup.py file in the current directory."""
        setup_code = f"""\
from setuptools import setup

setup(
    name={self.name!r},
    version={self.version!r},
    author={self.author!r},
    author_email={self.author_email!r},
    description={self.description!r},
    download_url={self.download_url!r},
    license={self.license!r},
    packages={self.packages!r},
    py_modules={self.py_modules!r},
    python_requires=">={{}}.{{}}".format({sys.version_info.major}, {sys.version_info.minor}),
    install_requires={self.requires!r},
    {", ".join(f"{k}={v!r}" for k, v in self.extra_kwds.items())}
)
"""
        (self.cwd / "setup.py").write_text(setup_code, encoding="utf-8")
        viz(f"setup.py generated for package: {self.name}")

    def __call__(self, generate:bool | None = None, *args, **kwargs):
        """Run the setup function when the instance is called."""
        self.generate_setup_py() if generate else self.setup()
        return self

def program_setup(
    name: str,
    version: str | float,
    description: str,
    author: str,
    author_email: str,
    download_url: str | URL,
    license_type: str,
    **extra_kwds: ExtraKwds | dict[str, Any] | None,
):
    setup_instance = SetUp(
        name=name,
        version=version,
        description=description,
        author=author,
        author_email=author_email,
        download_url=str(download_url),
        license=license_type,
        extra_kwds=extra_kwds if isinstance(extra_kwds, ExtraKwds | dict) else {},
    )
    setup_instance.generate_setup_py()

@contextmanager
def setup_context(program_name: str, cwd: Path | str | None = None):
    """Context manager for setting up a Python package."""
    yield SetUp(name=program_name, cwd=cwd)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate a setup.py file for the current project."
    )
    parser.add_argument("--name", required=True, help="Package name")
    parser.add_argument("--version", default="0.1.0", help="Package version")
    parser.add_argument("--description", default="", help="Package description")
    parser.add_argument("--author", default="Steven Kellum", help="Author name")
    parser.add_argument(
        "--author-email", default="sk@perfectatrifecta.com", help="Author email"
    )
    parser.add_argument("--download-url", default=None, help="Download URL")
    parser.add_argument("--license", default="Proprietary License", help="License type")

    args = parser.parse_args()

    setup_instance = SetUp(
        name=args.name,
        version=args.version,
        description=args.description,
        author=args.author,
        author_email=args.author_email,
        download_url=args.download_url,
        license=args.license,
    )
    setup_instance.generate_setup_py()


def test_keyword_arguments():
    extra_kwds = ExtraKwds(
        long_description_content_type="text/markdown",
        long_description="This package provides tools for initializing and managing Git repositories.",
        maintainer="Steven Kellum",
    )
    extra_kwds.DEEZ = "NUTS"
    extra_kwds['DEEZ'] = "NUTS"
    viz("Running setup with extra keywords:", extra_kwds)
    viz("Extra keywords:", extra_kwds)
    viz(f"Extra keyword: {extra_kwds.keys()}")
    viz(f"Extra keyword: {extra_kwds['maintainer']}")


if __name__ == "__main__":
    #    main()
    test_keyword_arguments()
