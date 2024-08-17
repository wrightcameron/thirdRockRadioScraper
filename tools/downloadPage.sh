#!/bin/bash
# Download static html page of Third Rock Radio's playlist.
# Mainly used to test script without needing to constantly interact with site.
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
DEST_DIR=$SCRIPT_DIR/../data
[ -d "$DEST_DIR" && ! -f "$DEST_DIR/index.html" ] || mkdir $DEST_DIR
# Download today
[ ! -f "$DEST_DIR/index.html" ] && wget https://onlineradiobox.com/us/thirdrock/playlist/ -P $DEST_DIR
# Download yesturday
[ ! -f "$DEST_DIR/yesturday.html" ] && wget https://onlineradiobox.com/us/thirdrock/playlist/1 -O $DEST_DIR/yesturday.html