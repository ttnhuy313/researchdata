from pygit2 import * 

repo_url = "https://github.com/tnlong311/trivia-app"
repo_path = "E:/FileC/Project/Research/repo/trivia-app"
repo = Repository(repo_path)
for commit in repo.walk(repo.head.target, GIT_SORT_TOPOLOGICAL):
    print(commit.oid)
    print(repo.__getitem__(commit.oid))
    print()

oid1 = "026c9aa82a05af9c3d36cb7d6265e937f094e761"
oid2 = "af84254e3fc79bdcbb7fe46ec80e8373721411b5"
print(repo.diff(repo.__getitem__(oid1), repo.__getitem__(oid2)).patch)