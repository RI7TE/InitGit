
from __future__ import annotations
import os,sys,ujson as json
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, NotRequired

sys.path.append(str(Path(__file__).absolute().parent))
if TYPE_CHECKING:
    import typing
from typing import Mapping, Any

from setuptools import Extension, Distribution, Command
Incomplete =  Any
import setuptools


class BuildInfo(TypedDict):
    sources: list[str] | tuple[str, ...]
    obj_deps: NotRequired[dict[str, list[str] | tuple[str, ...]]]
    macros: NotRequired[list[tuple[str] | tuple[str, str | None]]]
    include_dirs: NotRequired[list[str]]
    cflags: NotRequired[list[str]]

class ExtraKwds(dict):
    kwds:dict[str, Any] = {}

    def __init__(self, *,
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
        command_options: Mapping[
            str, Mapping[str, tuple[Incomplete, Incomplete]]
        ] | None = None,
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
        **attrs: Any,
    ):
        super().__init__(**attrs)
        self.kwds = dict(attrs)
        self.long_description_content_type = long_description_content_type
        self.long_description = long_description
        self.maintainer = maintainer
        self.maintainer_email = maintainer_email
        self.url = url
        self.scripts = scripts or []
        self.ext_modules = ext_modules or []
        self.classifiers = classifiers or []
        self.distclass = distclass
        self.script_name = script_name
        self.script_args = script_args or []
        self.options = options or {}
        self.keywords = keywords or []
        self.platforms = platforms or []
        self.cmdclass = cmdclass or {}
        self.data_files = data_files or []
        self.command_packages = command_packages or []
        self.command_options = command_options or {}
        self.package_data = package_data or {}
        self.include_package_data = include_package_data
        self.libraries = libraries or []
        self.headers = headers or []
        self.ext_package = ext_package
        self.include_dirs = include_dirs or []
        self.password = password
        self.fullname = fullname
        self.obsoletes = obsoletes or []
        self.provides = provides or []

    def __new__(cls, *args, **kwargs):
        """Create a new instance of ExtraKwds."""
        self =  super().__new__(cls)
        self.kwds = {}
        cls.kwds = self.kwds
        for key, value in kwargs.items():
            setattr(self, key, value)
            self.kwds[key] = value
        return self



    def __setattr__(self, name: str, value: Any) -> None:
        """Set an attribute in the dictionary."""
        if name in self.kwds:
            self.kwds[name] = value if hasattr(self, 'kwds') else {name: value}
        super().__setattr__(name, value)
        self[name] = value

    def __getitem__(self, key: str) -> Any:
        """Get an item from the dictionary."""
        return self.kwds[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an item in the dictionary."""
        self.kwds[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete an item from the dictionary."""
        if key in self.kwds:
            del self.kwds[key]
        else:
            raise KeyError(f"'{key}' not found in ExtraKwds")
    def __contains__(self, key: object) -> bool:
        """Check if a key is in the dictionary."""
        return key in self.keys() or key in self.kwds

    def __iter__(self):
        """Iterate over the keys in the dictionary."""
        return iter(self.kwds)

    def __len__(self) -> int:
        """Get the number of items in the dictionary."""
        return len(self.kwds)
    def __repr__(self) -> str:
        """Return a string representation of the ExtraKwds."""
        _kwds = {k: v for k, v in self.kwds.items() if v not in [None, ""] and len(v) >= 1}
        return f"ExtraKwds({', '.join(f'{k}={v!r}' for k, v in _kwds.items()) if self.kwds else None})"
class SetUp:
    def __init__(
        self,
        *,
        name: str,
        version: str | float | None = "0.1.0",
        description: str | None = "",
        author: str | None = None,
        author_email: str | None = None,
        download_url: str | None = None,
        py_modules: list[str] | None = None,
        license: str | None = "Proprietary License",
        package_dir: Mapping[str, str] | None = None,
        requires: list[str] | None = None,
        packages: list[str] | None = None,
        **extra_kwds: ExtraKwds | None,

    ):

        setuptools.setup(
    name=name,
    version="0.1.0",
    author="Steven Kellum",
    author_email="sk@perfectatrifecta.com",
    description="InitGit is a Python package that provides a set of tools for initializing and managing Git repositories.",
    download_url="https://github.com/RI7TE/InitGit.git",
    py_modules=["initgit", "_license", "__main__"],
    python_requires=">=3.10",
    requires=["colorama==0.4.6"],
    **extra_kwds if isinstance(extra_kwds, ExtraKwds | dict) else {},
)

if __name__ == "__main__":
    extra_kwds = ExtraKwds(
        long_description_content_type="text/markdown",
        long_description="This package provides tools for initializing and managing Git repositories.",
        maintainer="Steven Kellum",
    )
    print("Running setup with extra keywords:", extra_kwds)
    print("Extra keywords:", 'maintainer' in extra_kwds)
