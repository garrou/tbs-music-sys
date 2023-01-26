
################################################################
## Case Study: Build Your Own Recommendation System for Songs #
################################################################


# Data #
# The dataset used in this system contains the number of time a user listened music 
# from a particular artist. The dataset contains 92834 relations 
# between 1892 users and 17632 artists.


# OBJECTIVE #

# Predicting ratings and creating personalized recommendations for songs


## METHODOLOGY ##
# Users with similar preferences will rate items similarly.
# Missing ratings for a user can be predicted by first finding a neighborhood of similar users and 
# then aggregate the ratings of these users to form a prediction.
# If X and Y are two users, the similarity between X and Y can be defined by:
# sim(X,Y)=X*Y/||X||*||Y||


### Music Recommendation System ###
## Load Data
#Read artist File
artists = read.table("C:/Users/s.nyawa/Desktop/Social media analytics 2022 2023/Lectures/projectdata/artists.dat",sep="\t",stringsAsFactors = F,comment.char = "",quote="",header = T)
str(artists)

user_artists = read.table("C:/Users/s.nyawa/Desktop/Social media analytics 2022 2023/Lectures/projectdata/user_artists.dat",sep="\t",header = T)
str(user_artists)

### Data Transformation
## Long to wide
# The data provided is in long format. Let's convert to wider format such that each row represent the listened count of a user.

# install.packages("tidyr")
library(tidyr)

user_artists_wide <- spread(user_artists,key=artistID,value=weight)
dim(user_artists_wide)


## Create character Id
artists$charid=paste0("I",artists$id)
userids=user_artists_wide$userID
user_artists_wide$IuserID = NULL
rownames(user_artists_wide) = paste0("U",userids)
colnames(user_artists_wide) = paste0("I",colnames(user_artists_wide))
user_artists_wide[1:6,1:10]


# Select Top 1000 
visits_byitem=colSums(user_artists_wide[,-1],na.rm = T)
visits_1k = user_artists_wide[,order(visits_byitem,decreasing = T)[1:1000]]

# Select users who has listened to at least 11 artists
num_visits=apply(visits_1k,1,function(x) return(sum(!is.na(x))))
visits_1k = visits_1k[num_visits>10,]
dim(visits_1k)

# Data is centered and scaled
visits_1k=t(scale(t(visits_1k))[,])

# Split data for training and testing
library(recommenderlab)

# Convert visits_1k into a recommanderlab sparse matrix
visits_1k_rrm=as(as.matrix(visits_1k),"realRatingMatrix")
set.seed(100)

# POPULARITY RECOMMENDER
# The matrix is converted into a realRatingMatrix object which stores the data in sparse format 
# (only non-NA values are stored explicitly; NA values are represented by a dot)

r <- as(as.matrix(visits_1k), "realRatingMatrix")
r

# Have a view to the rating sparse matrix
getRatingMatrix(r)

# Understand the data better
as(r[1,], "list")

rowMeans(r[1,])

hist(getRatings(r), breaks=60)

hist(rowCounts(r), breaks=50)

hist(colMeans(r), breaks=20)

# Convert the rating matrix into a list of users with their ratings for closer inspection
as(r, "list")

# The rating matrix can converted into a data.frame with user/item/rating tuples.
head(as(r, "data.frame"))


#### Creating a recommender  ####

# Information about interesting recommandation methods for real-valued rating data
recommenderRegistry$get_entries(dataType = "realRatingMatrix")

# We create a recommender which generates recommendations solely on the popularity of items (songs)
# Create a recommender from the first 1470 users
rr <- Recommender(r[1:1470], method = "POPULAR")


# Obtain information about the model
names(getModel(rr))
getModel(rr)

# Recommendations in the form of an object of class TopNList
# We create top-5 recommendation lists for 8 users who were not used to learn the model.
recom <- predict(rr, r[1471:1478], n=5)
recom
recom@items
recom@ratings


# The result contains two ordered top-N recommendation lists, one for each user. 
# The recommended items can be inspected as a list
Myrecommendations<-as(recom, "list")

for (i in 1:5){
  print(Myrecommendations[i])
  print(artists$name[artists$charid %in% Myrecommendations[[i]]])
}

# The best 3 recommendations for each list using bestN().
recom3 <- bestN(recom, n = 3)
recom3
Myrecommendations3<-as(recom3, "list")

for (i in 1:3){
  print(Myrecommendations3[i])
  print(artists$name[artists$charid %in% Myrecommendations3[[i]]])
}

# Evaluation of predicted ratings
# For the test set 10 items will be given to the recommender algorithm 
# and the other items will be held out for computing the error

e <- evaluationScheme(r, method="split", train=0.8, given=10, goodRating=3)
e

# Using another recommander
# User-based collaborative filtering
r1 <- Recommender(getData(e, "train"), "UBCF")
r1

# POPULARITY method
r2 <- Recommender(getData(e, "train"), "POPULAR")
r2

# Compute predicted ratings for the known part of the test data  (10 items for each
# user) using the two algorithms.
p1 <- predict(r1, getData(e, "known"), type="ratings")
p1

p2 <- predict(r2, getData(e, "known"), type="ratings")
p2

# Error between the prediction and the unknown part of the test data
error <- rbind(
  UBCF = calcPredictionAccuracy(p1, getData(e, "unknown")),
  POPULAR = calcPredictionAccuracy(p2, getData(e, "unknown"))
)

error


# Evaluation of a top-N recommender algorithm
scheme <- evaluationScheme(r, method="cross", k=4, given=3, goodRating=3)
scheme

# Use the created evaluation scheme to evaluate the recommender method popular. 
# We evaluate top-1, top-3, top-5, top-10, top-15 and top-20 recommendation lists
results <- evaluate(scheme, method="POPULAR", type = "topNList",
                    n=c(1,3,5,10,15,20))
results

# confusion matrices for the 1st run
getConfusionMatrix(results)[[1]]

# Average confusion matrices for all the 4 runs
avg(results)

# ROC curve for recommender method POPULAR
plot(results, annotate=TRUE)

# Precision-recall plot for method POPULAR.
plot(results, "prec/rec", annotate=TRUE)

