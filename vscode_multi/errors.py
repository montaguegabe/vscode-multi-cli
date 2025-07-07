class NoRepositoriesError(Exception):
    pass


class MergeBranchError(Exception):
    pass


class GitError(Exception):
    pass


class RepoNotCleanError(Exception):
    pass


class RuleParseError(Exception):
    pass


class RulesNotCombinableError(Exception):
    pass
