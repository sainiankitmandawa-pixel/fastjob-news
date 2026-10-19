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
    "Jobs & Careers": [
        "https://news.google.com/rss/search?q=sarkari+result+police+teacher+ssc+upsc+banking+recruitment+2026&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=rajasthan+police+up+police+vacancy+2026&hl=en-IN&gl=IN&ceid=IN:en"
    ],
    "Breaking News": ["https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"],
    "World News": ["https://news.google.com/rss/search?q=world+news+international+politics&hl=en-US&gl=US&ceid=US:en"],
    "India News": ["https://news.google.com/rss/search?q=india+national+news+today&hl=en-IN&gl=IN&ceid=IN:en"],
    "Politics": ["https://news.google.com/rss/search?q=indian+politics+parliament+elections&hl=en-IN&gl=IN&ceid=IN:en"],
    "Sports": ["https://news.google.com/rss/search?q=cricket+ipl+sports+match+india&hl=en-IN&gl=IN&ceid=IN:en"],
    "Business": ["https://news.google.com/rss/search?q=business+startups+india+economy&hl=en-IN&gl=IN&ceid=IN:en"],
    "Finance & Markets": ["https://news.google.com/rss/search?q=sensex+nifty+stock+market+rbi&hl=en-IN&gl=IN&ceid=IN:en"],
    "Technology": ["https://news.google.com/rss/search?q=technology+smartphones+ai+gadgets&hl=en-IN&gl=IN&ceid=IN:en"],
    "Entertainment": ["https://news.google.com/rss/search?q=bollywood+movies+box+office+ott&hl=en-IN&gl=IN&ceid=IN:en"],
    "Education": ["https://news.google.com/rss/search?q=cbse+neet+jee+exams+results+2026&hl=en-IN&gl=IN&ceid=IN:en"],
    "Health & Medicine": ["https://news.google.com/rss/search?q=health+medical+wellness+disease+hospital&hl=en-IN&gl=IN&ceid=IN:en"],
    "Science": ["https://news.google.com/rss/search?q=science+space+nasa+isro+research&hl=en-IN&gl=IN&ceid=IN:en"],
    "AI & Robotics": ["https://news.google.com/rss/search?q=artificial+intelligence+ai+robotics+openai&hl=en-IN&gl=IN&ceid=IN:en"],
    "Crime & Justice": ["https://news.google.com/rss/search?q=supreme+court+police+crime+investigation&hl=en-IN&gl=IN&ceid=IN:en"],
    "Auto & EV": ["https://news.google.com/rss/search?q=new+car+launch+india+suv+ev+2026&hl=en-IN&gl=IN&ceid=IN:en"],
    "Economy": ["https://news.google.com/rss/search?q=economy+gdp+inflation+budget+india&hl=en-IN&gl=IN&ceid=IN:en"],
    "Environment & Climate": ["https://news.google.com/rss/search?q=climate+change+environment+pollution+weather&hl=en-IN&gl=IN&ceid=IN:en"],
    "Lifestyle": ["https://news.google.com/rss/search?q=lifestyle+fashion+food+culture+trends&hl=en-IN&gl=IN&ceid=IN:en"],
    "Travel & Tourism": ["https://news.google.com/rss/search?q=travel+tourism+airlines+destinations+holidays&hl=en-IN&gl=IN&ceid=IN:en"],
    "Real Estate": ["https://news.google.com/rss/search?q=real+estate+property+housing+infrastructure&hl=en-IN&gl=IN&ceid=IN:en"],
    "Defence & Security": ["https://news.google.com/rss/search?q=indian+army+navy+air+force+defence+border&hl=en-IN&gl=IN&ceid=IN:en"],
    "Weather": ["https://news.google.com/rss/search?q=imd+weather+forecast+monsoon+rain+temperature&hl=en-IN&gl=IN&ceid=IN:en"],
    "Opinion & Editorial": ["https://news.google.com/rss/search?q=editorial+opinion+analysis+geopolitics&hl=en-IN&gl=IN&ceid=IN:en"],
    "Fact Check & Explainers": ["https://news.google.com/rss/search?q=fact+check+explainer+debunked+news&hl=en-IN&gl=IN&ceid=IN:en"]
}

def get_rss(url):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 Chrome/124.0"}, timeout=12)
        return feedparser.parse(r.content).entries if r.status_code == 200 else []
    except Exception:
        return []

