#!/bin/bash
Rscript agmip.run.r agmip.fns.r ../../data/epic_hadgem2-es_hist_ssp2_co2_firr_yield_soy_annual_1980_2010.nc4 ../regionmap/WorldId.csv pr "null" 1980 2010 yield_soy out.csv lon lat soybean ../weightmap/
