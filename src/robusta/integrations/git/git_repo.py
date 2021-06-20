import logging
import os
import shutil
import threading
import traceback
from datetime import datetime

from dulwich import porcelain

GIT_DIR_NAME = "robusta-git-audit"
REPO_LOCAL_BASE_DIR = os.path.join(os.environ.get("REPO_LOCAL_BASE_DIR", "/app"), GIT_DIR_NAME)
try:
    os.makedirs(REPO_LOCAL_BASE_DIR, exist_ok=True)
except Exception as e:
    print(f"Failed to create git audit base path {REPO_LOCAL_BASE_DIR}", traceback.print_exc())
    raise e

class GitRepo:

    def __init__(self, https_repo_url : str, username : str, password : str):
        url_parts = https_repo_url.split("://")
        self.repo_lock = threading.RLock()
        self.https_repo_url = https_repo_url
        self.repo_url = f"{url_parts[0]}://{username}:{password}@{url_parts[1]}"
        self.repo_name = os.path.splitext(os.path.basename(https_repo_url))[0]
        self.repo_local_path = os.path.join(REPO_LOCAL_BASE_DIR, self.repo_name)
        self.init_repo()

    def init_repo(self):
        with self.repo_lock:
            if os.path.exists(self.repo_local_path):
                logging.info(f"Deleting local repo before init {self.repo_local_path}")
                shutil.rmtree(self.repo_local_path)

            logging.info(f"Cloning git repo {self.https_repo_url}. repo name {self.repo_name}")
            self.repo = porcelain.clone(self.repo_url, self.repo_local_path)

    def commit(self, file_data : str, file_path : str, file_name, commit_message: str = "Robusta Git"):
        with self.repo_lock:
            file_local_path = os.path.join(self.repo_local_path, file_path)
            try:
                os.makedirs(file_local_path, exist_ok=True)
                git_file_name = os.path.join(file_local_path, file_name)
                with open(git_file_name, 'w') as git_file:
                    git_file.write(file_data)

                porcelain.add(self.repo, git_file_name)
                porcelain.commit(self.repo, commit_message)
            except Exception as e:
                logging.error(f"Commit file failed {self.repo_local_path} {file_path} {file_name}", traceback.print_exc())
                raise e

    def push(self):
        with self.repo_lock:
            porcelain.push(self.repo)

    def commit_push(self, file_data : str, file_path : str, file_name, commit_message: str):
        with self.repo_lock:
            self.commit(file_data, file_path, file_name, commit_message)
            self.push()

    def delete(self, file_path: str, file_name):
        with self.repo_lock:
            file_local_path = os.path.join(self.repo_local_path, file_path)
            if not os.path.exists(file_local_path): # file not in repo. Might have been added before the audit playbook was configured
                return

            try:
                porcelain.remove(self.repo, [os.path.join(file_local_path, file_name)])
                porcelain.commit(self.repo, f"robusta audit {datetime.now()} - delete")
            except Exception as e:
                logging.error(f"Commit file failed {self.repo_local_path} {file_path} {file_name}", traceback.print_exc())
                raise e

    def delete_push(self, file_path : str, file_name):
        with self.repo_lock:
            self.delete(file_path, file_name)
            self.push()
