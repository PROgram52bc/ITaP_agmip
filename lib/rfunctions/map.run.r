sessionInfo()

#save arguments as variables
args <- commandArgs(TRUE)

source_file <- args[1]
syear<-args[2]
eyear<-args[3]
filename<-args[4]
cropModel <- args[5]
gcm <- args[6]
rcp <- args[7]
co2 <- args[8]
irr <- args[9]
crop <- args[10]


# maek full file name : filename.csv
full_filename<-paste(filename, "csv", sep=".")

# run map generation 
source(source_file)
