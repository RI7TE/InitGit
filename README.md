
# InitGit

InitGit is a Python command-line utility that streamlines Git repository initialization and management. It provides a comprehensive set of tools for working with Git repositories, especially for Python projects.

## Features

* Initialize Git repositories with appropriate setup files
* Stage, commit, and push changes
* Create remote GitHub repositories
* Generate Python project structure with [setup.py](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html)
* Manage project requirements
* Handle various Git operations (reset, revert, branch management, etc.)
* Support for visibility settings (public, private, internal)

## Installation

#Clone the repository

git clone https://github.com/RI7TE/InitGit.git

#Install the package

cd InitGit
pip install -e .


## Usage

InitGit can be used in various ways:

### Basic Git Operations

#Initialize a Git repository

initgit init

#Create a repository and push to GitHub

initgit create -u your_username -r repo_name

#Stage all changes

initgit add

#Commit changes

initgit commit -m "Your commit message"

#Push changes to remote

initgit push


### Advanced Operations


#Reset a file from staging

initgit reset -f filename.py

#Uncommit the last commit but keep changes

initgit uncommit

#Hard reset to a specific commit

initgit hard-reset --hash commit_hash

#Revert a pushed commit

initgit revert --hash commit_hash

#Set up a Python package structure

initgit setup --repo-name myproject --author "Your Name"

### Checking Status

#Check repository status

initgitstatus

#View commit log

initgitlog

#View branches

initgitbranch

#View differences

initgitdiff


## Environment Variables

InitGit uses the following environment variables:

* `GITHUB_USERNAME`: Your GitHub username
* [AUTHOR](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html): Default author name for license files
* [EMAIL](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html): Default email for license files
* `GITIGNORE_TEXTFILE`: Path to custom gitignore template (defaults to [_gitignore.txt](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html))

## License

Copyright (c) 2025 Steven Kellum. All Rights Reserved.

Licensed under the Personal Use License v1.0.

For commercial licensing inquiries, contact: Steven Kellum: [sk@perfectatrifecta.com](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html)

## Author

Steven Kellum [sk@perfectatrifecta.com](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html)

## Command Class

The core of the InitGit utility is the [Command](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html) class in [_command.py](vscode-file://vscode-app/Applications/Visual%20Studio%20Code%20-%20Insiders.app/Contents/Resources/app/out/vs/code/electron-browser/workbench/workbench.html), which provides a clean interface for executing shell commands with proper error handling. It manages subprocess execution, captures output and errors, and provides context management for running commands safely.
