# Twilio EC2 Manager

This allows managing an EC2 instance via Twilio SMS

## Set up

### Requirements

- [Python](https://www.python.org/)
- A Twilio account (with phone number setup to receive SMS) - [sign up](https://www.twilio.com/try-twilio)
- An AWS account - [sign up](https://aws.amazon.com/)
- Minecraft Server - [download](https://www.minecraft.net/en-us/download/server/)

### Pre-requisites

1. [Get a Minecraft Server running on an EC2 instance](https://medium.com/exampro/2018-modded-minecraft-server-on-aws-part-1-run-a-modded-minecraft-server-on-aws-ec2-instance-b37290462d8d)
2. [Setup a Lambda function to receive SMS from Twilio](https://www.twilio.com/docs/sms/tutorials/how-to-receive-and-reply-python-amazon-lambda)

With the above in place, you should have a working Minecraft Server running in EC2, and a simple Lambda setup with the API Gateway to receive events from Twilio.

### Lambda Environment Variables

Make sure to add the following environment variables to your Lambda function:

| Key                   | Description                                                                                                                                                                    |
| --------------------- | ---------------- |
| ADMIN_NUMBERS         | A comma delimited list of administrator phone numbers (e.g. `+12125552368,+12125551234`)                                                                                       |
| TWILIO_ACCOUNT_SID    | Your primary Twilio account identifier - find this [in the Console](https://www.twilio.com/console).                                                                           |
| TWILIO_AUTH_TOKEN     | Used to authenticate - [just like the above, you'll find this here](https://www.twilio.com/console).                                                                           |
| EC2_INSTANCE_ID       | The ID of the EC2 Instance you created above. [You can find it here](https://console.aws.amazon.com/ec2/v2/home).                                                              |
| EC2_REGION            | The region your EC2 instance is running in (e.g. `us-east-1b`)                                                                                                                 |
| EC2_SECURITY_GROUP_ID | The ID of the security group that is assigned to the EC2 Instance (e.g. `sg-1234567ab89cd0987`)                                                                                |
| TWILIO_NUMBER         | the Twilio phone number you setup to receive SMS (e.g. `+12125552368`, also found in your [Twilio Console](https://www.twilio.com/console))                                    |
| MINECRAFT_HOST        | The server domain or IP that points to your Minecraft Server (e.g. `minecraft.example.com`)                                                                                    |
| MINECRAFT_PORT        | e.g. `25565`                                                                                                                                                                   |
| REQUEST_URL           | The API Gateway endpoint you setup for the Lambda function and added as the SMS incoming webhook (e.g. `https://1somehash23.execute-api.us-east-1.amazonaws.com/prod/message`) |

### Lambda permissions

You will have to add the following actions to the permissions for your Lambda function:

| Action                              | Description                                             |
| ----------------------------------- | ------------------------------------------------------- |
| `ec2:AuthorizeSecurityGroupIngress` | Allows adding new IPs to the server whitelist           |
| `ec2:DescribeInstanceStatus`        | Allows checking the status of the instance              |
| `ec2:DescribeSecurityGroups`        | Allows looking for existing IPs in the server whitelist |
| `ec2:RevokeSecurityGroupIngress`    | Allows removing a whitelisted IP from the server        |
| `ec2:StartInstances`                | Allows starting the instance                            |
| `ec2:StopInstances`                 | Allows stopping the instance                            |
| `logs:CreateLogStream`              | Allows capturing output to logs                         |
| `logs:PutLogEvents`                 | Allows saving log events                                |

### Package the twilio-aws-minecraft Lambda script

This will create a packaged Lambda script with all required libraries in .zip file that you can upload to replace the existing Lambda script you created in
the previous step.

```bash
git clone https://github.com/codenamev/twilio-aws-minecraft.git \
cd twilio-aws-minecraft \
zip -r twilio_function.zip ./
```
Once you've saved the newly uploaded Lambda and deployed, you can test out your new EC2 manager by sending a command via SMS to your new Twilio EC2 Manager!
