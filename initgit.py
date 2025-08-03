#! /usr/bin/env python
from __future__ import annotations
import datetime as dt
import os
import sys

from os import environ as en
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import find_dotenv, load_dotenv


load_dotenv(find_dotenv())

__version__ = "0.1.0"
__license__ = "Proprietary"
__author__ = "Steven Kellum"
__email__ = "sk@perfectatrifecta.com"

sys.path.append(str(Path(__file__).absolute().parent))
if TYPE_CHECKING:
    import argparse
    import typing

import shlex

from contextlib import contextmanager
from curses.ascii import isdigit
from enum import Enum
from time import sleep

from _command import CURRENT_DIR, Command, CommandError, cmd
from _setup import ExtraKwds, SetUp, program_setup, setup_context
from yarl import URL

from _license import LICENSE_TEXT
from util import generate, stamp_date, toterm, viz


"""
1. git add .
2. git commit -a -m '{message}'
3. git branch -M master
4. git push -u origin master
5. touch setup.py
"To push changes, use: git push -u origin master"
"To pull changes, use: git pull origin master"
"To fetch changes, use: git fetch origin"
"To check the status, use: git status"
"To view the log, use: git log --oneline"
"To view the branches, use: git branch"
"To view the diff, use: git diff"
"""

GIT_USERNAME = (
    en.get("GITHUB_USERNAME")
    or shlex.quote(
        input("Enter your GitHub username: ").strip() or "your_username"
    ).strip()
)

GITDIR = CURRENT_DIR / ".git"
MSGFILE = GITDIR / "COMMIT_EDITMSG"

GIT_IGNORE_PATH = Path(__file__).absolute().parent / os.getenv(
    "GITIGNORE_TEXTFILE", "_gitignore.txt"
)
GIT_IGNORE = GIT_IGNORE_PATH.read_text().strip() if GIT_IGNORE_PATH.exists() else ""

LICENSE = shlex.quote(LICENSE_TEXT.strip()).strip()


class Selector(Enum):
    _GIT_INIT = '1'
    _PRE_STAGE = '2'
    _STAGE = "3"
    _COMMIT = "4"
    _STATUS = '5'
    _LOG = "6"
    _BRANCH = "7"
    _DIFF = "8"
    _VARS = "9"
    INIT = "init"
    CREATE = "create"
    ADD = "add"
    UPDATE = "update"
    COMMIT = "commit"
    DISCARD = "discard"
    UNCOMMIT = "uncommit"
    RESET = "reset"
    HARD_RESET = "hard-reset"
    REVERT = "revert"
    FETCH = "fetch"
    PULL = "pull"
    PUSH = "push"


class Visibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


# 1. In your project folder, initialize a git repo
def init_git(cwd: Path | str | None = None, *, branch: str | None = None):
    """Initialize a git repository in the current directory."""
    branch = shlex.quote(branch or "master").strip()
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    return cmd(f"git init -b {branch}", cwd=cwd)


# 2. Create files for Python/VSCode
def pre_stage(
    cwd: Path | str | None = None, description: str | None = None
) -> tuple[bool, str]:
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    repo_name = shlex.quote(
        input(f"Enter the name of the repository <DEFAULT: {cwd.name.title()}: ")
        or cwd.name.title()
    ).strip()
    description = shlex.quote(
        description or input("Enter a description for the repository: ")
    ).strip()
    gitignore_file = cwd / '.gitignore'
    readme_file = cwd / "README.md"
    license_file = cwd / "LICENSE.txt"
    requirements_file = generate(cwd)
    if not gitignore_file.exists():
        gitignore_file.touch()
    if not readme_file.exists():
        readme_file.touch()
    if not license_file.exists():
        license_file.touch()
    if not requirements_file.exists():
        requirements_file.touch()
        print(
            toterm(
                CommandError(
                    cmd="generate requirements.txt",
                    errcode=1,
                    stage="PRE-STAGE",
                    message="Failed to populate requirements.txt file",
                )
            )
        )
    try:
        gitignore_file.write_text(f'{GIT_IGNORE.strip()}')
        readme_file.write_text(f'{repo_name.strip()}\n{description.strip()}')
        license_file.write_text(f'{LICENSE.strip()}')
    except Exception as e:
        raise CommandError(cmd=" ".join(e.args), errcode=2, stage="PRE-STAGE") from e

    print(toterm(f"Pre-stage files created in {cwd}", "green"))
    return True, repo_name