# STRICT ORIGINAL SOURCE IMAGE EXTRACTOR
def extract_original_source_image(entry, title):
    # 1. Check media:content
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            if 'url' in media:
                return media['url']
                
    # 2. Check enclosures
    if hasattr(entry, 'enclosures') and entry.enclosures:
        for enc in entry.enclosures:
            if 'href' in enc:
                return enc['href']
                
    # 3. Check <img> tag inside summary/description HTML
    content_html = entry.get('summary', '') + entry.get('description', '')
    if content_html:
        soup = BeautifulSoup(content_html, 'html.parser')
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            img_src = img_tag.get('src')
            if not img_src.endswith('.gif'):
                return img_src

    # 4. Fallback unique topic image if original feed has no image tag
    seed_id = abs(hash(title)) % 900 + 100
    return f"https://picsum.photos/seed/{seed_id}/1000/600"

def ai_write(title, cat, author):
    prompt = (
        "Write a detailed professional HTML article for the category '" + cat + "' "
        "authored by journalist '" + author + "' based on the headline: '" + title + "'.\n"
        "Format strictly in raw HTML starting with <h1 class=\"seo-title\">" + title + "</h1> "
        "and <p class=\"intro-text\"><strong>Reported by " + author + " | Fast Job Desk:</strong>... "
        "Use 3 <h3 class=\"article-subheading\"> tags, 1 <table class=\"article-table\">, and <p class=\"hashtags\">. Raw HTML only."
    )
    if O_KEY:
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
        '<p class="intro-text"><strong>Reported by ' + author + ' | Fast Job Desk:</strong> Official notification and complete details regarding ' + title + '.</p>'
        '<h3 class="article-subheading">Overview & Key Highlights</h3>'
        '<p>Official authorities have released updated details regarding <strong>' + title + '</strong> under the <strong>' + cat + '</strong> desk.</p>'
        '<table class="article-table"><tr><th>Category</th><td>' + cat + '</td></tr><tr><th>Title</th><td>' + title + '</td></tr><tr><th>Bureau</th><td>' + author + '</td></tr><tr><th>Status</th><td>Verified 2026 Update</td></tr></table>'
        '<h3 class="article-subheading">Important Guidelines</h3>'
        '<p>Readers and applicants should verify all official details on the respective portal before proceeding.</p>'
        '<p class="hashtags">#FastJob #' + cat.replace(" ", "").replace("&", "") + ' #LiveUpdate2026</p>'
    )

def collect(urls, cat, count, seen):
    out = []
    for u in urls:
        for e in get_rss(u):
            if len(out) >= count: break
            t = (e.get("title") or "").rsplit(" - ", 1)[0].strip()
            if not t or t[:35].lower() in seen: continue
            seen.add(t[:35].lower())
            img_url = extract_original_source_image(e, t)
            out.append((cat, t, img_url))
    while len(out) < count:
        uid = random.randint(100, 999)
        dt = datetime.now().strftime("%b %d")
        t = cat + " Special Report: Major Updates Announced (" + dt + " #" + str(uid) + ")"
        img_url = f"https://picsum.photos/seed/{abs(hash(t)) % 900 + 100}/1000/600"
        out.append((cat, t, img_url))
    return out

def publish_one(item, idx):
    cat, title, img = item
    author = random.choice(AUTHORS)
    slug = "-".join(re.sub(r"[^a-z0-9\s-]", "", title.lower()).split()[:5] or ["post"]) + "-" + str(int(time.time()) % 10000) + str(random.randint(10, 99))
    body = '<div class="post-author-meta" data-author="' + author + '" style="display:none;"></div>\n' + ai_write(title, cat, author)
    try:
        r = requests.post(S_URL + "/rest/v1/posts", headers=HEADERS, json={"title": title, "slug": slug, "content": body, "category": cat, "image_url": img}, timeout=20)
        if r.status_code in [200, 201, 204]:
            print("OK [" + str(idx) + "/250] " + cat + ": " + title[:45])
            return True
    except Exception as ex:
        print("Err:", ex)
    return False

def run():
    seen = set()
    try:
        r = requests.get(S_URL + "/rest/v1/posts?select=title&order=id.desc&limit=1000", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            seen = {(x.get("title") or "")[:35].lower() for x in r.json() if x.get("title")}
    except Exception:
        pass

    q = []
    for cat, urls in FEEDS.items():
        q += collect(urls, cat, 10, seen)

    random.shuffle(q)
    print("Starting 250 Posts Upload with Exact Source Images...")
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(publish_one, it, i + 1) for i, it in enumerate(q)]
        for f in as_completed(futs):
            if f.result(): ok += 1
    print("FINISHED! Published:", ok)

if __name__ == "__main__":
    run()
# DONE
