import feedparser, re, random, time, os, requests
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

S_URL = "https://wioheljpjdcprozqumpv.supabase.co"
S_KEY = (os.environ.get("SUPABASE_KEY") or "").strip() or "sb_publishable_d_ROr-nG6RpIRlVWtIE-Fg_sciaLZXR"
O_KEY = (os.environ.get("OPENAI_API_KEY") or "").strip()
HEADERS = {"apikey": S_KEY, "Authorization": "Bearer " + S_KEY, "Content-Type": "application/json", "Prefer": "return=minimal"}

AUTHORS = [
    "Aarav Sharma (New Delhi)", "Priya Nair (Mumbai)", "Vikramaditya Rathore (India Desk)", "Ananya Chatterjee (Kolkata)",
    "Rohan Deshmukh (Pune)", "Siddharth Menon (Bengaluru)", "Kavita Iyer (Chennai)", "Kabir Malhotra (North India)",
    "Zoya Khan (Hyderabad)", "Devansh Joshi (Ahmedabad)", "Niharika Verma (Lucknow)", "Arjun Kapoor (South Asia)",
    "Ethan Brooks (New York)", "Madison Carter (Washington DC)", "Lucas Bennett (Silicon Valley)", "Olivia Hayes (Chicago)",
    "Noah Mitchell (Los Angeles)", "Chloe Sullivan (Boston)", "Mason Rivera (Miami)", "Harper Reed (Toronto)",
    "Logan Foster (Seattle)", "Sophia Jenkins (Houston)", "Oliver Sterling (London)", "Amelia Clarke (UK Bureau)",
    "Liam O'Connor (Dublin)", "Camille Laurent (Paris)", "Lukas Weber (Frankfurt)", "Elena Rostova (Geneva)",
    "Matteo Rossi (Milan)", "Sofia Lindqvist (Stockholm)", "Hugo Martinez (Madrid)", "Freya Van Der Berg (Amsterdam)",
    "Tariq Al-Mansoor (Dubai)", "Layla Haddad (Doha)", "Omar Farooq (Riyadh)", "Nadia El-Masri (Cairo)",
    "Kwame Mensah (Accra)", "Amara Okafor (Lagos)", "Zanele Khumalo (Johannesburg)", "Youssef Benali (Casablanca)",
    "Kenji Takahashi (Tokyo)", "Mei-Ling Tan (Singapore)", "Min-Jae Park (Seoul)", "Liam Thornton (Sydney)",
    "Isla MacLeod (Melbourne)", "Hiroshi Sato (Osaka)", "Mateo Silva (Sao Paulo)", "Valentina Gomez (Buenos Aires)",
    "Diego Hernandez (Mexico City)", "Camila Vargas (Santiago)"
]

# PREMIUM INDIA & INTERNATIONAL JOB SOURCES (Sarkari Results & Global Portals)
FEEDS = {
    "in_job": [
        "https://news.google.com/rss/search?q=sarkari+result+latest+jobs+recruitment+2026+apply+online&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=free+job+alert+government+vacancy+upsc+ssc+banking+2026&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=railway+rrb+police+teacher+defence+bharti+2026+notification&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=india+post+gds+state+psc+police+recruitment+2026&hl=en-IN&gl=IN&ceid=IN:en"
    ],
    "int_job": [
        "https://news.google.com/rss/search?q=visa+sponsorship+jobs+2026+uk+usa+canada+europe+dubai+hiring&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=remote+jobs+hiring+worldwide+2026+software+finance+healthcare&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=global+careers+abroad+employment+opportunities+2026&hl=en-US&gl=US&ceid=US:en"
    ],
    "auto": [
        "https://news.google.com/rss/search?q=new+car+launch+india+suv+ev+2026&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=maruti+tata+mahindra+hyundai+royal+enfield+2026&hl=en-IN&gl=IN&ceid=IN:en"
    ],
    "news": [
        ("Breaking News", "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"),
        ("World News", "https://news.google.com/rss/search?q=world+news+international&hl=en-US&gl=US&ceid=US:en"),
        ("India News", "https://news.google.com/rss/search?q=india+national+news+today&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Politics", "https://news.google.com/rss/search?q=indian+politics+parliament&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Sports", "https://news.google.com/rss/search?q=cricket+ipl+sports+india&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Business", "https://news.google.com/rss/search?q=business+startups+india+economy&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Finance & Markets", "https://news.google.com/rss/search?q=sensex+nifty+stock+market+rbi&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Technology", "https://news.google.com/rss/search?q=technology+smartphones+ai+news&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Education", "https://news.google.com/rss/search?q=cbse+neet+jee+exams+2026&hl=en-IN&gl=IN&ceid=IN:en"),
        ("Entertainment", "https://news.google.com/rss/search?q=bollywood+movies+box+office&hl=en-IN&gl=IN&ceid=IN:en")
    ]
}

IMGS = {
    "job": ["https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=1000&q=80", "https://images.unsplash.com/photo-1521791136064-7986c2920216?w=1000&q=80"],
    "auto": ["https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=1000&q=80", "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=1000&q=80"],
    "news": ["https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=1000&q=80", "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=1000&q=80"]
}

