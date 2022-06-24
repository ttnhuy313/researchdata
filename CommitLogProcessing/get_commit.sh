git clone https://github.com/tree-sitter/tree-sitter-python#!/bin/sh

cd $1
git config merge.renamelimit 99999
git config diff.renamelimit 99999
git config i18n.logOutputEncoding utf-8


if [ "$4" = "java" ]; then
    git log -p --function-context -- "*.java" > $2
    git log -p -- "*.java" > $3
else
    git log -p --function-context -- "*.py" > $2
git log -p -- "*.py" > $3
fi
