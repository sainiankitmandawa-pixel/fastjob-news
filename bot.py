import feedparser
import re
import random
import time
import threading
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
lock = threading.Lock()

# 50 UNIQUE WORLD-WIDE AUTHORS
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

# 1. INDIA JOBS FEEDS (Target: 30 Posts)
INDIA_JOBS_FEEDS = [
    "https://news.google.com/rss/search?q=sarkari+naukri+recruitment+2026+apply+online+india&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=ssc+upsc+railway+rrb+ibps+bank+vacancy+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=police+constable+teacher+psc+govt+jobs+2026+india&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=india+post+gds+army+agniveer+PSU+recruitment+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "https://timesofindia.indiatimes.com/rssfeeds/3012544.cms",
    "https://www.thehindu.com/education/careers/feeder/default.rss",
    "https://economictimes.indiatimes.com/jobs/rssfeeds/107115.cms"
]

# 2. INTERNATIONAL JOBS FEEDS (Target: 20 Posts)
INTL_JOBS_FEEDS = [
    "https://news.google.com/rss/search?q=remote+jobs+hiring+2026+worldwide+work+from+home&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=visa+sponsorship+jobs+2026+uk+canada+usa+europe+dubai&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=tech+hiring+software+engineer+ai+jobs+global+2026&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=healthcare+nursing+engineering+finance+jobs+abroad+2026&hl=en-US&gl=US&ceid=US:en"
]

# 3. AUTOMOBILE FEEDS (Target: 20 Posts)
AUTO_FEEDS = [
    "https://news.google.com/rss/search?q=new+car+launch+india+suv+electric+vehicle+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=maruti+tata+mahindra+hyundai+kia+toyota+new+cars+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=electric+scooter+bikes+royal+enfield+hero+bajaj+launch+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "https://timesofindia.indiatimes.com/rssfeeds/74317216.cms",
    "https://economictimes.indiatimes.com/industry/auto/rssfeeds/13359412.cms"
]

# 4. GENERAL TRENDING NEWS FEEDS (Target: 30 Posts)
NEWS_FEEDS_BY_CAT = {
    "Breaking News": ["https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"],
    "World News": ["https://news.google.com/rss/search?q=world+news+international+breaking&hl=en-US&gl=US&ceid=US:en", "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms"],
    "India News": ["https://news.google.com/rss/search?q=india+national+news+today&hl=en-IN&gl=IN&ceid=IN:en", "https://www.thehindu.com/news/national/feeder/default.rss"],
    "Politics": ["https://news.google.com/rss/search?q=indian+politics+government+cabinet+parliament&hl=en-IN&gl=IN&ceid=IN:en"],
    "Sports": ["https://news.google.com/rss/search?q=cricket+ipl+team+india+sports+news&hl=en-IN&gl=IN&ceid=IN:en", "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms"],
    "Business": ["https://news.google.com/rss/search?q=business+corporate+startups+india+economy&hl=en-IN&gl=IN&ceid=IN:en", "https://economictimes.indiatimes.com/news/company/rssfeeds/2146842.cms"],
    "Finance & Markets": ["https://news.google.com/rss/search?q=sensex+nifty+stock+market+gold+price+rbi&hl=en-IN&gl=IN&ceid=IN:en"],
    "Technology": ["https://news.google.com/rss/search?q=technology+smartphones+apple+samsung+google+ai&hl=en-IN&gl=IN&ceid=IN:en"],
    "Education": ["https://news.google.com/rss/search?q=cbse+ncert+neet+jee+board+exams+results+2026&hl=en-IN&gl=IN&ceid=IN:en"],
    "Entertainment": ["https://news.google.com/rss/search?q=bollywood+box+office+movies+ott+releases&hl=en-IN&gl=IN&ceid=IN:en"]
}

# HIGH-QUALITY CATEGORY IMAGES
JOB_IMAGES = [
    "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=1000&q=80"
]

AUTO_IMAGES = [
    "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1593941707882-a5bba14938c7?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?auto=format&fit=crop&w=1000&q=80"
]

NEWS_IMAGES = [
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1495020689067-958852a7765e?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1000&q=80"
]

def fetch_rss_entries(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.content)
            return feed.entries
    except Exception as e:
        print(f"RSS fetch warning for {url[:45]}: {e}")
    return []

def extract_real_image(entry, bucket_type="news"):
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
    if bucket_type == "job":
        return random.choice(JOB_IMAGES)
    elif bucket_type == "auto":
        return random.choice(AUTO_IMAGES)
    return random.choice(NEWS_IMAGES)

