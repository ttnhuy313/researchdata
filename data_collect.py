from github import Github
import pickle
import json
import requests

def analyzeCommits(repo):
    print('CURRENTLY WORKING WITH', repo.full_name)
    allCommits = repo.get_commits()
    numCommits = 40
    for commit in allCommits:
        if (numCommits == 0):
            break
        numCommits = numCommits - 1
        if (numCommits <= 36):
            continue
        
        print("    ", repo.get_commit(commit.sha).commit.url)
        commitURL = requests.get(repo.get_commit(commit.sha).commit.url)
        content = commitURL.json()
        print("     MESSAGE: ", content['message'])
        print("        ", len(commit.files), " files changed")
        for file in commit.files:
            print("        ", file.raw_url)
            print("        AFTER VERSION")
            print(file.patch)
            print("")
    print()
    print("**********************")
    print()

with open("credentials.dat", "rb") as file:
    data = pickle.load(file)
    token = data['token']

git = Github(token)
user = git.get_user()
print(git.get_rate_limit().core)

# repo = git.get_repo("tnlong311/trivia-app")
# commits = repo.get_commits()
# # print(repo.get_contents("lib/consts/app_styles.dart", ref = "a5fb80b8b177bd4c0ed6d8af08b9486c346077fb").decoded_content.decode())
# print(repo.get_commit("a5fb80b8b177bd4c0ed6d8af08b9486c346077fb").commit.url)
# for commit in commits:
#     print(commit.files[0].raw_url)

repositories = git.search_repositories(query = 'language:python')
cnt = 4
for repo in repositories:
    cnt = cnt - 1
    if (cnt == 0): 
        break
    print(repo.full_name)