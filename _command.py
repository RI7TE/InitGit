from __future__ import annotations
import shlex
import subprocess as sp
import sys
from pathlib import Path
from typing import TYPE_CHECKING

sys.path.append(str(Path(__file__).absolute().parent))
if TYPE_CHECKING:
    import typing

from contextlib import contextmanager
from time import sleep
from util import toterm

CURRENT_DIR = Path.cwd().absolute()

class CommandError(Exception):
    """Custom exception for command errors."""

    def __init__(
        self, cmd: str | None = None, errcode: int | None = None, *args, **kwds
    ):
        super().__init__(*args)
        self.error_code = errcode
        self.command = cmd
        self.message = (
            f"Command '{self.command}' failed with error: {self.error_code} {args[0] if args else ''}\n {' '.join(f'{k}={v}' for k, v in kwds.items())}"
            if args
            else f"Command '{self.command}' failed with error: {self.error_code}"
        )
        self.args = args

    def __str__(self):
        return f"CommandError: {self.message}"

    def __iter__(self):
        """Iterate over the error message."""
        args = self.command, self.error_code, self.args, self.message
        yield from args

    def __repr__(self):
        """Return a string representation of the error."""
        return f"CommandError(command={self.command!r}, message={self.message!r}, args={self.args!r})"


class Command:
    """A class to compile and run shell commands."""

    def __init__(self, command: str, cwd: Path | str | None = None, delay: float = 0):
        self.command = command
        self.cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
        self.text = shlex.quote(self.command.strip()).strip()
        self.args = shlex.split(self.text)
        self.name = self.args[0]
        self.error_code = 0
        self.error = None
        self.output = None
        self.delay = delay
        self._slept = False

    def __str__(self):
        return self.text

    def __repr__(self):
        return f"Command(command={self.command!r}, cwd={self.cwd!r})"

    def __iter__(self):
        """Iterate over the command attributes."""
        yield self.command
        yield self.cwd
        yield self.text
        yield self.args
        yield self.name
        yield self.return_code
        yield self.error
        yield self.output

    def __get__(self, instance, owner):
        """Get the command text."""
        return instance.text if instance.output is None else instance.output

    def __set__(self, instance, value):
        """Set the command text."""
        if isinstance(value, str):
            instance.command = value
            instance.text = shlex.quote(value.strip()).strip()
            instance.args = shlex.split(self.text)
            instance.name = self.args[0]
        else:
            raise ValueError("Command must be a string.")
        instance.error_code = 0
        instance.error = None

    @property
    def return_code(self):
        """Get the return code of the command."""
        return self.error_code

    def __enter__(self):
        """Enter the command context."""
        self.run()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the command context."""
        if exc_type is not None:
            self.error_code = exc_value.returncode if exc_value else 1
            self.error = exc_value
            print(
                toterm(
                    f"Command '{self.command}' failed with error: {exc_value}", "red"
                )
            )
            return False
        if self.error_code != 0:
            print(
                toterm(
                    f"Command '{self.command}' failed with error code: {self.error_code}",
                    "red",
                )
            )
            return False
        print(toterm(f"Command '{self.command}' executed successfully.", "green"))
        if not self._slept:
            sleep(self.delay)
            self._slept = True
        return True

    def run(self) -> str:
        """Run the command."""

        try:
            proc = sp.run(
                self.text,
                check=True,
                capture_output=True,
                cwd=self.cwd,
                shell=True,
                text=True,
            )
            self.args = shlex.split(proc.args)
            if proc and proc.stderr:
                print(toterm(f"Command stderr: {proc.stderr.strip()}", "yellow"))
                self.error = proc.stderr.strip()
            else:
                self.error = None
            self.output = proc.stdout.strip() if proc.stdout else None
            self.error_code = proc.returncode or 0
            if proc.stdout:
                self.output = proc.stdout.strip()
            proc.check_returncode()
            if self.error_code == 0:
                print(
                    toterm(f"Command '{self.command}' executed successfully.", "green")
                )
        except sp.CalledProcessError as e:
            self.command = e.cmd
            self.output = e.output
            self.error_code = e.returncode
            self.error = e
            raise CommandError(self.command, self.error_code, error=self.error) from e
        except FileNotFoundError as e:
            self.error_code = e.errno
            self.error = e
            self.output = f"File not found: 1. {e.filename}\n 2. {e.filename2}\t|\tOutput: {e.strerror}"
            raise CommandError(
                self.command,
                self.error_code,
                output=self.output,
                error=self.error,
            ) from e
        except Exception as e:
            self.error_code = 69
            self.error = e
            self.output = f"A generic error occurred in Command class: {e}"
            raise CommandError(
                self.command, self.error_code, error=self.error, output=self.output
            ) from e
        else:
            if proc and proc.returncode == 0:
                print(toterm(f"Command succeeded: {self.text}", "blue"))
            return (
                self.output
                or f"Command '{self.text}' executed successfully: {list(self)}"
            )

        finally:
            if not self._slept:
                sleep(self.delay)
                self._slept = True
            else:
                print(
                    toterm(
                        f"Command Output: '{self.output}'\n Command {self.text} completed with return code: {self.error_code}",
                        "green",
                    )
                )


@contextmanager
def cmd(
    command: str | Command, cwd: str | Path | None = None, **kwds
) -> typing.Generator[Command, typing.Any, None]:
    """Run a shell command."""
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    command = (
        Command(command=command, cwd=cwd, **kwds)
        if isinstance(command, str)
        else command
    )

    try:
        with command as com:
            if com.return_code != 0:
                print(toterm(f"Command failed with return code: {com.output}", "red"))
            else:
                print(toterm(f"Command output: {com.output}", "green"))
        yield command
    except Exception as e:
        raise CommandError from e
