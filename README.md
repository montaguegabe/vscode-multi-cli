# cursor-multi

`cursor-multi` is the best way to work with Cursor on multiple Git repos at once. Set up your "sub-repos", for quick access to:

- Automatic syncing of Cursor rule .mcd files from the sub-repos
- Automatic syncing of your `.vscode` folder: `launch.json`, `tasks.json`, `settings.json`

## Getting started

- First create a `multi.json` file in the root directory under which you would like the sub-repos to live:

E.g.:

```json
{
  "repos": [
    {
      "url": "https://github.com/myorg/myproject-backend"
    },
    {
      "url": "https://github.com/myorg/myproject-frontend"
    }
  ]
}
```
