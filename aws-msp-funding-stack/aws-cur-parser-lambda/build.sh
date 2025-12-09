URL_STRING="921888033920.dkr.ecr.us-west-2.amazonaws.com"
CONTAINER_STRING="cs-aws-funding-poc-dev"
IMAGE_STRING="latest"
ECR_IMAGE_URI="$URL_STRING/$CONTAINER_STRING:$IMAGE_STRING"
# log in to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin "$URL_STRING"
# remove previous images to save space
docker rmi "$URL_STRING/$CONTAINER_STRING"
docker rmi "$CONTAINER_STRING"
# build image
docker build --provenance=false --tag "$CONTAINER_STRING" .
# tag and push to AWS ECR
docker tag $CONTAINER_STRING:$IMAGE_STRING "$ECR_IMAGE_URI"
docker push "$ECR_IMAGE_URI"