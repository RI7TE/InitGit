from __future__ import annotations
import datetime as dt
import os
import sys

from pathlib import Path
from typing import TYPE_CHECKING


sys.path.append(str(Path(__file__).absolute().parent))
if TYPE_CHECKING:
    import typing

import importlib.util
import re
import subprocess
import sys

from contextlib import contextmanager, redirect_stdout
from pathlib import Path

from colorama import Fore, Style


def stamp_date() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M:%S")


def _color(color: str) -> str:
    """Convert color name to colorama color."""
    colors = {
        'red': Fore.RED,
        'blue': Fore.BLUE,
        'green': Fore.GREEN,
        'yellow': Fore.YELLOW,
        'magenta': Fore.MAGENTA,
        'cyan': Fore.CYAN,
        'white': Fore.WHITE,
        'black': Fore.BLACK,
    }
    return colors.get(color, Fore.BLACK) + Style.BRIGHT

def viz(
    *msg,
    color: str = Fore.BLUE,
    log=False,
    debug=False,
    log_file: str | Path = 'debug.log',
    term=True,
) -> str:
    """
    Print a message in the specified color.
    """
    color = _color(color)
    to_debug = os.getenv('DEBUG', '0') == '1' or debug
    to_log = os.getenv('LOG', '0') == '1' or log
    if len(msg) == 1 and isinstance(msg[0], (list, tuple)):
        msg = msg[0]
    elif len(msg) == 1 and isinstance(msg[0], dict):
        msg = [f"{k}: {v}" for k, v in msg[0].items()]
    _msg = ' '.join(map(str, msg))
    log_msg = (
        dt.datetime.now(dt.UTC).strftime("%d/%m/%Y, %H:%M:%S") + "\n" + "\t" + _msg
    )
    msg = f"{color}{' '.join(map(str, msg))}{Style.RESET_ALL}"

    @contextmanager
    def _log():  # Log to a file if LOG environment variable is set
        nonlocal log_file
        log_file = os.getenv('LOG_FILE', str(log_file))
        with Path(log_file).open('a') as f:
            if term:
                f.write(log_msg + '\n')
            yield f
        if sys.stdout.isatty():
            print(f"{Fore.BLACK}Logged to {log_file}{Style.RESET_ALL}", flush=True)
        else:
            print(
                f"{Fore.YELLOW}Warning: Logged to {log_file}{Style.RESET_ALL}",
                file=sys.stderr,
                flush=True,
            )

    if to_debug:
        if to_log:
            with _log() as f:
                print(
                    msg if term else log_msg,
                    file=sys.stderr if term else f,
                    flush=True,
                )
        else:
            print(msg, flush=True)
    elif to_log:
        with _log() as f:
            print(
                msg if term else log_msg,
                file=sys.stderr if term else f,
                flush=True,
            )
    elif sys.stdout.isatty():
        # Print to stdout if it is a terminal
        print(msg, flush=True)
        sys.stdout.flush()
    else:
        # Fallback to stderr if stdout is not a terminal
        print(
            f"{Fore.YELLOW}Warning: Not printing to stdout{Style.RESET_ALL}",
            file=sys.stderr,
            flush=True,
        )
        sys.stderr.write(msg + '\n')
        sys.stderr.flush()

    return _msg.strip()


def toterm(x, color: str = "red"):
    if color == "red":
        return Fore.RED + Style.BRIGHT + x + Style.RESET_ALL
    if color == "blue":
        return Fore.BLUE + Style.BRIGHT + x + Style.RESET_ALL
    if color == "green":
        return Fore.GREEN + Style.BRIGHT + x + Style.RESET_ALL
    if color == "yellow":
        return Fore.YELLOW + Style.BRIGHT + x + Style.RESET_ALL
    if color == "magenta":
        return Fore.MAGENTA + Style.BRIGHT + x + Style.RESET_ALL
    if color == "cyan":
        return Fore.CYAN + Style.BRIGHT + x + Style.RESET_ALL
    if color == "white":
        return Fore.WHITE + Style.BRIGHT + x + Style.RESET_ALL
    return Fore.BLACK + Style.BRIGHT + x + Style.RESET_ALL


# Directories to skip
SKIP_DIRS = {
    '.venv',
    '__pycache__',
    '.git',
    '.idea',
    '.mypy_cache',
    'node_modules',
    'dist',
    'build',
    '.tox',
    '.eggs',
    '.pytest_cache',
    ".ruff_cache",
}

