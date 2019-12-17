#!/bin/bash
set -e

current_commit=$(git -C doc_repo rev-parse HEAD)
comlist=$(git -C doc_repo log origin/gh-pages --pretty=format:'%H')

# delete all
rm -rf gh-pages/sasoptpy/version/*

vars=""

# echo $comlist
for i in $comlist; do
    co_cmd="git -C doc_repo checkout $i"
    echo $co_cmd
    $co_cmd
    if [[ ! -f "doc_repo/index.html" ]]; then
	continue
    fi

    ver_cmd="grep -o -r -P 'sasoptpy ([0-9\.]*) documentation' doc_repo/index.html | grep -m 1 -o '[0-9\.]*'"
    echo $ver_cmd
    if ! eval $ver_cmd; then
	continue
    fi
    ver_no=$(eval $ver_cmd)

    folder="gh-pages/sasoptpy/version/$ver_no"
    if [[ -d "$folder" ]]; then
	continue
    fi

    vars=${vars}${ver_no}" "
    
    echo "Version $ver_no folder does not exist!! Copying..."
    
    mkdir_cmd="mkdir -p $folder"
    echo $mkdir_cmd
    $mkdir_cmd

    copy_cmd="rsync --exclude 'version' -vazC doc_repo/ $folder/"
    echo $copy_cmd
    $copy_cmd
    
done

echo $vars


git -C doc_repo checkout $current_commit

verhtml='
<span id="version_switch">\n<select onchange="chooseVersion(this);" style="background-color: transparent; color: black; min-width: 33%; margin: 0px 0px 10px 10px;">\n<option value="latest">Latest</option>'
for i in $vars; do
    verhtml=$verhtml'\n<option value="'$i'">'$i'</option>'
done
verhtml=$verhtml'\n</select>\n</span>'

echo -e $verhtml > span.html

echo "Appending span element to every HTML file"

python3 append_span.py

echo "Completed..."
