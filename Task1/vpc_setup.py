import boto3

REGION = "ap-south-1"
ec2 = boto3.client("ec2", region_name=REGION)

def create_vpc():
    print("Creating VPC...")
    vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
    vpc_id = vpc['Vpc']['VpcId']
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})
    ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
    ec2.create_tags(Resources=[vpc_id], Tags=[{"Key": "Name", "Value": "Custom-VPC"}])
    print(f"VPC Created: {vpc_id}")
    return vpc_id

def create_subnets(vpc_id):
    print("Creating subnets...")
    subnets = {'public': [], 'private': []}
    azs = ['a', 'b', 'c']
    public_cidrs = ["10.0.1.0/24", "10.0.3.0/24", "10.0.5.0/24"]
    private_cidrs = ["10.0.2.0/24", "10.0.4.0/24", "10.0.6.0/24"]

    for i in range(3):
        # Public Subnet
        subnet = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=public_cidrs[i],
            AvailabilityZone=f"{REGION}{azs[i]}"
        )['Subnet']
        ec2.modify_subnet_attribute(SubnetId=subnet['SubnetId'], MapPublicIpOnLaunch={'Value': True})
        ec2.create_tags(Resources=[subnet['SubnetId']], Tags=[{"Key": "Name", "Value": f"Public-Subnet-{2*i+1}"}])
        subnets['public'].append(subnet['SubnetId'])

        # Private Subnet
        subnet = ec2.create_subnet(
            VpcId=vpc_id,
            CidrBlock=private_cidrs[i],
            AvailabilityZone=f"{REGION}{azs[i]}"
        )['Subnet']
        ec2.create_tags(Resources=[subnet['SubnetId']], Tags=[{"Key": "Name", "Value": f"Private-Subnet-{2*i+2}"}])
        subnets['private'].append(subnet['SubnetId'])

    print(f"Subnets Created: {subnets}")
    return subnets

def create_igw(vpc_id):
    print("Creating and attaching Internet Gateway...")
    igw = ec2.create_internet_gateway()
    igw_id = igw['InternetGateway']['InternetGatewayId']
    ec2.attach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    ec2.create_tags(Resources=[igw_id], Tags=[{"Key": "Name", "Value": "Custom-VPC-IGW"}])
    print(f"IGW Created: {igw_id}")
    return igw_id

def create_route_tables(vpc_id, igw_id, subnets):
    print("Creating Route Tables...")
    public_rt = ec2.create_route_table(VpcId=vpc_id)['RouteTable']
    public_rt_id = public_rt['RouteTableId']
    ec2.create_route(RouteTableId=public_rt_id, DestinationCidrBlock='0.0.0.0/0', GatewayId=igw_id)
    ec2.create_tags(Resources=[public_rt_id], Tags=[{"Key": "Name", "Value": "PublicRouteTable"}])

    for subnet_id in subnets['public']:
        ec2.associate_route_table(SubnetId=subnet_id, RouteTableId=public_rt_id)

    # Use default route table for private subnets
    rt_tables = ec2.describe_route_tables(Filters=[
        {'Name': 'vpc-id', 'Values': [vpc_id]},
        {'Name': 'association.main', 'Values': ['true']}
    ])
    default_rt_id = rt_tables['RouteTables'][0]['RouteTableId']
    ec2.create_tags(Resources=[default_rt_id], Tags=[{"Key": "Name", "Value": "PrivateRouteTable"}])

    for subnet_id in subnets['private']:
        ec2.associate_route_table(SubnetId=subnet_id, RouteTableId=default_rt_id)

    print("Route tables associated.")
    return public_rt_id, default_rt_id