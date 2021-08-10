#!/usr/bin/python3
# Purpose:      View stats of an SQS queue
# Date:         August 09, 2021
# Written by:   Frank Brenyah
#
# Use: python3 sqs_stats.py <queue_name>
# Ex: python3 sqs_stats.py MyQueue
#
import sys
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import random

def create_queue(name):
	# returns QueueURL
	# standard queue
	# default message size of 256KB
	# five day retention
	queue = sqs_client.create_queue(
		QueueName=q_name,
		Attributes={
			'MessageRetentionPeriod': '432000',
			'VisibilityTimeout': '15'
			}
		)
	return queue['QueueUrl']
#end create_queue

if __name__ == '__main__':
	q_name=sys.argv[1]

	print("SQS Stat Machine started.")

	# create queue and set attributes
	try:
		sqs_client = boto3.client('sqs')
		queue_url = create_queue(q_name)
	except ClientError as e:
		print("\tCould not get queue:", e)
		sys.exit()

	print("Queue: ", q_name)

	# print all attributes of the queue
	q_size=0
	q_attrs={}

	try:
		q_attrs = sqs_client.get_queue_attributes(
			QueueUrl=queue_url,
			AttributeNames=['All']
		)
	except ClientError as e:
		print("\t", e)
	
	q_size = int (q_attrs['Attributes']['ApproximateNumberOfMessages'])
	q_max_msg_size = int(q_attrs['Attributes']['MaximumMessageSize']) / 1024 # KBs
	q_msg_delays = int (q_attrs['Attributes']['ApproximateNumberOfMessagesDelayed'])
	q_last_modified = datetime.fromtimestamp(int(q_attrs['Attributes']['LastModifiedTimestamp']))
	q_birth = datetime.fromtimestamp(int(q_attrs['Attributes']['CreatedTimestamp']))

	print(f"\tQueue Size: {q_size} messages")
	print("\tQueue Created:", q_birth)
	print(f"\tMessages Delayed: {q_msg_delays} secs")
	print(f"\tMax Message Size: {q_max_msg_size} KBs")