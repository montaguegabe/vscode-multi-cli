# cursor-multi

`cursor-multi` is the best way to work with Cursor on multiple Git repos at once. Set up your "sub-repos", for quick access to:

- Automatic syncing of Cursor rule .mcd files from the sub-repos
- Automatic syncing of your `.vscode` folder: `launch.json`, `tasks.json`, `settings.json`

## Installation

### Using `brew`

Run:
`brew tap montaguegabe/cursor-multi`
then
`brew install cursor-multi`

### Using `pipx` (MacOS, Linux, Windows):

- Install [pipx](https://github.com/pypa/pipx)
- Run `pipx install cursor-multi`

## Getting started

To get started, create a new directory that will house all your related repos and run:

```
multi init
```

Then paste in the URLs of all the repositories you want to use with Cursor. You can optionally specify descriptions of what they do, which will be used to create a new repo-directories.mdc Cursor rule.

It is recommended you also install the [VSCode/Cursor Extension]() that automatically keeps your project synced based on edits to files. To manually sync, you can run `multi sync`.

## Git operations
