import re
import sys
import os
import logging
import json
from pathlib import Path

import spacy

logger = logging.getLogger("my_logger")

class Commit:
    nlp = spacy.load("en_core_web_sm")

    def __init__(self, commit, diffs, proj, url, lang, base_dir, lock, lg_debug):
        self.commit = commit
        self.proj = proj
        self.url = url
        self.diffs = diffs

        self.cc_lst_formatted = []
        # unformatted CCs
        self.cc_lst_raw = []
        self.lang = lang
        self.BASE_DIR = base_dir

        self.lock = lock
        self.lg_debug = lg_debug

    def _extract_topline_MSG(self):
        """
        return the 1st line of the commit
        """
        # okay
        reobj = re.compile(r"""
                                 (?<=date:)(?:.*?\n)\n    # skip the Date line (not capture it)
                                 \s*                      # skip the white spaces before the first line of commit message
                                 (\w.*?)\n                # capture the first line of commit message without the trailing newline character 
                             """,
                           re.VERBOSE | re.DOTALL | re.UNICODE)
        matchobj = reobj.search(self.commit)
        if matchobj:
            self.first_line_MSG = matchobj.group(1).strip().lower()
        else:
            self.first_line_MSG = ""

        return self.first_line_MSG


    def _extract_sha(self):
        self.sha = re.findall(r"^commit (\w*)", self.commit, re.MULTILINE | re.UNICODE)[0]

    def _format(self, text):
        text = re.sub(r"\b", r" ", text)  # insert a space into word boundaries
        text = re.sub(r"(\W)", r" \1 ", text)  # insert spaces around non-word characters
        text = re.sub(r"[ \t]+", r" ", text)  # shrink multiple spaces and tabs into one space
        text = re.sub(r"\n", r"<nl>", text)  # replace line break with <nl>
        text = text.strip()  # strip the leading and trailing spaces
        return text

    def _extract_cc_segments(self, diffs):
        """
        extract all code changes (CC) segments
        :param diffs: a list of  diff sections
        :return result: a list of list for CC segments
        """
        result = []
        for diff in diffs:
            result.append(re.findall(r"""
                                    @@.*?@@         # match the @@...@@ line indicating the beginning of the CC segment
                                    .*?$            # text after @@...@@ but on the same line, chunk header
                                    (.*?)           # group for the CC segment
                                    \s*             # exclude any whitespece chars trailing the CC segment
                                    (?=@@|diff|\Z)  # three ending criteria, \Z means the end of file
                                 """, diff, re.VERBOSE | re.DOTALL | re.MULTILINE | re.UNICODE)
                          )
        return result

    def _get_modified_lines(self, unfiltered_DiffCCs_2D):
        self.added = [] # list of formatted plus lines
        self.deleted = [] # list of formatted minus lines
        for a_diff_ccs_lst in unfiltered_DiffCCs_2D:
            for a_diff_cc in a_diff_ccs_lst:
                self.added.extend(re.findall(r"^\+(.*)", a_diff_cc, re.M))
                self.deleted.extend(re.findall(r"^-(.*)", a_diff_cc, re.M))

        # cannot form a input point, commit gets discarded
        if len(self.added) == 0 or len(self.deleted) == 0:
            return -1

        for a_diff_ccs_lst in unfiltered_DiffCCs_2D:
            for a_diff_cc in a_diff_ccs_lst:
                self.cc_lst_raw.append(a_diff_cc)
                self.cc_lst_formatted.append(self._format(a_diff_cc))

        self.added = [self._format(cc) for cc in self.added]
        self.deleted = [self._format(cc) for cc in self.deleted]


    def get_commit_type(self, unformatted_MSG):
        pos = [p.pos_ for p in Commit.nlp(unformatted_MSG)]
        # print(pos)
        if pos[0] == "VERB":
            commit_type = [p.lemma_ for p in Commit.nlp(unformatted_MSG)][0].lower()
        else:
            print(unformatted_MSG)
            print(self.lg_debug)
            raise TypeError("commit does not start with predefined verbs")

        return commit_type

    def process(self):
        """
        the whole processing pipeline
        :return: -1 if there is a diff greater than 1M or no valid todo, otherwise 0
        """
        self._extract_sha()

        unformatted_MSG = self._extract_topline_MSG()
        self.type = self.get_commit_type(unformatted_MSG)
        # format
        self.first_line_MSG = self._format(self.first_line_MSG)
        assert (self.first_line_MSG == self._format(self.lg_debug))


        if self.first_line_MSG == "":
            return -1

        assert(len(self.diffs) <= 2)

        if len(self.diffs) == 0:
            raise Exception("len(diffs) == 0 ")

        # remove commits with a diff larger than 1MB (tag:cc2vec)
        a_diff_greater_1M = False
        for diff in self.diffs:
            if ((sys.getsizeof(diff) / 1e6) > 1):
                # a diff > 1M
                a_diff_greater_1M = True
                break

        if a_diff_greater_1M == True:
            return -1

        # unfiltered_DiffCCs_2D => 2D list
        # e.g. unfiltered_DiffCCs_2D[0] is a list of all unformatted cc snippets for diff 1
        unfiltered_DiffCCs_2D = self._extract_cc_segments(self.diffs)

        error_code = self._get_modified_lines(unfiltered_DiffCCs_2D)

        if error_code == -1:
            return -1

        return 0

