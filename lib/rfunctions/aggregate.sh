#!/bin/bash
file="../../data/raw/PEGASUS/IPSL-CM5A-LR/hist/ssp2/co2/firr/soy/pegasus_ipsl-cm5a-lr_hist_ssp2_co2_firr_yield_soy_annual_1991_2000.nc4" # this one does not work
file="../../data/epic_hadgem2-es_hist_ssp2_co2_firr_yield_soy_annual_1980_2010.nc4" # this one works
Rscript \
	agmip.run.r \
	agmip.fns.r \
	$file \
	../regionmap/WorldId.csv \
	pr \
	"null" \
	1980 \
	2010 \
	yield_soy \
	out.csv \
	lon \
	lat \
	soybean \
	../weightmap/
