# pet-cuddle-o-tron(Aws Serverless Application) 

The application will load from an S3 bucket and run in browser
.. communicating with Lambda and Step functions via an API Gateway Endpoint
Using the application you will be able to configure reminders for 'pet cuddles' to be sent using email.


# VERIFY SES APPLICATION SENDING EMAIL ADDRESS 
1. Go to  `us-east-1`
2. Move to the `SES` console https://console.aws.amazon.com/ses/home?region=us-east-1#  
3. Click `Create Identity`
4. Check the 'Email Address' checkbox
5. Enter Email for verification, aws will send out a email
6. Take a note of `sending email` create in this step


# VERIFY SES APPLICATION CUSTOMER EMAIL ADDRESS

1. Repeat the Same Steps of previous Step
2. Take a note of `customer email` create in this step
3. After Completing both Step, Identity status should be `verified`

# CREATE THE Lambda Execution Role for Lambda
1. Service should be selected as Lambda if you are using console, Trust Policy Used
    ```
    {
    "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    ```
2. Permission for Lambda to push logs to CW Logs and full interaction with SES,SNS and StateMachine
    ```
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "arn:aws:logs:*:*:*",
                "Effect": "Allow"
            }
        ]
    }
    ```
    and
    ```
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "ses:*",
                    "sns:*",
                    "states:*"
                ],
                "Resource": "*",
                "Effect": "Allow"
            }
        ]
    }
    ```
3. Create a Role Named `LambdaRole-XXXX` with the above turst and permission's policy