# Regex to match import statements
# IMPORT_RE = re.compile(r'^\s*(?:import|from)\s+([a-zA-Z_][\w\.]*)',re.MULTILINE)
IMPORT_RE = re.compile(r'^\s*(?:import|from)\s+([a-zA-Z_][\w\.]*)', re.MULTILINE)


try:
    STDLIB_MODULES = sys.stdlib_module_names
except AttributeError:
    # Fallback for < 3.10
    STDLIB_MODULES = set()


def all_modules() -> set[str]:
    return {
        mod.__spec__.name.split('.')[0]
        for mod in sys.modules.values()
        if mod.__spec__ is not None
    }


def _is_stdlib(module_name: str) -> bool:
    """Return True if module is in Python standard library."""
    top_level = module_name.split('.')[0]
    if top_level in STDLIB_MODULES or module_name in STDLIB_MODULES:
        return True
    spec = importlib.util.find_spec(top_level)
    if spec is None or not spec.origin:
        return False
    if spec.origin == 'built-in':
        return True
    return 'site-packages' not in spec.origin and 'dist-packages' not in spec.origin


def is_stdlib(module_name: str) -> bool:
    """Check if a module is part of the Python standard library."""
    try:
        return _is_stdlib(module_name)
    except ModuleNotFoundError:
        return False
    except Exception as e:
        viz(f"Error checking module {module_name}: {e}", color='red')
        raise e from ImportError(f"Module {module_name} not found")


def find_imports(root: Path, package_name: str) -> list[str]:
    imports = set()
    index = 0
    for dirpath, dirnames, filenames in root.walk():
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        try:
            for _index, filename in enumerate(filenames):
                index = _index
                if filename.endswith('.py'):
                    text = Path(dirpath, filename).read_text(encoding='utf-8')
                    for mod in IMPORT_RE.findall(text):
                        top_level = mod.split('.')[0]
                        if top_level == package_name:
                            continue
                        if (
                            not is_stdlib(mod) or not is_stdlib(top_level)
                        ) and top_level in all_modules():
                            imports.add(top_level)
                            viz(f"Found import: {mod} in {filename}", color='green')
        except UnicodeDecodeError:
            viz(f"Skipping {filenames[index]} due to encoding error", color='yellow')
            continue
        except FileNotFoundError:
            viz(f"File not found: {filenames[index]}", color='red')
            continue
        except PermissionError:
            viz(f"Permission denied: {filenames[index]}", color='red')
            continue
        except Exception as e:
            viz(f"Error processing {filenames[index]}: {e}", color='red')
            continue
    if not imports:
        viz("No imports found in the specified directory.", color='yellow')
        return []
    viz(f"Found {len(imports)} unique imports in {root}", color='blue')
    return sorted(imports)


def find_top_package_name(root: Path) -> str | None:
    """Try to detect the package name from __init__.py location."""
    if not root.is_dir():
        viz(f"Provided path {root} is not a directory.", color='red')
        return None
    if (root / '__init__.py').exists():
        return root.name
    if (root / '__main__.py').exists():
        return root.name
    return (
        next(
            item.name
            for item in root.iterdir()
            if item.is_dir() and (item / '__init__.py').exists()
        )
        if any(item.is_dir() for item in root.iterdir())
        else None
    )


def requirements_exists(cwd: Path) -> bool:
    """Check if requirements.txt exists in the current directory."""
    return (cwd / 'requirements.txt').exists()


def get_installed_version(pkg: str) -> str | None:
    """Return installed version of package using pip."""
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pip", "show", pkg],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        for line in out.splitlines():
            if line.startswith("Version:"):
                return line.split(":", 1)[1].strip()
    except subprocess.CalledProcessError:
        return None
    return None

def generate_requirements(root: Path) -> list[str]:
    root = root or Path.cwd()
        # return root / "requirements.txt"
    if package_name := find_top_package_name(root):
        imports = find_imports(root, package_name)
    else:
        imports = find_imports(root, root.name)
    requirements = []
    for pkg in imports:
        version = get_installed_version(pkg)
        requirements.append(f"{pkg}=={version}" if version else pkg)
    return sorted(requirements)


