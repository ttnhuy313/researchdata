from pygit2 import *
from pathlib import Path
import os

startRepo = 0
endRepo = 2
BASE_DIR = Path.cwd()

def process(repo):
    name = repo.split('/')[1].split('\n')[0]
    fullName = repo
    print('Processing ', fullName)
    if not os.path.exists(BASE_DIR / "repo" / name):
        os.mkdir(BASE_DIR / "repo" / name)

    if os.path.exists(BASE_DIR / "repo" / name):
        os.rmdir(BASE_DIR / "repo" / name)

    
nameFile = open(BASE_DIR / "repo" / "repoName.txt", "r")
repoName = nameFile.readlines()
for i in range(startRepo, endRepo + 1):
    process(repoName[i])

