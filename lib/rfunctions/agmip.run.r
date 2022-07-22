
###########################
## args : source_file, agmip_file, worldid_file, functions, weight_file
##	  start_year, end_year, crop_id, output_filename, longitude_id, latitude_id, 
##	  fullNameofCrop, weightmap Directory
##		
args <- commandArgs(TRUE)
source_file <- args[1] #source_file <- "agmip.fns.r"
agmip_file <- args[2] #agmip_file <- "sample.nc4"
worldid_file <- args[3] #worldid_file <- "WorldId.RData"
functions <- args[4] # production / weighted.m / summary / weighted.m.custom                      #functions <- "NULL"
weight_file <- args[5] #weight_file <- "maizeyield.RData"
start_y <- args[6] #start_year <- "2005"
end_y <- args[7] #end_year <- "2010"
crop <- args[8] #crop <- "yield_mai"
output_filename <- args[9]
lon <- args[10]
lat <- args[11]
fullCrop <- args[12] 
weightMapDir <- args[13]

## Read functions to aggregate AgMIP yields:
source(source_file)

## Read AgMIP yields:
yield.long <- read.AgMIP.nc(file=c(agmip_file), start_year=start_y, end_year=end_y, yield_crop=crop, var_lon=lon, var_lat=lat)


region_map <- read.csv(worldid_file)
if( weight_file != "null") {
  weight_map <- read.csv(weight_file)
}


## Run
if( functions == "pr" ) {
  agg1 <- grid.agg(data2agg=yield.long, region.map=region_map, crop_name = fullCrop)
} else if(functions == "yi"){
  agg1 <- grid.agg(data2agg=yield.long, region.map=region_map, agg.function = "weighted.m", crop_name = fullCrop)
} else if(functions == "st"){
  agg1 <- grid.agg(data2agg=yield.long, region.map=region_map, agg.function="summary")
} else if(functions == "wa"){
  agg1 <-  grid.agg(data2agg=yield.long, region.map=region_map, agg.function="weighted.m.custom", weight.map = weight_map)
}



output_file <- paste(output_filename)
write.csv(agg1, file=output_file)
print(paste("output saved : ", output_file))


