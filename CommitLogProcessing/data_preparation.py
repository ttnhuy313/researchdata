import sys
import re
import subprocess
from pathlib import Path
from utils import *
import os
import logging
import spacy

logger = logging.getLogger("my_logger")

class Controller:
    BASE_DIR = Path.cwd().parent
    verbs = ['add', 'create', 'make', 'implement', 'fix', 'remove', 'update', 'upgrade', 'use', 'move', 'change', 'improve', 'allow']
    nlp = spacy.load("en_core_web_sm")

    def __init__(self, argv, _lock, fmt, cmt_cls):
        self.lang = argv[0]
        self.proj = argv[1]
        self.url = argv[2]
        self.fmt = fmt
        self.cmt_cls = cmt_cls
        self.lock = _lock
        self.cmt_types = []
        self.lg_debug = []

    def is_ascii(self, s):
        return all(ord(c) < 128 for c in s)

    def _separate_commits(self, subject):
        reobj = re.compile(r"""
                                commit.*?\n(?=commit|\Z)  # \Z is for catching the last commit
                            """,
                           re.VERBOSE | re.DOTALL | re.UNICODE)
        commits_lst = reobj.findall(subject)
        return commits_lst

    def _extract_diffs(self, commit):
        """
        extract diffs
        :param commit: whole commit from "log -p --function-context -- '*.java'"
        :return result: a list of diffs
        """
        result = []
        for matchobj in re.finditer(r"""
                                           ^diff.*?(?=diff|\Z)
                                       """, commit, re.VERBOSE | re.DOTALL | re.MULTILINE | re.UNICODE):
            result.append(matchobj.group())

        return result

    def process(self):
        file_name = self.proj

        # replace non-ascii characters with \ufffd (the replacement character)
        # later used \ufffd to filter out commits with non-english commit message
        with open(self.BASE_DIR / "scripts" / self.lang / self.fmt / file_name, "r", encoding="ascii", errors="replace") as outputFile:
            self.subject = outputFile.read()


        self.commits_lst = self._separate_commits(self.subject)
        self.commits_lst = [cmt.lower() for cmt in self.commits_lst]

        # print("BEFORE: ", len(self.commits_lst))
        self._filter_at_commit_level()
        # print("AFTER: ", len(self.commits_lst))


        self.commits_lst = list(filter(
                                lambda cmt: self._filter_at_MSG_level(cmt) != -1,
                                self.commits_lst
                                    )
                             )


        # register repo with no valid commit
        if len(self.commits_lst) == 0:
            logger.info(f"### {self.proj} {self.url} has no valid commit")
            return

        save = False
        assert(len(self.commits_lst) == len(self.lg_debug))
        for i, cmt in enumerate(self.commits_lst):
            diffs = self.diffs_lst[i]
            cmt_obj = self.cmt_cls(commit=cmt, diffs=diffs,
                                   proj=self.proj, url=self.url,
                                   lang=self.lang,
                                   base_dir=self.BASE_DIR, lock=self.lock,
                                   lg_debug=self.lg_debug[i])
            exit_code = cmt_obj.process()

            if exit_code == -1:
                continue

            # self.lock.acquire()
            cmt_obj.save()
            save = True
            # self.lock.release()

        if not save:
            logger.info(f"### {self.proj} has not output any data points")
            file = f"no_points_projects_{self.proj}.{self.lang}.log"
            with open(self.BASE_DIR / "CommitLogGeneration" / "log" / file, 'a') as f:
                f.write(self.proj + "\t" + self.url + "\n")
            return
        logger.info(f"### {self.proj} Done!")



    def _filter_at_commit_level(self):
        """
        implement all rules by which we filter commit at the commit level
        # 1.the commit is not a merge commit. there is a Merge line under the line of commit sha
        # 2.filter out diff that added or deleted a file
        # 3.After step 3 if the number of diffs remained in the commit is <= 2
        """



        # 1
        self.commits_lst = list(filter(
                                    lambda commit: re.search(r"^Merge", commit, re.MULTILINE | re.UNICODE) == None,
                                    self.commits_lst
                                    )
                                )

        # 2, 3
        commits_lst = []
        self.diffs_lst = []
        for commit in self.commits_lst:
            diffs = self._extract_diffs(commit)
            diffs = list(filter(lambda diff: re.search(r"^(new file mode | deleted file mode)", diff, re.MULTILINE | re.UNICODE) == None , diffs))
            if len(diffs) == 0:
                continue
            if len(diffs) <= 2:
                commits_lst.append(commit)
                self.diffs_lst.append(diffs)

        self.commits_lst = commits_lst



    def _filter_at_MSG_level(self, cmt):
        """
        implement all rules by which we filter out commit at the commit message level
        # 0. length of the commit massage is less than 5
        # 1.the commit message contains issue number
        # 2.the commit message contains non-english characters
        # 3.the commit message doesn't start with a verb
        # 4.the verb type doesn't belong to the predefined 13 verb types
        # 5. delete bot message (tag:cc2vec)
        # 6. delete trivial message (tag:cc2vec)
        # 7. delete rollback commit message (tag:cc2vec)
        """
        reobj = re.compile(r"""
                                (?<=date:)(?:.*?\n)\n    # skip the Date line (not capture it)
                                \s*                      # skip the white spaces before the first line of commit message
                                (\w.*?)\n                # capture the first line of commit message without the trailing newline character 
                            """,
                           re.VERBOSE | re.DOTALL | re.UNICODE)

        matchobj = reobj.search(cmt)
        if matchobj:
            self.first_line_MSG = matchobj.group(1).strip().lower()

            # 0
            if len(self.first_line_MSG) < 5:
                return -1

            # 1
            condition1 = re.search(r"\#\d{1,10}", self.first_line_MSG)
            condition2 = re.search(r"gh-\d{1,10}", self.first_line_MSG)

            if condition1 != None or condition2 != None:
                return -1

            # 2
            if not self.is_ascii(self.first_line_MSG):
                return -1

            # 3
            pos = [p.pos_ for p in Controller.nlp(self.first_line_MSG)]
            if pos[0] == "VERB":
                commit_type = [p.lemma_ for p in Controller.nlp(self.first_line_MSG)][0].lower()
            else:
                return -1

            # 4
            if commit_type not in Controller.verbs:
                return -1

            # 5
            if re.search(r'^ignore update \' .* \.$', self.first_line_MSG, re.MULTILINE | re.UNICODE) != None:
                return -1

            # 6
            if re.search(r'^update(d)? (changelog|gitignore|readme( . md| file)?)( \.)?$', self.first_line_MSG, re.M | re.U) != None:
                return -1

            if re.search(r'^prepare version (v)?[ \d.]+$', self.first_line_MSG, re.M | re.U) != None:
                return -1

            if re.search(r'^bump (up )?version( number| code)?( to (v)?[ \d.]+( - snapshot)?)?( \.)?$', self.first_line_MSG, re.M | re.U) != None:
                return -1

            if re.search(r'^modify (dockerfile|makefile)( \.)?$', self.first_line_MSG, re.M | re.U) != None:
                return -1

            if re.search(r'^update submodule(s)?( \.)?$', self.first_line_MSG, re.M | re.U) != None:
                return -1

            #  7
            if re.search(r'^revert', self.first_line_MSG, re.M | re.U) != None:
                return -1

            self.lg_debug.append(self.first_line_MSG)
            return 1

        return -1



def main(argv, lock, fmt):
    if len(argv) != 3:
        raise SystemExit(
            f'Usage: python {argv[0]} lang proj url\n'
        )

    lang = argv[0]
    if lang == "java":
        controller = Controller(argv, lock, fmt, Java_CommitBERT)
        controller.process()
    else:
        controller = Controller(argv, lock, fmt, Python_CommitBERT)
        controller.process()



if __name__ == "__main__":
    main(sys.argv[1:])
