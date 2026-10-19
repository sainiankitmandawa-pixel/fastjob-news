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

# DEDICATED INDIA JOBS (Strictly 50% of Job ratio)
INDIA_JOBS_FEEDS = [
    "https://news.google.com/rss/search?q=sarkari+naukri+government+jobs+recruitment+2026+india+vacancy&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=upsc+ssc+banking+railway+ibps+police+jobs+notification+india&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=state+psc+teacher+vacancy+recruitment+2026+india&hl=en-IN&gl=IN&ceid=IN:en"
]

# GLOBAL CAREERS & JOBS
GLOBAL_JOBS_FEEDS = [
    "https://news.google.com/rss/search?q=remote+jobs+hiring+tech+careers+global+opportunities&hl=en-US&gl=US&ceid=US:en",
    "https://economictimes.indiatimes.com/jobs/rssfeeds/107115.cms",
    "https://www.thehindu.com/education/careers/feeder/default.rss"
]

# OTHER 24 NEWS CATEGORIES
OTHER_RSS_FEEDS = {
    "Breaking News": ["https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"],
    "World News": ["https://news.google.com/rss/search?q=world+news+international&hl=en-US&gl=US&ceid=US:en"],
    "India News": ["https://news.google.com/rss/search?q=india+national+news&hl=en-IN&gl=IN&ceid=IN:en"],
    "Politics": ["https://news.google.com/rss/search?q=politics+government+elections+parliament&hl=en-IN&gl=IN&ceid=IN:en"],
    "Sports": ["https://news.google.com/rss/search?q=cricket+sports+football+match+live&hl=en-IN&gl=IN&ceid=IN:en"],
    "Business": ["https://news.google.com/rss/search?q=business+companies+startups+economy&hl=en-IN&gl=IN&ceid=IN:en"],
    "Finance & Markets": ["https://news.google.com/rss/search?q=stock+market+sensex+nifty+investment+finance&hl=en-IN&gl=IN&ceid=IN:en"],
    "Technology": ["https://news.google.com/rss/search?q=technology+gadgets+smartphones+innovation&hl=en-IN&gl=IN&ceid=IN:en"],
    "Entertainment": ["https://news.google.com/rss/search?q=entertainment+bollywood+hollywood+movies+ott&hl=en-IN&gl=IN&ceid=IN:en"],
    "Education": ["https://news.google.com/rss/search?q=education+exams+results+university+admit+card&hl=en-IN&gl=IN&ceid=IN:en"],
    "Health & Medicine": ["https://news.google.com/rss/search?q=health+medical+wellness+fitness+disease&hl=en-IN&gl=IN&ceid=IN:en"],
    "Science": ["https://news.google.com/rss/search?q=science+space+nasa+isro+discoveries&hl=en-IN&gl=IN&ceid=IN:en"],
    "AI & Robotics": ["https://news.google.com/rss/search?q=artificial+intelligence+ai+openai+robotics+tech&hl=en-IN&gl=IN&ceid=IN:en"],
    "Crime & Justice": ["https://news.google.com/rss/search?q=supreme+court+court+crime+police+investigation+india&hl=en-IN&gl=IN&ceid=IN:en"],
    "Auto & EV": ["https://news.google.com/rss/search?q=electric+vehicles+cars+bikes+automobile+launches&hl=en-IN&gl=IN&ceid=IN:en"],
    "Economy": ["https://news.google.com/rss/search?q=economy+gdp+inflation+rbi+budget+finance&hl=en-IN&gl=IN&ceid=IN:en"],
    "Environment & Climate": ["https://news.google.com/rss/search?q=climate+change+environment+pollution+green+energy&hl=en-IN&gl=IN&ceid=IN:en"],
    "Lifestyle": ["https://news.google.com/rss/search?q=lifestyle+fashion+food+culture+living+trends&hl=en-IN&gl=IN&ceid=IN:en"],
    "Travel & Tourism": ["https://news.google.com/rss/search?q=travel+tourism+airlines+railways+destinations+holidays&hl=en-IN&gl=IN&ceid=IN:en"],
    "Real Estate": ["https://news.google.com/rss/search?q=real+estate+property+housing+infrastructure+market&hl=en-IN&gl=IN&ceid=IN:en"],
    "Defence & Security": ["https://news.google.com/rss/search?q=indian+army+navy+air+force+defence+geopolitics&hl=en-IN&gl=IN&ceid=IN:en"],
    "Weather": ["https://news.google.com/rss/search?q=imd+weather+forecast+monsoon+rain+temperature&hl=en-IN&gl=IN&ceid=IN:en"],
    "Opinion & Editorial": ["https://news.google.com/rss/search?q=editorial+opinion+analysis+world+affairs&hl=en-IN&gl=IN&ceid=IN:en"],
    "Fact Check & Explainers": ["https://news.google.com/rss/search?q=fact+check+explainer+debunked+news&hl=en-IN&gl=IN&ceid=IN:en"]
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
    if img_tag and img_tag.get('src') and not img_tag.get('src').endswith('.gif') and 'google' not in img_tag.get('src'):
        return img_tag.get('src')
    return random.choice(FALLBACK_IMAGES)

def generate_content_openai(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are a senior recruitment expert and international journalist. Output only raw HTML."},
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
        
        all_cats = ["Jobs & Careers"] + list(OTHER_RSS_FEEDS.keys())
        for cat in all_cats:
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

def post_article(category, feeds, is_india_job, existing_titles):
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
                
                if is_india_job:
                    prompt = f"""
                    Write a detailed, verified Sarkari Naukri & Career Vacancy article for 'Jobs & Careers' by '{author_name}' based on:
                    Title: {title}
                    Details: {summary}
                    
                    REQUIREMENTS (800+ WORDS):
                    1. Focus heavily on Indian Government Jobs, eligibility, age limit, salary, application last date, and official links context.
                    2. Use 5 <h3 class="article-subheading"> tags with detailed paragraphs.
                    3. Format in raw HTML starting with <h1 class="seo-title">Catchy Title</h1> and <p class="intro-text"><strong>Reported by {author_name} | Fast Job Recruitment Desk:</strong>...
                    4. Include an <table class="article-table"> summarizing vacancy details, posts, and dates.
                    5. End with <p class="hashtags">#SarkariNaukri #GovtJobs #FastJob #Recruitment2026</p>. Output raw HTML only.
                    """
                else:
                    prompt = f"""
                    Write a comprehensive global news/job article for '{category}' by '{author_name}' based on:
                    Title: {title}
                    Context: {summary}
                    
                    REQUIREMENTS (800+ WORDS):
                    1. Write 800+ words with deep analysis and expert insights.
                    2. Use 5 <h3 class="article-subheading"> tags.
                    3. Format in raw HTML starting with <h1 class="seo-title">Catchy Title</h1> and <p class="intro-text"><strong>Reported by {author_name} | Fast Job Global Desk:</strong>...
                    4. Include an <table class="article-table"> for key highlights.
                    5. End with <p class="hashtags">#FastJob #{category.replace(' ', '')} #GlobalNews</p>. Output raw HTML only.
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
            print(f"Error in {category}: {e}")
            continue
    return False

def run_smart_ratio_workflow():
    print("Loading existing titles...")
    existing_res = supabase.table("posts").select("title").order("id", desc=True).limit(2000).execute()
    existing_titles = set()
    for row in existing_res.data:
        t = (row.get("title") or "")[:35].lower()
        if t:
            existing_titles.add(t)

    print("🚀 STARTING SMART RATIO WORKFLOW (70% Jobs [50% India Jobs] / 30% News)...")
    
    # 20 posts per execution cycle: 14 Jobs (7 India + 7 Global) + 6 News
    tasks = []
    
    # 7 India Jobs
    for _ in range(7):
        tasks.append(("Jobs & Careers", INDIA_JOBS_FEEDS, True))
    # 7 Global Jobs
    for _ in range(7):
        tasks.append(("Jobs & Careers", GLOBAL_JOBS_FEEDS, False))
    # 6 News from other 24 categories
    other_cats = list(OTHER_RSS_FEEDS.keys())
    for _ in range(6):
        c = random.choice(other_cats)
        tasks.append((c, OTHER_RSS_FEEDS[c], False))

    random.shuffle(tasks)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(post_article, cat, feeds, is_india, existing_titles) for cat, feeds, is_india in tasks]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Task error: {e}")

    generate_sitemap()
    print("🎉 WORKFLOW CYCLE COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    if not OPENAI_API_KEY or not SUPABASE_KEY:
        print("ERROR: API Keys missing!")
    else:
        run_smart_ratio_workflow()