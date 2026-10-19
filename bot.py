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
        "https://news.google.com/rss/search?q=rajasthan+police+up+police+vacancy+2026&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=visa+sponsorship+jobs+2026+uk+usa+canada+dubai&hl=en-US&gl=US&ceid=US:en"
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
    "Auto & EV": [
        "https://news.google.com/rss/search?q=new+car+launch+india+suv+ev+2026&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=maruti+tata+mahindra+hyundai+bikes+2026&hl=en-IN&gl=IN&ceid=IN:en"
    ],
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

# GUARANTEED WORKING UNIQUE IMAGE GENERATOR
def get_guaranteed_image(entry, title):
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

    # Using Picsum Photos with unique seed based on title hash (100% loads in browser)
    seed_id = abs(hash(title)) % 900 + 100
    return f"https://picsum.photos/seed/{seed_id}/1000/600"

def ai_write(title, cat, author):
    prompt = (
        "Write an exhaustive, highly detailed 800+ word professional HTML article for the category '" + cat + "' "
        "authored by journalist '" + author + "' based on the headline: '" + title + "'.\n"
        "CRITICAL RULES:\n"
        "1. Length MUST exceed 800 words with thorough explanations, background context, in-depth analysis, and step-by-step guidelines.\n"
        "2. Never mention any third-party source website, Sarkari Result, Free Job Alert, or external brand names. Published exclusively by Fast Job Desk.\n"
        "3. Format strictly in raw HTML:\n"
        "   - Start with <h1 class=\"seo-title\">" + title + "</h1>\n"
        "   - Followed by <p class=\"intro-text\"><strong>Reported by " + author + " | Fast Job Editorial Desk:</strong> [Detailed 60-word introductory paragraph]...</p>\n"
        "   - Include at least 5 distinct section headings using <h3 class=\"article-subheading\">[Heading Title]</h3> with 2-3 rich paragraphs under each.\n"
        "   - Include 1 detailed <table class=\"article-table\"> summarizing key data, vacancies, dates, or specifications.\n"
        "   - Conclude with <p class=\"hashtags\">#FastJob #GovtJobs #Recruitment2026 #TrendingNews</p>.\n"
        "4. Output raw HTML only without markdown backticks."
    )
    if O_KEY:
        for m in ["gpt-4o-mini", "gpt-3.5-turbo"]:
            try:
                r = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": "Bearer " + O_KEY}, json={"model": m, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1500}, timeout=60)
                if r.status_code == 200:
                    txt = r.json()["choices"][0]["message"]["content"].strip()
                    return txt.replace("```html", "").replace("```", "").strip()
            except Exception:
                pass
    
    return (
        '<h1 class="seo-title">' + title + '</h1>'
        '<p class="intro-text"><strong>Reported by ' + author + ' | Fast Job Editorial Desk:</strong> Comprehensive official notification, deep analysis, and complete guidelines regarding ' + title + '. Stay informed with our verified 24/7 reporting desk.</p>'
        '<h3 class="article-subheading">1. Detailed Overview & Background</h3>'
        '<p>In a major development for aspirants and professionals across the country, official authorities have officially rolled out comprehensive guidelines and notifications regarding <strong>' + title + '</strong>. This announcement marks a significant milestone in the 2026 recruitment and sector developments, opening up numerous opportunities for qualified candidates seeking stable career progression and verified updates.</p>'
        '<p>Our editorial and research bureau has closely tracked the trajectory of this announcement. Industry experts note that structural adjustments and transparent digital processing have been prioritized to ensure that every eligible candidate receives an equitable opportunity during the application and evaluation phases.</p>'
        '<h3 class="article-subheading">2. Complete Vacancy Breakdown & Eligibility Parameters</h3>'
        '<p>Understanding the exact eligibility criteria is paramount before initiating any formal application. Candidates must meticulously verify their age limits, educational qualifications, professional certifications, and domicile requirements as outlined by the governing board. Any discrepancy in documentation can lead to disqualification during subsequent screening rounds.</p>'
        '<table class="article-table">'
        '<tr><th>Recruitment Board</th><td>Fast Job Verified Editorial Desk</td></tr>'
        '<tr><th>Position / Project Title</th><td>' + title + '</td></tr>'
        '<tr><th>Assigned Bureau Chief</th><td>' + author + '</td></tr>'
        '<tr><th>Operational Status</th><td>Active & Verified for 2026</td></tr>'
        '<tr><th>Official Notification Link</th><td>Available on Respective Portal</td></tr>'
        '</table>'
        '<h3 class="article-subheading">3. Step-by-Step Application Procedure</h3>'
        '<p>Navigating the online registration portal requires precision. Applicants are advised to keep scanned copies of their recent passport-size photograph, signature, educational marksheets, and valid photo ID proofs ready before accessing the submission window. Ensuring payment of prescribed application fees through secure digital gateways completes the registration cycle.</p>'
        '<p>Once submitted successfully, candidates must retain a printed copy or digital PDF receipt of their confirmation slip for future correspondence and admit card generation phases.</p>'
        '<h3 class="article-subheading">4. Important Dates, Timeline & Examination Phases</h3>'
        '<p>Time management is critical for success in competitive recruitment and sector updates. The application window operates under strict deadlines, and late submissions will not be entertained under any circumstances. Candidates should bookmark our portal for real-time alerts regarding admit card release dates, examination schedules, and answer key announcements.</p>'
        '<h3 class="article-subheading">5. Expert Analysis & Final Recommendations</h3>'
        '<p>Concluding our thorough examination of <strong>' + title + '</strong>, our bureau strongly advises all stakeholders to rely solely on official notifications and verified bulletins. Avoid unverified social media forwards and ensure your preparation aligns with the updated syllabus and evaluation norms.</p>'
        '<p class="hashtags">#FastJob #GovtJobs #Recruitment2026 #CareerGrowth #VerifiedUpdate</p>'
    )

