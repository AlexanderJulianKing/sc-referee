values <- read.csv("data.csv")
aggregate(value ~ group, data = values, FUN = mean)
