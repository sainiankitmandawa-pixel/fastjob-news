import os
import feedparser
import re
from datetime import datetime
from supabase import create_client

SUPABASE_URL = "https://wioheljpjdcprozqumpv.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_KEY_HERE"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

RSS_FEEDS = {
    "National": [
        "https://www.thehindu.com/news/national/feeder/default.rss",
        "https://economictimes.indiatimes.com/rssfeedscs.cms"
    ]
}

def fetch_all_news():
    print("Fetching news...")

if __name__ == "__main__":
    fetch_all_news()
