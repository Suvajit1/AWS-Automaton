import boto3
import os

from vpc_setup import create_vpc, create_subnets, create_igw, create_route_tables

REGION = "ap-south-1"
AMI_ID = "ami-0f5ee92e2d63afc18"
INSTANCE_TYPE = "t2.micro"
KEY_NAME = "auto-key"
KEY_FILE = f"{KEY_NAME}.pem"

ec2 = boto3.client("ec2", region_name=REGION)

KEY_DIR = "keys"
PUBLIC_KEY_NAME = "public-key"


def create_key_pair(key_name):
    print(f"Creating Key Pair: {key_name}")
    key_path = os.path.join(KEY_DIR, f"{key_name}.pem")

    try:
        key_pair = ec2.create_key_pair(KeyName=key_name)
        os.makedirs(KEY_DIR, exist_ok=True)
        with open(key_path, "w") as file:
            file.write(key_pair["KeyMaterial"])
        os.chmod(key_path, 0o400)
        print(f"Key pair saved at: {key_path}")
    except ec2.exceptions.ClientError as e:
        if "InvalidKeyPair.Duplicate" in str(e):
            print(f"Key pair '{key_name}' already exists. Skipping creation.")
        else:
            raise

    return key_name


def create_security_group_public(vpc_id):
    print("Creating public security group...")
    sg_id = ec2.create_security_group(
        GroupName="pritunl-public-sg",
        Description="Allow SSH, HTTP, HTTPS, MySQL",
        VpcId=vpc_id
    )["GroupId"]

    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            # SSH
            {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
             "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            # HTTP
            {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
             "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            # HTTPS
            {"IpProtocol": "tcp", "FromPort": 443, "ToPort": 443,
             "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            # MySQL
            {"IpProtocol": "tcp", "FromPort": 3306, "ToPort": 3306,
             "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
        ]
    )
    print(f"Public SG created: {sg_id}")
    return sg_id


def launch_public_instance(subnet_id, sg_id, name_tag, key_name):
    print(f"Launching public instance: {name_tag}...")

    instance = ec2.run_instances(
        ImageId=AMI_ID,
        InstanceType=INSTANCE_TYPE,
        KeyName=key_name,
        MaxCount=1,
        MinCount=1,
        NetworkInterfaces=[
            {
                "SubnetId": subnet_id,
                "DeviceIndex": 0,
                "AssociatePublicIpAddress": True,
                "Groups": [sg_id]
            }
        ],
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": name_tag}]
            }
        ],
    )

    instance_id = instance["Instances"][0]["InstanceId"]
    print(f"Public Instance launched: {instance_id}")
    return instance_id


def main():
    vpc_id = create_vpc()
    subnets = create_subnets(vpc_id)
    igw_id = create_igw(vpc_id)
    create_route_tables(vpc_id, igw_id, subnets)

    public_sg = create_security_group_public(vpc_id)

    public_key = create_key_pair(PUBLIC_KEY_NAME)

    public_instance_id = launch_public_instance(subnets["public"][0], public_sg, "Public-Instance", public_key)
    # Save public instance ID to file
    with open("public_instance_id.txt", "w") as f:
        f.write(public_instance_id)


if __name__ == "__main__":
    main()