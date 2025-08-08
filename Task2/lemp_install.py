import boto3
import paramiko
import os

REGION = "ap-south-1"
KEY_PATH = os.path.join("keys", "public-key.pem")  # Using key created by ec2_setup.py
USERNAME = "ubuntu"  # Debian/Ubuntu default user

# MySQL user details
DB_USER = "webuser"
DB_PASS = "WebUserPass123!"

def get_instance_ip(instance_id):
    ec2 = boto3.client("ec2", region_name=REGION)
    reservations = ec2.describe_instances(InstanceIds=[instance_id])
    instance = reservations["Reservations"][0]["Instances"][0]
    ip = instance.get("PublicIpAddress")
    if not ip:
        raise Exception("Instance has no public IP — check if it's running in a public subnet.")
    return ip

def ssh_connect(hostname):
    print(f"[+] Connecting to {hostname} via SSH...")
    key = paramiko.RSAKey.from_private_key_file(KEY_PATH)
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname=hostname, username=USERNAME, pkey=key)
    return ssh_client

def run_cmd(ssh_client, cmd):
    print(f"[+] Running: {cmd}")
    stdin, stdout, stderr = ssh_client.exec_command(cmd)
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err.strip():
        print("[!] Error:", err.strip())

def install_lemp_with_mysql(ssh_client):
    cmds = [
        # System update
        "sudo apt update -y && sudo apt upgrade -y",

        # Install Nginx
        "sudo apt install nginx -y",
        "sudo systemctl enable nginx && sudo systemctl start nginx",

        # Install PHP
        "sudo apt install php-fpm php-mysql -y",

        # Install MySQL
        "sudo wget https://dev.mysql.com/get/mysql80-community-release-el9-1.noarch.rpm",
        "sudo dnf install mysql80-community-release-el9-1.noarch.rpm -y",
        "sudo rpm --import https://repo.mysql.com/RPM-GPG-KEY-mysql-2023",
        "sudo dnf install mysql-community-server -y",
        "sudo systemctl enable mysqld && sudo systemctl start mysqld",

        # MySQL user and database setup
        f"""sudo mysql -e "CREATE USER IF NOT EXISTS '{DB_USER}'@'%' IDENTIFIED BY '{DB_PASS}';" """,
        f"""sudo mysql -e "GRANT ALL ON *.* TO '{DB_USER}'@'%';" """,

        # Configure Nginx for PHP
        """echo 'server {
            listen 80;
            server_name _;
            root /var/www/html;
            index index.php index.html index.htm;
            location / { try_files $uri $uri/ =404; }
            location ~ \.php$ {
                include snippets/fastcgi-php.conf;
                fastcgi_pass unix:/run/php/php8.1-fpm.sock;
                fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
                include fastcgi_params;
            }
            location ~ /\.ht { deny all; }
        }' | sudo tee /etc/nginx/sites-available/default""",

        "sudo nginx -t && sudo systemctl reload nginx",

        # Create index.html
        "echo '<!DOCTYPE html><html><head><title>LEMP Test</title></head><body><h1>LEMP Stack is Working!</h1></body></html>' | sudo tee /var/www/html/index.html",

        # Create info.php
        "echo '<?php phpinfo(); ?>' | sudo tee /var/www/html/info.php",

        # Create dbtest.php for DB connectivity
        f"""echo '<?php
        $servername = "localhost";
        $username = "{DB_USER}";
        $password = "{DB_PASS}";
        
        try {{
            $conn = new PDO("mysql:host=$servername;", $username, $password);
            $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            echo "Database connection successful to as {DB_USER}!";
        }} catch(PDOException $e) {{
            echo "Connection failed: " . $e->getMessage();
        }}
        ?>' | sudo tee /var/www/html/dbtest.php""",

        # Set ownership
        "sudo chown -R www-data:www-data /var/www/html"
    ]
    for c in cmds:
        run_cmd(ssh_client, c)

if __name__ == "__main__":
    # Read instance ID from file created by ec2_setup.py
    with open("public_instance_id.txt", "r") as f:
        instance_id = f.read().strip()
    print(f"[*] Using Instance ID: {instance_id}")

    # Get public IP
    ip = get_instance_ip(instance_id)
    print(f"[+] EC2 Public IP: {ip}")

    # SSH connect
    ssh = ssh_connect(ip)

    # Install LEMP stack with MySQL + user/db
    install_lemp_with_mysql(ssh)

    ssh.close()
    print("\n✅ LEMP stack with MySQL and webuser created successfully!")
    print(f"Test HTML:  http://{ip}/")
    print(f"Test PHP:   http://{ip}/info.php")
    print(f"Test MySQL: http://{ip}/dbtest.php")
