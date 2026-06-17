"""Helper functions for git_utils API"""
import os

from functools import wraps
from typing import Callable, Optional, Union, cast

import git

from git.exc import InvalidGitRepositoryError


__all__ = [
    "repoRoot",
    "getLocalRepos",
    "findRepoByBranchName",
    "getCurrentBranchName",
    "getUnstagedFiles",
    "add",
    "commit",
    "push",
    "pull",
    "checkout"
]


def ensureRepo(func: Callable) -> Callable:
    """Decorator that ensures that a 'repo' arg passed to the wrapped function
    is converted to a valid git.Repo object.
    
    Note: Does not accept *args. Decorated function must enforce **kwargs.
    
    Args:
        func: A callable we can wrap
    
    Returns:
        The wrapped function with repo converted to git.Repo object
    
    """
    @wraps(func)
    def _wrapFunction(repo: Optional[Union[str, git.Repo]]=None, **kwargs):
        if not repo:
            repo = os.getcwd()
        
        if repo:
            try:
                if not isinstance(repo, git.Repo):
                    repo = git.Repo(repo)
            except InvalidGitRepositoryError as e:
                raise e
        return func(repo=repo, **kwargs)
    return _wrapFunction


def repoRoot() -> str:
    """Get the root to local git packages from the ENVOY_BNDL_ROOTS env var.

    This will not work if ENVOY_BNDL_ROOTS is not defined. This, like all of our
    git tools, assumes that the first or only entry in ENVOY_BNDL_ROOTS is the
    path to the git repos.
    
    Returns:
        Directory path to git repository root
        
    Raises:
        EnvironmentError: If ENVOY_BNDL_ROOTS is not defined
    
    """
    pkg_roots = os.getenv("ENVOY_BNDL_ROOTS")
    if not pkg_roots:
        raise EnvironmentError("No value in environment for ENVOY_BNDL_ROOTS")
    
    # The git root should be the first entry in ENVOY_BNDL_ROOTS
    return pkg_roots.split(';')[0]


def getLocalRepos(git_root: Optional[str]=None) -> list[git.Repo]:
    """Recursively collects all the local repositories from the git_root provided.
    
    Args:
        git_root: The directory path to the root of all local git repos.
                 If not provided, will call repoRoot()
    
    Returns:
        list of local repository as git.Repo objects
    
    Raises:
        IOError: If git_root is not a valid path
    
    """
    if not git_root:
        git_root = repoRoot()
        
    if not os.path.exists(git_root):
        raise IOError(f"git_root is not a valid path, got: {git_root}")
    
    git_repos = []
    
    for root, dirs, _ in os.walk(git_root, topdown=True):
        # If we find a '.git' folder in the dirs list we can stop recursion
        # and add the root as a known git repo.
        if ".git" in dirs:
            del dirs[:]
            git_repos.append(git.Repo(root))
    
    # Ensure there aren't duplicate entries and sort the results
    return git_repos


def findRepoByBranchName(branch_name: str, git_root: Optional[str]=None) -> list[git.Repo]:
    """Finds all repositories matching an exact branch name.
    
    Args:
        branch_name: Full name of branch
        git_root: The directory path to the root of all local git repos.
                 If not provided, will call repoRoot()
    
    Returns:
        List of local repo roots that have a branch matching the supplied branch_name
    
    """
    local_repos = getLocalRepos(git_root=git_root)
    
    matched_repos = []
    
    for repo in local_repos:
        # If a branch in the repo matches the supplied branch_name add it to the
        # collected list of repos.
        if any(b for b in repo.branches if b.name == branch_name):
            matched_repos.append(repo)
    return matched_repos


@ensureRepo
def getCurrentBranchName(*, repo: Optional[Union[str, git.Repo]]=None) -> str:
    """Return the active branch name of the supplied git repo path.
    
    Args:
        repo: Valid directory path to git repository or git.Repo object
    
    Returns:
        Active branch name of repository
        
    Raises:
        git.exc.NoSuchPathError: If repo is invalid path
        git.exc.InvalidGitRepositoryError: If repo is not a git repository
    
    """
    # ensureRepo decorator ensures repo is a git.Repo object
    repo = cast(git.Repo, repo)
    return repo.active_branch.name


