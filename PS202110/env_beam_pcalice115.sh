#!/bin/bash -

# Env command for .bashrc :
# cd ~/ITS3utils/PS202110;source env_beam_pcalice115.sh;cd $OLDPWD;
# - Change ~/ITS3utils/ to local repo adress

if [ -z $RUN_DIR ];then
  echo '[x] RUN_DIR not found. Set to ~/eudaq2/user/ITS3/misc as default'
  export RUN_DIR=~/eudaq2/user/ITS3/misc
else
  echo '[-] ITS3 running director : '$RUN_DIR
fi

export TRIGGER_PORT=/dev/serial/by-id/usb-CERN_ITS3_Trigger_Board_210512_1140-if01-port0
export TRIGGER_DIR=~/testbeam/trigger
export DATA_DIR=/media/T7/PS202110
export ALPIDE_DAQ_FW=~/testbeam/

alias ll='ls -l -h --group-directories-first'
alias senv='vim ~/.bashrc'
alias uenv='source ~/.bashrc'
alias alpide-ls='alpide-daq-program --list'
alias alpide-flash-all='alpide-daq-program --all --fx3 $ALPIDE_DAQ_FW/fx3.img --fpga $ALPIDE_DAQ_FW/fpga-v1.0.0.bit'
alias gorun='cd $RUN_DIR'
alias godata='cd $DATA_DIR'
function srun(){
  if [ -z $@ ];then
    echo '[X] INIT file missing. Try ITS3.ini as default.'
    ./ITS3start.sh ITS3.ini && tmux a -t ITS3
  else
    ./ITS3start.sh $@ && tmux a -t ITS3
  fi
}
alias crun='tmux a -t ITS3'
alias krun='tmux kill-session -t ITS3'

source power.sh
source trigger_beam.sh