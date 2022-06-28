from pygit2 import *
from pathlib import Path
import os
import shutil
import re

startRepo = 0
endRepo = 50
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

#Criteria for choosing a pair
# - Both are the first occurrence (Initialization of a variable?)
# - Not number (Change of number)
# - Not header of the diff patch (+++ a/lib/example.txt\n--- b/lib/example.txt) done
# - Not the use of other libraries' function (Colors.black vs Colors.white)
# - The structure of ast is too different (Change of the entire line of the same position)
# - Maybe select the smaller part in the token?
# - Same number of tokens? done
# - Only one difference in token position
# Not too short
def filter(ver1, ver2):
    if (len(ver1) <= 8 or len(ver2) <= 8):
        return False
    tokens1 = re.findall(r'\S+', ver1)
    tokens2 = re.findall(r'\S+', ver2)
    if (len(tokens1) != len(tokens2)):
        return False
    cnt = 0
    for i in range(0, len(tokens1)):
        if (tokens1[i] != tokens2[i]):
            cnt = cnt + 1
            if (len(re.findall(r'\d', tokens1[i])) > 1):
                return False
    if (cnt > 1 or cnt == 0):
        return False
    if (ver2[0] == '+'):
        return False
    return True

def process(repo):
    cnt = 0
    name = repo.split('/')[1].split('\n')[0]
    fullName = repo
    fullName = fullName[:-1]
    url = "https://github.com/" + fullName
    print(url)
    print('Processing ', fullName)

    if os.path.exists(BASE_DIR / "repo" / name):
        shutil.rmtree(BASE_DIR / "repo" / name, ignore_errors=True, onerror= onerror)
        os.rmdir(BASE_DIR / "repo" / name)

    if not os.path.exists(BASE_DIR / "repo" / name):
        os.mkdir(BASE_DIR / "repo" / name)
    print('cloning')
    repo = clone_repository(url, BASE_DIR / "repo" / name)
    print('ok')

    preOid = ''
    for commit in repo.walk(repo.head.target, GIT_SORT_TOPOLOGICAL):
        print(commit.oid)
        if (preOid != ''):
            diff = repo.diff(repo.__getitem__(commit.oid), repo.__getitem__(preOid)).patch
            matches = re.findall(r"[-](.*)[\n][+](.*)", diff)
            for match in matches:
                if (filter(match[0], match[1]) == False):
                    continue
                file = open('pair.txt', 'a', encoding="utf-8")
                file.write(fullName + '\n')
                file.write(repr(commit.oid) + ' ')
                file.write(repr(preOid) + '\n')
                for d in match:
                    file = open('pair.txt', 'a', encoding="utf-8")
                    file.write(d.strip() + '\n')
                    file.close()
                file = open('pair.txt', 'a', encoding="utf-8")
                file.write('--------------------------------END-----------------------------' + '\n')
                file.close()
        preOid = commit.oid
        
    if os.path.exists(BASE_DIR / "repo" / name):
        shutil.rmtree(BASE_DIR / "repo" / name, ignore_errors=True, onerror= onerror)

f = open('pair.txt', 'w')
f.close()
nameFile = open(BASE_DIR / "repo" / "repoName.txt", "r")
repoName = nameFile.readlines()
for i in range(startRepo, endRepo + 1):
    process(repoName[i])

