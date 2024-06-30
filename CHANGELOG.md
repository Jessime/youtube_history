# 2.0

* Skip downloading and analyzing videos that are actually Youtube Ads
* Fully remove the youtube-dl version of the watch history in favor of Google Takeout
* Massively speed up html parsing by moving to lxml
* Allow multiple named analyses in the output directory
* Replace printing with logging
* Dislikes have been removed, so use likes_to_views instead of average_rating
* HD and UHD aren't that interesting, so they've been removed in favor of comment stats