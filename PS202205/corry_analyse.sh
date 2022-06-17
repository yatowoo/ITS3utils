#!/bin/bash -

configs=(\
  analyseCE65_SF.conf \
  analyseCE65_AC.conf \
  analyseCE65_DC.conf \
  analyseCE65-A4_SF.conf \
  analyseCE65-A4_AC.conf \
  analyseCE65-A4_DC.conf \
)

for confFile in ${configs[@]}
do
  corry -c config/$confFile
done