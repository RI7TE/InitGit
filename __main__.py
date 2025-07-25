
from __future__ import annotations
import os
import sys

from pathlib import Path
from typing import TYPE_CHECKING

import ujson as json


sys.path.append(str(Path(__file__).absolute().parent))
if TYPE_CHECKING:
    import typing

import argparse

from initgit import CommandError, Selector, Visibility, main_init, toterm


__version__ = "1.0.0"

def parse_arguments():
    parser = argparse.ArgumentParser(
        prog="initgit",
        usage=toterm(
            """%(prog)s  <function_selector> | [options]
Function selectors:
  init
            Initialize a git repository in the current directory, stage, and commit.
  create
            Create a local repository on GitHub and add it as origin.
  discard
            Discard unstaged changes to a file.
  uncommit
            Un-commit the last commit but keep changes in the working tree.
  reset
            Hard reset to a specific commit.
  revert
            Revert a pushed commit by creating a new commit that undoes the changes.
   add
            Stage all files in the current directory.
  commit
            Commit staged files with a message.
  status
            Check the status of the git repository.
  log
            View the git log.
  branch
            View the git branches.
  diff
            View the git diff.
  push
            Push changes to the remote repository.
  pull
            Pull changes from the remote repository.
  fetch
            Fetch changes from the remote repository.
Options:
  --cwd
                The directory to initialize the git repository in.
  -d, --description
                Description for the repository. Default is the current directory name.
  -m, --message
                Commit message for the initial commit. Default is 'First commit'.
  -b, --branch
                Branch name for the initial commit. Default is 'master'.
  -u, --username
                GitHub username for creating a remote repository. Use with -r or --repo.
  -r, --repo
                Repo name for creating a remote repository. Use with -u or --username.
  -f, --filename
                Filename to reset stage for. If not provided, will prompt for input.
  --hash
                Commit hash to reset to for hard reset or revert.
  -v, --visibility
                Visibility of the repository. Default is 'public'.
  --remote
                Remote name for the repository. Default is 'origin'.
  --url
                URL for the repository. Default is None.
  --interactive
                Run the command in interactive mode.
    --version
                Show the version of the script.
    -h, --help
                Show this help message and exit.
""",
            "green",
        ),
        description="Initialize a git repository, create a remote repo, or manage git operations.",
        # add_help=True,
        allow_abbrev=True,
    )
    parser.add_argument(
        "function_selector",
        type=str,
        help=f"Function selector: {', '.join([selector.value for selector in Selector])}",
        metavar="<function_selector>",
        choices=[selector.value for selector in Selector],
        default=Selector.INIT.value,
    )
    parser.add_argument(
        "--cwd",
        type=str,
        default=Path.cwd(),
        help="The directory to initialize the git repository in.",
    )
    parser.add_argument(
        "-d",
        "--description",
        type=str,
        default=None,
        help="Description for the repository. Default is the current directory name.",
        dest="description",
        metavar="</DESCRIPTION/>",
    )
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        help="GitHub username for creating a remote repository.",
        dest="username",
        metavar="<username>",
    )
    parser.add_argument(
        "-r",
        "--repo",
        type=str,
        help="Repo name for creating a remote repository.",
        dest="repo_name",
        metavar="<repo_name>",
    )
    parser.add_argument(
        "-m",
        "--message",
        type=str,
        default="First commit",
        help="Commit message for the initial commit. Default is 'First commit'.",
        dest="message",
    )
    parser.add_argument(
        "-b",
        "--branch",
        type=str,
        default="master",
        help="Branch name for the initial commit. Default is 'master'.",
        dest="branch",
    )
    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        help="Filename to reset stage for. If not provided, will prompt for input.",
        dest="filename",
        metavar="<filename>",
    )
    parser.add_argument(
        "--hash",
        type=str,
        help="Commit hash to reset to for hard reset or revert.",
        dest="commit_hash",
        metavar="<commit_hash>",
    )
    parser.add_argument(
        "-v",
        "--visibility",
        type=Visibility,
        choices=list(Visibility),
        default=Visibility.PUBLIC,
        help="Visibility of the repository. Default is 'public'.",
        dest="visibility",
    )
    parser.add_argument(
        "--remote",
        type=str,
        default="origin",
        help="Remote name for the repository. Default is 'origin'.",
        dest="remote",
    )
    parser.add_argument(
        "--url",
        type=str,
        help="URL for the repository. Default is None.",
        dest="url",
        metavar="<url>",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run the command in interactive mode.",
        dest="interactive",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__name__} {__version__}",
        help="Show the version of the script.",
    )
    args = parser.parse_args()
    return args, parser


if __name__ == "__main__":
    args, parser = parse_arguments()
    try:
        main_init(args, parser)
    except CommandError as e:
        print(toterm(f"CommandError: {e}", "red"))
        sys.exit(e.error_code if e.error_code else 1)
    except Exception as e:
        print(toterm(f"An unexpected error occurred: {e}", "red"))
        sys.exit(1)
