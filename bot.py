import feedparser
import re
from datetime import datetime
from supabase import create_client
import requests
from bs4 import BeautifulSoup
import os

# Secure Cloud Environment Variables
SUPABASE_URL = "https://wioheljpjdcprozqumpv.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 7 Categories
RSS_FEEDS = {
    "Politics": ["https://www.thehindu.com/news/national/feeder/default.rss"],
    "Economy": ["https://economictimes.indiatimes.com/news/economy/rssfeeds/1377380.cms"],
    "Business": ["https://economictimes.indiatimes.com/news/company/rssfeeds/2146842.cms"],
    "Sports": ["https://timesofindia.indiatimes.com/rssfeeds/4719148.cms"],
    "Automobile": ["https://timesofindia.indiatimes.com/rssfeeds/74317216.cms"],
    "Tech & AI": ["https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"],
    "Jobs": ["https://timesofindia.indiatimes.com/rssfeeds/3012544.cms"]
}

def extract_real_image(entry):
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if 'url' in media and any(ext in media['url'] for ext in ['jpg', 'png', 'jpeg']): return media['url']
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'href' in enc and any(ext in enc['href'] for ext in ['jpg', 'png', 'jpeg']): return enc['href']
    content_html = entry.get('summary', '') + entry.get('description', '')
    soup = BeautifulSoup(content_html, 'html.parser')
    img_tag = soup.find('img')
    if img_tag and img_tag.get('src') and not img_tag.get('src').endswith('.gif'): return img_tag.get('src')
    if hasattr(entry, 'image') and 'href' in entry.image: return entry.image['href']
    return None 

def generate_content_openai(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a senior journalist and SEO expert. Output only the HTML requested."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"OpenAI API Error: {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'[\s-]+', '-', text).strip('-')

def fetch_and_insert():
    print(f"[{datetime.now()}] Bot started on Cloud Server! Fetching fresh posts...")
    
    if not OPENAI_API_KEY or not SUPABASE_KEY:
        print("ERROR: API Keys missing! Check GitHub Secrets.")
        return
    
    for category, feeds in RSS_FEEDS.items():
        for url in feeds:
            feed = feedparser.parse(url)
            added_in_category = 0
            
            for entry in feed.entries:
                # HAR GHANTE 2 POST PER CATEGORY (Daily 336 posts total)
                if added_in_category >= 2: break 
                
                image_url = extract_real_image(entry)
                if not image_url: continue 
                
                title = entry.title
                summary = entry.get('summary', '')
                slug = slugify(title) + "-" + str(int(datetime.now().timestamp()))
                
                check = supabase.table("posts").select("id").ilike("title", title).execute()
                if len(check.data) > 0:
                    continue 
                
                print(f"[{category}] Generating article for: {title[:30]}...")
                
                # YAHAN DATE AUR YEAR FIX KIYA HAI
                prompt = f"""
                Write a detailed, professional, and SEO-optimized news article in English (at least 800-900 words) about:
                Title: {title}
                Context: {summary}
                CRITICAL RULE: The current year is 2026. Treat this as breaking, modern news. DO NOT include outdated dates like 2023 or 2024 in tables or text unless historically necessary.
                Format strictly in HTML. Start with <p class="intro-text"><strong>(FastJob Alert Desk):</strong>... Use <h3 class="article-subheading"> for headings and include one <table class="article-table">. Do not include ```html or ``` markdown formatting, just the raw HTML code.
                """
                
                content = generate_content_openai(prompt)
                if not content: continue 
                
                content = content.strip()
                if content.startswith('```html'): content = content[7:-3]
                elif content.startswith('```'): content = content[3:-3]
                
                data = {
                    "title": title,
                    "slug": slug,
                    "content": content,
                    "category": category,
                    "image_url": image_url
                }
                
                try:
                    supabase.table("posts").insert(data).execute()
                    print(f"SUCCESS! Inserted [{category}] post.")
                    added_in_category += 1
                except Exception as e:
                    print(f"Supabase Error: {e}")

if __name__ == "__main__":
    fetch_and_insert()
