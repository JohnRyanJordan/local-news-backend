from pprint import pprint
import boto3
from botocore.exceptions import ClientError


def get_article(articleid, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

    table = dynamodb.Table('arkansas-news')

    try:
        response = table.get_item(Key={'articleid': articleid})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']


if __name__ == '__main__':
    article = get_article("https://www.nwahomepage.com/?p=479368",)
    if article:
        print("Get article succeeded:")
        pprint(article)
