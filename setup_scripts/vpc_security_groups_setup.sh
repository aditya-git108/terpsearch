VPC_ID="vpc-0ced549d0518a6c1c"
REGION="us-east-1"
FLASK_PORT="5000"
FASTAPI_PORT="8000"
REDIS_PORT="6379"

# 1. Create ALB Security Group (TerpsearchALB-SG)
SG_ALB=$(aws ec2 create-security-group \
    --group-name TerpsearchALB-SG \
    --description "ALB Security Group (public-facing)" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'GroupId' --output text)

echo "Created TerpsearchALB-SG: $SG_ALB"

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ALB \
    --protocol tcp --port 80 --cidr 0.0.0.0/0 \
    --region $REGION

aws ec2 authorize-security-group-ingress \
    --group-id $SG_ALB \
    --protocol tcp --port 443 --cidr 0.0.0.0/0 \
    --region $REGION

# 2. Create Flask Security Group (TerpsearchFlask-SG)
SG_FLASK=$(aws ec2 create-security-group \
    --group-name TerpsearchFlask-SG \
    --description "Flask ECS Service Security Group (behind ALB)" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'GroupId' --output text)

echo "Created TerpsearchFlask-SG: $SG_FLASK"

aws ec2 authorize-security-group-ingress \
    --group-id $SG_FLASK \
    --protocol tcp --port $FLASK_PORT \
    --source-group $SG_ALB \
    --region $REGION

# 3. Create FastAPI Security Group (TerpsearchFastAPI-SG)
SG_FASTAPI=$(aws ec2 create-security-group \
    --group-name TerpsearchFastAPI-SG \
    --description "FastAPI ECS Service Security Group (internal)" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'GroupId' --output text)

echo "Created TerpsearchFastAPI-SG: $SG_FASTAPI"

aws ec2 authorize-security-group-ingress \
    --group-id $SG_FASTAPI \
    --protocol tcp --port $FASTAPI_PORT \
    --source-group $SG_FLASK \
    --region $REGION

# 4. Create Celery Security Group (TerpsearchCelery-SG)
SG_CELERY=$(aws ec2 create-security-group \
    --group-name TerpsearchCelery-SG \
    --description "Celery ECS Service Security Group (internal only)" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'GroupId' --output text)

echo "Created TerpsearchCelery-SG: $SG_CELERY"

# (Optional) Allow inbound from FastAPI or Flask if needed:
# Uncomment if Celery needs direct trigger
# aws ec2 authorize-security-group-ingress \
#     --group-id $SG_CELERY \
#     --protocol tcp --port 5555 \
#     --source-group $SG_FASTAPI \
#     --region $REGION

# 5. Create Redis Security Group (TerpsearchRedis-SG)
SG_REDIS=$(aws ec2 create-security-group \
    --group-name TerpsearchRedis-SG \
    --description "Redis ECS Service Security Group (internal only)" \
    --vpc-id $VPC_ID \
    --region $REGION \
    --query 'GroupId' --output text)

echo "Created TerpsearchRedis-SG: $SG_REDIS"

aws ec2 authorize-security-group-ingress \
    --group-id $SG_REDIS \
    --protocol tcp --port $REDIS_PORT \
    --source-group $SG_CELERY \
    --region $REGION

echo "✅ All 5 Security Groups created successfully!"
