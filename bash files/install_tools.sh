#!/bin/bash
set -e

echo " Updating packages..."
sudo apt update -y && sudo apt upgrade -y
sudo apt install -y unzip curl tar gzip

echo " Installing AWS CLI v2..."
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -o awscliv2.zip
sudo ./aws/install
rm -rf awscliv2.zip aws

echo " Installing kubectl (latest stable)..."
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

echo " Installing eksctl (latest)..."
curl -sL "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz" -o eksctl.tar.gz
tar -xzf eksctl.tar.gz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin/
rm eksctl.tar.gz

echo " Installing Helm..."
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

echo " Installation complete!"
echo " Versions:"
aws --version
kubectl version --client
eksctl version
helm version