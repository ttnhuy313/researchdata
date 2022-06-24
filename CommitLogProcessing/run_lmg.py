import re
import subprocess
import sys
import os
import multiprocessing
import logging
from pathlib import Path
import argparse
import data_preparation
from copy import copy

# create folders that will hold data
BASE_DIR = Path.cwd().parent
# with open(BASE_DIR/"no_todos_repos.txt") as file:
#     no_todo_repos = [line.rstrip('\n') for line in file]

# create log folder
if not os.path.isdir(BASE_DIR / "CommitLogGeneration" / "log"):
    os.mkdir(BASE_DIR / "CommitLogGeneration" / "log")
if not os.path.isdir(BASE_DIR / "CommitLogGeneration" / "log" / "java"):
    os.mkdir(BASE_DIR / "CommitLogGeneration" / "log" / "java")
if not os.path.isdir(BASE_DIR / "CommitLogGeneration" / "log" / "python"):
    os.mkdir(BASE_DIR / "CommitLogGeneration" / "log" / "python")

# create outputs folder
if not os.path.isdir(BASE_DIR / "CommitLogGeneration" / "data"):
    os.mkdir(BASE_DIR / "CommitLogGeneration" / "data")


logger = logging.getLogger("my_logger")
logger.addHandler(logging.StreamHandler())

def clean_repos(lang, fmt):
    proj_names = Utils.get_proj_names_in_scripts_folder(lang, fmt)
    anbiguous_lst, proj_tmp, url_tmp = Utils.get_ambiguous_proj(lang)

    # delete anbiguous repos
    for proj in proj_names:
        if proj in anbiguous_lst:
            idx = proj_tmp.index(proj)
            del proj_tmp[idx]
            del url_tmp[idx]

    # delete unsuccessfully downloaded repos
    proj_tmp_copy = copy(proj_tmp)
    for proj in proj_tmp_copy:
        if proj not in proj_names:
            idx = proj_tmp.index(proj)
            del proj_tmp[idx]
            del url_tmp[idx]

    return proj_tmp, url_tmp

def run(lang, fmt, repo_num):
    lock = multiprocessing.Manager().Lock()

    # counter = multiprocessing.Value("i", lock=True)
    # counter.value = 0
    # _, _, url_tmp = Utils.get_ambiguous_proj(lang)
    proj_tmp, url_tmp = clean_repos(lang, fmt)
    assert(len(url_tmp) == len(proj_tmp))

    for i, proj in enumerate(proj_tmp):
        if proj_tmp[i] == "quasar":
            print(url_tmp[i])

    n_repos = len(proj_tmp)
    print(n_repos)
    if repo_num != None:
        if repo_num > n_repos:
            raise Exception("Not enough repos")
        else:
            url_tmp = url_tmp[:repo_num]
            proj_tmp = proj_tmp[:repo_num]
            n_repos = repo_num

    logger.info(f"Number of repos: {len(proj_tmp)}")
    pool = multiprocessing.Pool(15)
    pool.map(clone_project,
             zip(url_tmp, proj_tmp, range(1, n_repos + 1), [lang] * n_repos, [lock] * n_repos, [fmt] * n_repos))
    pool.close()

def clone_project(t):
    url = t[0]
    proj= t[1]
    i = t[2]
    lang = t[3]
    lock = t[4]
    fmt = t[5]

    proj=proj.strip("'").strip("$").strip("\n")
    if proj not in url:
        print("mismatch")
    begin = url.find("https:")
    end = url.find(".git")
    url = url[begin:end + 4]

    data_preparation.main([lang, proj, url], lock, fmt)


def get_args():
    parser = argparse.ArgumentParser(
        description="A simple argument parser",
    )

    parser.add_argument('lang', choices=['java', 'python'])
    parser.add_argument('fmt', choices=['our_proj', 'tdcleaner'])
    parser.add_argument('-n', '--repo_num', nargs='?', default=None)

    return parser.parse_args()

class Utils:
    @staticmethod
    def get_proj_names_in_scripts_folder(lang, fmt):
        proj_lst = os.listdir(BASE_DIR / "scripts" / lang / fmt)
        return proj_lst

    @staticmethod
    def get_ambiguous_proj(lang):
        # few projects have the same name in lang.names file
        # however, as they are from different github projects, their urls in lang.urls file are different
        # this function returns proj_lst contains proj names of such cases
        file = lang + ".urls"
        with open(BASE_DIR/file, "r") as url_file:
            url_lines = [line.strip() for line in url_file]

        file = lang + ".names"
        with open(BASE_DIR/file, "r") as proj_file:
            proj_lines = [line.strip() for line in proj_file]

        assert (len(url_lines) == len(proj_lines))
        n = len(url_lines)
        proj_tmp = []
        url_tmp = []
        ambiguous_projs = []

        for i in range(n):
            if proj_lines[i] in proj_tmp:
                if url_lines[i] not in url_tmp:
                    # projects with the same name but different url
                    ambiguous_projs.append(proj_lines[i])
                    continue
                else:
                    # A project that appreared multiple times in lang.url and lang.names
                    continue
            else:
                proj_tmp.append(proj_lines[i])
                url_tmp.append(url_lines[i])

        # print("ambiguous_projs:", "TouTiao" in ambiguous_projs)
        # print("proj_tmp:","TouTiao" in proj_tmp)


        return ambiguous_projs, proj_tmp, url_tmp


def test():
    Utils.get_no_todo_projects("python")

def main(args):
    # repo_num = int(args.repo_num)
    lang = args.lang
    fmt = args.fmt
    if args.repo_num != None:
        repo_num = int(args.repo_num)
    else:
        repo_num = None

    process = multiprocessing.Process(target=run, args=(lang, fmt, repo_num))
    process.start()
    process.join()

if __name__ == "__main__":
    # test()
    import time

    args = get_args()

    log_file_name = args.lang + "_" + args.fmt + "_" + str(args.repo_num)+".log"

    logging.basicConfig(
        level=logging.DEBUG,
        filemode='w',
        filename= BASE_DIR / "CommitLogGeneration" / "log"/ log_file_name,
        format='%(asctime)s %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p'
    )

    start = time.time()
    main(args)
    end = time.time()
    logger.info(f"The Whole Process Was Taken : {end - start:.3f}s")