# Create the email_reminder_lambda function
1. Make sure you are in `us-east-1`
2. Move to the `Lambda` console https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/begin
3. Click on `Create Function`
4. Select `Author from scratch`  
5. For `Function name` enter `email_reminder_lambda`  
6. and for runtime click the dropdown and pick `Python 3.10`  
7. Expand `Change default execution role`  
8. Pick to `Use an existing Role`  
9. Click the `Existing Role` dropdown and pick `LambdaRole` Create previously in [This Step](#create-the-lambda-execution-role-for-lambda)
10. Click `Create Function`  

# Configure the email_reminder_lambda function
1. Scroll Down to Code Source and change the code to the following
This function will send an email to an address it's supplied with (by step functions) and it will be FROM the email address we specify. 
    ```
    import boto3, os, json

    FROM_EMAIL_ADDRESS = 'REPLACE_ME'

    ses = boto3.client('ses')

    def lambda_handler(event, context):
        # Print event data to logs .. 
        print("Received event: " + json.dumps(event))
        # Publish message directly to email, provided by EmailOnly or EmailPar TASK
        ses.send_email( Source=FROM_EMAIL_ADDRESS,
            Destination={ 'ToAddresses': [ event['Input']['email'] ] }, 
            Message={ 'Subject': {'Data': 'Whiskers Commands You to attend!'},
                'Body': {'Text': {'Data': event['Input']['message']}}
            }
        )
        return 'Success!'
    
    ```
2. Select `REPLACE_ME` and replace with the `SES Sending Address` Created previously in [This Step](#verify-ses-application-sending-email-address) 
3. Click `Deploy` to configure the lambda function
4. After Creating, Scroll and Click `Copy ARN` Take note of the `Lambda arn`

# CREATE STATE MACHINE ROLE
1. Trust Policy Used for Statemachine 
    ```
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "states.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    ```
2. Permission for logging,invokie lambda and interacting with statemachine
    ```
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:CreateLogDelivery",
                    "logs:GetLogDelivery",
                    "logs:UpdateLogDelivery",
                    "logs:DeleteLogDelivery",
                    "logs:ListLogDeliveries",
                    "logs:PutResourcePolicy",
                    "logs:DescribeResourcePolicies",
                    "logs:DescribeLogGroups"
                ],
                "Resource": "*",
                "Effect": "Allow"
            }
        ]
    }
    ```
    and
    ```
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": [
                    "lambda:InvokeFunction",
                    "sns:*"
                ],
                "Resource": "*",
                "Effect": "Allow"
            }
        ]
    }
    ```
3. Create a Role Named `StateMachineRole-XXXX` with the above turst and permission's policy

# CREATE STATE MACHINE
1. Move to the AWS Step Functions Console https://console.aws.amazon.com/states/home?region=us-east-1#/homepage  
2. Click the `Hamburger Menu` at the top left and click `State Machines`  
3. Click `Create State Machine`  
4. Select `Write your workflow in code` which will allow you to use Amazon States Language  
5. Scroll down for `type` select `standard`  
6. Use the following json to replace the define ASL
the state machine starts ... and then waits for a certain time period based on the `Timer` state. This is controlled by the web front end. Then the `email` is used Which sends an email reminder
    ```
    {
        "Comment": "Pet Cuddle-o-Tron - using Lambda for email.",
        "StartAt": "Timer",
        "States": {
            "Timer": {
            "Type": "Wait",
            "SecondsPath": "$.waitSeconds",
            "Next": "Email"
            },
            "Email": {
            "Type" : "Task",
            "Resource": "arn:aws:states:::lambda:invoke",
            "Parameters": {
                "FunctionName": "EMAIL_LAMBDA_ARN",
                "Payload": {
                "Input.$": "$"
                }
            },
            "Next": "NextState"
            },
            "NextState": {
            "Type": "Pass",
            "End": true
            }
        }
    }
    ```
7. Select `EMAIL_LAMBDA_ARN` and replace with the `Lambda ARN` Created previously in [This Step](#configure-the-email_reminder_lambda-function)

# CONFIGURE STATE MACHINE 
1. Scroll down to the bottom and click `next` 
2. For `State machine name` use `PetCuddleOTron`  
3. Scroll down and under `Permissions` select `Choose an existing role` and select `StateMachineRole` Created in [This Step](#create-state-machine-role) 
4. Scroll down, under `Logging`, change the `Log Level` to `All`  
5. Scroll down to the bottom and click `Create state machine`  
6. After Creating the State Machine, Take a note of the `State Machine ARN`

# CREATE API LAMBDA FUNCTION WHICH SUPPORTS APIGATEWAY
1. Move to the Lambda console https://console.aws.amazon.com/lambda/home?region=us-east-1#/functions  
2. Click on `Create Function`  
3. for `Function Name` use `api_lambda`  
4. for `Runtime` use `Python 3.9`  
5. Expand `Change default execution role`  
6. Select `Use an existing role`  
7. Choose the `LambdaRole` , Create previously in [This Step](#create-the-lambda-execution-role-for-lambda)
8. Click `Create Function`  

# CONFIGURE THE LAMBDA FUNCTION (Using the current UI)
1. Scroll Down can change the handler code to 
function accepts some information from you, via API Gateway and then it starts a state machine execution
    ```
    # This code is a bit ...messy and includes some workarounds
    # It functions fine, but needs some cleanup
    # Checked the DecimalEncoder and Checks workarounds 20200402 and no progression towards fix

    import boto3, json, os, decimal

    SM_ARN = 'YOUR_STATEMACHINE_ARN'

    sm = boto3.client('stepfunctions')

    def lambda_handler(event, context):
        # Print event data to logs .. 
        print("Received event: " + json.dumps(event))

        # Load data coming from APIGateway
        data = json.loads(event['body'])
        data['waitSeconds'] = int(data['waitSeconds'])
        
        # Sanity check that all of the parameters we need have come through from API gateway
        # Mixture of optional and mandatory ones
        checks = []
        checks.append('waitSeconds' in data)
        checks.append(type(data['waitSeconds']) == int)
        checks.append('message' in data)

        # if any checks fail, return error to API Gateway to return to client
        if False in checks:
            response = {
                "statusCode": 400,
                "headers": {"Access-Control-Allow-Origin":"*"},
                "body": json.dumps( { "Status": "Success", "Reason": "Input failed validation" }, cls=DecimalEncoder )
            }
        # If none, start the state machine execution and inform client of 2XX success :)
        else: 
            sm.start_execution( stateMachineArn=SM_ARN, input=json.dumps(data, cls=DecimalEncoder) )
            response = {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin":"*"},
                "body": json.dumps( {"Status": "Success"}, cls=DecimalEncoder )
            }
        return response

    # This is a workaround for: http://bugs.python.org/issue16535
    # Solution discussed on this thread https://stackoverflow.com/questions/11942364/typeerror-integer-is-not-json-serializable-when-serializing-json-in-python
    # https://stackoverflow.com/questions/1960516/python-json-serialize-a-decimal-object
    # Credit goes to the group:)
    class DecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, decimal.Decimal):
                return int(obj)
            return super(DecimalEncoder, self).default(obj)
    ```
2. Select `YOUR_STATEMACHINE_ARN` and replace with the `State Machine ARN` Created previously in [This Step](#configure-state-machine)
3. Click `Deploy` to save the lambda function and configuration
4. After Creating, Scroll and Click `Copy ARN` Take note of the `Lambda arn`

# CREATE API
1. Move to the API Gateway console https://console.aws.amazon.com/apigateway/main/apis?region=us-east-1  
2. Click `APIs` on the menu on the left  
3. Locate the `REST API` box, and click `Build` (Not RESTAPI private)
4. If there is a popup dialog `Create your first API` dismiss it by clicking `OK`  
5. Under `Create new API` ensure `New API` is selected.  
6. For `API name*` enter `petcuddleotron`  
7. for `Endpoint Type` pick `Regional` 
8. Click `create API`  

# CREATE RESOURCE
1. Click the `Actions` dropdown and Click `Create Resource`  
2. Under resource name enter `petcuddleotron`  
make sure that `Configure as proxy resource` is **NOT** ticked - this forwards everything as is, through to a lambda function, because we want some control, we **DONT** want this ticked.  

3. Towards the bottom **MAKE SURE TO TICK** `Enable API Gateway CORS`.  
This relaxes the restrictions on things calling on our API with a different DNS name, it allows the code loaded from the S3 bucket to call the API gateway endpoint.  
**if you DONT check this box, the API will fail**   
4. Click `Create Resource`  

# CREATE METHOD
1. Ensure you have the `/petcuddleotron` resource selected, click `Actions` dropdown and click `create method`  
2. In the small dropdown box which appears below `/petcuddleotron` select `POST` and click the `tick` symbol next to it.  
this method is what the front end part of the application will make calls to.  
Its what the api_lambda will provide services for.  

3. Ensure for `Integration Type` that `Lambda Function` is selected.  
4. Make sure `us-east-1` is selected for `Lambda Region`  
In the `Lambda Function` box.. start typing `api_lambda` and it should autocomplete, click this auto complete (**Make sure you pick api_lambda and not email reminder lambda**)  

5. Make sure that `Use Default Timeout` box **IS** ticked.  
6. Make sure that `Use Lambda Proxy integration` box **IS** ticked, this makes sure that all of the information provided to this API is sent on to lambda for processing in the `event` data structure.  
**if you don't tick this box, the API will fail**  
7. Click `Save`  
8. You may see a dialogue stating `You are about to give API Gateway permission to invoke your Lambda function:`. AWS is asking for your OK to adjust the `resource policy` on the lambda function to allow API Gateway to invoke it.  This is a different policy to the `execution role policy` which controls the permissions lambda gets.  

# DEPLOY API 
1. Click `Actions` Dropdown and `Deploy API`  
2. For `Deployment Stage` select `New Stage`  
3. for stage name and stage description enter `prod`  
4. Click `Deploy`
5. Take Note of `Invoke URL`, This URL will be used by Client Side Component

# CREATE THE S3 BUCKET
1. Move to the S3 Console https://s3.console.aws.amazon.com/s3/home?region=us-east-1#
2. Click `Create bucket`  
3. Choose a unique bucket name
4. Ensure the region is set to `US East (N.Virginia) us-east-1`  
5. Scroll Down and **UNTICK** `Block all public access`  
6. Tick the box under `Turning off block all public access might result in this bucket and the objects within becoming public` to acknowledge you understand that you can make the bucket public.  
7. Scroll Down to the bottom and click `Create bucket`

# SET THE BUCKET AS PUBLIC
1. Go into the bucket you just created.  
2. Click the `Permissions` tab.  
3. Scroll down and in the `Bucket Policy` area, click `Edit`, Paste the Policy below
    ```
    {
        "Version":"2012-10-17",
        "Statement":[
        {
            "Sid":"PublicRead",
            "Effect":"Allow",
            "Principal": "*",
            "Action":["s3:GetObject"],
            "Resource":["REPLACEME_PET_CUDDLE_O_TRON_BUCKET_ARN/*"]
        }
        ]
    }

    ```
4. Replace the `REPLACEME_PET_CUDDLE_O_TRON_BUCKET_ARN` (being careful NOT to include the `/*`) with the bucket ARN, which you can see near to `Bucket ARN `
5. Click `Save Changes` 

# ENABLE STATIC HOSTING
1. Click on the `Properties Tab`  
2. Scroll down and locate `Static website hosting`  
3. Click `Edit`  
4. Select `Enable` 
5. Select `Host a static website`  
6. For both `Index Document` and `Error Document` enter `index.html` 
7. Click `Save Changes`  
8. Scroll down and locate `Static website hosting` again.  
9. Under `Bucket Website Endpoint` copy and note down the bucket endpoint URL.  

# Configure Frontend files
1. Open the `serverless.js` in a code/text editor.
2. Locate the placeholder `REPLACEME_API_GATEWAY_INVOKE_URL` . replace it with your API Gateway [Invoke URL](#deploy-api)
3. at the end of this URL.. add `/petcuddleotron`
it should look something like this `https://somethingsomething.execute-api.us-east-1.amazonaws.com/prod/petcuddleotron` 
4. Save the file.  

# Upload to S3
1. Return to the S3 console
2. Click on the `Objects` Tab.  
3. Click `Upload`  
4. Drag the 4 files from the serverless_frontend folder onto this tab, including the serverless.js file you just edited.
**MAKE SURE ITS THE EDITED VERSION**

5. Click `Upload` and wait for it to complete.  
6. Click `Exit`  
7. Verify All 4 files are in the `Objects` area of the bucket.  
