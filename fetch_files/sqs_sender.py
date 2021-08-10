#!/usr/bin/python3
# Purpose:      Send messages to an SQS queue
# Date:         August 09, 2021
# Written by:   Frank Brenyah
#
# Use: python3 sqs_sender.py <queue_name>
# Ex: python3 sqs_sender.py MyQueue
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

def send_message(msg, limit):
	print("\tSending messages...")
	start_time=1
	end_time=0
	total_msg=0
	fail_msg=0

	while True:
		try:
			start_time = round(time.time() * 1000)
			sqs_client.send_message(
			QueueUrl=queue_url,
			MessageBody=msg
			)
			end_time = round(time.time() * 1000)
			total_msg += 1
		except ClientError as e:
			print("\tMessage failed: ", e)
			fail_msg += 1

		print("\tMessages Sent:", total_msg)
		print("\tMessages Failed:", fail_msg)
		print(f"\tLatency: {end_time - start_time} ms")
		print("")

		if total_msg >= limit:
			break
		else:
			time.sleep(1)
			continue
#end send_message

if __name__ == '__main__':
	q_name=sys.argv[1]
	global sqs_client
	global queue_url

	print("SQS Sender has started.")

	# create queue and set attributes
	try:
		sqs_client = boto3.client('sqs')
		queue_url = create_queue(q_name)
	except ClientError as e:
		print("\tCould not get queue:", e)
		sys.exit()

	message = "MSG {} goop".format(random.randint(30,303)*54)

	print("Queue: ", q_name)

	# add message to queue, specific limit
	send_message(message, 33)