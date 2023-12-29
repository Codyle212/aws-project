# architecture-evolution
 single instance Wordpress to ELB+ASG+RDS enabled Wordpress

# Create VPC
1. use A4LVPC.yaml to provision VPC in CloudFormation

# Create an EC2 Instance to run wordpress
1. Move to the EC2 console https://console.aws.amazon.com/ec2/v2/home?region=us-east-1  
2. Click `Launch Instance`  

3. For `name` use `Wordpress-Manual`  
4. Select `Amazon Linux`  
5. From the dropdown make sure `Amazon Linux 2023` AMI is selected  
6. ensure `64-bit (x86)` is selected in the architecture dropdown.  
7. Under `instance type`  
8. Select whatever instance shows as `Free tier eligible` (probably t2 or t3.micro)  
9. Under `Key Pair(login)` select `Proceed without a KeyPair (not recommended)`  
10. For `Network Settings`, click `Edit` and in the VPC download select `A4LVPC`  
11. for `Subnet` select `sn-Pub-A`  
12. Make sure for both `Auto-assign public IP` and `Auto-assign IPv6 IP` you set to `Enable`  
13. Under security Group, Check `Select an existing security group`  
14. Select `A4LVPC-SGWordpress` it will have randomness after it, thats ok  
15. We will leave storage as default so make no changes here  
16. Expand `Advanced Details`  
17. For `IAM instance profile role` select `A4LVPC-WordpressInstanceProfile`  **THIS BIT IS IMPORTANT**  
18. Find the `Credit Specification Dropdown` and choose `Standard` (some accounts aren't enabled for Unlimited)
19. Click `Launch Instance`    
20. Click `View All instances` 

# Create SSM Parameter Store values for wordpress
This Step create parameters that will be used in latter parts
1. Open a new tab to https://console.aws.amazon.com/systems-manager/home?region=us-east-1  
2. Click on `Parameter Store` on the menu on the left
3. Creating Parameters for Database
## Create Parameter - DBUser (the login for the specific wordpress DB)  
Click `Create Parameter`
Set Name to `/A4L/Wordpress/DBUser`
Set Description to `Wordpress Database User`  
Set Tier to `Standard`  
Set Type to `String`  
Set Data type to `text`  
Set `Value` to `a4lwordpressuser`  
Click `Create parameter`  

## Create Parameter - DBName (the name of the wordpress database)  
Click `Create Parameter`
Set Name to `/A4L/Wordpress/DBName`
Set Description to `Wordpress Database Name`  
Set Tier to `Standard`  
Set Type to `String`  
Set Data type to `text`  
Set `Value` to `a4lwordpressdb`  
Click `Create parameter` 

## Create Parameter - DBEndpoint (the endpoint for the wordpress DB .. )  
Click `Create Parameter`
Set Name to `/A4L/Wordpress/DBEndpoint`
Set Description to `Wordpress Endpoint Name`  
Set Tier to `Standard`  
Set Type to `String`  
Set Data type to `text`  
Set `Value` to `localhost`  
Click `Create parameter`  

## Create Parameter - DBPassword (the password for the DBUser)  
Click `Create Parameter`
Set Name to `/A4L/Wordpress/DBPassword`
Set Description to `Wordpress DB Password`  
Set Tier to `Standard`  
Set Type to `SecureString`  
Set `KMS Key Source` to `My Current Account`  
Leave `KMS Key ID` as default (should be `alias/aws/ssm`).  
Set `Value` to `4n1m4l54L1f3`  
Click `Create parameter`  

## Create Parameter - DBRootPassword (the password for the database root user, used for self-managed admin)  
Click `Create Parameter`
Set Name to `/A4L/Wordpress/DBRootPassword`
Set Description to `Wordpress DBRoot Password`  
Set Tier to `Standard`  
Set Type to `SecureString`  
Set `KMS Key Source` to `My Current Account`  
Leave `KMS Key ID` as default (should be `alias/aws/ssm`).   
Set `Value` to `4n1m4l54L1f3`  
Click `Create parameter`  

# Connect to the instance and install a database and wordpress
1. Right click on `Wordpress-Manual` choose `Connect`
2. Choose `Session Manager`  
3. Click `Connect`  (if connect isn't highlighted then just wait a few minutes and try again).
*if after 5-10 minutes this still doesn't let you connect, it's possible you didn't add the `A4LVPC-WordpressInstanceProfile` instance role. You need to right click on the instance, security, modify IAM role and then add `A4LVPC-WordpressInstanceProfile`.  Once done, reboot the instance*   
4. type `sudo bash` and press enter  
5. type `cd` and press enter  
6. type `clear` and press enter

## Bring in the parameter values from SSM

Run the commands below to bring the parameter store values into ENV variables to make the manual build easier. 
**IF AT ANY POINT YOU ARE DISCONNECTED, RERUN THE BLOCK BELOW, THEN CONTINUE FROM WHERE YOU DISCONNECTED FROM**

```
DBPassword=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBPassword --with-decryption --query Parameters[0].Value)
DBPassword=`echo $DBPassword | sed -e 's/^"//' -e 's/"$//'`

DBRootPassword=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBRootPassword --with-decryption --query Parameters[0].Value)
DBRootPassword=`echo $DBRootPassword | sed -e 's/^"//' -e 's/"$//'`

DBUser=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBUser --query Parameters[0].Value)
DBUser=`echo $DBUser | sed -e 's/^"//' -e 's/"$//'`

DBName=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBName --query Parameters[0].Value)
DBName=`echo $DBName | sed -e 's/^"//' -e 's/"$//'`

DBEndpoint=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBEndpoint --query Parameters[0].Value)
DBEndpoint=`echo $DBEndpoint | sed -e 's/^"//' -e 's/"$//'`
```
## Install updates

```
sudo dnf -y update

```

## Install Pre-Reqs and Web Server

```
sudo dnf install wget php-mysqlnd httpd php-fpm php-mysqli mariadb105-server php-json php php-devel stress -y

```

## Set DB and HTTP Server to running and start by default

```
sudo systemctl enable httpd
sudo systemctl enable mariadb
sudo systemctl start httpd
sudo systemctl start mariadb
```

## Set the MariaDB Root Password

```
sudo mysqladmin -u root password $DBRootPassword
```

## Download and extract Wordpress

```
sudo wget http://wordpress.org/latest.tar.gz -P /var/www/html
cd /var/www/html
sudo tar -zxvf latest.tar.gz
sudo cp -rvf wordpress/* .
sudo rm -R wordpress
sudo rm latest.tar.gz
```

## Configure the wordpress wp-config.php file 

```
sudo cp ./wp-config-sample.php ./wp-config.php
sudo sed -i "s/'database_name_here'/'$DBName'/g" wp-config.php
sudo sed -i "s/'username_here'/'$DBUser'/g" wp-config.php
sudo sed -i "s/'password_here'/'$DBPassword'/g" wp-config.php
```

## Fix Permissions on the filesystem

```
sudo usermod -a -G apache ec2-user   
sudo chown -R ec2-user:apache /var/www
sudo chmod 2775 /var/www
sudo find /var/www -type d -exec chmod 2775 {} \;
sudo find /var/www -type f -exec chmod 0664 {} \;
```

## Create Wordpress User, set its password, create the database and configure permissions

```
sudo echo "CREATE DATABASE $DBName;" >> /tmp/db.setup
sudo echo "CREATE USER '$DBUser'@'localhost' IDENTIFIED BY '$DBPassword';" >> /tmp/db.setup
sudo echo "GRANT ALL ON $DBName.* TO '$DBUser'@'localhost';" >> /tmp/db.setup
sudo echo "FLUSH PRIVILEGES;" >> /tmp/db.setup
sudo mysql -u root --password=$DBRootPassword < /tmp/db.setup
sudo rm /tmp/db.setup
```

## Test Wordpress is installed

Open the EC2 console https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances:sort=desc:tag:Name  
Select the `Wordpress-Manual` instance  
copy the `IPv4 Public IP` into your clipboard (**DON'T CLICK THE OPEN LINK ... just copy the IP**)
Open that IP in a new tab  
You should see the wordpress welcome page  

## Perform Initial Configuration and make a post

in `Site Title` enter `Catagram`  
in `Username` enter `admin`
in `Password` enter `4n1m4l54L1f3`  
in `Your Email` enter your email address  
Click `Install WordPress`
Click `Log In`  
In `Username or Email Address` enter `admin`  
in `Password` enter the previously noted down strong password  
Click `Log In`  

Click `Posts` in the menu on the left  
Select `Hello World!` 
Click `Bulk Actions` and select `Move to Trash`
Click `Apply`  

Click `Add New`  
If you see any popups close them down  
For title `The Best Animal(s)!`  
Click the `+` under the title, select  `Gallery` 
Click `Upload`  
Select some animal pictures.... if you dont have any use google images to download some  
Upload them  
Click `Publish`  
Click `Publish`
Click `view Post`

## Clean up
1. Open the EC2 console https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances:sort=desc:tag:Name 
2. Right click on `Wordpress-Manual` and select `Terminate Instance` and confirm that termination. 


# Create the Launch Template
Create a reusable template of automatice deployment of instance 
1. Open the EC2 console https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances:sort=desc:tag:Name  
2. Click `Launch Templates` under `Instances` on the left menu  
3. Click `Create Launch Template`  
4. Under `Launch Template Name` enter `Wordpress`  
5. Under `Template version description` enter `Single server DB and App`  
6. Check the `Provide guidance to help me set up a template that I can use with EC2 Auto Scaling` box  

7. Under `Application and OS Images (Amazon Machine Image)` click `Quick Start`  
8. Click `Amazon Linux`  
9. in the `Amazon Machine Image` dropdown, locate `Amazon Linux 2023 AMI` and set the Architecture to `64-bit (x86)`  
10. Under `Instance Type` select whichever instance is free tier eligible from either `t3.micro` and `t2.micro`    
11. Under `Key pair (login)` select `Don't include in launch template`  
12. Under `networking Settings` `select existing security group` and choose `A4LVPC-SGWordpress`
13. Leave storage volumes unchanged  
14. Leave Resource Tags Unchanged  
15. Expand `Advanced Details`
16. Under `IAM instance profile` select `A4LVPC-WordpressInstanceProfile` there will be some random at the end, thats ok!  
17. Under `Credit specification` select `Standard`

# Add Userdata for Launch Template
1. Add the following scripts as userdata for launch template
```
#!/bin/bash -xe

DBPassword=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBPassword --with-decryption --query Parameters[0].Value)
DBPassword=`echo $DBPassword | sed -e 's/^"//' -e 's/"$//'`

DBRootPassword=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBRootPassword --with-decryption --query Parameters[0].Value)
DBRootPassword=`echo $DBRootPassword | sed -e 's/^"//' -e 's/"$//'`

DBUser=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBUser --query Parameters[0].Value)
DBUser=`echo $DBUser | sed -e 's/^"//' -e 's/"$//'`

DBName=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBName --query Parameters[0].Value)
DBName=`echo $DBName | sed -e 's/^"//' -e 's/"$//'`

DBEndpoint=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBEndpoint --query Parameters[0].Value)
DBEndpoint=`echo $DBEndpoint | sed -e 's/^"//' -e 's/"$//'`

dnf -y update

dnf install wget php-mysqlnd httpd php-fpm php-mysqli mariadb105-server php-json php php-devel stress -y

systemctl enable httpd
systemctl enable mariadb
systemctl start httpd
systemctl start mariadb

mysqladmin -u root password $DBRootPassword

wget http://wordpress.org/latest.tar.gz -P /var/www/html
cd /var/www/html
tar -zxvf latest.tar.gz
cp -rvf wordpress/* .
rm -R wordpress
rm latest.tar.gz

sudo cp ./wp-config-sample.php ./wp-config.php
sed -i "s/'database_name_here'/'$DBName'/g" wp-config.php
sed -i "s/'username_here'/'$DBUser'/g" wp-config.php
sed -i "s/'password_here'/'$DBPassword'/g" wp-config.php
sed -i "s/'localhost'/'$DBEndpoint'/g" wp-config.php

usermod -a -G apache ec2-user   
chown -R ec2-user:apache /var/www
chmod 2775 /var/www
find /var/www -type d -exec chmod 2775 {} \;
find /var/www -type f -exec chmod 0664 {} \;

echo "CREATE DATABASE $DBName;" >> /tmp/db.setup
echo "CREATE USER '$DBUser'@'localhost' IDENTIFIED BY '$DBPassword';" >> /tmp/db.setup
echo "GRANT ALL ON $DBName.* TO '$DBUser'@'localhost';" >> /tmp/db.setup
echo "FLUSH PRIVILEGES;" >> /tmp/db.setup
mysql -u root --password=$DBRootPassword < /tmp/db.setup
rm /tmp/db.setup

```
2. Ensure to leave a blank line at the end  
3. Click `Create Launch Template`  
4. Click `View launch templates`  

# Manually Launch an instance with launch template
1. Select the launch template in the list ... it should be called `Wordpress`  
2. Click `Actions` and `Launch instance from template`
3. Under `Key Pair(login` click the dropdown and select `Proceed without a key pair(Not Recommended)`  
4. Scroll down to `Network settings` and under `Subnet` select `sn-pub-A`  
5. Scroll to `Resource Tags` click `Add tag`
6. Set `Key` to `Name` and `Value` to `Wordpress-LT`
7. Scroll to the bottom and click `Launch Instance`  
8. Click the instance id in the `Success` box

# Testing 
Test the Wordpress created using Launch Template works
## Test Wordpress is installed

Open the EC2 console https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances:sort=desc:tag:Name  
Select the `Wordpress-Manual` instance  
copy the `IPv4 Public IP` into your clipboard (**DON'T CLICK THE OPEN LINK ... just copy the IP**)
Open that IP in a new tab  
You should see the wordpress welcome page  

## Perform Initial Configuration and make a post

in `Site Title` enter `Catagram`  
in `Username` enter `admin`
in `Password` enter `4n1m4l54L1f3`  
in `Your Email` enter your email address  
Click `Install WordPress`
Click `Log In`  
In `Username or Email Address` enter `admin`  
in `Password` enter the previously noted down strong password  
Click `Log In`  

Click `Posts` in the menu on the left  
Select `Hello World!` 
Click `Bulk Actions` and select `Move to Trash`
Click `Apply`  

Click `Add New`  
If you see any popups close them down  
For title `The Best Animal(s)!`  
Click the `+` under the title, select  `Gallery` 
Click `Upload`  
Select some animal pictures.... if you dont have any use google images to download some  
Upload them  
Click `Publish`  
Click `Publish`
Click `view Post`

# Create RDS Subnet Group
decouple Database and EC2 hosting WordPress application
1. Move to the RDS Console https://console.aws.amazon.com/rds/home?region=us-east-1#  
2. Click `Subnet Groups`  
3. Click `Create DB Subnet Group`  
4. Under `Name` enter `WordPressRDSSubNetGroup`  
5. Under `Description` enter `RDS Subnet Group for WordPress`  
6. Under `VPC` select `A4LVPC`  

7. Under `Add subnets` 
8. In `Availability Zones` select `us-east-1a` & `us-east-1b` & `us-east-1c`  
9. Under `Subnets` check the box next to 
    - 10.16.16.0/20 (this is sn-db-A)
    - 10.16.80.0/20 (this is sn-db-B)
    - 10.16.144.0/20 (this is sn-db-C)
10. Click `Create`  

# Create RDS Instance
1. Click `Databases`  
2. Click `Create Database`  
3. Click `Standard Create`  
4. Click `MySql`  
5. Under `Version` select `MySQL 8.0.32`   

6. Scroll down and select `Free Tier` under templates
_this ensures there will be no costs for the database but it will be single AZ only_

7. under `Db instance identifier` enter `a4lWordPress`
8. under `Master Username` enter `a4lwordpressuser`  
9. under `Master Password` and `Confirm Password` enter `4n1m4l54L1f3`   

10. Under `DB Instance size`, then `DB instance class`, then `Burstable classes (includes t classes)` make sure db.t3.micro or db.t2.micro or db.t4g.micro is selected  

11. Scroll down, under `Connectivity`, `Compute resource` select `Don’t connect to an EC2 compute resource`  
12. under `Connectivity`, `Network type` select `IPv4`  
13. under `Connectivity`, `Virtual private cloud (VPC)` select `A4LVPC`  
14. under `Subnet group` that `wordpressrdssubnetgroup` is selected  
15. Make sure `Public Access` is set to `No`  
16. Under `VPC security groups` make sure `choose existing` is selected, remove `default` and add `A4LVPC-SG-Database`  
17. Under `Availability Zone` set `us-east-1a`  

**IMPORTANT .. DON'T MISS THIS STEP**

18. Scroll down past `Database Authentication` & `Monitoring` and expand `Additional configuration`  
19. in the `Initial database name` box enter `a4lwordpressdb`  
20. Scroll to the bottom and click `create Database`  

# Migrate WordPress data from MariaDB to RDS
1. Open the EC2 Console https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Home:  
2. Click `Instances`  
3. Locate the `WordPress-LT` instance, right click, `Connect` and choose `Session Manager` and then click `Connect`  
4. Type `sudo bash`  
5. Type `cd`  
6. Type `clear`  

## Populate Environment Variables

You're going to do an export of the SQL database running on the local ec2 instance

First run these commands to populate variables with the data from Parameter store, it avoids having to keep locating passwords  
```
DBPassword=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBPassword --with-decryption --query Parameters[0].Value)
DBPassword=`echo $DBPassword | sed -e 's/^"//' -e 's/"$//'`

DBRootPassword=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBRootPassword --with-decryption --query Parameters[0].Value)
DBRootPassword=`echo $DBRootPassword | sed -e 's/^"//' -e 's/"$//'`

DBUser=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBUser --query Parameters[0].Value)
DBUser=`echo $DBUser | sed -e 's/^"//' -e 's/"$//'`

DBName=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBName --query Parameters[0].Value)
DBName=`echo $DBName | sed -e 's/^"//' -e 's/"$//'`

DBEndpoint=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBEndpoint --query Parameters[0].Value)
DBEndpoint=`echo $DBEndpoint | sed -e 's/^"//' -e 's/"$//'`

```

## Take a Backup of the local DB

To take a backup of the database run

```
mysqldump -h $DBEndpoint -u $DBUser -p$DBPassword $DBName > a4lWordPress.sql
```
** in production you wouldnt put the password in the CLI like this, its a security risk since a ps -aux can see it .. but security isnt the focus of this demo its the process of rearchitecting **

## Restore that Backup into RDS

Move to the RDS Console https://console.aws.amazon.com/rds/home?region=us-east-1#databases:  
Click the `a4lWordPressdb` instance  
Copy the `endpoint` into your clipboard  
Move to the Parameter store https://console.aws.amazon.com/systems-manager/parameters?region=us-east-1  
Check the box next to `/A4L/Wordpress/DBEndpoint` and click `Delete` (please do delete this, not just edit the existing one)  
Click `Create Parameter`  

Under `Name` enter `/A4L/Wordpress/DBEndpoint`  
Under `Descripton` enter `WordPress DB Endpoint Name`  
Under `Tier` select `Standard`    
Under `Type` select `String`  
Under `Data Type` select `text`  
Under `Value` enter the RDS endpoint endpoint you just copied  
Click `Create Parameter`  

Update the DbEndpoint environment variable with 

```
DBEndpoint=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/DBEndpoint --query Parameters[0].Value)
DBEndpoint=`echo $DBEndpoint | sed -e 's/^"//' -e 's/"$//'`
```

Restore the database export into RDS using

```
mysql -h $DBEndpoint -u $DBUser -p$DBPassword $DBName < a4lWordPress.sql 
```

## Change the WordPress config file to use RDS

this command will substitute `localhost` in the config file for the contents of `$DBEndpoint` which is the RDS instance

```
sudo sed -i "s/'localhost'/'$DBEndpoint'/g" /var/www/html/wp-config.php
```


## Stop the MariaDB Service

```
sudo systemctl disable mariadb
sudo systemctl stop mariadb
```
# Testing Wordpress(Initialization is done during launch template section)
1. Move to the EC2 Console https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances:sort=desc:tag:Name  
2. Select the `WordPress-LT` Instance  
3. copy the `IPv4 Public IP` into your clipboard  
4. Open the IP in a new tab  
5. You should see the blog, working, even though MariaDB on the EC2 instance is stopped and disabled
6. Its now running using RDS  

# Update the LT so it doesnt install MariaDB
1. Move to the EC2 Console https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Home:  
2. Under `Instances` click `Launch Templates`  
3. Select the `WordPress` launch Template (select, dont click)
4. Click `Actions` and `Modify Template (Create new version)`  
5. This template version will be based on the existing version ... so many of the values will be populated already  
6. Under `Template version description` enter `Single server App Only - RDS DB`

7. Scroll down to `Advanced details` and expand it  
8. Scroll down to `User Data` and expand the text box as much as possible
9. Locate and remove the following lines
```
systemctl enable mariadb
systemctl start mariadb
mysqladmin -u root password $DBRootPassword


echo "CREATE DATABASE $DBName;" >> /tmp/db.setup
echo "CREATE USER '$DBUser'@'localhost' IDENTIFIED BY '$DBPassword';" >> /tmp/db.setup
echo "GRANT ALL ON $DBName.* TO '$DBUser'@'localhost';" >> /tmp/db.setup
echo "FLUSH PRIVILEGES;" >> /tmp/db.setup
mysql -u root --password=$DBRootPassword < /tmp/db.setup
rm /tmp/db.setup

```
10. Click `Create Template Version`  
11. Click `View Launch Template`  
12. Select the template again (dont click)
13. Click `Actions` and select `Set Default Version`  
14. Under `Template version` select `2`  
15. Click `Set as default version`

# Create EFS File System
Create Shared Storage/FS for Wordpress application
## File System Settings

1. Move to the EFS Console https://console.aws.amazon.com/efs/home?region=us-east-1#/get-started  
2. Click on `Create file System`  
We're going to step through the full configuration options
3. Click on `Customize`  
4. For `Name` type `A4L-WORDPRESS-CONTENT`  
5. This is critical data so for `Storage Class` leave this set to `Standard` and ensure `Enable Automatic Backups` is enabled.  
6. for `LifeCycle management` ...  
7. for `Transition into IA` set to `30 days since last access`  
8. for `Transition out of IA` set to `None`  
9. Untick `Enable encryption of data at rest` .. in production you would leave this on, but for this demo which focusses on architecture it simplifies the implementation. 

10. Scroll down...  
11. For `throughput modes` choose `Bursting`   
12. Expand `Additional Settings` and ensure `Performance Mode` is set to `General Purpose`  
13. Click `Next`

## Network Settings

1. In the `Virtual Private Cloud (VPC)` dropdown select `A4LVPC`  
You should see 3 rows.  
2. Make sure `us-east-1a`, `us-east-1b` & `us-east-1c` are selected in each row.  
3. In `us-east-1a` row, select `sn-App-A` in the subnet ID dropdown, and in the security groups dropdown select `A4LVPC-SGEFS` & remove the default security group  
4. In `us-east-1b` row, select `sn-App-B` in the subnet ID dropdown, and in the security groups dropdown select `A4LVPC-SGEFS` & remove the default security group  
5. In `us-east-1c` row, select `sn-App-C` in the subnet ID dropdown, and in the security groups dropdown select `A4LVPC-SGEFS` & remove the default security group  

6. Click `next`  
7. Leave all these options as default and click `next`  
We wont be setting a file system policy  
8. click `Create`  

The file system will start in the `Creating` State and then move to `Available` once it does..  
9. Click on the file system to enter it and click `Network`  
Scroll down and all the mount points will show as `creating` keep hitting refresh and wait for all 3 to show as available before moving on.  

10. Note down the `fs-XXXXXXXX` or `DNS name` (either will work) once visible at the top of this screen, you will need it in the next step.  

# Add File System ID to Parameter Store
1. Move to the Systems Manager console https://console.aws.amazon.com/systems-manager/home?region=us-east-1#  
2. Click on `Parameter Store` on the left menu  
3. Click `Create Parameter`  
4. Under `Name` enter `/A4L/Wordpress/EFSFSID` 
5. Under `Description` enter `File System ID for Wordpress Content (wp-content)`  
6. for `Tier` set `Standard`  
7. For `Type` set `String`  
8. for `Data Type` set `text`  
9. for `Value` set the file system ID `fs-XXXXXXX` Created in [This Step](#create-efs-file-system)
10. Click `Create Parameter`  

# Connect the file system to the EC2 instance & copy data
1. Open the EC2 console and go to running instances https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Instances:sort=desc:tag:Name  
2. Select the `Wordpress-LT` instance, right click, `Connect`, Select `Session Manager` and click `Connect`  
3. type `sudo bash` and press enter   
4. type `cd` and press enter  
5. type `clear` and press enter  
6. First we need to install the amazon EFS utilities to allow the instance to connect to EFS. EFS is based on NFS which is standard but the EFS tooling makes things easier.  

```
sudo dnf -y install amazon-efs-utils
```

7. next you need to migrate the existing media content from wp-content into EFS, and this is a multi step process.

First, copy the content to a temporary location and make a new empty folder.

```
cd /var/www/html
sudo mv wp-content/ /tmp
sudo mkdir wp-content
```

then get the efs file system ID from parameter store

```
EFSFSID=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/EFSFSID --query Parameters[0].Value)
EFSFSID=`echo $EFSFSID | sed -e 's/^"//' -e 's/"$//'`
```

Next .. add a line to /etc/fstab to configure the EFS file system to mount as /var/www/html/wp-content/

```
echo -e "$EFSFSID:/ /var/www/html/wp-content efs _netdev,tls,iam 0 0" >> /etc/fstab
```

```
mount -a -t efs defaults
```

now we need to copy the origin content data back in and fix permissions

```
mv /tmp/wp-content/* /var/www/html/wp-content/
```

```
chown -R ec2-user:apache /var/www/

```
8. reboot the EC2 wordpress instance, then test the wordpress instance with new EFS as storage

# Update the launch template with the config to automate the EFS mounting

1. Go to the EC2 console https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Home:  
2. Click `Launch Templates`  
3. Check the box next to the `Wordpress` launch template, click `Actions` and click `Modify Template (Create New Version)`  
4. for `Template version description` enter `App only, uses EFS filesystem defined in /A4L/Wordpress/EFSFSID`  
5. Scroll to the bottom and expand `Advanced Details`  
6. Scroll to the bottom and find `User Data` expand the entry box as much as possible.  

7. After `#!/bin/bash -xe` position cursor at the end & press enter twice to add new lines
paste in this

```
EFSFSID=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/EFSFSID --query Parameters[0].Value)
EFSFSID=`echo $EFSFSID | sed -e 's/^"//' -e 's/"$//'`

```

8. Find the line which says `dnf install wget php-mysqlnd httpd php-fpm php-mysqli php-json php php-devel stress -y`
after `stress` add a space and paste in `amazon-efs-utils`  
it should now look like `dnf install wget php-mysqlnd httpd php-fpm php-mysqli php-json php php-devel stress amazon-efs-utils -y`  

9. locate `systemctl start httpd` position cursor at the end & press enter twice to add new lines  

paste in the following

```
mkdir -p /var/www/html/wp-content
chown -R ec2-user:apache /var/www/
echo -e "$EFSFSID:/ /var/www/html/wp-content efs _netdev,tls,iam 0 0" >> /etc/fstab
mount -a -t efs defaults
```

10. Scroll down and click `Create template version`  
11. Click `View Launch Template`  
12. Select the template again (dont click)
13. Click `Actions` and select `Set Default Version`  
14. Under `Template version` select `3`  
15. Click `Set as default version`  

# Create the load balancer
adding load balancing+auto scaling

1. Move to the EC2 console https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Home:  
2. Click `Load Balancers` under `Load Balancing`  
3. Click `Create Load Balancer`  
4. Click `Create` under `Application Load Balancer`  
5. Under name enter `A4LWORDPRESSALB`  
6. Ensure `internet-facing` is selected  
7. ensure `ipv4` selected for `IP Address type`  

8. Under `Network Mapping` select `A4LVPC` in the `VPC Dropdown`  
9. Check the boxes next to `us-east-1a` `us-east-1b` and `us-east-1c`  
10. Select `sn-pub-A`, `sn-pub-B` and `sn-pub-C` for each.  

11. Scroll down and under `Security Groups` remove `default` and select the `A4LVPC-SGLoadBalancer` from the dropdown.  

12. Under `Listener and Routing` 
13. Ensure `Protocol` is set to `HTTP` and `Port` is set to `80`.  
14. Click `Create target group` which will open a new tab  
15. for `Target Type` choose `Instances` 
16. for Target group name choose `A4LWORDPRESSALBTG`  
17. For `Protocol` choose `HTTP`  
18. For `Port` choose `80`  
19. Make sure the `VPC` is set to `A4LVPC`  
20. Check that `Protocol Version` is set to `HTTP1`  

21. Under `Health checks`
22. for `Protocol` choose `HTTP`
23. and for `Path` choose `/`  
24. Click `Next`  
25. We wont register any right now so click `Create target Group`  
26. Go back to the previous tab where you are creating the Load Balancer
27. Click the `Refresh Icon` and select the `A4LWORDPRESSALBTG` item in the dropdown.  
28. Scroll down to the bottom and click `Create load balancer`  
29. Click `View Load Balancer` and select the load balancer you are creating.  
30. Scroll down and copy the `DNS Name` into your clipboard  

# Create a new Parameter store value with the ELB DNS name

1. Move to the systems manager console https://console.aws.amazon.com/systems-manager/home?region=us-east-1#  
2. Click `Parameter Store`  
3. Click `Create Parameter`  
4. Under `Name` enter `/A4L/Wordpress/ALBDNSNAME` 
5. Under `Description` enter `DNS Name of the Application Load Balancer for wordpress`  
6. for `Tier` set `Standard`  
7. For `Type` set `String`  
8. for `Data Type` set `text`  
9. for `Value` set the DNS name of the load balancer you copied into your clipboard
10. Click `Create Parameter`

# Update the Launch template to wordpress is updated with the ELB DNS as its home
1. Go to the EC2 console https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#Home:  
2. CLick `Launch Templates`  
3. Check the box next to the `Wordpress` launch template, click `Actions` and click `Modify Template (Create New Version)`  
4. for `Template version description` enter `App only, uses EFS filesystem defined in /A4L/Wordpress/EFSFSID, ALB home added to WP Database`  
5. Scroll to the bottom and expand `Advanced Details`  
6. Scroll to the bottom and find `User Data` expand the entry box as much as possible.  

7. After `#!/bin/bash -xe` position cursor at the end & press enter twice to add new lines
paste in this

```
ALBDNSNAME=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/ALBDNSNAME --query Parameters[0].Value)
ALBDNSNAME=`echo $ALBDNSNAME | sed -e 's/^"//' -e 's/"$//'`

```

8. Move all the way to the bottom of the `User Data` and paste in this block

```
cat >> /home/ec2-user/update_wp_ip.sh<< 'EOF'
#!/bin/bash
source <(php -r 'require("/var/www/html/wp-config.php"); echo("DB_NAME=".DB_NAME."; DB_USER=".DB_USER."; DB_PASSWORD=".DB_PASSWORD."; DB_HOST=".DB_HOST); ')
SQL_COMMAND="mysql -u $DB_USER -h $DB_HOST -p$DB_PASSWORD $DB_NAME -e"
OLD_URL=$(mysql -u $DB_USER -h $DB_HOST -p$DB_PASSWORD $DB_NAME -e 'select option_value from wp_options where option_id = 1;' | grep http)

ALBDNSNAME=$(aws ssm get-parameters --region us-east-1 --names /A4L/Wordpress/ALBDNSNAME --query Parameters[0].Value)
ALBDNSNAME=`echo $ALBDNSNAME | sed -e 's/^"//' -e 's/"$//'`

$SQL_COMMAND "UPDATE wp_options SET option_value = replace(option_value, '$OLD_URL', 'http://$ALBDNSNAME') WHERE option_name = 'home' OR option_name = 'siteurl';"
$SQL_COMMAND "UPDATE wp_posts SET guid = replace(guid, '$OLD_URL','http://$ALBDNSNAME');"
$SQL_COMMAND "UPDATE wp_posts SET post_content = replace(post_content, '$OLD_URL', 'http://$ALBDNSNAME');"
$SQL_COMMAND "UPDATE wp_postmeta SET meta_value = replace(meta_value,'$OLD_URL','http://$ALBDNSNAME');"
EOF

chmod 755 /home/ec2-user/update_wp_ip.sh
echo "/home/ec2-user/update_wp_ip.sh" >> /etc/rc.local
/home/ec2-user/update_wp_ip.sh
```

9. Scroll down and click `Create template version`  
10. Click `View Launch Template`  
11. Select the template again (dont click)
12. Click `Actions` and select `Set Default Version`  
13. Under `Template version` select `4`  
14. Click `Set as default version`

# Create an auto scaling group 
1. Move to the EC2 console  
2. under `Auto Scaling`  
3. click `Auto Scaling Groups`  
4. Click `Create an Auto Scaling Group`  
5. For `Auto Scaling group name` enter `A4LWORDPRESSASG`  
6. Under `Launch Template` select `Wordpress`  
7. Under `Version` select `Latest`  
8. Scroll down and click `Next`  
9. For `Network` `VPC` select `A4LVPC`  
10. For `Subnets` select `sn-Pub-A`, `sn-pub-B` and `sn-pub-C`  
11. Click `next` 

# Configure ASG to be used with Load Balancer
1. heck the `Attach to an existing Load balancer` box  
2. Ensure `Choose from your load balancer target groups` is selected.  
3. for `existing load balancer targer groups` select `A4LWORDPRESSALBTG`  
4. don't make any changes to `VPC Lattice integration options`  

5. Under `health Checks` check `Turn on Elastic Load Balancing health checks`  
6. Under `Additional Settings` check `Enable group metrics collection within CloudWatch`  


7. Scroll down and click `Next`  

8. For now leave `Desired` `Mininum` and `Maximum` at `1`   
9. For `Scaling policies - optional` leave it on `None`  
10. Make sure `Enable instance scale-in protection` is **NOT** checked  
11. Click `Next`  
12. We wont be adding notifications so click `Next` Again  
13. Click `Add Tag`  
14. for `Key` enter `Name` and for `Value` enter `Wordpress-ASG` 
15. make sure `Tag New instances` is checked
16. Click `Next` 
17. Click `Create Auto Scaling Group`  

18. Right click on instances and open in a new tab  
19. Right click Wordpress-LT, `Terminate Instance` and confirm.   
20. This removes the old manually created wordpress instance
21. Click `Refresh` and you should see a new instance being created... `Wordpress-ASG` this is the one created automatically by the ASG using the launch template - this is because the desired capacity is set to `1` and we currently have `0`  

# Add scaling with Policies

1. Move to the AWS Console https://console.aws.amazon.com/ec2/autoscaling/home?region=us-east-1#AutoScalingGroups:  
2. Click `Auto Scaling Groups`  
3. Click the `A4LWORDPRESSASG` ASG  
4. Click the `Automatic SCaling` Tab  

We're going to add two policies, scale in and scale out.

## SCALEOUT when CPU usage on average is above 40%

Click `Create dynamic Scaling Policy`  
For policy `type` select `Simple scaling`  
for `Scaling Policy name` enter `HIGHCPU`  
Click `Create a CloudWatch Alarm`  
Click `Select Metric`  
Click `EC2`  
Click `By Auto Scaling Group` (if this doesn't show in your list, wait a while and refresh)  
Check `A4LWORDPRESSASG CPU Utilization`  (if this doesn't show in your list, wait a while and refresh)  
Click `Select Metric`  
Scroll Down... select `Threashhold style` `static`, select `Greater` and enter `40` in the `than` box and click `Next`
Click `Remove` next to notification if you see anything listed here
Click `Next`
Enter `WordpressHIGHCPU` in `Alarm Name`  
Click `Next`  
Click `Create Alarm`  
Go back to the AutoScalingGroup tab and click the `Refresh SYmbol` next to Cloudwatch Alarm  
Click the dropdown and select `WordpressHIGHCPU`  
For `Take the action` choose `Add` `1` Capacity units  
Click `Create`


## SCALEIN when CPU usage on average ie below 40%

Click `Create Dynamic Scaling Policy`  
For policy `type` select `Simple scaling`  
for `Scaling Policy name` enter `LOWCPU`  
Click `Create a CloudWatch Alarm`  
Click `Select Metric`  
Click `EC2`  
Click `By Auto Scaling Group`
Check `A4LWORDPRESSASG CPU Utilization`  
Click `Select Metric`  
Scroll Down... select `Static`, `Lower` and enter `40` in the `than` box and click `next`
Click `Remove` next to notification
Click `Next`
Enter `WordpressLOWCPU` in `Alarm Name`  
Click `Next`  
Click `Create Alarm`  
Go back to the AutoScalingGroup tab and click the `Refresh Symbol` next to Cloudwatch Alarm  
Click the dropdown and select `WordpressLOWCPU`  
For `Take the action` choose `Remove` `1` Capacity units  
Click `Create`

## ADJUST ASG Values

5. Click `Details Tab`  
6. Under `Group Details` click `Edit`  
7. Set `Desired 1`, Minimum `1` and Maximum `3`  
8. Click `Update`  

# Test Scaling & Self Healing
1. Select the/one running `Wordpress-ASG` instance, right click, `Connect`, Select `Session Manager` and click `Connect`  
2. type `sudo bash` and press enter   
3. type `cd` and press enter  
4. type `clear` and press enter  

5. run `stress -c 2 -v -t 3000`

this stresses the CPU on the instance, while running go to the ASG tag, and refresh the activities tab. it might take a few minutes, but the ASG will detect high CPU load and begin provisioning a new EC2 instance. 
if you want to see the monitoring stats, change to the monitoring tag on the ASG Console
Check `enable` next to Auto Scaling Group Metrics Collection

At some point another instance will be added. This will be auto built based on the launch template, connect to the RDS instance and EFS file system and add another instance of capacity to the platform.
Try terminating one of the EC2 instances ...
Watch what happens in the activity tab of the auto scaling group console.
This is an example of self-healing, a new instance is provisioned to take the old ones place.