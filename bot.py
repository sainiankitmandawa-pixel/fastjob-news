import feedparser
import re
import random
import time
from datetime import datetime
from supabase import create_client
import requests
from bs4 import BeautifulSoup
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

SUPABASE_URL = "https://wioheljpjdcprozqumpv.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 50 UNIQUE WORLD-WIDE AUTHORS (GLOBAL JOURNALISTS)
WORLD_AUTHORS = [
    "Aarav Sharma (New Delhi)", "Priya Nair (Mumbai)", "Vikramaditya Rathore (India Desk)",
    "Ananya Chatterjee (Kolkata)", "Rohan Deshmukh (Pune)", "Siddharth Menon (Bengaluru)",
    "Kavita Iyer (Chennai)", "Kabir Malhotra (North India)", "Zoya Khan (Hyderabad)",
    "Devansh Joshi (Ahmedabad)", "Niharika Verma (Lucknow)", "Arjun Kapoor (South Asia)",
    "Ethan Brooks (New York)", "Madison Carter (Washington DC)", "Lucas Bennett (Silicon Valley)",
    "Olivia Hayes (Chicago)", "Noah Mitchell (Los Angeles)", "Chloe Sullivan (Boston)",
    "Mason Rivera (Miami)", "Harper Reed (Toronto)", "Logan Foster (Seattle)",
    "Sophia Jenkins (Houston)", "Oliver Sterling (London)", "Amelia Clarke (UK Bureau)",
    "Liam O'Connor (Dublin)", "Camille Laurent (Paris)", "Lukas Weber (Frankfurt)",
    "Elena Rostova (Geneva)", "Matteo Rossi (Milan)", "Sofia Lindqvist (Stockholm)",
    "Hugo Martinez (Madrid)", "Freya Van Der Berg (Amsterdam)", "Tariq Al-Mansoor (Dubai)",
    "Layla Haddad (Doha)", "Omar Farooq (Riyadh)", "Nadia El-Masri (Cairo)",
    "Kwame Mensah (Accra)", "Amara Okafor (Lagos)", "Zanele Khumalo (Johannesburg)",
    "Youssef Benali (Casablanca)", "Kenji Takahashi (Tokyo)", "Mei-Ling Tan (Singapore)",
    "Min-Jae Park (Seoul)", "Liam Thornton (Sydney)", "Isla MacLeod (Melbourne)",
    "Hiroshi Sato (Osaka)", "Mateo Silva (Sao Paulo)", "Valentina Gomez (Buenos Aires)",
    "Diego Hernandez (Mexico City)", "Camila Vargas (Santiago)"
]