# 3. Stage and commit your files
def stage(cwd: Path | str | None = None):
    """Stage all files in the current directory."""
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    return cmd(f"git add {cwd}", cwd=cwd, delay=1)


def commit_message(cwd: Path | str | None = None, message: str | None = None):
    """Commit staged files with a message. Commits the tracked changes and prepares them to be pushed to a remote repository."""
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    message = shlex.quote(
        message or input(f"Enter commit message <DEFAULT:'{stamp_date()}'>: ")
    ).strip()
    try:
        if not GITDIR.exists():
            print(
                toterm(
                    "No git repository found. Please initialize a git repository first.",
                    "red",
                )
            )
            raise CommandError(
                "initgit commit",
                69,
                "No git repository found on disk.",
                message="No git repository found on disk.",
            )
        if MSGFILE.exists():
            messages = shlex.split(
                shlex.quote(
                    MSGFILE.read_text().strip() if MSGFILE.exists() else ""
                ).strip()
            )
            if (
                message in messages
                or message in [m.strip() for m in messages]
                or not message
            ):
                print(
                    toterm(
                        f"Commit message already exists or no message: {message}",
                        "yellow",
                    )
                )
                message = (
                    shlex.quote(input("Enter a new commit message: ").strip()).strip()
                    or dt.datetime.now(dt.UTC).strftime("%Y-%m-%d %H:%M:%S").strip()
                )
                commit_message(cwd=cwd, message=message)
        message = message.strip() or stamp_date().strip()
    except ValueError as e:
        print(toterm(f"Invalid commit message: {e}", "red"))
        message = shlex.quote(input("Enter a valid commit message: ").strip()).strip()
        if not message:
            print(toterm("No commit message provided. Aborting commit.", "yellow"))
            sys.exit(1)
    else:
        return message

from contextlib import _GeneratorContextManager


def commit(
    cwd: Path | str | None = None, message: str | None = None
) -> _GeneratorContextManager[Command, None, None]:
    message = commit_message(cwd=cwd, message=message)
    try:
        command = cmd(f"git commit -a -m '{message}'", cwd=cwd, delay=2)
    except CommandError as e:
        print(toterm(f"Commit failed: {e.message}", "red"))
        print(toterm(f"No changes to commit. Please stage files first: {e}", "yellow"))
        raise e from e
    else:
        return command


def initialize(
    cwd: Path,
    description: str | None = None,
    message: str | None = None,
    branch: str | None = None,
) -> tuple[str, str, str]:
    """Initialize a git repository, create pre-stage files, and commit them."""
    _results = []
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    username = shlex.quote(
        input(f"Enter your GitHub username <DEFAULT: {GIT_USERNAME}: ").strip()
        or GIT_USERNAME
    ).strip()
    description = shlex.quote(
        description or input("Enter a description for the repository: ")
    ).strip()
    with init_git(cwd, branch=branch) as com:
        _results.append(com.output)
    staged, repo_name = pre_stage(cwd, description=description)
    sleep(1)
    if staged:
        with stage(cwd) as com:
            _results.append(com)
        with commit(cwd, message=message) as com:
            _results.append(com)
    if all(i.return_code == 0 for i in _results):
        return username, repo_name, description
    print(toterm("Pre-stage failed. Aborting commit context."))
    for i in _results:
        print(
            toterm(
                f"Command: {i.text} | Output: {i.output} | Return Code: {i.return_code}",
                "red",
            )
        )
    raise CommandError("initialize", 1, "Pre-stage failed. Aborting commit context.")


@contextmanager
def commit_context(
    cwd: Path,
    description: str | None = None,
    message: str | None = None,
    branch: str | None = None,
) -> typing.Generator[tuple[str | None, str | None, str | None]]:
    """Context manager to prepare for staging files."""
    if username_reponame_description := initialize(
        cwd, description=description, message=message, branch=branch
    ):
        yield username_reponame_description
    else:
        print(toterm("Pre-stage failed. Aborting commit context."))
        yield None, None, None
        sys.exit(1)


