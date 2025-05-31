import json
import os
import boto3
from botocore.exceptions import ClientError

# Replace with your verified sender email address
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'your-verified-ses-email@example.com')
# Replace with your recipient email address
RECIPIENT_EMAIL = os.environ.get('RECIPIENT_EMAIL', 'your-recipient-email@example.com')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1') # e.g., 'us-east-1'

ses_client = boto3.client('ses', region_name=AWS_REGION)

def lambda_handler(event, context):
    try:
        # API Gateway sends data in the 'body' attribute as a JSON string
        if 'body' not in event:
            return {
                'statusCode': 400,
                'headers': { "Access-Control-Allow-Origin": "*" },
                'body': json.dumps({"message": "Request body missing"})
            }

        body = json.loads(event['body'])
        name = body.get('name')
        email = body.get('email')
        message = body.get('message')

        if not all([name, email, message]):
            return {
                'statusCode': 400,
                'headers': { "Access-Control-Allow-Origin": "*" },
                'body': json.dumps({"message": "Missing form data (name, email, or message)"})
            }

        # Construct the email
        SUBJECT = f"New Contact Form Submission from {name}"
        BODY_TEXT = (
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Message:\n{message}"
        )
        BODY_HTML = f"""
        <html>
        <head></head>
        <body>
          <h1>New Contact Form Submission</h1>
          <p><strong>Name:</strong> {name}</p>
          <p><strong>Email:</strong> {email}</p>
          <p><strong>Message:</strong></p>
          <p>{message.replace('\n', '<br>')}</p>
        </body>
        </html>
        """

        try:
            response = ses_client.send_email(
                Destination={
                    'ToAddresses': [
                        RECIPIENT_EMAIL,
                    ],
                },
                Message={
                    'Body': {
                        'Html': {
                            'Charset': "UTF-8",
                            'Data': BODY_HTML,
                        },
                        'Text': {
                            'Charset': "UTF-8",
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': "UTF-8",
                        'Data': SUBJECT,
                    },
                },
                Source=SENDER_EMAIL,
                ReplyToAddresses=[
                    email, # Allows you to reply directly to the user
                ]
            )
            print(f"Email sent! Message ID: {response['MessageId']}")

            return {
                'statusCode': 200,
                'headers': {
                    "Access-Control-Allow-Origin": "*", # Required for CORS
                    "Access-Control-Allow-Methods": "OPTIONS,POST",
                    "Access-Control-Allow-Headers": "Content-Type",
                    "Content-Type": "application/json"
                },
                'body': json.dumps({"message": "Email sent successfully!"})
            }

        except ClientError as e:
            print(e.response['Error']['Message'])
            return {
                'statusCode': 500,
                'headers': { "Access-Control-Allow-Origin": "*" },
                'body': json.dumps({"message": "Error sending email.", "details": e.response['Error']['Message']})
            }

    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'headers': { "Access-Control-Allow-Origin": "*" },
            'body': json.dumps({"message": "Invalid JSON in request body."})
        }
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'headers': { "Access-Control-Allow-Origin": "*" },
            'body': json.dumps({"message": "An unexpected server error occurred."})
        }