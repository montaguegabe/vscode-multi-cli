class NoRepositoriesError(Exception):
    pass


class GitError(Exception):
    pass


class RepoNotCleanError(GitError):
    pass
