import feedparser
import re
import random
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

SUPABASE_URL = "https://wioheljpjdcprozqumpv.supabase.co"
SUPABASE_KEY = (os.environ.get("SUPABASE_KEY") or "").strip() or "sb_publishable_d_ROr-nG6RpIRlVWtIE-Fg_sciaLZXR"
OPENAI_API_KEY = (os.environ.get("OPENAI_API_KEY") or "").strip()

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": "Bearer " + SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

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

INDIA_JOBS_FEEDS = [
    "https://news.google.com/rss/search?q=sarkari+naukri+recruitment+2026+apply+online+india&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=ssc+upsc+railway+rrb+ibps+bank+vacancy+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=police+constable+teacher+psc+govt+jobs+2026+india&hl=en-IN&gl=IN&ceid=IN:en",
    "https://timesofindia.indiatimes.com/rssfeeds/3012544.cms"
]

INTL_JOBS_FEEDS = [
    "https://news.google.com/rss/search?q=remote+jobs+hiring+2026+worldwide+work+from+home&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=visa+sponsorship+jobs+2026+uk+canada+usa+europe+dubai&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=tech+hiring+software+engineer+ai+jobs+global+2026&hl=en-US&gl=US&ceid=US:en"
]

AUTO_FEEDS = [
    "https://news.google.com/rss/search?q=new+car+launch+india+suv+electric+vehicle+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=maruti+tata+mahindra+hyundai+kia+toyota+new+cars+2026&hl=en-IN&gl=IN&ceid=IN:en",
    "https://timesofindia.indiatimes.com/rssfeeds/74317216.cms"
]

NEWS_FEEDS_BY_CAT = {
    "Breaking News": ["https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"],
    "World News": ["https://news.google.com/rss/search?q=world+news+international+breaking&hl=en-US&gl=US&ceid=US:en"],
    "India News": ["https://news.google.com/rss/search?q=india+national+news+today&hl=en-IN&gl=IN&ceid=IN:en"],
    "Politics": ["https://news.google.com/rss/search?q=indian+politics+government+parliament&hl=en-IN&gl=IN&ceid=IN:en"],
    "Sports": ["https://news.google.com/rss/search?q=cricket+ipl+team+india+sports+news&hl=en-IN&gl=IN&ceid=IN:en"],
    "Business": ["https://news.google.com/rss/search?q=business+corporate+startups+india+economy&hl=en-IN&gl=IN&ceid=IN:en"],
    "Finance & Markets": ["https://news.google.com/rss/search?q=sensex+nifty+stock+market+gold+price+rbi&hl=en-IN&gl=IN&ceid=IN:en"],
    "Technology": ["https://news.google.com/rss/search?q=technology+smartphones+apple+samsung+google+ai&hl=en-IN&gl=IN&ceid=IN:en"],
    "Education": ["https://news.google.com/rss/search?q=cbse+ncert+neet+jee+board+exams+results+2026&hl=en-IN&gl=IN&ceid=IN:en"],
    "Entertainment": ["https://news.google.com/rss/search?q=bollywood+box+office+movies+ott+releases&hl=en-IN&gl=IN&ceid=IN:en"]
}

JOB_IMAGES = [
    "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?auto=format&fit=crop&w=1000&q=80"
]

AUTO_IMAGES = [
    "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1000&q=80"
]

NEWS_IMAGES = [
    "https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1495020689067-958852a7765e?auto=format&fit=crop&w=1000&q=80",
    "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?auto=format&fit=crop&w=1000&q=80"
]

