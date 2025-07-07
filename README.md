# vscode-multi

`vscode-multi` is the best way to work with VS Code on multiple Git repos at once. It allows more flexibility than VS Code multi root workspaces.

-   Automatic syncing of your `.vscode` folder: `launch.json`, `tasks.json`, `settings.json`

## Installation

### Using `brew`

Run:
`brew tap montaguegabe/vscode-multi`
then
`brew install vscode-multi`

### Using `pipx` (MacOS, Linux, Windows):

-   Install [pipx](https://github.com/pypa/pipx)
-   Run `pipx install vscode-multi`

## Getting started

To get started, create a new directory that will house all your related repos and run:

```
multi init
```

Then paste in the URLs of all the repositories you want to use with VS Code. You can optionally specify descriptions of what they do, which will be used to create a new repo-directories.mdc Cursor rule.

It is recommended you also install the [VS Code Extension]() that automatically keeps your project synced based on edits to files. To manually sync, you can run `multi sync`.

## Git operations

## TODO:

https://github.com/dawidd6/action-homebrew-bump-formula