RSS_FEEDS = {
    "Breaking News": [
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "https://feeds.feedburner.com/ndtvnews-top-stories",
        "https://www.indiatoday.in/rss/home"
    ],
    "World News": [
        "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
        "https://feeds.feedburner.com/ndtvnews-world-news",
        "https://www.thehindu.com/news/international/feeder/default.rss"
    ],
    "India News": [
        "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
        "https://feeds.feedburner.com/ndtvnews-india-news",
        "https://www.thehindu.com/news/national/feeder/default.rss"
    ],
    "Politics": [
        "https://www.thehindu.com/news/national/feeder/default.rss",
        "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
        "https://www.indiatoday.in/rss/1206514"
    ],
    "Sports": [
        "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms",
        "https://feeds.feedburner.com/ndtvsports-latest",
        "https://www.thehindu.com/sport/feeder/default.rss"
    ],
    "Business": [
        "https://economictimes.indiatimes.com/news/company/rssfeeds/2146842.cms",
        "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms",
        "https://feeds.feedburner.com/ndtvprofit-latest"
    ],
    "Finance & Markets": [
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "https://economictimes.indiatimes.com/wealth/rssfeeds/837555174.cms",
        "https://www.livemint.com/rss/markets"
    ],
    "Technology": [
        "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
        "https://timesofindia.indiatimes.com/rssfeeds/66949542.cms",
        "https://feeds.feedburner.com/gadgets360-latest"
    ],
    "Entertainment": [
        "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms",
        "https://feeds.feedburner.com/ndtvmovies-latest",
        "https://www.thehindu.com/entertainment/feeder/default.rss"
    ],
    "Education": [
        "https://timesofindia.indiatimes.com/rssfeeds/913168846.cms",
        "https://www.thehindu.com/education/feeder/default.rss",
        "https://www.indiatoday.in/rss/1206550"
    ],
    "Jobs & Careers": [
        "https://timesofindia.indiatimes.com/rssfeeds/3012544.cms",
        "https://www.thehindu.com/education/careers/feeder/default.rss",
        "https://economictimes.indiatimes.com/jobs/rssfeeds/107115.cms"
    ],
    "Health & Medicine": [
        "https://timesofindia.indiatimes.com/rssfeeds/3908999.cms",
        "https://www.thehindu.com/sci-tech/health/feeder/default.rss",
        "https://feeds.feedburner.com/ndtvcooks-latest"
    ],
    "Science": [
        "https://timesofindia.indiatimes.com/rssfeeds/-2128672765.cms",
        "https://www.thehindu.com/sci-tech/science/feeder/default.rss"
    ],
    "AI & Robotics": [
        "https://economictimes.indiatimes.com/tech/technology/rssfeeds/78570561.cms",
        "https://www.livemint.com/rss/AI",
        "https://www.livemint.com/rss/technology"
    ],
    "Crime & Justice": [
        "https://timesofindia.indiatimes.com/rssfeeds/2950623.cms",
        "https://www.indiatoday.in/rss/1206576",
        "https://feeds.feedburner.com/ndtvnews-cities"
    ],
    "Auto & EV": [
        "https://timesofindia.indiatimes.com/rssfeeds/74317216.cms",
        "https://economictimes.indiatimes.com/industry/auto/rssfeeds/13359412.cms"
    ],
    "Economy": [
        "https://economictimes.indiatimes.com/news/economy/rssfeeds/1377380.cms",
        "https://www.thehindu.com/business/Economy/feeder/default.rss"
    ],
    "Environment & Climate": [
        "https://timesofindia.indiatimes.com/rssfeeds/2647163.cms",
        "https://www.thehindu.com/sci-tech/energy-and-environment/feeder/default.rss"
    ],
    "Lifestyle": [
        "https://timesofindia.indiatimes.com/rssfeeds/2886704.cms",
        "https://www.thehindu.com/life-and-style/feeder/default.rss"
    ],
    "Travel & Tourism": [
        "https://timesofindia.indiatimes.com/rssfeeds/3112014.cms",
        "https://www.thehindu.com/life-and-style/travel/feeder/default.rss"
    ],
    "Real Estate": [
        "https://economictimes.indiatimes.com/wealth/real-estate/rssfeeds/48997585.cms",
        "https://www.thehindu.com/real-estate/feeder/default.rss"
    ],
    "Defence & Security": [
        "https://economictimes.indiatimes.com/news/defence/rssfeeds/47117033.cms",
        "https://www.thehindu.com/news/national/feeder/default.rss"
    ],
    "Weather": [
        "https://timesofindia.indiatimes.com/rssfeeds/2647163.cms",
        "https://feeds.feedburner.com/ndtvnews-india-news"
    ],
    "Opinion & Editorial": [
        "https://www.thehindu.com/opinion/editorial/feeder/default.rss",
        "https://www.thehindu.com/opinion/lead/feeder/default.rss",
        "https://www.livemint.com/rss/opinion"
    ],
    "Fact Check & Explainers": [
        "https://www.thehindu.com/news/national/feeder/default.rss",
        "https://www.indiatoday.in/rss/fact-check",
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"
    ]
}

FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1495020689067-958852a7765e?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1000&q=80"
]

def extract_real_image(entry):
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if 'url' in media and any(ext in media['url'].lower() for ext in ['jpg', 'png', 'jpeg', 'webp', 'cms']):
                return media['url']
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'href' in enc and any(ext in enc['href'].lower() for ext in ['jpg', 'png', 'jpeg', 'webp', 'cms']):
                return enc['href']
    content_html = entry.get('summary', '') + entry.get('description', '')
    soup = BeautifulSoup(content_html, 'html.parser')
    img_tag = soup.find('img')
    if img_tag and img_tag.get('src') and not img_tag.get('src').endswith('.gif'):
        return img_tag.get('src')
    if hasattr(entry, 'image') and 'href' in entry.image:
        return entry.image['href']
    return random.choice(FALLBACK_IMAGES)

