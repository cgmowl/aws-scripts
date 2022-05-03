#!/bin/bash

previous=$(aws lambda get-alias --function-name $functionname --name previous --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')
prod=$(aws lambda get-alias --function-name $functionname --name prod --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')
latest=$(aws lambda get-alias --function-name $functionname --name latest --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')

echo "The current versioning is:"
echo "Latest: $latest"
echo "Prod: $prod"
echo "Previous: $previous"

echo "Override prod: $overrideprod"
if [[ $overrideprod -ne 0 ]];
then
	echo "Setting the live/prod version to a custom version"
	echo "Setting the tag 'prod' to $overrideprod"

	aws lambda update-alias --function-name $functionname --name prod --function-version $overrideprod --region $region
	aws lambda update-alias --function-name $functionname --name previous --function-version $prod --region $region

	postprevious=$(aws lambda get-alias --function-name $functionname --name previous --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')
	postprod=$(aws lambda get-alias --function-name $functionname --name prod --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')
	postlatest=$(aws lambda get-alias --function-name $functionname --name latest --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')

	echo "The current versioning is now:"
	echo "Latest: $postlatest"
	echo "Prod: $postprod"
	echo "Previous: $postprevious"

else 
	echo "Rolling back prod to previous version"
	echo "Setting the tag 'prod' to $previous"

	aws lambda update-alias --function-name $functionname --name prod --function-version $previous --region $region

	postprevious=$(aws lambda get-alias --function-name $functionname --name previous --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')
	postprod=$(aws lambda get-alias --function-name $functionname --name prod --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')
	postlatest=$(aws lambda get-alias --function-name $functionname --name latest --region $region | awk '/"FunctionVersion"/' | awk 'BEGIN{FS="\""}{print $4}')

	echo "The current versioning is now:"
	echo "Latest: $postlatest"
	echo "Prod: $postprod"
	echo "Previous: $postprevious"
fi
