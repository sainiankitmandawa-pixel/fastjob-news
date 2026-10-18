import feedparser
import re
import random
import time
from datetime import datetime
from supabase import create_client
import requests
from bs4 import BeautifulSoup
import os

SUPABASE_URL = "https://wioheljpjdcprozqumpv.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    except Exception as e:
        print(f"Request failed: {e}")
    return None

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    words = text.split()
    return "-".join(words[:4])

# NEW: DYNAMIC SITEMAP GENERATOR FOR GOOGLE INDEXING
def generate_sitemap():
    try:
        print("Generating sitemap.xml for Google Indexing...")
        posts = supabase.table("posts").select("slug, created_at").order("id", desc=True).execute()
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        xml += '  <url>\n    <loc>https://fastjob.online/</loc>\n    <changefreq>always</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
        
        for p in posts.data:
            date_str = p['created_at'].split('T')[0]
            xml += f'  <url>\n    <loc>https://fastjob.online/{p["slug"]}</loc>\n    <lastmod>{date_str}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
        
        xml += '</urlset>'
        
        with open('sitemap.xml', 'w', encoding='utf-8') as f:
            f.write(xml)
        print("sitemap.xml updated successfully!")
    except Exception as e:
        print(f"Sitemap Error: {e}")

def fetch_and_insert_single():
    categories = list(RSS_FEEDS.keys())
    random.shuffle(categories)
    
    for category in categories:
        feeds = RSS_FEEDS[category]
        random.shuffle(feeds)
        
        for url in feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    image_url = extract_real_image(entry)
                    if not image_url: continue 
                    
                    title = entry.title.strip()
                    summary = entry.get('summary', '')
                    
                    check = supabase.table("posts").select("id").ilike("title", f"%{title[:30]}%").execute()
                    if len(check.data) > 0:
                        continue 
                    
                    short_id = str(int(datetime.now().timestamp()))[-4:]
                    slug = slugify(title) + "-" + short_id
                    
                    print(f"[{category}] Generating SEO article for: {title[:30]}...")
                    
                    prompt = f"""
                    Write a highly engaging, comprehensive, and SEO-optimized news article based on:
                    Original Title: {title}
                    Context: {summary}
                    
                    CRITICAL INSTRUCTIONS FOR LENGTH & STRUCTURE (STRICTLY 800+ WORDS):
                    1. You MUST write a very detailed article exceeding 800 words. Expand on the topic by providing: detailed background history, current implications, expert analysis, and future outlook.
                    2. Use at least 5-6 <h3 class="article-subheading"> tags. Under each heading, write 2 to 3 long, detailed paragraphs.
                    3. Create a highly ranked, catchy SEO Title for the article.
                    4. Year is 2026. Treat as breaking modern news.
                    5. Format strictly in HTML. Start with <h1 class="seo-title">YOUR Catchy Title Here</h1> then <p class="intro-text"><strong>(FastJob Alert Desk):</strong>...
                    6. Include one <table class="article-table"> for key highlights.
                    7. At the very end of the article, add a paragraph with 5-6 trending hashtags (e.g., <p class="hashtags">#News #Trending ...</p>).
                    8. Do not include ```html or markdown formatting, just raw HTML.
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
                    
                    supabase.table("posts").insert(data).execute()
                    print(f"SUCCESS! Posted 1 article in [{category}].")
                    return True
            except Exception as e:
                print(f"Error in {category}: {e}")
                continue
    return False

if __name__ == "__main__":
    if not OPENAI_API_KEY or not SUPABASE_KEY:
        print("ERROR: API Keys missing!")
    else:
        print(f"[{datetime.now()}] Bot activated for a 1-Hour continuous cycle!")
        for i in range(6):
            print(f"\n--- Starting Post {i+1} of 6 ---")
            success = fetch_and_insert_single()
            if success:
                generate_sitemap() # Auto-update sitemap after every successful post
            else:
                print("No new posts found right now.")
            
            if i < 5:
                print("Waiting 10 minutes (600 seconds) for the next post...")
                time.sleep(600)
        print("\n1-Hour cycle complete.")
