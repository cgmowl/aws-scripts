#!/bin/bash

echo "Promoting the latest version to prod"

previous=$(aws lambda get-alias --function-name $functionname --name previous --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')
prod=$(aws lambda get-alias --function-name $functionname --name prod --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')
latest=$(aws lambda get-alias --function-name $functionname --name latest --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')

echo "The version number for this previous tag is $previous"
echo "The version number for the prod tag is $prod"
echo "The version number for the latest tag is $latest"

echo "Setting the tag 'prod' to $latest"

aws lambda update-alias --function-name $functionname --name prod --function-version $latest --region $region

echo "Setting the tag 'previous' to $prod"

aws lambda update-alias --function-name $functionname --name previous --function-version $prod --region $region

postprevious=$(aws lambda get-alias --function-name $functionname --name previous --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')
postprod=$(aws lambda get-alias --function-name $functionname --name prod --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')
postlatest=$(aws lambda get-alias --function-name $functionname --name latest --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')

echo "The current versioning is now:"
echo "Latest: $postlatest"
echo "Prod: $postprod"
echo "Previous: $postprevious"
