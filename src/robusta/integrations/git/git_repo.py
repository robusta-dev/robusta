import logging
import os
import shutil
import textwrap
import threading
from collections import defaultdict
import traceback
import uuid
from datetime import datetime

from dulwich import porcelain

GIT_DIR_NAME = "robusta-git"
REPO_LOCAL_BASE_DIR = os.path.join(
    os.environ.get("REPO_LOCAL_BASE_DIR", "/app"), GIT_DIR_NAME
)
SSH_ROOT_DIR = os.environ.get("SSH_ROOT_DIR", "/root/.ssh")


class GitRepoManager:

    manager_lock = threading.Lock()
    repo_map = defaultdict(None)

    @staticmethod
    def get_git_repo(git_repo_url: str, git_key: str):
        with GitRepoManager.manager_lock:
            repo = GitRepoManager.repo_map.get(git_repo_url)
            if repo is not None:
                return repo
            repo = GitRepo(git_repo_url, git_key)
            GitRepoManager.repo_map[git_repo_url] = repo
            return repo

    @staticmethod
    def remove_git_repo(git_repo_url):
        with GitRepoManager.manager_lock:
            del GitRepoManager.repo_map[git_repo_url]

    @staticmethod
    def clear_git_repos():
        with GitRepoManager.manager_lock:
            GitRepoManager.repo_map.clear()


class GitRepo:

    initialized: bool = False

    def __init__(self, git_repo_url: str, git_key: str):
        GitRepo.init()
        self.key_file_name = self.init_key(git_key)
        self.repo_lock = threading.RLock()
        self.git_repo_url = git_repo_url
        self.repo_name = os.path.splitext(os.path.basename(git_repo_url))[0]
        self.repo_local_path = os.path.join(REPO_LOCAL_BASE_DIR, self.repo_name)
        self.init_repo()

    def init_key(self, git_key):
        pkey_name = str(uuid.uuid4())
        key_file_name = os.path.join(REPO_LOCAL_BASE_DIR, pkey_name)
        with open(key_file_name, "w") as key_file:
            key_file.write(textwrap.dedent(f"{git_key}"))
        os.chmod(key_file_name, 0o400)
        if not os.path.exists(SSH_ROOT_DIR):
            os.mkdir(SSH_ROOT_DIR)
        os.system(f"ssh-keyscan -H github.com >> {SSH_ROOT_DIR}/known_hosts")
        return key_file_name

    @staticmethod
    def init():
        if GitRepo.initialized:
            return
        try:
            os.makedirs(REPO_LOCAL_BASE_DIR, exist_ok=True)
        except Exception as e:
            print(
                f"Failed to create git audit base path {REPO_LOCAL_BASE_DIR}",
                traceback.print_exc(),
            )
            raise e
        GitRepo.initialized = True

    def init_repo(self):
        with self.repo_lock:
            if os.path.exists(self.repo_local_path):
                logging.info(f"Deleting local repo before init {self.repo_local_path}")
                shutil.rmtree(self.repo_local_path)

            logging.info(
                f"Cloning git repo {self.git_repo_url}. repo name {self.repo_name}"
            )
            self.repo = porcelain.clone(
                self.git_repo_url, self.repo_local_path, key_filename=self.key_file_name
            )

    def commit(
        self,
        file_data: str,
        file_path: str,
        file_name,
        commit_message: str = "Robusta Git",
    ):
        with self.repo_lock:
            self.pull_rebase()
            file_local_path = os.path.join(self.repo_local_path, file_path)
            try:
                os.makedirs(file_local_path, exist_ok=True)
                git_file_name = os.path.join(file_local_path, file_name)
                with open(git_file_name, "w") as git_file:
                    git_file.write(file_data)

                porcelain.add(self.repo, git_file_name)
                porcelain.commit(self.repo, commit_message)
            except Exception as e:
                logging.error(
                    f"Commit file failed {self.repo_local_path} {file_path} {file_name}",
                    traceback.print_exc(),
                )
                GitRepoManager.remove_git_repo(self.git_repo_url)
                raise e

    def push(self):
        with self.repo_lock:
            try:
                porcelain.push(self.repo, key_filename=self.key_file_name)
            except Exception as e:
                GitRepoManager.remove_git_repo(self.git_repo_url)
                logging.error(
                    f"Push failed {self.repo_local_path}", traceback.print_exc()
                )
                raise e

    def pull_rebase(self):
        with self.repo_lock:
            os.system(
                f"cd {self.repo_local_path} && GIT_SSH_COMMAND='ssh -i {self.key_file_name} -o IdentitiesOnly=yes' git pull --rebase origin master"
            )

    def commit_push(
        self, file_data: str, file_path: str, file_name, commit_message: str
    ):
        with self.repo_lock:
            self.commit(file_data, file_path, file_name, commit_message)
            self.push()

    def delete(self, file_path: str, file_name):
        with self.repo_lock:
            file_local_path = os.path.join(self.repo_local_path, file_path)
            if not os.path.exists(
                file_local_path
            ):  # file not in repo. Might have been added before the audit playbook was configured
                return

            try:
                self.pull_rebase()
                porcelain.remove(self.repo, [os.path.join(file_local_path, file_name)])
                porcelain.commit(self.repo, f"robusta audit {datetime.now()} - delete")
            except Exception as e:
                logging.error(
                    f"Commit file failed {self.repo_local_path} {file_path} {file_name}",
                    traceback.print_exc(),
                )
                GitRepoManager.remove_git_repo(self.git_repo_url)
                raise e

    def delete_push(self, file_path: str, file_name):
        with self.repo_lock:
            self.delete(file_path, file_name)
            self.push()
