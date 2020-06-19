import time
import datetime

import boto3
from boto3.dynamodb.conditions import Key

# Boto3 is the AWS SDK library for Python.
# The "resources" interface allows for a higher-level abstraction than the low-level client interface.
# For more details, go to http://boto3.readthedocs.io/en/latest/guide/resources.html
# dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

table = dynamodb.Table('arkansas-news')

# When adding a global secondary index to an existing table, you cannot query the index until it has been backfilled.
# This portion of the script waits until the index is in the “ACTIVE” status, indicating it is ready to be queried.
while True:
    if not table.global_secondary_indexes or table.global_secondary_indexes[0]['IndexStatus'] != 'ACTIVE':
        print('Waiting for index to backfill...')
        time.sleep(5)
        table.reload()
    else:
        break

now = datetime.datetime.now()
three_hours_ago = now - datetime.timedelta(hours=3)

resp = table.query(
    # Add the name of the index you want to use in your query.
    IndexName="monthYear_datePublished",
    KeyConditionExpression=Key('monthYear').eq(now.isoformat()[0:7]) & Key('datePublished').between(three_hours_ago.isoformat(), now.isoformat())
)

print("The query returned the following items:")
for item in resp['Items']:
    print(item)