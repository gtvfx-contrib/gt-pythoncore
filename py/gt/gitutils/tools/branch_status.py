
"""Prints out the rev-list of each git repo with matching branch name"""
import click
import git
from pathlib import Path

from threading import Lock, Thread
from typing import Optional

from gt.repl import ReplProgress
from gt.gitutils import findRepoByBranchName, getLocalRepos, getCurrentBranchName


class BranchStatusReporter:
    """Thread-safe reporter for collecting git repository branch status."""
    
    def __init__(self, show_clean: bool = False):
        """Initialize the reporter.
        
        Args:
            show_clean: If True, include reports for repos that are not behind
        """
        self._report_lines: list[str] = []
        self._lock = Lock()
        self._show_clean = show_clean
    
    def check_repo_status(self, repo_path: str, branch: Optional[str] = None) -> None:
        """Gets the rev list of the supplied repo_path and adds to the report.
        
        Args:
            repo_path: Valid path to git repo root
            branch: A branch name to check. If None, uses current branch

        """
        path = Path(repo_path)
        repo_name = "-".join(path.parts[-3:])
        
        repo = git.Repo(path)
        
        if not branch:
            branch = getCurrentBranchName(repo=path)
        
        try:
            output = repo.git.rev_list( # type: ignore
                "--left-right",
                "--count",
                f"origin/HEAD...{branch}"
            )
        except git.GitCommandError:
            return
        
        output_list = output.split()
        
        try:
            behind_count = int(output_list[0])
            ahead_count = int(output_list[1])
        except (ValueError, IndexError):
            # Error parsing rev-list output
            return
        
        if behind_count == 0 and not self._show_clean:
            return
        
        # Thread-safe append to report
        with self._lock:
            self._report_lines.append(f"\n{repo_name}")
            self._report_lines.append(f"behind: {behind_count} | ahead: {ahead_count}")
    
    def get_report(self) -> str:
        """Get the compiled report.
        
        Returns:
            The formatted report string
        """
        if not self._report_lines:
            return ""
        return "\n".join(self._report_lines)


@click.command(name='branch_status')
@click.option('-b', '--branch', default=None, required=False, help='Branch name to check')
@click.option('-s', '--show_clean', is_flag=True, help='Show repos that are up to date')
def main(branch: Optional[str] = None, show_clean: bool = False) -> None:
    """Check branch status across all local git repositories."""
    if branch:
        local_repos = findRepoByBranchName(branch)
    else:
        local_repos = getLocalRepos()
    
    if not local_repos:
        print("Unable to find any local git repositories")
        return
    
    reporter = BranchStatusReporter(show_clean=show_clean)
    
    progress_bar = ReplProgress(
        len(local_repos),
        caption="Preparing threads...",
        bar_length=60
    )
    
    progress_bar.start()
    threads = [
        Thread(target=reporter.check_repo_status, args=(Path(repo.working_dir), branch))
        for repo in local_repos
    ]
    
    # Start the threads
    for thread in threads:
        progress_bar.step()
        thread.start()
    
    # Wait for the threads to complete
    for thread in threads:
        thread.join()
    
    report = reporter.get_report()
    if report:
        print(f"\n{report}")
    else:
        print("All repos are up to date.")
    


if __name__ == "__main__":
    main()
