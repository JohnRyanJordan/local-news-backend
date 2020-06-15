import boto3

def delete_arkansas_news_table(dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")

    table = dynamodb.Table('arkansas-news')
    table.delete()


if __name__ == '__main__':
    delete_arkansas_news_table()
    print("Arkansas news table deleted.")