def generate_content_openai(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    
    for model_name in ["gpt-4o-mini", "gpt-3.5-turbo"]:
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a senior recruitment editor and international journalist. Output strictly raw HTML."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        for attempt in range(2):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=60)
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']
                elif response.status_code == 429:
                    time.sleep(3)
                else:
                    break
            except Exception as e:
                print(f"OpenAI error ({model_name}): {e}")
                time.sleep(2)
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
        
        all_cats = [
            "Jobs & Careers", "Breaking News", "World News", "India News", "Politics", "Sports",
            "Business", "Finance & Markets", "Technology", "Entertainment", "Education",
            "Health & Medicine", "Science", "AI & Robotics", "Crime & Justice",
            "Auto & EV", "Economy", "Environment & Climate", "Lifestyle", "Travel & Tourism",
            "Real Estate", "Defence & Security", "Weather", "Opinion & Editorial", "Fact Check & Explainers"
        ]
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

# Fallback generators so the bot NEVER fails to reach 100 posts even if RSS has duplicates
def generate_fallback_items(bucket, needed_count):
    items = []
    stamp = datetime.now().strftime("%b %d")
    
    india_orgs = [
        "SSC CGL & CHSL Tier-1", "Railway RRB NTPC & Group D", "SBI PO & Clerk", "IBPS Regional Rural Bank",
        "UPSC Civil Services & NDA", "India Post GDS Circle", "DRDO Scientist & Technician", "ISRO Technical Assistant",
        "UP Police Constable & SI", "Rajasthan RSMSSB CET", "Bihar BPSC Teacher", "MPPSC State Services",
        "LIC AAO & ADO", "FCI Watchman & Manager", "BSF & CRPF Paramedical", "NTPC Engineering Executive",
        "ONGC Graduate Trainee", "BHEL Artisan & Engineer", "AIIMS Nursing Officer NORCET", "KVS & NVS PGT TGT Teacher",
        "Delhi DSSSB Various Posts", "Haryana HSSC Group C & D", "Maharashtra Police Bharti", "Gujarat GSSSB Clerk",
        "Coal India Management Trainee", "HAL Design Trainee", "BEL Probationary Engineer", "IOCL Apprentice",
        "EPFO Social Security Assistant", "NABARD Grade A & B Officer"
    ]
    intl_orgs = [
        "USA Remote Software & Cloud", "UK NHS Healthcare & Nursing Visa", "Canada Express Entry Tech",
        "Dubai & UAE Tax-Free Engineering", "Germany EU Blue Card IT", "Australia Skilled Migration",
        "Singapore FinTech & Banking", "Remote AI Prompt Engineer", "Global Cybersecurity Analyst",
        "Amazon Global Fulfillment & Tech", "Google Cloud Remote Operations", "Microsoft Global Support Engineer",
        "Qatar Airways Aviation & Ground", "Saudi NEOM Mega-Project", "Netherlands English-Speaking Tech",
        "Ireland Dublin Data Science", "New Zealand Accredited Employer", "Japan English Teaching & IT",
        "Remote Full-Stack Developer", "Global Digital Marketing & SEO"
    ]
    auto_topics = [
        "Tata Motors Next-Gen Electric SUV", "Mahindra Born-Electric XUV Series", "Maruti Suzuki Hybrid & EV Lineup",
        "Hyundai Creta EV & Smart SUV", "Kia Next-Gen Compact SUV", "Royal Enfield 450cc & 650cc Cruiser",
        "Ola & Ather Next-Gen Electric Scooter", "Toyota Fortuner Mild-Hybrid Edition", "BYD Long-Range Blade Battery EV",
        "Tesla Global Autonomous EV Update", "Hero Vida & Bajaj Chetak EV Expansion", "Skoda-VW India Compact SUV",
        "MG Windsor & Cloud EV Pro", "Honda Elevate & Next-Gen Hybrid", "TVS iQube ST & Electric Motorcycle",
        "BMW & Mercedes Luxury EV Launch", "Renault-Nissan New CMF-B SUV", "Force Gurkha 5-Door Off-Roader",
        "Audi e-tron GT & Q8 Facelift", "Jeep Compass & Meridian Trailhawk"
    ]
    news_topics = [
        ("Breaking News", "Global Economic Summit Announces Major Trade and Digital Infrastructure Pact"),
        ("World News", "UN Security Council convenes on International Peace and Climate Action"),
        ("India News", "Central Government Approves New High-Speed Rail and Expressway Corridors"),
        ("Politics", "Parliamentary Committee Reviews Key Digital Governance and Reforms Bill"),
        ("Sports", "BCCI Announces Squad and Schedule for Upcoming International Cricket Series"),
        ("Business", "Indian Unicorn Startups Record Strong Q3 Revenue and Global Expansion"),
        ("Finance & Markets", "Sensex and Nifty Hit Fresh Highs Amid Strong Institutional Inflows"),
        ("Technology", "Next-Generation AI Chips and 6G Trials Accelerate Digital Transformation"),
        ("Education", "Ministry of Education Announces New National Scholarship and Skill Portal"),
        ("AI & Robotics", "Breakthrough Humanoid Robots Deployed in Manufacturing and Healthcare")
    ]

    for i in range(needed_count):
        uid = random.randint(100, 999)
        if bucket == "india_job":
            org = india_orgs[i % len(india_orgs)]
            title = f"{org} Recruitment 2026: Notification Out for {random.randint(1200, 18500)} Vacancies ({stamp} Update #{uid})"
            items.append(("Jobs & Careers", title, f"Official recruitment update for {org} in India.", random.choice(JOB_IMAGES), "india_job"))
        elif bucket == "intl_job":
            org = intl_orgs[i % len(intl_orgs)]
            title = f"{org} Hiring 2026: Apply Online for High-Paying International Roles ({stamp} Alert #{uid})"
            items.append(("Jobs & Careers", title, f"Global career and visa-sponsored opportunity in {org}.", random.choice(JOB_IMAGES), "intl_job"))
        elif bucket == "auto":
            car = auto_topics[i % len(auto_topics)]
            title = f"{car} 2026 Model Price, Mileage, Specs & Launch Review ({stamp} Update #{uid})"
            items.append(("Auto & EV", title, f"Complete specifications, price, and review of {car}.", random.choice(AUTO_IMAGES), "auto"))
        else:
            cat, base_title = news_topics[i % len(news_topics)]
            title = f"{base_title} - Key Developments ({stamp} Report #{uid})"
            items.append((cat, title, base_title, random.choice(NEWS_IMAGES), "news"))
    return items

def collect_bucket_tasks(feeds, category_name, target_count, bucket_type, existing_titles):
    collected = []
    shuffled_feeds = list(feeds)
    random.shuffle(shuffled_feeds)

    for url in shuffled_feeds:
        if len(collected) >= target_count:
            break
        entries = fetch_rss_entries(url)
        for entry in entries:
            if len(collected) >= target_count:
                break
            title = (entry.get("title") or "").strip()
            if not title:
                continue
            if " - " in title:
                title = title.rsplit(" - ", 1)[0].strip()
            title_key = title[:40].lower()
            if title_key in existing_titles:
                continue
            existing_titles.add(title_key)
            img = extract_real_image(entry, "job" if "job" in bucket_type else ("auto" if bucket_type == "auto" else "news"))
            summary = entry.get("summary", "")
            collected.append((category_name, title, summary, img, bucket_type))

    # If RSS didn't have enough new items, fill the remaining with guaranteed fallback topics
    if len(collected) < target_count:
        shortfall = target_count - len(collected)
        print(f"[{bucket_type}] RSS gave {len(collected)} new items. Generating {shortfall} fresh trending topics to hit {target_count}...")
        collected.extend(generate_fallback_items(bucket_type, shortfall))

    return collected

def process_single_task(task, index, total):
    category, title, summary, image_url, bucket_type = task
    author_name = random.choice(WORLD_AUTHORS)
    short_id = f"{int(time.time()) % 10000}{random.randint(10, 99)}"
    slug = slugify(title) + "-" + short_id

    if bucket_type == "india_job":
        prompt = f"""
        Write a comprehensive, SEO-optimized Indian Sarkari Naukri & Recruitment article for 'Jobs & Careers' by '{author_name}':
        Title: {title}
        Context: {summary}
        
        REQUIREMENTS (600-800 WORDS):
        1. Cover Vacancy Overview, Important Dates, Eligibility Criteria, Age Limit, Salary/Pay Scale, Selection Process, and How to Apply Online in India.
        2. Use 5 <h3 class="article-subheading"> tags with detailed paragraphs.
        3. Format strictly in raw HTML starting with <h1 class="seo-title">{title}</h1> and <p class="intro-text"><strong>Reported by {author_name} | Fast Job India Recruitment Desk:</strong>...
        4. Include one <table class="article-table"> summarizing Post Name, Qualification, Age Limit, and Salary.
        5. End with <p class="hashtags">#SarkariNaukri #IndiaJobs #FastJob #Recruitment2026</p>. Output raw HTML only.
        """
    elif bucket_type == "intl_job":
        prompt = f"""
        Write a comprehensive International Career & Global Hiring article for 'Jobs & Careers' by '{author_name}':
        Title: {title}
        Context: {summary}
        
      