class Java_CommitBERT(Commit):
    def save(self):
        with self.lock:
            data = {"added": self.added, "deleted": self.deleted,
                    "cc_formated_lst": self.cc_lst_formatted, "cc_raw_lst": self.cc_lst_raw,
                    "type": self.type,
                    "proj": self.proj, "url": self.url,
                    "sha": self.sha, "first_line_MSG": self.first_line_MSG}
            json_string = json.dumps(data)

            with open(self.BASE_DIR / "CommitLogGeneration" / "data" /"data_commitbert.java.jsonl", 'a') as outfile:
                print(json.dumps(json_string), file=outfile)


class Python_CommitBERT(Commit):
    def save(self):
        with self.lock:
            data = {"added": self.added, "deleted": self.deleted,
                    "cc_formated_lst": self.cc_lst_formatted, "cc_raw_lst": self.cc_lst_raw,
                    "type": self.type,
                    "proj": self.proj, "url": self.url,
                    "sha": self.sha, "first_line_MSG": self.first_line_MSG}
            json_string = json.dumps(data)

            with open(self.BASE_DIR / "CommitLogGeneration" / "data" /"data_commitbert.python.jsonl", 'a') as outfile:
                print(json.dumps(json_string), file=outfile)


def create_file_structures(BASE_DIR):
    # create folders that will hold data
    BASE_DIR = Path.cwd().parent
    BASE_DIR = BASE_DIR.parent.parent / "data" / "tdconcord"
    # create log folder
    if not os.path.isdir(BASE_DIR / "log"):
        os.mkdir(BASE_DIR / "log")
    if not os.path.isdir(BASE_DIR / "log" / "java"):
        os.mkdir(BASE_DIR / "log" / "java")
    if not os.path.isdir(BASE_DIR / "log" / "python"):
        os.mkdir(BASE_DIR / "log" / "python")

    # create scripts folder
    if not os.path.isdir(BASE_DIR / "scripts"):
        os.mkdir(BASE_DIR / "scripts")
    if not os.path.isdir(BASE_DIR / "scripts" / "java"):
        os.mkdir(BASE_DIR / "scripts" / "java")
    if not os.path.isdir(BASE_DIR / "scripts" / "java" / "tdcleaner"):
        os.mkdir(BASE_DIR / "scripts" / "java" / "tdcleaner")
    if not os.path.isdir(BASE_DIR / "scripts" / "java" / "our_proj"):
        os.mkdir(BASE_DIR / "scripts" / "java" / "our_proj")
    if not os.path.isdir(BASE_DIR / "scripts" / "python"):
        os.mkdir(BASE_DIR / "scripts" / "python")
    if not os.path.isdir(BASE_DIR / "scripts" / "python" / "tdcleaner"):
        os.mkdir(BASE_DIR / "scripts" / "python" / "tdcleaner")
    if not os.path.isdir(BASE_DIR / "scripts" / "python" / "our_proj"):
        os.mkdir(BASE_DIR / "scripts" / "python" / "our_proj")

    # create outputs folder
    if not os.path.isdir(BASE_DIR / "outputs"):
        os.mkdir(BASE_DIR / "outputs")
    if not os.path.isdir(BASE_DIR / "outputs" / "java"):
        os.mkdir(BASE_DIR / "outputs" / "java")
    if not os.path.isdir(BASE_DIR / "outputs" / "python"):
        os.mkdir(BASE_DIR / "outputs" / "python")

    # create project folder
    if not os.path.isdir(BASE_DIR / "projects"):
        os.mkdir(BASE_DIR / "projects")
    if not os.path.isdir(BASE_DIR / "projects" / "java"):
        os.mkdir(BASE_DIR / "projects" / "java")
    if not os.path.isdir(BASE_DIR / "projects" / "python"):
        os.mkdir(BASE_DIR / "projects" / "python")