@ensureRepo
def getUnstagedFiles(*, repo: Optional[Union[str, git.Repo]]=None) -> list[str]:
    """Returns updated and untracked files.
    
    Args:
        repo: The git repo root directory or git.Repo object
    
    Returns:
        List of file paths that are modified or untracked
    
    """
    # ensureRepo decorator ensures repo is a git.Repo object
    repo = cast(git.Repo, repo)
    # Get any updated files
    changedFiles = [item.a_path for item in repo.index.diff(None) if item.a_path is not None]
    # Return the updated files as well as any new untracked files
    return changedFiles + [f for f in repo.untracked_files if isinstance(f, str)]


@ensureRepo
def add(*, repo: Union[str, git.Repo], cmd: Optional[str]=None) -> None:
    """Run an 'add' command on the supplied repo.
    
    Args:
        repo: The git repo root directory or git.Repo object
        cmd: Command passed to 'add'
    
    """
    # ensureRepo decorator ensures repo is a git.Repo object
    repo = cast(git.Repo, repo)
    assert repo.git, "Could not resolve a valid git repository"
    repo.git.add(cmd)


@ensureRepo
def commit(*, repo: Union[str, git.Repo], message: str) -> None:
    """Run a 'commit' command on the repo.
    
    Args:
        repo: The git repo root directory or git.Repo object
        message: Commit message
    
    """
    # ensureRepo decorator ensures repo is a git.Repo object
    repo = cast(git.Repo, repo)
    assert repo.git, "Could not resolve a valid git repository"
    repo.index.commit(message)


@ensureRepo
def push(*, repo: Union[str, git.Repo], remote: str="origin") -> None:
    """Run a 'push' command on the repo.
    
    Args:
        repo: The git repo root directory or git.Repo object
        remote: The remote branch to push to
    
    """
    # ensureRepo decorator ensures repo is a git.Repo object
    repo = cast(git.Repo, repo)
    remote_repo = repo.remote(name=remote)
    remote_repo.push()


@ensureRepo
def pull(*, repo: Union[str, git.Repo], remote: str="origin", rebase: bool=False) -> None:
    """Run a 'pull' command on the repo.
    
    Args:
        repo: The git repo root directory or git.Repo object
        remote: The remote branch to pull from
        rebase: If True, perform a rebase instead of merge
    
    """
    # ensureRepo decorator ensures repo is a git.Repo object
    repo = cast(git.Repo, repo)
    remote_repo = repo.remote(name=remote)
    if rebase:
        remote_repo.pull(rebase=True)
    else:
        remote_repo.pull()
    

@ensureRepo
def checkout(*, repo: Union[str, git.Repo], branch_name: str, remote: bool=False) -> bool:
    """Run a 'checkout' command on the repo.
    
    Args:
        repo: The git repo root directory or git.Repo object
        branch_name: The branch to checkout
        remote: Checkout a remote branch. Will pass '-B' which will reset
               any local branch of the same name if it exists and checkout from remote
    
    Returns:
        True if checkout was successful
    
    Raises:
        AssertionError: If branch_name is not provided or remote branch doesn't exist
    
    """
    # ensureRepo decorator ensures repo is a git.Repo object
    repo = cast(git.Repo, repo)
    assert branch_name, "Supply valid branch name"
    assert repo.git, "Could not resolve a valid git repository"
    
    if remote:
        remote_branch_name = f"origin/{branch_name}"
        
        # Verify that the supplied branch name exists on the remote repo
        msg = f"No remote branch matches supplied branch_name: {branch_name}"
        assert repo.git.rev_parse(remote_branch_name, verify=True), msg
        
        repo.git.checkout("-B", branch_name, remote_branch_name)
    else:
        repo.git.checkout(branch_name)
    
    return True
