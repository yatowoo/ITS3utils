#!/bin/bash -

configs=(\
  analyseCE65_B4-SF.conf \
  analyseCE65_B4-AC.conf \
  analyseCE65_B4-DC.conf \
  analyseCE65-A4_SF.conf \
  analyseCE65-A4_AC.conf \
  analyseCE65-A4_DC.conf \
)

for confFile in ${configs[@]}
do
  corry -c config/$confFile
done