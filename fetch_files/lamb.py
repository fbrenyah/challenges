# Purpose:      A lambda function to poll an SQS queue for messages
# Date:         August 11, 2021
# Written by:   Frank Brenyah
#
# Use: Deploy in AWS Lambda with an SQS trigger
#
import boto3

print("Lambda: Polling Queue...")

sqs = boto3.client('sqs')

def lambda_handler(event, context):
	if event['Records'] != "":
		for msg in event['Records']:
			print("\tMessage:", msg['body'])
			sqs.delete_message(
				QueueUrl='https://sqs.avail-zone-1.amazonaws.com/ID/QueueName',
				ReceiptHandle=msg['receiptHandle']
			)
	else:
		print("\tNo message(s) available.")