def _reset_stage(filename: str | Path | None = None, cwd: Path | str | None = None):
    """unstage a file."""
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    filename = shlex.quote(
        str(filename).strip()
        or input(
            toterm(
                f"Which file would you like to reset?\n{list(enumerate(cwd.iterdir()))} ",
                "cyan",
            )
        ).strip()
    )
    if not filename:
        print(toterm("No filename provided. Aborting reset stage."))
        return None
    with cmd(f"git reset HEAD {filename}", cwd=cwd) as com:
        return com.output


def _reset_commit(cwd: Path | str | None = None):
    """To remove this commit and modify the file. You can then commit and add the file again."""
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    with cmd('git reset --soft HEAD~1') as com:
        return com.output


def reset(cwd: Path | str | None = None, filename: str | Path | None = None):
    """reset file stage or commit."""
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    if filename:
        return _reset_stage(filename, cwd)
    which = (
        input(
            "Do you want to reset a file stage or commit? (Options:\nPress 'f' for file\nPress 'c' for commit\nPress 'x' to exit): "
        )
        .strip()
        .lower()
    )
    if which in ["f", "file"]:
        filename = input(
            "Enter the filename to reset stage for (or press Enter to skip): "
        ).strip()
        return _reset_stage(cwd=cwd, filename=filename or None)
    if which in ["commit", "c"]:
        return _reset_commit(cwd=cwd)
    print(toterm("Invalid option. Please choose 'file' or 'commit'."))
    return reset(cwd=cwd)


def _repo_command(
    cwd: str | Path | None,
    *,
    visibility: Visibility | None = None,
    username: str | None = None,
    repo_name: str | None = None,
    interactive: bool = False,
    remote_name: str | None = None,
    description: str | None = None,
    url: str | URL | None = None,
) -> str:
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    base_cmd = "gh repo create "
    if interactive:
        return base_cmd
    repo_name = shlex.quote(repo_name.strip()).strip() if repo_name else cwd.name
    full_repo_name = (
        f"{shlex.quote(username).strip()}/{repo_name}" if username else repo_name
    )
    base_cmd += f" {full_repo_name}"

    visibility = visibility or Visibility.PUBLIC
    base_cmd += f" --source={cwd} --{visibility.value}"
    if remote_name:
        base_cmd += f" --remote={shlex.quote(remote_name.strip()).strip()}"
    if description:
        base_cmd += f" --description={shlex.quote(description.strip()).strip()}"
    if url:
        base_cmd += f" --homepage={shlex.quote(str(url).strip()).strip()}"
    return base_cmd


def update_repo(
    filename: str | None = None,
    message: str | None = None,
    cwd: Path | str | None = None,
):
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    cmds = [
        f"git add {filename or cwd}",
        f"git commit -m '{shlex.quote(message).strip().strip() if message else stamp_date().strip()}'  {shlex.quote(str(filename).strip()).strip()}"
        if filename
        else f"git commit -a -m '{shlex.quote(message.strip() if message else stamp_date()).strip()}'",
        "git branch -M master",
        "git push -u origin master",
    ]
    try:
        for command in cmds:
            with cmd(command, cwd=cwd, delay=2) as result:
                if result.return_code != 0:
                    raise CommandError(
                        command,
                        result.return_code,
                        f"Command '{command}' failed with error: {result.error}",
                    )
                print(toterm(f"Command '{command}' executed successfully.", "green"))
    except CommandError as e:
        print(toterm(f"Command Error: {e.message}", "red"))
        raise CommandError(
            e.command,
            e.error_code,
            f"Failed to update repository {filename or cwd.name}. Check the commands and try again.",
        ) from e
    else:
        print(
            toterm(f"Repository {filename or cwd.name} updated successfully.", "green")
        )
        return "\n".join(cmds)


