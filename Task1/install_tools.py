import boto3
import time

REGION = "ap-south-1"

ssm = boto3.client("ssm", region_name=REGION)
ec2 = boto3.client("ec2", region_name=REGION)

def get_instance_id():
    try:
        with open("public_instance_id.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Instance ID file not found. Run ec2_setup.py first.")
        exit(1)

def is_instance_ssm_ready(instance_id):
    response = ssm.describe_instance_information()
    instance_ids = [info["InstanceId"] for info in response.get("InstanceInformationList", [])]
    return instance_id in instance_ids

def send_install_command(instance_id):
    print("Sending install command via SSM...")

    commands = [
        "sudo apt update -y && sudo apt upgrade -y",
        "sudo apt install -y unzip curl tar gzip",

        # Install AWS CLI
        "curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip'",
        "unzip -o awscliv2.zip",
        "sudo ./aws/install",
        "rm -rf awscliv2.zip aws",

        # Install kubectl (latest)
        "curl -LO https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl",
        "chmod +x kubectl",
        "sudo mv kubectl /usr/local/bin/",

        # Install eksctl (latest)
        "curl -sL https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz -o eksctl.tar.gz",
        "tar -xzf eksctl.tar.gz -C /tmp",
        "sudo mv /tmp/eksctl /usr/local/bin/",
        "rm eksctl.tar.gz",

        # Install Helm
        "curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash",

        # Confirm installations
        "aws --version",
        "kubectl version --client",
        "eksctl version",
        "helm version"
    ]

    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': commands},
    )

    command_id = response['Command']['CommandId']
    print(f"Command sent. Command ID: {command_id}")
    return command_id

def wait_for_ssm(instance_id, timeout=300):
    print("Waiting for SSM agent on the instance...")
    for _ in range(timeout // 10):
        if is_instance_ssm_ready(instance_id):
            print("SSM agent is ready.")
            return True
        time.sleep(10)
    print("[X] SSM agent not ready after timeout.")
    return False

def main():
    instance_id = get_instance_id()
    if wait_for_ssm(instance_id):
        send_install_command(instance_id)

if __name__ == "__main__":
    main()
