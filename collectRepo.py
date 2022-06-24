import os
from unicodedata import name
from github import Github
from pathlib import Path
import pickle
from time import sleep

BASE_DIR = Path.cwd()

if not os.path.exists(BASE_DIR / "repo" / "repoName.txt"):
    with open(BASE_DIR / "repo" / "repoName.txt", 'w') as nameFile:
        pass

if not os.path.exists(BASE_DIR / "repo" / "repoURL.txt"):
    with open(BASE_DIR / "repo" / "repoURL.txt", 'w') as urlFile:
        pass

#log in github to use search api
with open("credentials.dat", "rb") as file:
    data = pickle.load(file)
    token = data['token']
git = Github(token)
user = git.get_user()

repositories = git.search_repositories(query = 'language:python')
cnt = 5000

for repo in repositories:
    cnt = cnt - 1
    if (cnt == 0): 
        break
    urlFile = open(BASE_DIR / "repo" / "repoURL.txt", 'a')
    nameFile = open(BASE_DIR / "repo" / "repoName.txt", 'a')
    urlFile.write(repo.url + '\n')
    nameFile.write(repo.full_name + '\n')
    urlFile.close()
    nameFile.close()
    print(repo.url)
    sleep(2)
