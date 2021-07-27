# Beam test - SPS July 2021 (@pcepaid02)
export RUN_DIR=/home/llautner/eudaq2/user/ITS3/misc/
alias cdrun='cd $RUN_DIR'
export DATA_DIR=/media/T71/SPSjuly2021/
alias cdata='cd $DATA_DIR'

function find-new-runs(){
  timestamp=$(date +%Y-%m-%d -d "$1")
  TMP_FILE=/tmp/find-new-runs.log
  find $DATA_DIR -name *.raw -newermt $timestamp -type f -print | tee $TMP_FILE
  fileCount=$(wc -l $TMP_FILE | cut -d' ' -f1)
  echo "------>"
  echo "DATA directory : $DATA_DIR"
  echo "Find raw data newer than $timestamp ($1)"
  echo "Result: $fileCount new run(s) found."
  rm $TMP_FILE
}