def get_rss(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 Chrome/124.0"}, timeout=12)
        return feedparser.parse(r.content).entries if r.status_code == 200 else []
    except Exception:
        return []

def ai_write(title, cat, author):
    # Strict rule: Never mention source websites, only original Fast Job reporting
    prompt = (
        "Write a 700-word professional HTML career/news article for " + cat + " by journalist " + author + " on: " + title + ". "
        "CRITICAL RULE: Never mention any third-party source website, Sarkari Result, Free Job Alert, or external brand names. "
        "The article must look completely independent and published exclusively by Fast Job Desk. "
        "Start with <h1 class=\"seo-title\">" + title + "</h1> and <p class=\"intro-text\"><strong>Reported by " + author + " | Fast Job Recruitment Desk:</strong>... "
        "Use 3 <h3 class=\"article-subheading\"> tags, 1 <table class=\"article-table\"> summarizing vacancies/details, and <p class=\"hashtags\">#FastJob #SarkariNaukri #GovtJobs</p>. Raw HTML only."
    )
    if O_KEY:
        for m in ["gpt-4o-mini", "gpt-3.5-turbo"]:
            try:
                r = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": "Bearer " + O_KEY}, json={"model": m, "messages": [{"role": "user", "content": prompt}]}, timeout=45)
                if r.status_code == 200:
                    txt = r.json()["choices"][0]["message"]["content"].strip()
                    return txt.replace("```html", "").replace("```", "").strip()
            except Exception:
                pass
    return (
        '<h1 class="seo-title">' + title + '</h1>'
        '<p class="intro-text"><strong>Reported by ' + author + ' | Fast Job Recruitment Desk:</strong> Official notification and complete vacancy details regarding ' + title + '.</p>'
        '<h3 class="article-subheading">Vacancy Overview & Key Highlights</h3>'
        '<p>The official recruitment board has announced new career opportunities under the <strong>' + cat + '</strong> category for <strong>' + title + '</strong>. Eligible candidates can review the official parameters below.</p>'
        '<table class="article-table"><tr><th>Recruitment Board</th><td>Fast Job Verified Desk</td></tr><tr><th>Position Title</th><td>' + title + '</td></tr><tr><th>Reporting Editor</th><td>' + author + '</td></tr><tr><th>Session</th><td>2026 Active Vacancy</td></tr></table>'
        '<h3 class="article-subheading">Eligibility Criteria & Important Dates</h3>'
        '<p>Applicants must check all educational qualifications, age relaxation norms, and application deadlines before submitting their forms on the official portal.</p>'
        '<p class="hashtags">#FastJob #GovtJobs #Recruitment2026 #JobAlerts</p>'
    )

def collect(urls, cat, count, kind, seen):
    out = []
    for u in urls:
        for e in get_rss(u):
            if len(out) >= count: break
            t = (e.get("title") or "").rsplit(" - ", 1)[0].strip()
            if not t or t[:35].lower() in seen: continue
            seen.add(t[:35].lower())
            out.append((cat, t, random.choice(IMGS[kind])))
    while len(out) < count:
        uid = random.randint(100, 999)
        dt = datetime.now().strftime("%b %d")
        if kind == "job":
            t = "Latest Recruitment 2026: Apply Online for Major Vacancies (" + dt + " Alert #" + str(uid) + ")"
        elif kind == "auto":
            t = "New 2026 SUV & EV Launch: Price, Specs & Official Review (" + dt + " Update #" + str(uid) + ")"
        else:
            t = cat + " Special Report: Major Developments Announced (" + dt + " #" + str(uid) + ")"
        out.append((cat, t, random.choice(IMGS[kind])))
    return out

def publish_one(item, idx):
    cat, title, img = item
    author = random.choice(AUTHORS)
    slug = "-".join(re.sub(r"[^a-z0-9\s-]", "", title.lower()).split()[:5] or ["post"]) + "-" + str(int(time.time()) % 10000) + str(random.randint(10, 99))
    body = '<div class="post-author-meta" data-author="' + author + '" style="display:none;"></div>\n' + ai_write(title, cat, author)
    try:
        r = requests.post(S_URL + "/rest/v1/posts", headers=HEADERS, json={"title": title, "slug": slug, "content": body, "category": cat, "image_url": img}, timeout=20)
        if r.status_code in [200, 201, 204]:
            print("OK [" + str(idx) + "/100] " + cat + ": " + title[:45])
            return True
    except Exception as ex:
        print("Err:", ex)
    return False

def run():
    seen = set()
    try:
        r = requests.get(S_URL + "/rest/v1/posts?select=title&order=id.desc&limit=800", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            seen = {(x.get("title") or "")[:35].lower() for x in r.json() if x.get("title")}
    except Exception:
        pass

    q = []
    q += collect(FEEDS["in_job"], "Jobs & Careers", 30, "job", seen)
    q += collect(FEEDS["int_job"], "Jobs & Careers", 20, "job", seen)
    q += collect(FEEDS["auto"], "Auto & EV", 20, "auto", seen)
    for c, u in FEEDS["news"]:
        q += collect([u], c, 3, "news", seen)

    random.shuffle(q)
    print("Starting 100 Posts Upload...")
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(publish_one, it, i + 1) for i, it in enumerate(q[:100])]
        for f in as_completed(futs):
            if f.result(): ok += 1
    print("FINISHED! Published:", ok)

if __name__ == "__main__":
    run()
# DONE
