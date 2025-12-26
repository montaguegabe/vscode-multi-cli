class NoRepositoriesError(Exception):
    pass


class GitError(Exception):
    pass


class RepoNotCleanError(GitError):
    pass


class RulesError(Exception):
    pass


class RuleParseError(RulesError):
    pass


class RulesNotCombinableError(RulesError):
    pass