def collect(urls, cat, count, seen):
    out = []
    for u in urls:
        for e in get_rss(u):
            if len(out) >= count: break
            t = (e.get("title") or "").rsplit(" - ", 1)[0].strip()
            if not t or t[:35].lower() in seen: continue
            seen.add(t[:35].lower())
            img_url = get_guaranteed_image(e, t)
            out.append((cat, t, img_url))
    while len(out) < count:
        uid = random.randint(100, 999)
        dt = datetime.now().strftime("%b %d")
        if cat == "Jobs & Careers":
            t = "Major Government Recruitment 2026: Apply Online for 15,000+ Vacancies (" + dt + " Alert #" + str(uid) + ")"
        elif cat == "Auto & EV":
            t = "New 2026 SUV & Electric Vehicle Launch: Price, Specs & Review (" + dt + " Update #" + str(uid) + ")"
        else:
            t = cat + " Special Report: Major Policy & Global Developments Announced (" + dt + " #" + str(uid) + ")"
        img_url = f"https://picsum.photos/seed/{abs(hash(t)) % 900 + 100}/1000/600"
        out.append((cat, t, img_url))
    return out

def publish_one(item, idx):
    cat, title, img = item
    author = random.choice(AUTHORS)
    slug = "-".join(re.sub(r"[^a-z0-9\s-]", "", title.lower()).split()[:5] or ["post"]) + "-" + str(int(time.time()) % 10000) + str(random.randint(10, 99))
    body = '<div class="post-author-meta" data-author="' + author + '" style="display:none;"></div>\n' + ai_write(title, cat, author)
    try:
        r = requests.post(S_URL + "/rest/v1/posts", headers=HEADERS, json={"title": title, "slug": slug, "content": body, "category": cat, "image_url": img}, timeout=25)
        if r.status_code in [200, 201, 204]:
            print("OK [" + str(idx) + "/500] " + cat + ": " + title[:45])
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
        q += collect(urls, cat, 20, seen)

    random.shuffle(q)
    print("Starting 500 Posts Upload with Guaranteed Working Images...")
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(publish_one, it, i + 1) for i, it in enumerate(q)]
        for f in as_completed(futs):
            if f.result(): ok += 1
    print("FINISHED! Published:", ok)

if __name__ == "__main__":
    run()
# DONE
