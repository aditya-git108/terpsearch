#!/bin/bash

# === CONFIGURATION ===
CLUSTER_NAME="TerpsearchCluster"
REGION="us-east-1"

# Replace these with your actual values
SUBNET_1="subnet-b4f9ebfe"
SUBNET_2="subnet-0ba0ef57"
SUBNETS="[\"$SUBNET_1\",\"$SUBNET_2\"]"

SG_APP="sg-090a9bdd57337467b"       # Flask + FastAPI
SG_REDIS="sg-066279ef5fd4c5f1b"     # Redis
SG_CELERY="sg-09cabf01745847b0d"    # Celery

# Task definitions
TASK_FLASK="terpsearch-task"
TASK_FASTAPI="fastapi-task"
TASK_REDIS="redis-task"
TASK_CELERY="celery-task"
# =======================

echo "*** Deploying Flask service (2 replicas)... ***"
aws ecs create-service \
  --cluster "$CLUSTER_NAME" \
  --service-name flask-service \
  --task-definition "$TASK_FLASK" \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=$SUBNETS,securityGroups=[\"$SG_APP\"],assignPublicIp=ENABLED}" \
  --region "$REGION"

echo "*** Deploying FastAPI service... ***"
aws ecs create-service \
  --cluster "$CLUSTER_NAME" \
  --service-name fastapi-service \
  --task-definition "$TASK_FASTAPI" \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=$SUBNETS,securityGroups=[\"$SG_APP\"],assignPublicIp=ENABLED}" \
  --region "$REGION"

echo "🚀 Deploying Redis service..."
aws ecs create-service \
  --cluster "$CLUSTER_NAME" \
  --service-name redis-service \
  --task-definition "$TASK_REDIS" \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=$SUBNETS,securityGroups=[\"$SG_REDIS\"],assignPublicIp=DISABLED}" \
  --region "$REGION"

echo "🚀 Deploying Celery service..."
aws ecs create-service \
  --cluster "$CLUSTER_NAME" \
  --service-name celery-service \
  --task-definition "$TASK_CELERY" \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=$SUBNETS,securityGroups=[\"$SG_CELERY\"],assignPublicIp=DISABLED}" \
  --region "$REGION"

echo "✅ All services launched!"