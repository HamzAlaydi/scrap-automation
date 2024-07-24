from fastapi import FastAPI, HTTPException, UploadFile, File
from login import login_to_twitter
from scraper import TweetScraper
from csv_helper import save_tweets_to_csv
import logging
import httpx
import asyncio
import csv
import json
import os

app = FastAPI()
logging.basicConfig(level=logging.DEBUG)

ACCOUNTS_DIR = 'uploaded_files'
accounts = []  # List to store the accounts from the CSV
ACCOUNT_INDEX_FILE = 'account_index.json'
account_index = 0  # Global index for round-robin account selection


def save_account_index():
    """Save the current account index to a file."""
    with open(ACCOUNT_INDEX_FILE, 'w') as f:
        json.dump({'account_index': account_index}, f)


def load_account_index():
    """Load the account index from the file."""
    global account_index
    if os.path.exists(ACCOUNT_INDEX_FILE):
        with open(ACCOUNT_INDEX_FILE, 'r') as f:
            data = json.load(f)
            account_index = data.get('account_index', 0)


def load_accounts():
    accounts = []
    for filename in os.listdir(ACCOUNTS_DIR):
        if filename.endswith('.csv'):
            with open(os.path.join(ACCOUNTS_DIR, filename), mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    cleaned_row = {key.lstrip('\ufeff'): value for key, value in row.items()}
                    accounts.append(cleaned_row)
    return accounts


@app.on_event("startup")
async def startup_event():
    global accounts
    try:
        # Load accounts from the directory on startup
        accounts = load_accounts()

        # Load the last used account index
        load_account_index()

        logging.debug(f"Accounts loaded on startup: {accounts}")
        logging.debug(f"Starting from account index: {account_index}")
    except Exception as e:
        logging.error(f"Error loading accounts on startup: {e}")


@app.post("/upload_accounts")
async def upload_accounts(file: UploadFile = File(...)):
    global accounts, account_index
    file_location = f"{ACCOUNTS_DIR}/{file.filename}"

    try:
        # Save the uploaded file
        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())

        # Load accounts from the uploaded CSV file
        accounts = load_accounts()
        account_index = 0  # Reset account index

        # Save the account index
        save_account_index()

        if not accounts:
            raise HTTPException(status_code=400, detail="No accounts found in the CSV file")

        logging.debug(f"Accounts loaded: {accounts}")

        return {"status": "success", "accounts_uploaded": len(accounts)}

    except Exception as e:
        logging.error(f"Error uploading accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scrape_tweets")
async def scrape_tweets(keyword: str, post_limit: int):
    global account_index
    # Load accounts from uploaded files
    accounts = load_accounts()

    if not accounts:
        raise HTTPException(status_code=400,
                            detail="No accounts available. Please upload accounts using /upload_accounts")

    # Select the account using round-robin
    account = accounts[account_index]
    account_index = (account_index + 1) % len(accounts)  # Update index for next request

    # Save the account index
    save_account_index()

    logging.debug(f"Using account: {account}")

    # Ensure all required keys are present in the account
    required_keys = ['username', 'password', '2fa']
    if not all(key in account for key in required_keys):
        logging.error(f"Account missing required keys: {account}")
        raise HTTPException(status_code=400, detail="Account data is incomplete")

    username = account['username']
    password = account['password']
    two_fa = account['2fa']

    logging.debug(f"Received scrape request for keyword: {keyword} using account: {username}")

    try:
        # Request 2FA OTP
        otp_response = await get_otp(two_fa)
        otp = otp_response.get('data').get('otp')
        time_remaining = otp_response.get('data').get('timeRemaining')

        if not otp:
            raise HTTPException(status_code=500, detail="Failed to get 2FA OTP")

        # If timeRemaining is less than 10 seconds, wait before proceeding
        if time_remaining < 10:
            await asyncio.sleep(time_remaining + 1)

        # Login to Twitter
        cookies = login_to_twitter(username, password, otp)
        if not cookies:
            raise HTTPException(status_code=500, detail="Login failed")

        # Initialize TweetScraper and scrape tweets
        scraper = TweetScraper()
        tweets = await scraper.search_and_scrape_tweets(keyword, post_limit, cookies)

        # Save tweets to CSV
        await save_tweets_to_csv(tweets, keyword)

        response_data = {
            "status": "Scraping and saving successful",
            "tweets": tweets
        }

        return response_data

    except Exception as e:
        logging.error(f"An error occurred during scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_otp(two_fa: str):
    url = f"https://2fa.fb.rip/api/otp/{two_fa}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
