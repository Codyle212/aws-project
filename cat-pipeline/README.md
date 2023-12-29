# cat-pipeline
project demostrate aws codepipline with docker application deployed to ECS Fargate

# Setting Up CodeCommit
creating and configuring a code commit repo

## Generating an SSH key authenticate with codecommit
1. Run `cd ~/.ssh`
2. Run `ssh-keygen -t rsa -b 4096` and call the key 'codecommit', don't set any password for the key.  
3. Run `cat ~/.ssh/codecommit.pub` and copy the output onto your clipboard.  
4. In the AWS console move to the IAM console ( https://us-east-1.console.aws.amazon.com/iamv2/home?region=us-east-1#/home )  
5. Move to Users=>iamadmin & open that user  
6. Move to the `Security Credentials` tab.  
7. Under the AWS Codecommit section, upload an SSH key & paste in the copy of your clipboard.  
8. Copy down the `SSH key id` into your clipboard  

9. From your terminal, run `vim ~/.ssh/config` or open it code editor and at the top of the file add the following:

```
Host git-codecommit.*.amazonaws.com
  User KEY_ID_YOU_COPIED_ABOVE_REPLACEME
  IdentityFile ~/.ssh/codecommit
```

10. Change the `KEY_ID_YOU_COPIED_ABOVE_REPLACEME` placeholder to be the actual SSH key ID you copied above. 
11. Save the file and run a `chmod 600 ~/.ssh/config` to configure permissions correctly(omit for windows) 

12. Test with `ssh git-codecommit.us-east-1.amazonaws.com` and if successful it should show something like this.  

```
You have successfully authenticated over SSH. You can use Git to interact with AWS CodeCommit. Interactive shells are not supported.Connection to git-codecommit.us-east-1.amazonaws.com closed by remote host.
```

## Creating the code commit repo for cat pipeline

1. Move to the code commit console (https://us-east-1.console.aws.amazon.com/codesuite/codecommit/repositories?region=us-east-1)  
2. Create a repository.  
3. Call it `catpipeline-codecommit-XXX` where XXX is some unique numbers.  
4. Once created, locate the connection steps details and click `SSH`  
5. Locate the instructions for your specific operating system.  
6. Locate the command for `Clone the repository` and copy it into your clipboard.  
7. In your terminal, move to the folder where you want the repo stored. Generally i create a `repos` folder in my home folder using the `mkdir ~/repos` command, then move into this folder with `cd ~/repos`  
8. then run the clone command, which should look something like `ssh://git-codecommit.us-east-1.amazonaws.com/v1/repos/catpipeline-codecommit-XXX`  

## Adding the code to repo
1. Change Directory to `pwd` 
2. Run following commands
``` 
git add -A . 
git commit -m “container of cats” 
git push 
```

# Setting Up CodeBuild and ECR
configure ECR,use CodeBuild to built container and push to ECR

## CREATE A PRIVATE CONTAINER REPOSITORY
1. Move to the ECR Services console, the repositories (https://us-east-1.console.aws.amazon.com/ecr/repositories?region=us-east-1)  
2. Create a Repository.  
3. It should be a private repository
4. For the alias/name pick `catpipeline`
5. Note down the URL and name (it should match the above name)
This is the repository that codebuild will store the docker image in, created from the codecommit repo.  

## SETUP A CODEBUILD PROJECT

1. Move to the codebuild console (https://us-east-1.console.aws.amazon.com/codesuite/codebuild/projects?region=us-east-1)  
2. Create code build project
  
### PROJECT CONFIGURATION
1. For `Project name` put `catpipeline-build`.  
2. Leave all other options in this section as default.  

### SOURCE
1. For `Source Provider` choose `AWS CodeCommit`  
2. For `Repository` choose the repo you created in stage 1  
3. Check the `Branch` checkbox and pick the branch from the `Branch` dropdown (there should only be one).  

### ENVIRONMENT
1. for `Environment image` pick `Managed Image`  
2. Under `Operating system` pick `Amazon Linux 2`  
3. under `Runtime(s)` pick `Standard`
4. under `Image` pick `aws/codebuild/amazonlinux2-x86_64-standard:X.0` where X is the highest number.  
5. Under `Image version` `Always use the latest image for this runtime version`  
6. Under `Envrironment Type` pick `Linux`  
7. Check the `Privileged` box (Because we're creating a docker image)  
8. For `Service role` pick `New Service Role` and leave the default suggested name which should be something like `codebuild-catpipeline-service-role`  
9. Expand `Additional Configuration`  

Adding some Enviroment variables
10. Add the following:

```
AWS_DEFAULT_REGION with a value of us-east-1
AWS_ACCOUNT_ID with a value of your AWS_ACCOUNT_ID_REPLACEME
IMAGE_TAG with a value of latest
IMAGE_REPO_NAME with a value of your ECR_REPO_NAME_REPLACEME
```

### BUILDSPEC
The buildspec.yml file is what tells codebuild how to build your code.. the steps involved, what things the build needs, any testing and what to do with the output (artifacts).

A build project can have build commands included... or, you can point it at a buildspec.yml file, i.e one which is hosted on the same repository as the code.. and that's what you're going to do.  

1. Check `Use a buildspec file`  
you don't need to enter a name as it will use by default buildspec.yml in the root of the repo. If you want to use a different name, or have the file located elsewhere (i.e in a folder) you need to specify this here.  

### ARTIFACTS
No changes to this section, as we're building a docker image and have no testing yet, this part isn't needed.

### LOGS

This is where the logging is configured, to Cloudwatch logs or S3 (optional).  

1. For `Groupname` enter `a4l-codebuild`  
2. For `Stream Name` enter `catpipeline`  

3. Create the build Project

## BUILD SECURITY AND PERMISSIONS

Our build project will be accessing ECR to store the resultant docker image, and we need to ensure it has the permissons to do that. The build process will use an IAM role created by codebuild, so we need to update that roles permissions with ALLOWS for ECR.  

1. Go to the IAM Console (https://us-east-1.console.aws.amazon.com/iamv2/home#/home)  
2. Then Roles  
3. Locate and click the codebuild cat pipeline role i.e. `codebuild-catpipeline-build-service-role`  
4. Click the `Permissions` tab and we need to Add a permission and it will be an `inline policy`  
5. Select to edit the raw `JSON` and delete the skeleton JSON, replacing it with

```
{
  "Statement": [
	{
	  "Action": [
		"ecr:BatchCheckLayerAvailability",
		"ecr:CompleteLayerUpload",
		"ecr:GetAuthorizationToken",
		"ecr:InitiateLayerUpload",
		"ecr:PutImage",
		"ecr:UploadLayerPart"
	  ],
	  "Resource": "*",
	  "Effect": "Allow"
	}
  ],
  "Version": "2012-10-17"
}
```

6. Move on and review the policy.  
7. Name it `Codebuild-ECR` and create the policy
8. This means codebuild can now access ECR.  

## BUILDSPEC.YML

1. Create a file in the local copy of the `catpipeline-codecommit-XXX` repo called `buildspec.yml`  
2. Into this file add the following contents :-  (**use a code editor and convert tabs to spaces, also check the indentation is correct**)  

```
version: 0.2

phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - docker build -t $IMAGE_REPO_NAME:$IMAGE_TAG .
      - docker tag $IMAGE_REPO_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker image...
      - docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:$IMAGE_TAG
```

3. Then add this locally, commit and stage

``` 
git add -A .
git commit -m “add buildspec.yml”
git push 
```

## TEST THE CODEBUILD PROJECT

1. Open the CodeBuild console (https://us-east-1.console.aws.amazon.com/codesuite/codebuild/projects?region=us-east-1)  
2. Open `catpipeline-build`  
3. Start Build  
4. Check progress under phase details tab and build logs tab  

## TEST THE DOCKER IMAGE

1. Using CloudFormation to Deploy `ec2docker.yml` in `testing_infra` folder
2. Wait for this to move into the `CREATE_COMPLETE` state before continuing

3. Move to the EC2 Console ( https://us-east-1.console.aws.amazon.com/ec2/home?region=us-east-1#Home: )  
4. Select `A4L-PublicEC2`, right click, connect  
5. Choose EC2 Instance Connect, leave everything with defaults and connect.  

Docker should already be preinstalled and the EC2 instance has a role which gives ECR permissions which you will need for the next step.

6. test docker via  `docker ps` command
it should output an empty list  

7. run a `aws ecr get-login-password --region us-east-1`, this command gives us login information for ECR which can be used with the docker command. To use it use this command.

you will need to replace the placeholder with your AWS Account ID (with no dashes)

8. `aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNTID_REPLACEME.dkr.ecr.us-east-1.amazonaws.com`

9. Go to the ECR console (https://us-east-1.console.aws.amazon.com/ecr/repositories?region=us-east-1)  
Repositories  
10. Click the `catpipeline` repository  
11. For `latest` copy the URL into your clipboard  

run the command below pasting in your clipboard after docker p
12. `docker pull ` but paste in your clipboard after the space, i.e 
13. `docker pull ACCOUNTID_REPLACEME.dkr.ecr.us-east-1.amazonaws.com/catpipeline:latest` (this is an example, you will need your image URI)  

14. run `docker images` and copy the image ID into your clipboard for the `catpipeline` docker image

15. run the following command replacing the placeholder with the image ID you copied above.  

16. `docker run -p 80:80 IMAGEID_REPLACEME`

17. Move back to the EC2 console tab  
18. Click `Instances` and get the public IPv4 address for the A4L-PublicEC2 instance.  
19. open that IP in a new tab, ensuring it's http://IP not https://IP  
You should see the docker container running, with cats in containers... if so, this means your automated build process is working.  

# Setting Up CodePipeline
Create Codepipeline that use CodeCommit and CodeBuild to create a Continous Build process for pushing changes to ECR

## PIPELINE CREATION

1. Move to the codepipeline console (https://us-east-1.console.aws.amazon.com/codesuite/codepipeline/pipelines)  
2. Create a pipeline  
3. For `Pipeline name` put `catpipeline`.  
4. Chose to create a `new service role` and keep the default name, it should be called `AWSCodePipelineServiceRole-us-east-1-catpipeline` 
5. Expand `Advanced Settings` and make sure that `default location` is set for the artifact store and `default AWS managed key` is set for the `Encryption key`  
6. Move on

### Source Stage

1. Pick `AWS CodeCommit` for the `Source Provider`  
2. Pick `catpipeline-codecommit` for the report name
3. Select the branch from the `Branch name` dropdown
4. From `Detection options` pick `Amazon CloudWatch Events` and for `Output artifact format` pick `CodePipeline default`  
5. Move on

### Build Stage

1. Pick `AWS CodeBuild` for the `Build provider`  
2. Pick `US East (N.Virginia)` for the `Region`  
3. Choose the project you created earlier in the `Project name` search box  
4. For `Build type` choose `Single Build`
5. Move on

### Deploy Stage

1. Skip deploy Stage, and confirm  
2. Create the pipeline

## PIPELINE TESTS
The pipeline will do an initial execution and it should complete without any issues.  
You can click details in the build stage to see the progress...or wait for it to complete  

1. Open the S3 console in a new tab (https://s3.console.aws.amazon.com/s3/) and open the `codepipeline-us-east-1-XXXX` bucket  
2. Click `catpipeline/`  
This is the artifacts area for this pipeline, leave this tab open you will be using in later in the demo.  

## UPDATE THE BUILD STAGE

1. Find your local copy of the catpipeline-codecommit repo and update the buildspec.yml file as below
**(use a code editor and convert tabs to spaces, also check the indentation is correct)**  

```
version: 0.2

phases:
  pre_build:
	commands:
	  - echo Logging in to Amazon ECR...
	  - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
	  - REPOSITORY_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME
	  - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
	  - IMAGE_TAG=${COMMIT_HASH:=latest}
  build:
	commands:
	  - echo Build started on `date`
	  - echo Building the Docker image...          
	  - docker build -t $REPOSITORY_URI:latest .
	  - docker tag $REPOSITORY_URI:latest $REPOSITORY_URI:$IMAGE_TAG    
  post_build:
	commands:
	  - echo Build completed on `date`
	  - echo Pushing the Docker image...
	  - docker push $REPOSITORY_URI:latest
	  - docker push $REPOSITORY_URI:$IMAGE_TAG
	  - echo Writing image definitions file...
	  - printf '[{"name":"%s","imageUri":"%s"}]' "$IMAGE_REPO_NAME" "$REPOSITORY_URI:$IMAGE_TAG" > imagedefinitions.json
artifacts:
  files: imagedefinitions.json
```

## TEST A COMMIT

1. run to make update to the repo

```
git add -A .
git commit -m "updated buildspec.yml"
git push
```

Watch the pipeline run, and generate a new version of the image in ECR automatically when the commit happens.

# Setting up CodeDeploy
configure automated deployment of the cat pipeline application to ECS Fargate

## Configure a load balancer

1. Go to the EC2 Console (https://us-east-1.console.aws.amazon.com/ec2/v2/home?region=us-east-1#Home:) then Load Balancing -> Load Balancers -> Create Load Balancer.  
2. Create an application load balancer.  
4. Call it `catpipeline`  
5. Internet Facing
6. IPv4
7. For network, select your default VPC and pick ALL subnets in the VPC.  
8. Create a new security group (this will open a new tab)
9. Call it `catpipeline-SG` and put the same for description
10. Delect the default VPC in the list
11. Add an inbound rule, select HTTP and for the source IP address choose 0.0.0.0/0
12. Create the security group.  

13. Return to the original tab, click the refresh icon next to the security group dropdown, and select `catpinepine-SG from the list` and remove the default security group.  

14. Under `listners and routing` make sure HTTP:80 is configured for the listner.  
15. Create a target group, this will open a new tab
16. call it `catpipelineA-TG`, ensure that `IP`, HTTP:80, HTTP1 and the default VPC are selected.  
17. Click next and then create the target group, for now we wont register any targets.  
18. Return to the original tab, hit the refresh icon next to target group and pick `catpipelineA-TG` from the list.  
19. Then create the load balancer. 
20. This will take a few minutes to create, but you can continue on with the next part while this is creatign.


## Configure a Fargate cluster

1. Move to the ECS console (https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/getStarted)
2. Clusters, Create a Cluster.    
3. Move on, and name the cluster `allthecatapps`
4. We will be using the default VPC so make sure it's selected and that all subnets in the VPC are listed.  
5. Create the cluster. 

## Create Task and Container Definitions

1. Go to the ECS Cluster (https://us-east-1.console.aws.amazon.com/ecs/home?region=us-east-1#/clusters)  
2. Move to `Task Definitions` and create a task definition.   
3. Call it `catpipelinedemo`.  
4. In `Container Details`, `Name` put `catpipeline`, then in `Image URI` move back to the ECR console and clikc `Copy URI` next to the latest image.  
5. Scroll to the bottom and click `Next`  

6. and for `operating system family` put `Linux/X86_64`   
7. Pick `0.5vCPU` for task CPU and `1GB` for task memory.   
8. Select `ecsTaskExecutionRole` under task role and task execution role.  
9. Click `Next` and then `Create`.  


## DEPLOY TO ECS - CREATE A SERVICE
1. Click Deploy then `Create Service`.
2. for `Launch type` pick `FARGATE`
3. for `Service Name` pick `catpipelineservice`  
4. for `Desired Tasks` pick 2
5. Expand `Deployment Options`, then for `Deployment type` pick `rolling update`
6. Expand `Networking`.  
7. for `VPC` pick the default VPC
8. for `Subnets` make sure all subnets are selected.  
9. for `Security Group`, choose `User Existing Security Group` and ensure that `Default` and `catpipeline-SG` are selected.  
10. for `public IP` choose `Turned On`  
11. for `Load Balancer Type` pick `Application Load Balancer`
12. for `Load balancer name` pick `catpipeline`  
13. for `container to load balance` select 'catpipeline:80:80'  
14. select `Use an existing Listener` select `80:HTTP` from the dropdown
15. for choose `Use an existing target group` and for `Target group name` pick `catpipelineA-TG` 
16. Expand `Service auto scaling` and make sure it's **not** selected.  
17. Click `create`  
Wait for the service to finished deploying.  
The service is now running with the :latest version of the container on ECR, this was done using a manual deployment

## TEST

1. Move to the load balancer console (https://us-east-1.console.aws.amazon.com/ec2/v2/home?region=us-east-1#LoadBalancers)  
2. Pick the `catpipeline` load balancer  
3. Copy the `DNS name` into your clipboard  
4. Open it in a browser, ensuring it is using http:// not https://  
You should see the container of cats website - if it fits, i sits


## ADD A DEPLOY STAGE TO THE PIPELINE

1. Move to the code pineline console (https://us-east-1.console.aws.amazon.com/codesuite/codepipeline/pipelines?region=us-east-1)
2. Click `catpipeline` then `edit`
3. Click `+ Add Stage`  
4. Call it `Deploy` then Add stage  
5. Click `+ Add Action Group`  
6. for `Action name` put `Deploy`  
7. for `Action Provider` put `Amazon ECS`  
8. for `Region` pick `US East (N.Virginia)`  
9. for `Input artifacts` select `Build Artifact`  (this will be the `imagedefinitions.json` info about the container)  
10. for `Cluster Name` pick `allthecatapps`  
11. for `Service Name` pick `catpipelineservice`  
12. for `Image Definitions file` put `imagedefinitions.json`  
13. Click Done
14. Click Save & Confirm

## TEST

1. in the local repo edit the `index.html` file and add ` - WITH AUTOMATION` to the `h1` line text.  Save the file.  
2. then run

```
git add -A .
git commit -m "test pipeline"
git push
```
 
watch the code pipeline console (https://us-east-1.console.aws.amazon.com/codesuite/codepipeline/pipelines/catpipeline/view?region=us-east-1)

make sure each pipeline step completes

Go back to the tab with the application open via the load balancer, refresh and see how the text has changed.  


