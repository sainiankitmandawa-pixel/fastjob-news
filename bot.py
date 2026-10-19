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

FEEDS = {
    "in_job": [
        "https://news.google.com/rss/search?q=sarkari+naukri+recruitment+2026+india&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=ssc+upsc+railway+ibps+bank+vacancy+2026&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=police+teacher+psc+govt+jobs+2026+india&hl=en-IN&gl=IN&ceid=IN:en"
    ],
    "int_job": [
        "https://news.google.com/rss/search?q=remote+jobs+hiring+2026+worldwide&hl=en-US&gl=US&ceid=US:en",
        "https://news.google.com/rss/search?q=visa+sponsorship+jobs+2026+uk+canada+usa+dubai&hl=en-US&gl=US&ceid=US:en"
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
    if O_KEY:
        prompt = "Write a 650-word HTML news/recruitment article for " + cat + " by " + author + " on: " + title + ". Start with <h1 class=\"seo-title\">" + title + "</h1> and <p class=\"intro-text\"><strong>Reported by " + author + ":</strong>... Use 3 <h3 class=\"article-subheading\">, 1 <table class=\"article-table\">, and <p class=\"hashtags\">. Raw HTML only."
        for m in ["gpt-4o-mini", "gpt-3.5-turbo"]:
            try:
                r = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": "Bearer " + O_KEY}, json={"model": m, "messages": [{"role": "user", "content": prompt}]}, timeout=40)
                if r.status_code == 200:
                    txt = r.json()["choices"][0]["message"]["content"].strip()
                    return txt.replace("```html", "").replace("```", "").strip()
            except Exception:
                pass
    return (
        '<h1 class="seo-title">' + title + '</h1>'
        '<p class="intro-text"><strong>Reported by ' + author + ' | Fast Job Desk:</strong> Official live update and complete details regarding ' + title + '.</p>'
        '<h3 class="article-subheading">Official Notification & Key Highlights</h3>'
        '<p>The <strong>' + cat + '</strong> desk has released verified updates on <strong>' + title + '</strong>. Applicants and readers are advised to check the key parameters in the table below.</p>'
        '<table class="article-table"><tr><th>Category</th><td>' + cat + '</td></tr><tr><th>Title</th><td>' + title + '</td></tr><tr><th>Bureau</th><td>' + author + '</td></tr><tr><th>Year</th><td>2026 Live Update</td></tr></table>'
        '<h3 class="article-subheading">Important Guidelines & Next Steps</h3>'
        '<p>Candidates and readers should verify all official dates, eligibility criteria, and documentation on the official portal before applying.</p>'
        '<p class="hashtags">#FastJob #' + cat.replace(" ", "").replace("&", "") + ' #LiveUpdate2026</p>'
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
            t = cat + " Recruitment 2026: Apply Online for Latest Vacancies (" + dt + " Alert #" + str(uid) + ")"
        elif kind == "auto":
            t = "New 2026 SUV & EV Launch: Price, Mileage, Specs & Review (" + dt + " Update #" + str(uid) + ")"
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
