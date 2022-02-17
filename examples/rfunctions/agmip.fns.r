## The function read.AgMIP.nc takes as an argument a file name
## (character string) that identifies a unique ntcdf file, start year,
## end year and variable id for yield, longitude, and latutude. 
## Please look into the hearder of your ncdf4 file for these variables.
## The function converts the selected ncdf file into a table with four
## columns: lon, lat, year, and projected.yield. NAs are eliminated. 
## 

read.AgMIP.nc <- function(file, start_year, end_year, yield_crop, var_lon, var_lat){
    require(ncdf4, quietly=TRUE)
    suppressMessages(require(reshape, quietly=TRUE))
    ncfile <- nc_open(file)
    ## Get the longitudes and latitudes --- these are later used to
    ## identify the coordinate pairs for each climate observation:
    lon <- ncvar_get(ncfile, varid=var_lon)
    lat <- ncvar_get(ncfile, varid=var_lat)
    time <- c(start_year:end_year)

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


grid.agg <- function(data2agg=NULL, region.map=NULL, agg.function= "production", weight.map=NULL, crop_name=NULL){
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
    if(agg.function %in% c("summary")){
        agg <- d %>% group_by(id, time) %>%
            summarize(mean = mean(value), median = median(value), sd = sd(value), min = min(value), pctle25 = quantile(value, 0.25), pctle75 = quantile(value, 0.75), max = max(value))
    }else if(agg.function %in% c("weighted.m.custom")){
        if(is.null(weight.map) == TRUE)
            stop("For using this aggregation option you must upload/specify a weigthing scheme as an argument to weight.map")
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
    }else if(agg.function %in% c("weighted.m")){ ## DEFAULT BEHAVIOR:
        weight.map <- read.csv( paste(weightMapDir, crop_name, "_hectares_30min.csv", sep = "") )
        suppressMessages(d <- left_join(d, weight.map, by =c("lon","lat")))
        d <- d[complete.cases(d),]
        agg <- d%>% group_by(id,time) %>% summarize(harea.w.yield = weighted.mean(value, weight))
    }else if(agg.function %in% c("production")){ ## AREA WEIGHTED AVERAGE BEHAVIOR:
        # if(is.null(crop_name) == TRUE)stop("For using this aggregation option we need to code an option in the GUI that passess the name (e.g., maize) of the crop.")
        weight.map <- read.csv( paste(weightMapDir, crop_name, "_hectares_30min.csv", sep = "") )
        suppressMessages(d <- left_join(d,weight.map, by =c("lon","lat")))
        d <- d[complete.cases(d),]
        agg <- d %>% group_by(id,time) %>% summarize(production = sum(value*weight))
    }else{ 
        stop("A proper agg.function must be specified. Acceptable values are: 'production', 'weighted.m', 'summary', and 'weighted.m.custom'")
    }
    agg
}


