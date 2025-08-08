import boto3
import time

iam = boto3.client("iam")
ec2 = boto3.client("ec2")
REGION = "ap-south-1"
ROLE_NAME = "SSMInstanceRole"
PROFILE_NAME = "SSMInstanceProfile"

def create_iam_role():
    try:
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": { "Service": "ec2.amazonaws.com" },
                "Action": "sts:AssumeRole"
            }]
        }

        print("Creating IAM role...")
        iam.create_role(
            RoleName=ROLE_NAME,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy)
        )

        print("Attaching AmazonSSMManagedInstanceCore policy...")
        iam.attach_role_policy(
            RoleName=ROLE_NAME,
            PolicyArn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
        )

        print("Creating instance profile...")
        iam.create_instance_profile(InstanceProfileName=PROFILE_NAME)

        print("Adding role to instance profile...")
        iam.add_role_to_instance_profile(
            InstanceProfileName=PROFILE_NAME,
            RoleName=ROLE_NAME
        )

        # Wait for instance profile propagation
        print("Waiting for IAM role propagation...")
        time.sleep(10)

    except iam.exceptions.EntityAlreadyExistsException:
        print("IAM role or instance profile already exists.")

def attach_role_to_instance(instance_id):
    print(f"Attaching IAM profile to instance {instance_id}...")
    ec2.associate_iam_instance_profile(
        IamInstanceProfile={
            'Name': PROFILE_NAME
        },
        InstanceId=instance_id
    )
    print("IAM role attached.")

if __name__ == "__main__":
    import json
    instance_id = open("public_instance_id.txt").read().strip()
    create_iam_role()
    attach_role_to_instance(instance_id)