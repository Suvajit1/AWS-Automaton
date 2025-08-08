#!/bin/bash
set -e

REGION="ap-south-1"
ROLE_NAME="SSMInstanceRole"
PROFILE_NAME="SSMInstanceProfile"
INSTANCE_ID_FILE="public_instance_id.txt"

# Read instance ID from file
if [ ! -f "$INSTANCE_ID_FILE" ]; then
    echo "Instance ID file not found. Run ec2_setup.py first."
    exit 1
fi
INSTANCE_ID=$(cat "$INSTANCE_ID_FILE")

echo "Creating IAM Role: $ROLE_NAME ..."
aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": { "Service": "ec2.amazonaws.com" },
            "Action": "sts:AssumeRole"
        }]
    }' \
    --region "$REGION" || echo " Role already exists."

echo "Attaching AmazonSSMManagedInstanceCore policy..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore \
    --region "$REGION" || true

echo "Creating Instance Profile: $PROFILE_NAME ..."
aws iam create-instance-profile \
    --instance-profile-name "$PROFILE_NAME" \
    --region "$REGION" || echo "Instance profile already exists."

echo "Adding Role to Instance Profile..."
aws iam add-role-to-instance-profile \
    --instance-profile-name "$PROFILE_NAME" \
    --role-name "$ROLE_NAME" \
    --region "$REGION" || echo " Role already in profile."

echo "Waiting for IAM role propagation..."
sleep 10

echo "Attaching IAM Instance Profile to EC2 instance $INSTANCE_ID ..."
aws ec2 associate-iam-instance-profile \
    --instance-id "$INSTANCE_ID" \
    --iam-instance-profile Name="$PROFILE_NAME" \
    --region "$REGION"

echo "IAM role setup complete!"
