args <- commandArgs(TRUE)
sayHello <- function(){
   print(args)
   print('hello')
}

sayHello()
