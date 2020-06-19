import os, boto3, json, feedparser
import dateutil.parser as dateparser

from boto3.dynamodb.conditions import Key, Attr
import datetime
from datetime import date, timedelta
from botocore.vendored import requests
from decimal import Decimal
from botocore.errorfactory import ClientError
import requests, json, re

# dynamodb = boto3.resource('dynamodb')
# # For Local dev
dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000") # Connect to local dynamodb instance

table = dynamodb.Table('arkansas-news')
print("Connected to table")

sourceFile = "sources.json"

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

# Reads file and loads it as json object
def get_file(file):
    with open(file) as read_file:
        data = json.load(read_file)
        return data

# Compile usable rss source list
def get_sources(data):
    source = {}
    count = 0
    for item in data['sources']:
        source[item['source']] = item['rssurl']
        count += 1
    return source, count

# Parse rss url string
def parse_rss(rssurl):
    return feedparser.parse(rssurl)

# Get rss feed for each source
def get_feed(sources):
    feed = {}
    for attr, value in sources.items():
        feed[attr] = parse_rss(value)
    return feed

# Article attribute helper functions
def get_title(article):
    return article.title

def get_link(article):
    return article.link

def get_author(article):
    return article.author

def get_authors(article):
    return article.authors

def get_description(article):
    return article.summary

def get_content(article):
    return article.content

def get_guid(article):
    return article.id

def get_id(article):
    return article['post-id']

def get_datePublished(article):
    date = dateparser.parse(article.published)
    return date.isoformat()

# Aggregate all articles from listed sources
def extract_articles(feeds):
    keys = []
    newer = set()
    update_articles = {}
    source = {}
    print('Number of feeds: ', len(feeds))

    for src, val in feeds.items():
        print('Number of entries "', src, '": ', len(val.entries))

        for entry in val.entries:
            source = src
            title = get_title(entry)
            link = get_link(entry)
            author = get_author(entry)
            description = get_description(entry)
            datePublished = get_datePublished(entry)
            content = get_content(entry)
            # id = get_id(entry)
            guid = get_guid(entry)
            obj = {
                "source": src,
                "title": title,
                "link": link,
                "author": author,
                "description": description,
                "datePublished": datePublished,
                "monthYear": datePublished[0:7],
                "content": content,
                # "id": id,
                "guid": guid
            }
            keys += [{
                'articleid': guid
            }]
            newer.add(guid)
            update_articles[guid] = obj

    print("Read and parsed articles")
    return keys, newer, update_articles

# Checks against database for new articles
def compare(keys):
    already_have = dynamodb.batch_get_item(
        RequestItems={
            'arkansas-news': {
                "AttributesToGet": [ "articleid" ],
                'Keys': keys,
                'ConsistentRead': True
            }
        },
        ReturnConsumedCapacity='TOTAL'
    )['Responses']['arkansas-news']
    have = set()
    if len(already_have) < 1:
        pass
    else:
        for ah in already_have:
            artid = ah['articleid']
            have.add(artid)
    print("Check database for exisiting copies")
    return have

# Add any new articles to database
def add_new_articles():
    file = get_file(sourceFile)
    values, threads = get_sources(file)
    feed = get_feed(values)
    keys, newer, update = extract_articles(feed)
    have = compare(keys)
    should_update =  list(newer - have)
    print("Compare local and exisiting")
    print("%s articles that need to be updated" % len(should_update))
    print("Running logic and writing to db")
    for su in should_update:
        item = update[su]
        print(item['guid'])
        try:
            rsp = table.put_item(Item={
            "articleid":item['guid'], "title":item['title'], "source":item['source'], "description":item['description'], "link":item['link'],
            "author": item['author'], "datePublished": item['datePublished'], "monthYear": item['monthYear'], "content": item['content'] })
        except ClientError as e:
            print("passed")
            pass

def main(event, context):
    add_new_articles()
    result = {"action":"updated"}
    return {
        'statusCode': 200,
        'body': json.dumps(result, default=decimal_default)
    }
