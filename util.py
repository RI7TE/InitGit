from __future__ import annotations
import datetime as dt
import os
import sys

from pathlib import Path
from typing import TYPE_CHECKING

import ujson as json


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


def all_modules():
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
    for item in root.iterdir():
        if item.is_dir() and (item / '__init__.py').exists():
            return item.name
    return None


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
    if requirements_exists(root):
        viz(
            "requirements.txt already exists. Skipping file generation. If you want to retry, delete the requirements.txt file in the working directory.",
            color='yellow',
        )
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


def generate(root: Path) -> Path:
    requirements = generate_requirements(root or Path.cwd())
    (root / "requirements.txt").write_text(
        "\n".join(requirements) + "\n", encoding='utf-8'
    )
    viz(f"requirements.txt created with {len(requirements)} packages.")
    return root / "requirements.txt"


# finding local packages and modules
def find_packages(base_dir: Path):
    """Find all Python packages (directories with __init__.py)."""
    packages = []
    for path in base_dir.rglob('__init__.py'):
        # Skip unwanted dirs
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue
        pkg = ".".join(path.parent.relative_to(base_dir).parts)
        packages.append(pkg)
    return sorted(packages)


def find_py_modules(base_dir: Path):
    """Find all standalone Python modules (not part of a package)."""
    modules = []
    modules.extend(
        py_file.stem
        for py_file in base_dir.glob("*.py")
        if py_file.is_file() and py_file.name != '__init__.py'
    )
    return sorted(modules)


def get_packages_modules(cwd: Path | None = None) -> dict[str, list[str]]:
    base_dir = Path.cwd()
    packages = find_packages(base_dir)
    py_modules = find_py_modules(base_dir)

    print("# For setup.py")
    print(f"packages={packages}")
    print(f"py_modules={py_modules}")
    return {
        "packages": packages,
        "modules": py_modules,
    }