def generate_content_openai(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a senior international journalist and SEO expert. Output only raw HTML."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"OpenAI Request failed: {e}")
    return None

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    words = text.split()
    return "-".join(words[:5])

def to_cat_slug(cat):
    return cat.lower().replace(' & ', '-').replace(' ', '-')

def generate_sitemap():
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        xml += f'  <url>\n    <loc>https://fastjob.online/</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>always</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
        
        for cat in RSS_FEEDS.keys():
            c_slug = to_cat_slug(cat)
            xml += f'  <url>\n    <loc>https://fastjob.online/category/{c_slug}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>hourly</changefreq>\n    <priority>0.9</priority>\n  </url>\n'
            
        static_slugs = ['about-us', 'privacy-policy', 'terms-and-conditions', 'disclaimer', 'editorial-policy', 'contact-us']
        for s_slug in static_slugs:
            xml += f'  <url>\n    <loc>https://fastjob.online/{s_slug}</loc>\n    <lastmod>{today}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.6</priority>\n  </url>\n'
        
        posts = supabase.table("posts").select("slug, created_at").order("id", desc=True).limit(1000).execute()
        for p in posts.data:
            date_str = p['created_at'].split('T')[0] if p.get('created_at') else today
            xml += f'  <url>\n    <loc>https://fastjob.online/{p["slug"]}</loc>\n    <lastmod>{date_str}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
        
        xml += '</urlset>'
        with open('sitemap.xml', 'w', encoding='utf-8') as f:
            f.write(xml)
    except Exception as e:
        print(f"Sitemap Error: {e}")

def post_one_for_category(category, existing_titles):
    feeds = list(RSS_FEEDS[category])
    random.shuffle(feeds)
    
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title.strip()
                if not title:
                    continue
                
                title_key = title[:35].lower()
                if any(title_key in t for t in existing_titles):
                    continue
                
                image_url = extract_real_image(entry)
                summary = entry.get('summary', '')
                
                # Pick 1 of the 50 Global Authors
                author_name = random.choice(WORLD_AUTHORS)
                
                short_id = str(random.randint(1000, 9999))
                slug = slugify(title) + "-" + short_id
                
                prompt = f"""
                Write a comprehensive, engaging, and SEO-optimized news article for the '{category}' desk by journalist '{author_name}' based on:
                Original Title: {title}
                Context: {summary}
                
                CRITICAL INSTRUCTIONS (800+ WORDS):
                1. Write a detailed article of 800+ words covering background, key developments, analysis, and future outlook.
                2. Use 5 <h3 class="article-subheading"> tags with 2-3 detailed paragraphs under each.
                3. Year is 2026. Treat as breaking modern news.
                4. Format strictly in raw HTML starting with <h1 class="seo-title">Catchy SEO Title</h1> and <p class="intro-text"><strong>Reported by {author_name} | FastJob Global Desk:</strong>...
                5. Include one <table class="article-table"> for key highlights.
                6. End with <p class="hashtags">#FastJobAlert #{category.replace(' ', '')} #BreakingNews ...</p>.
                7. Output raw HTML only, no markdown backticks.
                """
                
                content = generate_content_openai(prompt)
                if not content:
                    continue
                
                content = content.strip()
                if content.startswith('```html'): content = content[7:-3].strip()
                elif content.startswith('```'): content = content[3:-3].strip()
                
                # Embed hidden author metadata tag so frontend can read it without changing Supabase table schema
                author_meta = f'<div class="post-author-meta" data-author="{author_name}" style="display:none;"></div>\n'
                full_content = author_meta + content
                
                data = {
                    "title": title,
                    "slug": slug,
                    "content": full_content,
                    "category": category,
                    "image_url": image_url
                }
                
                supabase.table("posts").insert(data).execute()
                existing_titles.add(title_key)
                print(f"✅ [{category}] By {author_name}: {title[:40]}...")
                return True
        except Exception as e:
            print(f"Error in {category} feed: {e}")
            continue
    return False

def run_bulk_15_per_category():
    existing_res = supabase.table("posts").select("title, category").limit(1000).execute()
    cat_counts = {cat: 0 for cat in RSS_FEEDS.keys()}
    existing_titles = set()
    
    for row in existing_res.data:
        c = row.get("category")
        t = (row.get("title") or "")[:35].lower()
        if t:
            existing_titles.add(t)
        if c in cat_counts:
            cat_counts[c] += 1

    needs_bulk = any(count < 15 for count in cat_counts.values())
    
    if needs_bulk:
        print("🚀 BULK TURBO MODE: Filling 15 posts in all 25 categories with 50 Global Authors!")
        for round_num in range(1, 16):
            pending_cats = [cat for cat, count in cat_counts.items() if count < 15]
            if not pending_cats:
                break
            print(f"\n================ ROUND {round_num} / 15 ================")
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_cat = {
                    executor.submit(post_one_for_category, cat, existing_titles): cat 
                    for cat in pending_cats
                }
                for future in as_completed(future_to_cat):
                    cat = future_to_cat[future]
                    try:
                        if future.result():
                            cat_counts[cat] += 1
                    except Exception as e:
                        print(f"Worker error in {cat}: {e}")
            generate_sitemap()
    else:
        print("Running normal 10-minute cycle with 50 Global Authors...")
        for i in range(6):
            cat = random.choice(list(RSS_FEEDS.keys()))
            post_one_for_category(cat, existing_titles)
            generate_sitemap()
            if i < 5:
                time.sleep(600)

if __name__ == "__main__":
    if not OPENAI_API_KEY or not SUPABASE_KEY:
        print("ERROR: API Keys missing!")
    else:
        run_bulk_15_per_category()
