from playwright.async_api import async_playwright
from login import login_to_twitter
from urllib.parse import quote

class TweetScraper:
    def login_to_twitter(self, username: str, password: str):
        return login_to_twitter(username, password)

    async def search_and_scrape_tweets(self, keyword: str, number_of_tweets: int, cookies: list):
        tweets = []
        seen_tweets = set()

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context(viewport={"width": 1000, "height": 800})

            try:
                if cookies:
                    parsed_cookies = self.parse_cookies(cookies)
                    await context.clear_cookies()
                    await context.add_cookies(parsed_cookies)

                page = await context.new_page()
                search_url = f"https://twitter.com/search?q={quote(keyword)}&src=typed_query"
                await page.goto(search_url)
                await page.wait_for_selector("[data-testid='primaryColumn']")

                while len(tweets) < number_of_tweets:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                    await page.wait_for_timeout(1000)

                    tweet_elements = await page.query_selector_all("[data-testid='tweet']")
                    for tweet_element in tweet_elements:
                        tweet_info = {}

                        tweet_text_elem = await tweet_element.query_selector("div[data-testid='tweetText']")
                        tweet_info['text'] = await tweet_text_elem.inner_text() if tweet_text_elem else "No text available"

                        like_element = await tweet_element.query_selector("[data-testid='like']")
                        num_likes = await like_element.inner_text() if like_element else "0"
                        tweet_info['likes'] = num_likes.strip() if isinstance(num_likes, str) else num_likes

                        tweet_url_elem = await tweet_element.query_selector("a[href*='/status/']")
                        tweet_info['url'] = await tweet_url_elem.get_attribute("href") if tweet_url_elem else None

                        user_elem = await tweet_element.query_selector("div[data-testid='User-Name'] span")
                        tweet_info['user'] = await user_elem.inner_text() if user_elem else "Unknown"

                        quote_element = await tweet_element.query_selector("[data-testid='quote']")
                        num_quotes = await quote_element.inner_text() if quote_element else "0"
                        tweet_info['quotes'] = num_quotes.strip() if isinstance(num_quotes, str) else num_quotes

                        retweet_element = await tweet_element.query_selector("[data-testid='retweet']")
                        num_retweets = await retweet_element.inner_text() if retweet_element else "0"
                        tweet_info['retweets'] = num_retweets.strip() if isinstance(num_retweets, str) else num_retweets

                        comment_element = await tweet_element.query_selector("[data-testid='reply']")
                        num_comments = await comment_element.inner_text() if comment_element else "0"
                        tweet_info['comments'] = num_comments.strip() if isinstance(num_comments, str) else num_comments

                        if tweet_info['url'] in seen_tweets:
                            continue
                        seen_tweets.add(tweet_info['url'])

                        tweets.append(tweet_info)

                        if len(tweets) >= number_of_tweets:
                            break

                    if len(tweets) >= number_of_tweets:
                        break

            except Exception as e:
                print(f"An error occurred during scraping: {e}")
            finally:
                await browser.close()

        return tweets[:number_of_tweets]

    def parse_cookies(self, cookies: list) -> list:
        parsed_cookies = []
        for cookie in cookies:
            parsed_cookies.append({
                "name": cookie['name'],
                "value": cookie['value'],
                "domain": cookie['domain'],
                "path": cookie['path']
            })
        return parsed_cookies
