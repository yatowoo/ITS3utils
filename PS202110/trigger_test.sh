#!/bin/sh -

set -x
echo "[-] Using TRG0 only for dryrun / fake trigger chain test"
$TRIGGER_DIR/software/settrg.py -p $TRIGGER_PORT --trg='trg0&dt_trg>10000 &dt_veto>10000 & !bsy' --veto='ntrg>0'
$TRIGGER_DIR/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c0 -v1
$TRIGGER_DIR/software/mcp4728.py -p $TRIGGER_PORT -a 96 -c1 -v1
set +x
$TRIGGER_DIR/software/readtrgincnts.py -p $TRIGGER_PORT --dt 1 -n 10000 xxxR