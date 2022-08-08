## The function read.AgMIP.nc takes as an argument a file name
## (character string) that identifies a unique ntcdf file, start year,
## end year and variable id for yield, longitude, and latutude.
## Please look into the hearder of your ncdf4 file for these
## variables.  The function converts the selected ncdf file into a
## table with four columns: lon, lat, year, and projected.yield. NAs
## are eliminated.  This function is not used for the version of the
## tool using the second generation of the GGCMI runs, but it is kept for legacy.

read.AgMIP.nc <- function(file, start_year, end_year, yield_crop, var_lon, var_lat){
    require(ncdf4, quietly=TRUE)
    suppressMessages(require(reshape, quietly=TRUE))
    ncfile <- nc_open(file)
    ## Get the longitudes and latitudes --- these are later used to
    ## identify the coordinate pairs for each climate observation:
    lon <- ncvar_get(ncfile, varid=var_lon)
    lat <- ncvar_get(ncfile, varid=var_lat)
    time <- c(start_year:end_year)

    # print(lon)
    # print(lat)
    # print(time)
    # print(list(lon,lat,time))

    ## Read yields (an array of 720X360X6):
    yield <- ncvar_get(ncfile, varid=yield_crop)

    # Change to three dimensional data
    if(length(dim(yield))==2) {
        yield <- array(yield, dim=c(dim(yield)[1], dim(yield)[2], 1))
    }
    ## Assign the longitudes and latitudes to facilitate merging with
    ## the other files:

    dimnames(yield) <- list(lon,lat,time)

    ## Set non-land areas to NA before further processing:
    fillvalue <- ncatt_get(ncfile,yield_crop,"_FillValue")
    yield[yield==fillvalue$value] <- NA
    ## Collapse the yield array so it becomes a column:
    yield.long <- melt(yield)
    names(yield.long) <- c("lon","lat","time","value")
    ## Eliminate NAs
    yield.long <- yield.long[complete.cases(yield.long),]
}

#########################################################################
## read.AgMIP.RData: Function to read yield data (relative changes in
## percent compared with the reference period 1983-2013) from the
## second generation of GGCMI runs provided by Jonas Jägermeyr on June
## 01, 2022. The function produces a dataset with four columns
## ("lon","lat","time","value"). "time" are all the years in the
## dataset (2016:2099), and value are the relative yields for
## crop. The data is ready to be aggregated geographically by
## grid.agg, which merges the lon/lat variables to a lower resolution,
## and allows for production or area weights.
#########################################################################

## The function takes two arguments: file and crop

## file: Character string with the name of a RData file provided by
## Jonas (may include a path address), for example
## "../data/dssat-pythia_gfdl-esm4_ssp126_default_production_and_yield_grid.RData".
## Each RData object data has three arrays of dimensions 720x360x84x5
## [lon x lat x 84 years (2016:2099) x 5 crops (mai, wwh, swh, soy,
## ric)]. The arrays are "yield_grid", "yield_grid_ir",
## "yield_grid_rf". "yield_grid" combines rainfed (rf) and irrigated
## (ir) yields, using area weights--"yield_grid" will be the dataset
## we wiill use. All the yields are relative changes in percent
## compared with the reference period 1983-2013:


