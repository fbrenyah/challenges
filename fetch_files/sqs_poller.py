#!/usr/bin/python3
# Purpose:      Poll an SQS queue for messages
# Date:         August 09, 2021
# Written by:   Frank Brenyah
#
# Use: python3 sqs_poller.py <queue_name>
# Ex: python3 sqs_poller.py MyQueue
#
import sys
import boto3
from botocore.exceptions import ClientError
import time
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

def retrieve_message(name):
	print("\tProccessing messages...")
	q_size=0
	total_msg=0
	fail_msg=0
	start_time=1
	end_time=0
	handle=""

	# poll for 5 messages
	while True:
		try:
			start_time = round(time.time() * 1000)
			message = sqs_client.receive_message(
				QueueUrl=queue_url,
				MaxNumberOfMessages=1,
				WaitTimeSeconds=2
			)
			end_time = round(time.time() * 1000)
			if message['Messages'] != "":
				print("\tMessage:", message['Messages'][0]['Body'])
				handle = message['Messages'][0]['ReceiptHandle']
				total_msg += 1
			else:
				print("\tNo message available")
				fail_msg += 1
		except Exception as e:
			print("\t", e)

		# delete messages
		try:
			sqs_client.delete_message(
				QueueUrl=queue_url,
				ReceiptHandle=handle
			)
		except ClientError as e:
			fail_msg += 1
			print("\t", e)

		print("\tProcessed:", total_msg)
		print("\tFailed:", fail_msg)
		print(f"\tLatency: {end_time - start_time} ms")
		print("")
		time.sleep(1)
	# end while loop
#end retrieve_message

if __name__ == '__main__':
	q_name=sys.argv[1]
	global sqs_client

	print("SQS Poller has started.")

	# create queue and set attributes
	try:
		sqs_client = boto3.client('sqs')
		queue_url = create_queue(q_name)
	except ClientError as e:
		print("\tCould not get queue:", e)
		sys.exit()

	print("Queue: ", q_name)

	# process message from queue
	retrieve_message(q_name)