def generate(root: Path | str | None = None) -> Path:
    root = root or Path.cwd()
    if isinstance(root, str):
        root = Path(root)
    if requirements_exists(root):
        viz(
            "requirements.txt already exists. Skipping file generation. If you want to retry, delete the requirements.txt file in the working directory.",
            color='yellow',
        )
    requirements = generate_requirements(root)
    root = root / "requirements.txt"
    if not root.exists():
        root.touch()
    if not requirements:
        viz(
            "No requirements found. Skipping requirements.txt creation.", color='yellow'
        )
        return root
    root.write_text("\n".join(requirements) + "\n", encoding='utf-8')
    viz(f"requirements.txt created with {len(requirements)} packages.")
    return root


# finding local packages and modules


class Packages:
    def __init__(self, packages: list[str] | None = None):
        """Initialize with a list of packages."""
        self.py_packages = packages or []

    def __iter__(self):
        """Iterate over the packages."""
        yield from self.py_packages

    def __get__(self, instance, owner):
        """Return the packages."""
        return instance.py_packages

    def __set__(self, instance, value):
        """Set the packages."""
        if isinstance(value, list):
            instance.py_packages = value
            self.py_packages = value
        else:
            raise TypeError("Value must be a list of packages.")

    def __repr__(self):
        """Return a string representation of the packages."""
        return f"Packages({self.py_packages})"

    def __len__(self):
        """Return the number of packages."""
        return len(self.py_packages)

    def __contains__(self, item):
        """Check if a package is in the list."""
        return item in self.py_packages

    def __getitem__(self, index):
        """Get a package by index."""
        return self.py_packages[index]


class Modules:
    """Class to hold Python modules."""

    def __init__(self, py_modules: list[str] | None = None):
        self.py_modules = py_modules or []

    def __iter__(self):
        """Iterate over the modules."""
        yield from self.py_modules

    def __len__(self):
        """Return the number of modules."""
        return len(self.py_modules)

    def __contains__(self, item):
        """Check if a module is in the list."""
        return item in self.py_modules

    def __getitem__(self, index):
        """Get a module by index."""
        return self.py_modules[index]

    def __get__(self, instance, owner):
        """Return the modules."""
        return instance.py_modules

    def __set__(self, instance, value):
        """Set the modules."""
        if isinstance(value, list):
            instance.py_modules = value
            self.py_modules = value
            # self.py_modules = value
        else:
            raise TypeError("Value must be a list of modules.")

    def __repr__(self):
        """Return a string representation of the modules."""
        return f"Modules({','.join(self.py_modules)})"


