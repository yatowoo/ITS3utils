#!/bin/sh -

set -x
$TRIGGER_DIR/software/settrg.py -p $TRIGGER_PORT --trg='trg0' --veto='ntrg>0'
$TRIGGER_DIR/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c0 -v1
$TRIGGER_DIR/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c1 -v0.1
set +x
trigger-mon xxxR