import threading
from collections import defaultdict

from .git_repo import GitRepo


class GitRepoManager:

    manager_lock = threading.Lock()
    repo_map = defaultdict(None)

    @staticmethod
    def get_git_repo(https_repo_url : str, username : str, password: str):
        with GitRepoManager.manager_lock:
            repo = GitRepoManager.repo_map.get(https_repo_url)
            if repo is not None:
                return repo
            repo = GitRepo(https_repo_url, username, password)
            GitRepoManager.repo_map[https_repo_url] = repo
            return repo