class PackagesAndModules:
    """Class to hold packages and modules."""

    packages: Packages = Packages()
    modules: Modules = Modules()

    def __init__(self, base_dir: Path | str | None = None):
        base_dir = Path(base_dir) if base_dir else Path.cwd()
        if not base_dir.is_dir():
            raise ValueError(f"Provided path {base_dir} is not a directory.")
        self.packages, self.modules, self._base_dir = self.get_packages_modules(
            base_dir
        )

    def __iter__(self):
        yield from self.packages
        yield from self.modules

    @property
    def base_dir(self) -> Path:
        """Return the base directory."""
        return self._base_dir

    @base_dir.setter
    def base_dir(self, value: Path | str):
        """Set the base directory."""
        if isinstance(value, str):
            value = Path(value).absolute()
        if not value.is_dir():
            raise ValueError(f"Provided path {value} is not a directory.")
        self._base_dir = value
        self.packages, self.modules, self._base_dir = self.get_packages_modules(value)

    def find_packages(self, base_dir: Path) -> list[typing.Any]:
        """Find all Python packages (directories with __init__.py)."""
        packages = []
        for path in base_dir.rglob('*.py'):
            # Skip unwanted dirs
            if any(skip in path.parts for skip in SKIP_DIRS):
                continue
            pkg = ".".join(path.parent.relative_to(base_dir).parts)
            packages.append(pkg)
            [packages.remove(i) for i in packages if not i]
        return sorted(packages)

    def find_py_modules(self, base_dir: Path):
        """Find all standalone Python modules (not part of a package)."""
        modules = []
        modules.extend(
            py_file.stem
            for py_file in base_dir.glob("*.py")
            if py_file.is_file() and py_file.name != '__init__.py'
        )
        return sorted(modules)

    def get_packages_modules(
        self, cwd: Path | str | None = None
    ) -> tuple[list[str], list[str], Path]:
        if isinstance(cwd, str):
            cwd = Path(cwd)
        base_dir = cwd or Path.cwd()
        py_packages = self.find_packages(base_dir)
        py_modules = self.find_py_modules(base_dir)

        self._base_dir = base_dir
        self.py_packages = py_packages
        self.py_modules = py_modules
        return self.py_packages, self.py_modules, self._base_dir

    @property
    def all_packages(self) -> list[str]:
        """Return the list of packages."""
        return self.py_packages

    @property
    def all_modules(self) -> list[str]:
        """Return the list of modules."""
        return self.py_modules

    @property
    def root(self) -> Path:
        """Return the root directory."""
        return self.base_dir

    @root.setter
    def root(self, value: Path | str):
        self.base_dir = Path(value) if isinstance(value, str) else value

    @property
    def packages_and_modules(self) -> dict[str, list[str]]:
        """Return a dictionary of packages and modules."""
        return {
            'packages': self.packages,
            'modules': self.modules,
        }

    def __repr__(self):
        """Return a string representation of the packages and modules."""
        return f"PackagesAndModules(base_dir={self.base_dir})"

    def __str__(self):
        """Return a string representation of the packages and modules."""
        return f"Packages: {self.packages}, Modules: {self.modules}, Base Directory: {self.base_dir}"

    def __getattr__(self, item):
        """Get an attribute from the packages or modules."""
        if item in self.py_packages:
            return self.py_packages[item]
        if item in self.py_modules:
            return self.py_modules[item]
        if item in self.__dict__:
            return self.__dict__[item]
        if item in self.__class__.__dict__:
            return self.__class__.__dict__[item]
        if item in self:
            return super().__getattribute__(item)
        raise AttributeError(f"{item} not found in packages or modules.")

    def __getitem__(self, item: int | str):
        """Get a package or module by index."""
        if isinstance(item, int):
            if item < len(self.py_packages):
                return self.py_packages[item]
            item -= len(self.py_packages)
            if item < len(self.py_modules):
                return self.modules[item]
            raise IndexError("Index out of range for packages and modules.")
        if item in self.py_packages:
            return self.py_packages[self.py_packages.index(item)]
        if item in self.py_modules:
            return self.py_modules[self.py_modules.index(item)]
        if item in self.__dict__:
            return self.__dict__[item]
        if item in self.__class__.__dict__:
            return self.__class__.__dict__[item]
        if item in self:
            return super().__getattribute__(item)
        raise KeyError(f"{item} not found in packages or modules.")

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

    def __contains__(self, item):
        """Check if a package or module is in the packages and modules."""
        return (
            item in self.packages
            or item in self.modules
            or item in self.__dict__
            or item in self.__class__.__dict__
        )


def test_get_packages_modules(pam: PackagesAndModules):
    """Test function for get_packages_modules."""
    cwd = Path(__file__).parent

    class Test:
        """Test class to simulate instance."""

        packages_and_modules: PackagesAndModules = pam

    test_instance = Test()
    result = test_instance.packages_and_modules
    viz(f"ResultType: {type(result)}", color='blue')
    viz(f"Result: {result}", color='green')
    assert isinstance(result, PackagesAndModules | dict), (
        "Result should be a dictionary"
    )
    assert isinstance(result.packages_and_modules, dict), (
        "Result should be a dictionary"
    )
    assert 'packages' in result, "Result should contain 'packages' key"
    assert 'modules' in result, "Result should contain 'modules' key"
    print("Test passed successfully!")
    viz("result", result, color='red')
    return result


def test_find_top_package_name():
    """Test function for find_top_package_name."""
    cwd = Path(__file__).parent
    package_name = find_top_package_name(cwd)
    assert isinstance(package_name, str) or package_name is None, (
        "Result should be a string or None"
    )
    print(f"Top package name: {package_name}")
    return package_name


def test():
    """Run all tests."""
    pam = PackagesAndModules(base_dir=Path(__file__).parent.parent)
    print("Running tests...")
    test_get_packages_modules(pam)
    test_find_top_package_name()
    viz("All tests passed successfully!")
    pam.root = Path(__file__).parent
    viz("PAM", pam['py_packages'], color='green')