def supabase_get_posts(select_query="title", limit=1000):
    try:
        url = SUPABASE_URL + "/rest/v1/posts?select=" + select_query + "&order=id.desc&limit=" + str(limit)
        r = requests.get(url, headers={"apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY}, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print("GET warning:", e)
    return []

def supabase_insert_post(data):
    try:
        url = SUPABASE_URL + "/rest/v1/posts"
        r = requests.post(url, headers=SUPABASE_HEADERS, json=data, timeout=25)
        if r.status_code in [200, 201, 204]:
            return True
        print("Insert status:", r.status_code, r.text[:120])
    except Exception as e:
        print("Insert error:", e)
    return False

def fetch_rss_entries(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return feedparser.parse(resp.content).entries
    except Exception as e:
        print("RSS warning:", e)
    return []

def extract_real_image(entry, bucket_type="news"):
    if hasattr(entry, "media_content") and entry.media_content:
        for media in entry.media_content:
            if "url" in media and any(ext in media["url"].lower() for ext in ["jpg", "png", "jpeg", "webp", "cms"]):
                return media["url"]
    if "job" in bucket_type:
        return random.choice(JOB_IMAGES)
    if bucket_type == "auto":
        return random.choice(AUTO_IMAGES)
    return random.choice(NEWS_IMAGES)

def generate_content_openai(prompt):
    if not OPENAI_API_KEY:
        return None
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer " + OPENAI_API_KEY}
    for model_name in ["gpt-4o-mini", "gpt-3.5-turbo"]:
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a senior recruitment editor and journalist. Output strictly raw HTML."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        try:
            response = requests.post(url, headers=headers, json=data, timeout=50)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print("OpenAI warning:", e)
    return None

def build_rich_fallback_html(title, summary, category, author_name):
    clean_summary = BeautifulSoup(summary or title, "html.parser").get_text()
    parts = [
        '<h1 class="seo-title">' + title + '</h1>',
        '<p class="intro-text"><strong>Reported by ' + author_name + ' | Fast Job Global Desk:</strong> ' + clean_summary + '</p>',
        '<h3 class="article-subheading">Official Notification & Key Highlights</h3>',
        '<p>In a major development under the <strong>' + category + '</strong> desk, official sources have released updated details regarding <strong>' + title + '</strong>. Candidates and readers tracking this update are advised to review the complete specifications below.</p>',
        '<table class="article-table">',
        '<tr><th>Category Desk</th><td>' + category + '</td></tr>',
        '<tr><th>Update Title</th><td>' + title + '</td></tr>',
        '<tr><th>Reported By</th><td>' + author_name + '</td></tr>',
        '<tr><th>Status</th><td>Verified Live Update (2026)</td></tr>',
        '</table>',
        '<h3 class="article-subheading">Eligibility, Impact & Guidelines</h3>',
        '<p>Applicants and stakeholders should verify all official requirements, important dates, and documentation guidelines on the portal before proceeding with online applications.</p>',
        '<p class="hashtags">#FastJob #' + category.replace(" ", "").replace("&", "") + ' #LiveUpdate2026</p>'
    ]
    return "\n".join(parts)

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    words = text.split()
    return "-".join(words[:5]) if words else "news-update"

def to_cat_slug(cat):
    return cat.lower().replace(" & ", "-").replace(" ", "-")

def generate_sitemap():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            '  <url><loc>https://fastjob.online/</loc><lastmod>' + today + '</lastmod><changefreq>always</changefreq><priority>1.0</priority></url>'
        ]
        all_cats = [
            "Jobs & Careers", "Breaking News", "World News", "India News", "Politics", "Sports",
            "Business", "Finance & Markets", "Technology", "Entertainment", "Education",
            "Health & Medicine", "Science", "AI & Robotics", "Crime & Justice",
            "Auto & EV", "Economy", "Environment & Climate", "Lifestyle", "Travel & Tourism",
            "Real Estate", "Defence & Security", "Weather", "Opinion & Editorial", "Fact Check & Explainers"
        ]
        for cat in all_cats:
            lines.append('  <url><loc>https://fastjob.online/category/' + to_cat_slug(cat) + '</loc><lastmod>' + today + '</lastmod><changefreq>hourly</changefreq><priority>0.9</priority></url>')
        static_slugs = ["about-us", "privacy-policy", "terms-and-conditions", "disclaimer", "editorial-policy", "contact-us"]
        for s_slug in static_slugs:
            lines.append('  <url><loc>https://fastjob.online/' + s_slug + '</loc><lastmod>' + today + '</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>')
        posts = supabase_get_posts("slug,created_at", 1000)
        for p in posts:
            date_str = p["created_at"].split("T")[0] if p.get("created_at") else today
            lines.append('  <url><loc>https://fastjob.online/' + p["slug"] + '</loc><lastmod>' + date_str + '</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>')
        lines.append("</urlset>")
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    except Exception as e:
        print("Sitemap Error:", e)

def generate_fallback_items(bucket, needed_count):
    items = []
    stamp = datetime.now().strftime("%b %d")
    india_orgs = [
        "SSC CGL & CHSL Tier-1", "Railway RRB NTPC & Group D", "SBI PO & Clerk", "IBPS Regional Rural Bank",
        "UPSC Civil Services & NDA", "India Post GDS Circle", "DRDO Scientist & Technician", "ISRO Technical Assistant",
        "UP Police Constable & SI", "Rajasthan RSMSSB CET", "Bihar BPSC Teacher", "MPPSC State Services",
        "LIC AAO & ADO", "FCI Watchman & Manager", "BSF & CRPF Paramedical", "NTPC Engineering Executive",
        "ONGC Graduate Trainee", "BHEL Artisan & Engineer", "AIIMS Nursing Officer NORCET", "KVS & NVS PGT TGT Teacher"
    ]
    intl_orgs = [
        "USA Remote Software & Cloud", "UK NHS Healthcare & Nursing Visa", "Canada Express Entry Tech",
        "Dubai & UAE Tax-Free Engineering", "Germany EU Blue Card IT", "Australia Skilled Migration",
        "Singapore FinTech & Banking", "Remote AI Prompt Engineer", "Global Cybersecurity Analyst",
        "Amazon Global Fulfillment & Tech", "Google Cloud Remote Operations", "Microsoft Global Support Engineer"
    ]
    auto_topics = [
        "Tata Motors Next-Gen Electric SUV", "Mahindra Born-Electric XUV Series", "Maruti Suzuki Hybrid & EV Lineup",
        "Hyundai Creta EV & Smart SUV", "Kia Next-Gen Compact SUV", "Royal Enfield 450cc & 650cc Cruiser",
        "Ola & Ather Next-Gen Electric Scooter", "Toyota Fortuner Mild-Hybrid Edition", "BYD Long-Range Blade Battery EV",
        "Hero Vida & Bajaj Chetak EV Expansion", "Skoda-VW India Compact SUV", "MG Windsor & Cloud EV Pro"
    ]
    news_topics = [
        ("Breaking News", "Global Economic Summit Announces Major Trade and Digital Infrastructure Pact"),
        ("World News", "UN Security Council Convenes on International Peace and Climate Action"),
        ("India News", "Central Government Approves New High-Speed Rail and Expressway Corridors"),
        ("Politics", "Parliamentary Committee Reviews Key Digital Governance and Reforms Bill"),
        ("Sports", "BCCI Announces Squad and Schedule for Upcoming International Cricket Series"),
        ("Business", "Indian Unicorn Startups Record Strong Q3 Revenue and Global Expansion"),
        ("Finance & Markets", "Sensex and Nifty Hit Fresh Highs Amid Strong Institutional Inflows"),
        ("Technology", "Next-Generation AI Chips and 6G Trials Accelerate Digital Transformation"),
        ("Education", "Ministry of Education Announces New National Scholarship and Skill Portal"),
        ("Entertainment", "Major Pan-India Blockbuster Releases Set New Box Office Records")
    ]
    for i in range(needed_count):
        uid = random.randint(100, 999)
        if bucket == "india_job":
            org = india_orgs[i % len(india_orgs)]
            title = org + " Recruitment 2026: Apply Online for " + str(random.randint(1500, 15000)) + " Vacancies (" + stamp + " #" + str(uid) + ")"
            items.append(("Jobs & Careers", title, "Official India recruitment notification for " + org, random.choice(JOB_IMAGES), "india_job"))
        elif bucket == "intl_job":
            org = intl_orgs[i % len(intl_orgs)]
            title = org + " Hiring 2026: High-Paying International & Remote Jobs (" + stamp + " #" + str(uid) + ")"
            items.append(("Jobs & Careers", title, "Global career opportunity in " + org, random.choice(JOB_IMAGES), "intl_job"))
        elif bucket == "auto":
            car = auto_topics[i % len(auto_topics)]
            title = car + " 2026 Price, Mileage, Specs & Official Review (" + stamp + " #" + str(uid) + ")"
            items.append(("Auto & EV", title, "Full specifications and launch details of " + car, random.choice(AUTO_IMAGES), "auto"))
        else:
            cat, base_title = news_topics[i % len(news_topics)]
            title = base_title + " (" + stamp + " Report #" + str(uid) + ")"
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
            img = extract_real_image(entry, bucket_type)
            summary = entry.get("summary", "")
            collected.append((category_name, title, summary, img, bucket_type))
    if len(collected) < target_count:
        collected.extend(generate_fallback_items(bucket_type, target_count - len(collected)))
    return collected

def process_single_task(task, index, total):
    category, title, summary, image_url, bucket_type = task
    author_name = random.choice(WORLD_AUTHORS)
    short_id = str(int(time.time()) % 10000) + str(random.randint(10, 99))
    slug = slugify(title) + "-" + short_id

    prompt = (
        "Write a comprehensive 700-word SEO article for the '" + category + "' desk by journalist '" + author_name + "'. "
        "Title: " + title + ". Context: " + str(summary) + ". "
        "Format strictly in raw HTML starting with <h1 class=\"seo-title\">" + title + "</h1> and "
        "<p class=\"intro-text\"><strong>Reported by " + author_name + " | Fast Job Desk:</strong>... "
        "Use 4 <h3 class=\"article-subheading\"> tags, one <table class=\"article-table\">, and end with <p class=\"hashtags\">. "
        "Output raw HTML only without markdown backticks."
    )

    content = generate_content_openai(prompt)
    if not content:
        content = build_rich_fallback_html(title, summary, category, author_name)

    content = content.strip()
    if content.startswith("```html"):
        content = content[7:-3].strip()
    elif content.startswith("```"):
        content = content[3:-3].strip()

    author_meta = '<div class="post-author-meta" data-author="' + author_name + '" style="display:none;"></div>\n'
    data = {
        "title": title,
        "slug": slug,
        "content": author_meta + content,
        "category": category,
        "image_url": image_url
    }
    if supabase_insert_post(data):
        print("SUCCESS [" + str(index) + "/" + str(total) + "] (" + category + "): " + title[:45])
        return True
    return False

def run_100_posts_trigger():
    print("Connecting to Supabase REST API...")
    existing_rows = supabase_get_posts("title", 1000)
    existing_titles = set()
    for row in existing_rows:
        t = (row.get("title") or "")[:40].lower()
        if t:
            existing_titles.add(t)

    india_job_tasks = collect_bucket_tasks(INDIA_JOBS_FEEDS, "Jobs & Careers", 30, "india_job", existing_titles)
    intl_job_tasks = collect_bucket_tasks(INTL_JOBS_FEEDS, "Jobs & Careers", 20, "intl_job", existing_titles)
    auto_tasks = collect_bucket_tasks(AUTO_FEEDS, "Auto & EV", 20, "auto", existing_titles)

    news_tasks = []
    for cat, urls in NEWS_FEEDS_BY_CAT.items():
        news_tasks.extend(collect_bucket_tasks(urls, cat, 3, "news", existing_titles))
    news_tasks = news_tasks[:30]

    all_100_tasks = india_job_tasks + intl_job_tasks + auto_tasks + news_tasks
    random.shuffle(all_100_tasks)

    total_tasks = len(all_100_tasks)
    print("Publishing " + str(total_tasks) + " Posts (30 India Jobs + 20 Intl Jobs + 20 Auto + 30 News)...")

    success_count = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(process_single_task, task, idx + 1, total_tasks)
            for idx, task in enumerate(all_100_tasks)
        ]
        for future in as_completed(futures):
            try:
                if future.result():
                    success_count += 1
            except Exception as e:
                print("Worker e