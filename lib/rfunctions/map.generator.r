## Loading requried packages
require(maptools)
require(rgeos)
require(classInt)
require(methods)
require(RColorBrewer)
require(rworldmap)

## Read a inputfile 
dat<-read.csv(full_filename,header=TRUE)
## draw a simple world map in background
data(wrld_simpl)
## Index ctry.names by position in the map.
dat$pos<-match(dat$id,wrld_simpl$ISO3)
dat<-dat[order(dat$time, dat$pos),]

#variable for interval in a Legend
nclr<-9
plotclr <- brewer.pal(nclr,"YlOrRd")

for(year in syear:eyear) {
	mapdat<-subset(dat, time==year)
	

	image_name = paste(filename, year, sep="_")
	full_image_name = paste(image_name, "png", sep=".")
	png(full_image_name,width=1260,height=840)

	
	### Variable to be plotted
	plotvar <- mapdat$yield
	legendTitle <- ""
	unitString <- ""
	varName <- "yield"

	if(is.null(plotvar)){ 
		plotvar <- mapdat$production
		varName <- "production"
		legendTitle <- "Production (MT)"
		unitString <- "Units: tons"
	}
	if(is.null(plotvar)){ 
		plotvar <- mapdat$harea.w.yield
		varName <- "harea.w.yield"
		legendTitle <- "Yields (Area-weighted average)"
		unitString <- "Units: tons / hectare"
	}
	if(is.null(plotvar)){ 
		plotvar <- mapdat$x
		varName <- "x"
		legendTitle <- ""
		unitString <- "Units: tons / hectare"
	}
	if(is.null(plotvar)){ 
		plotvar <- mapdat$w.ave.yield
		varName <- "w.ave.yield"
		legendTitle <- "Weighted-average Yields (custom)"
		unitString <- "Units: tons / hectare"
	}
	if(is.null(plotvar)){ 
		plotvar <- mapdat$mean
		varName <- "mean"
		legendTitle <- "Average yields"
		unitString <- "Units: tons / hectare"
	}


	sPDF <- joinCountryData2Map(mapdat, joinCode = "ISO3", nameJoinColumn = "id")
	mapParams <- mapCountryData( sPDF, mapTitle='', nameColumnToPlot=varName, addLegend=FALSE )
	do.call( addMapLegend, c(mapParams, legendLabels='all', legendArgs=c(mtext(paste(legendTitle, ", ", year, ", GGCM: ", cropModel, ", GCM: ", gcm, sep=""), line=0.8, side=3, adj=0.5, padj=0.4, cex=2.5),
											mtext(paste('RCP: ', rcp, ", SSP2, CO2: ", co2, ", Irrigation: ", irr, ", Crop: ", crop, sep=""), line=-1.8, side=3, adj=0.5, padj=0.4, cex=2.5), 
											mtext(paste(unitString, sep=""), side=1, adj=0.07, padj=-0.8, cex=2.0)), digits=3, labelFontSize=2.0, legendWidth=2.5, legendMar = 2))
	
	
	dev.off()
	print(paste("map generated: ", full_image_name))
}
print("map.genrator.r terminated")
