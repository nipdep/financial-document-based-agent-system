# Project Name

Welcome to the Project Name repository. This document will guide you through the folder structure, branching strategy, commit method, README update method, PR method, and dataset pushing rules.

## Table of Contents

- [Project Name](#project-name)
  - [Table of Contents](#table-of-contents)
  - [Folder Structure](#folder-structure)
  - [Branching Strategy](#branching-strategy)
  - [Commit Method](#commit-method)
  - [README Update Method](#readme-update-method)
  - [PR Method](#pr-method)
  - [Dataset Pushing Rules](#dataset-pushing-rules)
  - [Contact](#contact)

## Folder Structure

```
your_project/
├── docs/ # Documentation files
│ ├── Makefile # Sphinx Makefile for building docs
│ ├── source/ # Source files for Sphinx
│ │ ├── conf.py # Sphinx configuration file
│ │ ├── index.rst # Main index file for documentation
│ │ ├── ...
│ ├── _build/ # Build directory for Sphinx
├── src/ # Main project directory
│ ├── init.py # Package initializer
│ ├── module1.py # Module 1
│ ├── module2.py # Module 2
│ ├── ...
├── notebooks/ # Main project directory
│ ├── init.ipynb # Package initializer
│ ├── module1.ipynb # Module 1
│ ├── module2.ipynb # Module 2
│ ├── ...
├── tests/ # Test files
│ ├── test_module1.py # Tests for Module 1
│ ├── test_module2.py # Tests for Module 2
│ ├── ...
├── .gitignore # Git ignore file
├── requirements.txt # Python dependencies
├── README.md # This README file
├── ...
```

## Branching Strategy

We follow a Git branching strategy to streamline our development process:

- **main**: The stable branch. Contains the latest stable release.
- **dev**: The development branch. All new features and bug fixes are merged here first.
- **feature/\<Clicup-ticket-ID\>\<feature-name\>**: Feature branches. Created from `dev` for developing new features.
- **bugfix/\<Clicup-ticket-ID\>\<bug-name\>**: Bug fix branches. Created from `dev` for fixing bugs.
- **hotfix/\<Clicup-ticket-ID\>\<hotfix-name\>**: Hotfix branches. Created from `main` for urgent fixes.

## Commit Method

We use the following commit message format to maintain clear and consistent commit history:
`[<type>] : <subject>`

Types include:

- feat: A new feature
- fix: A bug fix
- docs: Documentation only changes
- style: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
- refactor: A code change that neither fixes a bug nor adds a feature
- test: Adding missing or correcting existing tests
- chore: Changes to the build process or auxiliary tools and libraries

## README Update Method
To update this README file:

1. Create a new branch from dev (e.g., docs/update-readme).
2. Make the necessary updates.
3. Commit your changes following the commit method guidelines.
4. Create a PR to dev for review.

## PR Method
When creating a Pull Request (PR):

1. Ensure your branch is up-to-date with dev.
2. Write a clear and concise title and description for the PR.
3. Link related issues (if any).
4. Request reviews from relevant team members.
5. Address any feedback and make necessary changes.
6. Once approved, the PR will be merged into dev.

## Dataset Pushing Rules
Do not push datasets or any large files to the repository. Instead, use the following guidelines:

1. Add the dataset files to .gitignore.
2. Use an external storage solution (e.g., AWS S3, Google Drive) to store datasets.
3. Provide instructions in the README or separate documentation on how to access and download the datasets.

## Contact
For any questions or issues, please contact the project maintainers.
@nipdep 