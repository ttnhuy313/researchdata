from pygit2 import *
from pathlib import Path
import os
import shutil

startRepo = 0
endRepo = 2
BASE_DIR = Path.cwd()

def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.
    
    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def process(repo):
    name = repo.split('/')[1].split('\n')[0]
    fullName = repo
    fullName = fullName[:-1]
    url = "https://github.com/" + fullName
    print(url)
    print('Processing ', fullName)

    if os.path.exists(BASE_DIR / "repo" / name):
        shutil.rmtree(BASE_DIR / "repo" / name, ignore_errors=True, onerror= onerror)

    if not os.path.exists(BASE_DIR / "repo" / name):
        os.mkdir(BASE_DIR / "repo" / name)
    repo = clone_repository(url, BASE_DIR / "repo" / name)

    preOid = ''
    for commit in repo.walk(repo.head.target, GIT_SORT_TOPOLOGICAL):
        print(commit.oid)
        if (preOid != ''):
            print(repo.diff(repo.__getitem__(commit.oid), repo.__getitem__(preOid)).patch)
        print()
        preOid = commit.oid
        
    if os.path.exists(BASE_DIR / "repo" / name):
        shutil.rmtree(BASE_DIR / "repo" / name, ignore_errors=True, onerror= onerror)

    
nameFile = open(BASE_DIR / "repo" / "repoName.txt", "r")
repoName = nameFile.readlines()
for i in range(startRepo, endRepo + 1):
    process(repoName[i])

