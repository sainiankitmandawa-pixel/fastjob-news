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

# 25 CATEGORIES WITH GOOGLE TRENDS & HIGH-VOLUME GLOBAL FEEDS ("Jobs & Careers" prioritized)
RSS_FEEDS = {
    "Jobs & Careers": [
        "https://news.google.com/rss/search?q=sarkari+naukri+government+jobs+recruitment+vacancy+2026&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=upsc+ssc+banking+railway+jobs+notification&hl=en-IN&gl=IN&ceid=IN:en",
        "https://timesofindia.indiatimes.com/rssfeeds/3012544.cms",
        "https://www.thehindu.com/education/careers/feeder/default.rss",
        "https://economictimes.indiatimes.com/jobs/rssfeeds/107115.cms"
    ],
    "Breaking News": [
        "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "https://feeds.feedburner.com/ndtvnews-top-stories",
        "https://www.indiatoday.in/rss/home"
    ],
    "World News": [
        "https://news.google.com/rss/search?q=world+news+international+trending&hl=en-US&gl=US&ceid=US:en",
        "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms",
        "https://www.thehindu.com/news/international/feeder/default.rss"
    ],
    "India News": [
        "https://news.google.com/rss/search?q=india+national+news+trending&hl=en-IN&gl=IN&ceid=IN:en",
        "https://www.thehindu.com/news/national/feeder/default.rss"
    ],
    "Politics": [
        "https://news.google.com/rss/search?q=politics+government+elections+parliament&hl=en-IN&gl=IN&ceid=IN:en",
        "https://www.thehindu.com/news/national/feeder/default.rss"
    ],
    "Sports": [
        "https://news.google.com/rss/search?q=cricket+sports+football+match+live&hl=en-IN&gl=IN&ceid=IN:en",
        "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms"
    ],
    "Business": [
        "https://news.google.com/rss/search?q=business+companies+startups+economy&hl=en-IN&gl=IN&ceid=IN:en",
        "https://economictimes.indiatimes.com/news/company/rssfeeds/2146842.cms"
    ],
    "Finance & Markets": [
        "https://news.google.com/rss/search?q=stock+market+sensex+nifty+investment+finance&hl=en-IN&gl=IN&ceid=IN:en",
        "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
    ],
    "Technology": [
        "https://news.google.com/rss/search?q=technology+gadgets+smartphones+innovation&hl=en-IN&gl=IN&ceid=IN:en",
        "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"
    ],
    "Entertainment": [
        "https://news.google.com/rss/search?q=entertainment+bollywood+hollywood+movies+ott&hl=en-IN&gl=IN&ceid=IN:en",
        "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms"
    ],
    "Education": [
        "https://news.google.com/rss/search?q=education+exams+results+university+admit+card&hl=en-IN&gl=IN&ceid=IN:en",
        "https://www.thehindu.com/education/feeder/default.rss"
    ],
    "Health & Medicine": [
        "https://news.google.com/rss/search?q=health+medical+wellness+fitness+disease&hl=en-IN&gl=IN&ceid=IN:en",
        "https://timesofindia.indiatimes.com/rssfeeds/3908999.cms"
    ],
    "Science": [
        "https://news.google.com/rss/search?q=science+space+nasa+isro+discoveries&hl=en-IN&gl=IN&ceid=IN:en",
        "https://www.thehindu.com/sci-tech/science/feeder/default.rss"
    ],
    "AI & Robotics": [
        "https://news.google.com/rss/search?q=artificial+intelligence+ai+openai+robotics+tech&hl=en-IN&gl=IN&ceid=IN:en",
        "https://economictimes.indiatimes.com/tech/technology/rssfeeds/78570561.cms"
    ],
    "Crime & Justice": [
        "https://news.google.com/rss/search?q=supreme+court+court+crime+police+investigation+india&hl=en-IN&gl=IN&ceid=IN:en",
        "https://timesofindia.indiatimes.com/rssfeeds/2950623.cms"
    ],
    "Auto & EV": [
        "https://news.google.com/rss/search?q=electric+vehicles+cars+bikes+automobile+launches&hl=en-IN&gl=IN&ceid=IN:en",
        "https://timesofindia.indiatimes.com/rssfeeds/74317216.cms"
    ],
    "Economy": [
        "https://news.google.com/rss/search?q=economy+gdp+inflation+rbi+budget+finance&hl=en-IN&gl=IN&ceid=IN:en",
        "https://economictimes.indiatimes.com/news/economy/rssfeeds/1377380.cms"
    ],
    "Environment & Climate": [
        "https://news.google.com/rss/search?q=climate+change+environment+pollution+green+energy&hl=en-IN&gl=IN&ceid=IN:en",
        "https://timesofindia.indiatimes.com/rssfeeds/2647163.cms"
    ],
    "Lifestyle": [
        "https://news.google.com/rss/search?q=lifestyle+fashion+food+culture+living+trends&hl=en-IN&gl=IN&ceid=IN:en",
        "https://timesofindia.indiatimes.com/rssfeeds/2886704.cms"
    ],
    "Travel & Tourism": [
        "https://news.google.com/rss/search?q=travel+tourism+airlines+railways+destinations+holidays&hl=en-IN&gl=IN&ceid=IN:en",
        "https://timesofindia.indiatimes.com/rssfeeds/3112014.cms"
    ],
    "Real Estate": [
        "https://news.google.com/rss/search?q=real+estate+property+housing+infrastructure+market&hl=en-IN&gl=IN&ceid=IN:en",
        "https://economictimes.indiatimes.com/wealth/real-estate/rssfeeds/48997585.cms"
    ],
    "Defence & Security": [
        "https://news.google.com/rss/search?q=indian+army+navy+air+force+defence+geopolitics&hl=en-IN&gl=IN&ceid=IN:en",
        "https://economictimes.indiatimes.com/news/defence/rssfeeds/47117033.cms"
    ],
    "Weather": [
        "https://news.google.com/rss/search?q=imd+weather+forecast+monsoon+rain+temperature&hl=en-IN&gl=IN&ceid=IN:en"
    ],
    "Opinion & Editorial": [
        "https://news.google.com/rss/search?q=editorial+opinion+analysis+world+affairs&hl=en-IN&gl=IN&ceid=IN:en",
        "https://www.thehindu.com/opinion/editorial/feeder/default.rss"
    ],
    "Fact Check & Explainers": [
        "https://news.google.com/rss/search?q=fact+check+explainer+debunked+news&hl=en-IN&gl=IN&ceid=IN:en",
        "https://www.indiatoday.in/rss/fact-check"
    ]
}

FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1495020689067-958852a7765e?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=1000&q=80"
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
    if img_tag and img_tag.get('src') and not img_tag.get('src').endswith('.gif') and 'google' not in img_tag.get('src'):
        return img_tag.get('src')
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
                if " - " in title:
                    title = title.rsplit(" - ", 1)[0].strip()

                title_key = title[:35].lower()
                if title_key in existing_titles:
                    continue
                
                existing_titles.add(title_key)
                image_url = extract_real_image(entry)
                summary = entry.get('summary', '')
                author_name = random.choice(WORLD_AUTHORS)
                
                short_id = str(random.randint(1000, 9999))
                slug = slugify(title) + "-" + short_id
                
                prompt = f"""
                Write a comprehensive, engaging, and SEO-optimized global news article for the '{category}' desk by journalist '{author_name}' based on:
                Original Title: {title}
                Context: {summary}
                
                CRITICAL INSTRUCTIONS (800+ WORDS):
                1. Write a detailed article of 800+ words covering background, key developments, analysis, and future outlook.
                2. Use 5 <h3 class="article-subheading"> tags with 2-3 detailed paragraphs under each.
                3. Year is 2026. Treat as breaking modern news.
                4. Format strictly in raw HTML starting with <h1 class="seo-title">Catchy SEO Title</h1> and <p class="intro-text"><strong>Reported by {author_name} | Fast Job Global Desk:</strong>...
                5. Include one <table class="article-table"> for key highlights.
                6. End with <p class="hashtags">#FastJob #{category.replace(' ', '')} #TrendingNews</p>.
                7. Output raw HTML only, no markdown backticks.
                """
                
                content = generate_content_openai(prompt)
                if not content:
                    continue
                
                content = content.strip()
                if content.startswith('```html'): content = content[7:-3].strip()
                elif content.startswith('```'): content = content[3:-3].strip()
                
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
                print(f"✅ [{category}] By {author_name}: {title[:45]}...")
                return True
        except Exception as e:
            print(f"Error in {category} feed: {e}")
            continue
    return False

def run_bulk_workflow():
    print("Loading existing titles to avoid duplicates...")
    existing_res = supabase.table("posts").select("title, category").order("id", desc=True).limit(2000).execute()
    existing_titles = set()
    cat_counts = {cat: 0 for cat in RSS_FEEDS.keys()}
    
    for row in existing_res.data:
        c = row.get("category")
        t = (row.get("title") or "")[:35].lower()
        if t:
            existing_titles.add(t)
        if c in cat_counts:
            cat_counts[c] += 1

    print(f"Current category post counts: {cat_counts}")

    # Jobs gets 30 posts, others get 15 posts each
    target_counts = {cat: 30 if cat == "Jobs & Careers" else 15 for cat in RSS_FEEDS.keys()}

    print("🚀 STARTING BULK POSTING (Jobs & Careers prioritized at top with 30 posts!)...")
    for round_num in range(1, 31):
        pending_cats = [cat for cat in RSS_FEEDS.keys() if cat_counts[cat] < target_counts[cat]]
        if not pending_cats:
            print("All categories have reached their target post count!")
            break

        print(f"\n================ ROUND {round_num} / 30 (Remaining: {len(pending_cats)} categories) ================")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
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
        print(f"--- Round {round_num} Complete! ---")

    print("\n🎉 BULK POSTING FINISHED SUCCESSFULLY!")

if __name__ == "__main__":
    if not OPENAI_API_KEY or not SUPABASE_KEY:
        print("ERROR: API Keys missing!")
    else:
        run_bulk_workflow()
