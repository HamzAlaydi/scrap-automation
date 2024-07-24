import csv

async def save_tweets_to_csv(tweets: list, keyword: str):
    filename = f"{keyword}_tweets.csv"
    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        fieldnames = ['link', 'text', 'user', 'likes', 'quotes', 'retweets', 'comments']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for tweet in tweets:
            writer.writerow({
                'link': tweet['url'],
                'text': tweet['text'],
                'user': tweet['user'],
                'likes': tweet['likes'],
                'quotes': tweet['quotes'],
                'retweets': tweet['retweets'],
                'comments': tweet['comments']
            })