def create_repo(
    cwd: Path | str | None = None,
    *,
    username: str | None = None,
    repo_name: str | None = None,
    branch: str | None = None,
    description: str | None = None,
    message: str | None = None,
    visibility: Visibility | None = None,
    remote: str | None = None,
    url: URL | str | None = None,
    interactive: bool = False,
    author: str | None = None,
    author_email: str | None = None,
    version: str | None = None,
    license_type: str | None = None,
):
    """Create a remote GitHub repository and add it as a remote."""
    # This assumes you have the GitHub CLI installed and authenticated
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    with commit_context(
        cwd, description=description, message=message, branch=branch
    ) as (uname, rname, desc):
        repo_name = repo_name or rname
        username = username or uname
        description = description or desc
        url = f"https://github.com/{username}/{repo_name}.git"
        with setup_context(program_name=repo_name or cwd.name, cwd=cwd) as setup:
            setup.description = description
            setup.author = author or username
            setup.author_email = author_email or __email__
            setup.version = version or __version__
            setup.license = license_type or __license__
            setup.download_url = url
            setup(generate=True)
        try:
            repo_cmd = _repo_command(
                cwd,
                username=username,
                repo_name=repo_name,
                visibility=visibility,
                remote_name=remote,
                description=description,
                url=url,
                interactive=interactive,
            )
            with cmd(repo_cmd, cwd, delay=3) as com:
                return com.output
        except CommandError as e:
            print(toterm(f"Command failed: {e.message}", "red"))
            return alternate_commands(url)

def alternate_commands(url: str | URL | None = None):
    _results = []
    backupcmds = [
        f"git remote add origin {shlex.quote(str(url).strip())}",
        "git branch -M master",
        "git push -u origin master",
    ]
    try:
        print(toterm("trying alternate", "yellow"))
        commands = [cmd(c) for c in backupcmds]
        for command in commands:
            with command as com:
                _results.append(com.output)
                if com.return_code != 0:
                    raise CommandError(
                        com.command,
                        com.return_code,
                        f"Command '{com.command}' failed with error: {com.error}",
                    )
                print(
                    toterm(f"Command '{com.command}' executed successfully.", "green")
                )
    except CommandError as e:
        print(toterm(f"Backup commands failed: {e.message}", "red"))
        _results.append((e.command, e))
    else:
        print(toterm("Backup commands executed successfully.", "green"))
        return " ".join(_results)


# 4. Create an empty repo on GitHub, then add it as remote
# 5. In VS Code, use the Source Control tab to see changes, stage, unstage, commit, and push

# 6. To discard unstaged edits to a file:
def discard_changes(file_path: str,cwd: Path | str | None = None):
    """Discard unstaged changes to a file."""
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    return cmd(f"git checkout -- {file_path}",cwd)

# 7. To un-commit the last commit but keep changes in your working tree:
def uncommit_last(cwd: Path | str | None = None):
    """Un-commit the last commit but keep changes in the working tree."""
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    return _reset_commit(cwd=cwd)

# 8. To hard-reset to a previous commit (warning: this deletes newer commits):
def hard_reset(commit_hash: str, cwd: Path | str | None = None):
    """Hard reset to a specific commit."""
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    return cmd(f"git reset --hard {commit_hash.strip()}",cwd)

# 9. To revert a pushed commit (creates a new “undo” commit):
def revert_commit(commit_hash: str,cwd: Path | str | None = None):
    """Revert a pushed commit by creating a new commit that undoes the changes."""
    cwd = Path(cwd).absolute() if cwd else CURRENT_DIR
    return cmd(f"git revert {commit_hash.strip()}",cwd)




