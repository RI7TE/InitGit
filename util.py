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
            print(Fore.BLACK + f"Logged to {log_file}" + Style.RESET_ALL, flush=True)
        else:
            print(
                Fore.YELLOW + f"Warning: Logged to {log_file}" + Style.RESET_ALL,
                file=sys.stderr,
                flush=True,
            )

    if to_debug:
        if to_log:
            with _log() as f:
                print(
                    log_msg if not term else msg,
                    file=f if not term else sys.stderr,
                    flush=True,
                )
        else:
            print(msg, flush=True)
    elif to_log:
        with _log() as f:
            print(
                log_msg if not term else msg,
                file=f if not term else sys.stderr,
                flush=True,
            )
    elif sys.stdout.isatty():
        # Print to stdout if it is a terminal
        print(msg, flush=True)
        sys.stdout.flush()
    else:
        # Fallback to stderr if stdout is not a terminal
        print(
            Fore.YELLOW + "Warning: Not printing to stdout" + Style.RESET_ALL,
            file=sys.stderr,
            flush=True,
        )
        sys.stderr.write(msg + '\n')
        sys.stderr.flush()

    return _msg.strip()


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

def generate(root: Path) -> None:
    root = root or Path.cwd()
    if requirements_exists(root):
        viz(
            "requirements.txt already exists. Skipping file generation. If you want to retry, delete the requirements.txt file in the working directory.",
            color='yellow',
        )
        return
    if package_name := find_top_package_name(root):
        imports = find_imports(root, package_name)
    else:
        imports = find_imports(root, root.name)
    requirements = []
    for pkg in imports:
        version = get_installed_version(pkg)
        requirements.append(f"{pkg}=={version}" if version else pkg)
    Path("requirements.txt").write_text(
        "\n".join(requirements) + "\n", encoding='utf-8'
    )
    viz(f"requirements.txt created with {len(requirements)} packages.")


def main(args):
    if len(args) > 1:
        root = Path(args[1])
        if not root.is_dir():
            viz(f"Error: {root} is not a directory.", color='red')
            sys.exit(1)
    else:
        root = Path.cwd()
    generate(root)

if __name__ == "__main__":
    main(sys.argv)
