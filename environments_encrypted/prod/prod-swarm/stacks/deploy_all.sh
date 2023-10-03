#!/bin/bash

check_result () {
    ___RESULT=$?
    if [ $___RESULT -ne 0 ]; then
        echo $1
        exit 1
    fi
}

CUR_PWD="$(pwd)"
for f in *_*; do
    cd "$CUR_PWD"
    if [ -d "$f" ]; then
        cd "$f"
        bash deploy.sh
        check_result "failed to deploy $f"
    fi
done
cd "$CUR_PWD"