def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> tuple[argparse.Namespace, argparse.ArgumentParser]:
    global GIT_USERNAME
    if args.function_selector not in [str(selector.value) for selector in Selector]:
        parser.error(toterm(f"Invalid function selector: {args.function_selector}. Must be one of {[selector.value for selector in Selector]}."))
    if args.function_selector == Selector.INIT.value:
        #if not args.username or not args.repo_name:
        print(toterm("This command takes care of 'git init' through 'git commit'.", "green"))
    elif args.function_selector in [Selector.REVERT.value, Selector.HARD_RESET.value]:
        if not args.commit_hash:
            args.commit_hash = shlex.quote(input("Enter the commit hash to reset to: ").strip())
        if not args.commit_hash:
            parser.error(toterm("No commit hash provided. Aborting reset operation."))
        args.commit_hash = shlex.quote(args.commit_hash.strip())
    if args.description:
        args.description = shlex.quote(args.description.strip())
    if args.message:
        args.message = shlex.quote(args.message.strip())
    if args.branch:
        args.branch = shlex.quote(args.branch.strip())
    if args.username:
        args.username = shlex.quote(args.username.strip())
        GIT_USERNAME = args.username
    if args.repo_name:
        args.repo_name = shlex.quote(args.repo_name.strip())
    if args.filename:
        args.filename = Path(shlex.quote(args.filename)).absolute()
        if not args.filename.exists():
            parser.error(toterm(f"The specified file does not exist: {args.filename}"))
    args.cwd = Path(args.cwd).absolute() if args.cwd else CURRENT_DIR
    if not args.cwd.exists():
        parser.error(toterm(f"The specified directory does not exist: {args.cwd}"))
    if not args.cwd.is_dir():
        parser.error(toterm(f"The specified path is not a directory: {args.cwd}"))
    if args.url:
        args.url = URL(args.url.strip()) if isinstance(args.url, str) else args.url
        if not args.url.is_absolute():
            parser.error(toterm(f"The specified URL is not absolute: {args.url}"))
    if args.remote:
        args.remote = shlex.quote(args.remote.strip())
        if not args.remote:
            parser.error(toterm("Remote name cannot be empty."))
    if args.visibility and args.visibility not in Visibility:
            parser.error(toterm(f"Invalid visibility: {args.visibility}. Must be one of {[v.value for v in Visibility]}."))
    return args,parser

def single_init(args:argparse.Namespace,parser: argparse.ArgumentParser,cwd:Path | str | None = None):
    if args.function_selector == Selector._GIT_INIT.value:
        init_git(cwd, branch=args.branch)
        print(
            toterm(
                f"Git repository initialized in {cwd} with branch: {args.branch}",
                "green",
            )
        )
    elif args.function_selector == Selector._PRE_STAGE.value:
        staged, repo_name = pre_stage(cwd, description=args.description)
        if staged:
            print(
                toterm(
                    f"Pre-stage files created in {cwd} with repo name: {repo_name}",
                    "blue",
                )
            )
        else:
            print(toterm("Failed to create pre-stage files."))
    elif args.function_selector in [Selector._STAGE.value, Selector.ADD.value]:
        stage(cwd=cwd)
        print(toterm(f"Files staged in {cwd}", "cyan"))
    elif args.function_selector in [Selector._COMMIT.value, Selector.COMMIT.value]:
        msg = shlex.quote(args.message if args.message else input("Enter commit message: ")).strip()
        commit(cwd=cwd, message=msg)
        print(toterm(f"Changes committed in {cwd} with message: {msg}", "yellow"))
    elif args.function_selector == Selector._STATUS.value:
        status = cmd("git status", cwd=cwd)
        print(toterm(f"Git status in {cwd}:\n{status}", "yellow"))
    elif args.function_selector == Selector._BRANCH.value:
        branch = cmd("git branch -a", cwd=cwd)
        print(toterm(f"Git branches in {cwd}:\n{branch}", "magenta"))
    elif args.function_selector == Selector._LOG.value:
        log = cmd("git log --oneline", cwd=cwd)
        print(toterm(f"Git log in {cwd}:\n{log}", "blue"))
    elif args.function_selector == Selector._DIFF.value:
        diff = cmd("git diff", cwd=cwd)
        print(toterm(f"Git diff in {cwd}:\n{diff}", "green"))
    elif args.function_selector in [Selector.DISCARD.value, Selector.UNCOMMIT.value]:
        file_path = shlex.quote(
            input("Enter the file path to discard changes: ")
        ).strip()
        if args.function_selector != Selector.UNCOMMIT.value:
            discard_changes(file_path, cwd)
            print(toterm(f"Unstaged changes discarded for {file_path}", "yellow"))
        else:
            uncommit_last(cwd)
            print(
            toterm("Last commit uncommitted but changes kept in working tree."),
            "yellow",
        )
    elif args.function_selector in [Selector.HARD_RESET.value, Selector.REVERT.value]:
        commit_hash = shlex.quote(input("Enter the commit hash to reset to: ")).strip()
        if not commit_hash:
            raise CommandError(
                args.function_selector,
                1,
                f"No commit hash provided. Aborting {args.function_selector}.",
            )
        if args.function_selector == Selector.HARD_RESET.value:
            hard_reset(commit_hash, cwd)
        elif args.function_selector == Selector.REVERT.value:
            revert_commit(commit_hash, cwd)
        print(
            toterm(f"{args.function_selector.title()} to commit {commit_hash} completed."),
            "cyan",
        )

    elif args.function_selector == Selector.PUSH.value:
        cmd("git push -u origin master", cwd=cwd)
        print(toterm(f"Changes pushed to remote repository in {cwd}", "yellow"))
    elif args.function_selector == Selector.PULL.value:
        cmd("git pull origin master", cwd=cwd)
        print(toterm(f"Changes pulled from remote repository in {cwd}", "yellow"))
    elif args.function_selector == Selector.FETCH.value:
        cmd("git fetch origin", cwd=cwd)
        print(toterm(f"Changes fetched from remote repository in {cwd}", "yellow"))
    elif args.function_selector == Selector._VARS.value:
        print(toterm(f"Current working directory: {cwd}", "cyan"))
        print(toterm(f"Git username: {GIT_USERNAME}", "blue"))
        print(toterm(f"Git ignore file content:\n{GIT_IGNORE.strip()}", "green"))
        print(toterm(f"License file content:\n{LICENSE.strip()}", "magenta"))

    else:
        raise parser.error(
            f"Invalid function selector: {args.function_selector}. Must be one of {[selector.value for selector in Selector]}."
        )
