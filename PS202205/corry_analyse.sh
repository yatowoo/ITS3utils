#!/bin/bash -

configs=(\
  analyseCE65-B4_SF.conf \
  analyseCE65-B4_AC.conf \
  analyseCE65-B4_DC.conf \
  analyseCE65-A4_SF.conf \
  analyseCE65-A4_AC.conf \
  analyseCE65-A4_DC.conf \
)

for confFile in ${configs[@]}
do
  corry -c config/$confFile
done