## crop: one of maize, winter wheat, spring wheat, soybeans, rice
read.AgMIP.RData <- function(file = NULL, crop = NULL){
    cropnames <- c("maize", "winter_wheat", "spring_wheat", "soybeans", "rice")
    if( !crop %in% cropnames ){
        stop('Specify one of maize, winter_wheat, spring_wheat, soybeans, rice')
        }
    if( is.null(file) ){
        stop('Needs a RData file provided by Jonas, for example
"dssat-pythia_gfdl-esm4_ssp126_default_production_and_yield_grid.RData"')
    }else{
        load(file)
    }
    ## Add names to the dimensions of the arrays to facilitate
    ## aggregation by grid.agg.2:
    lons <- seq(from = -179.75, to = 179.75, by = 0.5)
    lats <- seq(from = 89.75, to = -89.75, by = -0.5)
    years <- c(2016:2099)
    dimnames(yield_grid) <- list(lons, lats, years, cropnames)
    ## Select specific crop:
    yield_grid_c  <- yield_grid[,,,crop]
    ## Collapse the yield array so it becomes a column:
    require(reshape2, quietly=TRUE)
    yield.long <- melt(yield_grid_c)
    names(yield.long) <- c("lon","lat","time","value")
    ## Eliminate NAs
    yield.long <- yield.long[complete.cases(yield.long),]
    return(yield.long)
    }

#########################################################################
## read.weights: read the weights used by grid.agg. Three types of
## weights are allowed: weights: "none", "area", "tonnes". Notices
## that relative paths are hardwired and need to be modified if the
## data is in a different directory.
#########################################################################
read.weights <- function(crop, weights){
    ## crop.m ensures that there is a weighting map for each crop by
    ## using soybean instead of soybeans or wheat instead of spring
    ## and winter wheat.
    crop.m <- ifelse( crop == "soybeans", "soybean",
              ifelse( crop %in% c("winter_wheat", "spring_wheat"), "wheat",
                     crop))
    ## Assign the right weighting map:
    if( weights == "none" ){
        .w <- NULL
    }else{
        if( weights == "area" ){
            .w <- read.csv( paste("./agg/examples/weightmap/",crop.m,"_hectares_30min.csv", sep ="") )
        }else{
            if( weights == "tonnes" ){
                .w <- read.csv( paste("./agg/examples/weightmap/",crop.m,"_tonnes_30min.csv", sep ="") )
            }else{
                stop(paste(' weights must be one of either "none", "area", "tonnes", however', weights, 'is found'))
            }}}
    return(.w)
}

#########################################################################
## grid.agg: Aggregates from the gridcell to the regions in
## region.map. The function read.AgMIP.RData produces the input to
## data2agg. read.weights produces the data for weight.map.
#########################################################################

grid.agg <- function(data2agg=NULL, region.map=NULL, weight.map=NULL){
    require(dplyr, quietly=TRUE)
    ## Check data to be aggregated:
    if(ncol(data2agg)>4)
        stop('Data to be aggregated must have four columns labeled lon, lat, time, and value')
    if((c("lon") %in% names(data2agg) &
        c("lat") %in% names(data2agg) &
        c("time") %in% names(data2agg) &
        c("value") %in% names(data2agg))==FALSE)
        stop('Data to be aggregated must be labeled lon, lat, time, and id')
    ## Check regional mapping file:
    if(ncol(region.map)>4)
        stop('Regional mapping must have three columns labeled lon, lat, and id')
    if((c("lon") %in% names(region.map) &
        c("lat") %in% names(region.map) &
        c("id") %in% names(region.map))==FALSE)
        stop('Regional mapping must be labeled lon, lat, and id')
    ## Merge AgMIP yields with regional mapping:
    suppressMessages(d <- left_join(data2agg, region.map, by.x=c("lon","lat"), by.y=c("lon","lat")))
    d <- d[complete.cases(d),]
    ## AGGREGATION
    if(is.null(weight.map)){
        agg <- d %>% group_by(id, time) %>%
            summarize(mean = mean(value))
    }else{
        ## Check weigths file:
        if(ncol(weight.map)>4)
            stop('Weights file must have three columns labeled lon, lat, and weight')
        if((c("lon") %in% names(weight.map) & c("lat") %in% names(weight.map) & c("weight") %in% names(weight.map))==FALSE)
            stop('Weights file must be labeled lon, lat, and weight')
        ## If weights file is correct, merge with yields and is data:
        suppressMessages(d <- left_join(d,weight.map , by =c("lon","lat")))
        d <- d[complete.cases(d),]
        ## Weighted Average:
        agg <- d%>% group_by(id,time) %>% summarize(w.ave.yield = weighted.mean(value, weight))
    }
    agg
}


## agg.wrapper: runs weight.map, yielddat, and yielddat.agg
## sequentially. The idea is that the four arguments can be taken
## directly from the GUI:
agg.wrapper <- function(file, crop, region.map, weights){
    weight.map <- read.weights(crop, weights)
    yielddat <- read.AgMIP.RData( file = file ,crop = crop )
    yielddat.agg <- grid.agg( data2agg = yielddat,
                             region.map= region.map,
                             weight.map = weight.map)
    }


args <- commandArgs(TRUE)
rdata_file <- args[1]
worldid_file <- args[2]
crop <- args[3]
weights <- args[4]
output_file <- args[5]

agg <- agg.wrapper(file = rdata_file,
                    crop = crop,
                    region.map = read.csv(worldid_file),
                    weights = weights)

head(agg)
write.csv(agg, file=output_file)