def main_init(args:argparse.Namespace, parser: argparse.ArgumentParser):
    args, parser = validate_args(args, parser)
    global CURRENT_DIR
    CURRENT_DIR = Path(args.cwd).absolute()
    if len(args.function_selector) < 2 and isdigit(args.function_selector):
        args.function_selector = Selector(str(args.function_selector)).value
    if args.function_selector in [Selector._GIT_INIT.value, Selector._PRE_STAGE.value, Selector._STAGE.value, Selector._COMMIT.value, Selector._STATUS.value, Selector._LOG.value, Selector._BRANCH.value, Selector._DIFF.value, Selector.PUSH.value, Selector.PULL.value, Selector.FETCH.value, Selector.UNCOMMIT.value, Selector.DISCARD.value, Selector.REVERT.value, Selector.HARD_RESET.value, Selector.COMMIT.value, Selector._VARS.value]:
        single_init(args, cwd=CURRENT_DIR, parser=parser)
    elif args.function_selector == Selector.INIT.value:
        username, repo_name,description = initialize(
            CURRENT_DIR,
            description=args.description,
            message=args.message,
            branch=args.branch,
        )
        if username and repo_name and description:
            print(
                toterm(
                    f"Initialized git repository in {CURRENT_DIR} with username: {username} and repo name: {repo_name} and description: {description}",
                    "blue",
                )
            )
        else:
            print(toterm("Failed to initialize git repository."))
    elif args.function_selector == Selector.CREATE.value:
        create_repo(
            cwd=CURRENT_DIR,
            description=args.description,
            message=args.message,
            branch=args.branch,
            username=args.username,
            repo_name=args.repo_name,
            visibility=args.visibility,
            remote=args.remote,
            url=args.url,
            interactive=args.interactive,
        )
        print(
            toterm(
                f"Remote repository created and added as origin in {CURRENT_DIR}",
                "green",
            )
        )
    elif args.function_selector == Selector.RESET.value:
        reset(cwd=CURRENT_DIR, filename=args.filename)
        print(toterm(f"Reset operation completed in {CURRENT_DIR}", "magenta"))
    elif args.function_selector == Selector.UPDATE.value:
        if not args.filename:
            args.filename = shlex.quote(
                input("Enter the filename to update<DEFAULT: '.': ").strip()
            )
        if not args.filename:
            print(toterm("No filename provided. Updating all.", "magenta"))
            args.filename = "."
        if not args.message:
            args.message = shlex.quote(
                input(
                    f"Enter the commit message for update<DEFAULT: 'Update @ {stamp_date()}'>: "
                ).strip()
                or f"Updated @ {stamp_date()}"
            )
        update_repo(
            filename=args.filename,
            message=args.message,
            cwd=CURRENT_DIR,
        )
