import feedparser, re, random, time, os, requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

S_URL = "https://wioheljpjdcprozqumpv.supabase.co"
S_KEY = (os.environ.get("SUPABASE_KEY") or "").strip() or "sb_publishable_d_ROr-nG6RpIRlVWtIE-Fg_sciaLZXR"
O_KEY = (os.environ.get("OPENAI_API_KEY") or "").strip()
HEADERS = {"apikey": S_KEY, "Authorization": "Bearer " + S_KEY, "Content-Type": "application/json", "Prefer": "return=minimal"}
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"}

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

# DIRECT PUBLISHER & BING FEEDS THAT CONTAIN REAL ARTICLE IMAGES & LINKS
FEEDS = {
    "Jobs & Careers": [
        "https://www.news18.com/commonfeeds/v1/eng/rss/education-career.xml",
        "https://indianexpress.com/section/jobs/feed/",
        "https://timesofindia.indiatimes.com/rssfeeds/3012544.cms",
        "https://www.thehindu.com/education/careers/feeder/default.rss",
        "https://economictimes.indiatimes.com/jobs/rssfeeds/107115.cms",
        "https://www.bing.com/news/search?q=sarkari+recruitment+vacancy+apply+online+2026&format=rss",
        "https://www.bing.com/news/search?q=upsc+ssc+railway+bank+police+recruitment+2026&format=rss",
        "https://www.bing.com/news/search?q=visa+sponsorship+remote+jobs+hiring+2026&format=rss"
    ],
    "Breaking News": ["https://feeds.feedburner.com/ndtvnews-top-stories", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "https://www.indiatoday.in/rss/home"],
    "World News": ["http://feeds.bbci.co.uk/news/world/rss.xml", "https://www.news18.com/commonfeeds/v1/eng/rss/world.xml", "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms"],
    "India News": ["https://www.news18.com/commonfeeds/v1/eng/rss/india.xml", "https://www.thehindu.com/news/national/feeder/default.rss", "https://indianexpress.com/section/india/feed/"],
    "Politics": ["https://www.news18.com/commonfeeds/v1/eng/rss/politics.xml", "https://indianexpress.com/section/political-pulse/feed/"],
    "Sports": ["https://www.news18.com/commonfeeds/v1/eng/rss/sports.xml", "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms", "https://indianexpress.com/section/sports/feed/"],
    "Business": ["https://www.news18.com/commonfeeds/v1/eng/rss/business.xml", "https://economictimes.indiatimes.com/news/company/rssfeeds/2146842.cms"],
    "Finance & Markets": ["https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "https://www.livemint.com/rss/markets"],
    "Technology": ["https://www.news18.com/commonfeeds/v1/eng/rss/tech.xml", "https://www.livemint.com/rss/technology", "https://techcrunch.com/feed/"],
    "Entertainment": ["https://www.news18.com/commonfeeds/v1/eng/rss/movies.xml", "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms"],
    "Education": ["https://indianexpress.com/section/education/feed/", "https://www.thehindu.com/education/feeder/default.rss"],
    "Health & Medicine": ["https://timesofindia.indiatimes.com/rssfeeds/3908999.cms", "https://indianexpress.com/section/lifestyle/health/feed/"],
    "Science": ["https://www.thehindu.com/sci-tech/science/feeder/default.rss", "https://www.livemint.com/rss/science"],
    "AI & Robotics": ["https://www.bing.com/news/search?q=artificial+intelligence+openai+robotics+2026&format=rss", "https://economictimes.indiatimes.com/tech/technology/rssfeeds/78570561.cms"],
    "Crime & Justice": ["https://www.bing.com/news/search?q=supreme+court+high+court+police+investigation+india&format=rss", "https://indianexpress.com/section/cities/feed/"],
    "Auto & EV": ["https://www.news18.com/commonfeeds/v1/eng/rss/auto.xml", "https://timesofindia.indiatimes.com/rssfeeds/74317216.cms", "https://www.cartoq.com/feed/"],
    "Economy": ["https://economictimes.indiatimes.com/news/economy/rssfeeds/1377380.cms", "https://www.thehindu.com/business/Economy/feeder/default.rss"],
    "Environment & Climate": ["https://timesofindia.indiatimes.com/rssfeeds/2647163.cms", "https://www.thehindu.com/sci-tech/energy-and-environment/feeder/default.rss"],
    "Lifestyle": ["https://www.news18.com/commonfeeds/v1/eng/rss/lifestyle-2.xml", "https://timesofindia.indiatimes.com/rssfeeds/2886704.cms"],
    "Travel & Tourism": ["https://timesofindia.indiatimes.com/rssfeeds/3112014.cms", "https://indianexpress.com/section/lifestyle/destination-of-the-week/feed/"],
    "Real Estate": ["https://economictimes.indiatimes.com/wealth/real-estate/rssfeeds/48997585.cms", "https://www.bing.com/news/search?q=real+estate+property+housing+india&format=rss"],
    "Defence & Security": ["https://economictimes.indiatimes.com/news/defence/rssfeeds/47117033.cms", "https://www.bing.com/news/search?q=indian+army+navy+air+force+drdo+defence&format=rss"],
    "Weather": ["https://www.bing.com/news/search?q=imd+weather+forecast+rain+monsoon+india&format=rss"],
    "Opinion & Editorial": ["https://www.thehindu.com/opinion/editorial/feeder/default.rss", "https://indianexpress.com/section/opinion/feed/"],
    "Fact Check & Explainers": ["https://www.indiatoday.in/rss/fact-check", "https://indianexpress.com/section/explained/feed/"]
}

def is_valid_real_img(u):
    if not u or not isinstance(u, str) or not u.startswith("http"): return False
    bad = ["google", "gstatic", "googleusercontent", "picsum", "unsplash", "logo", "icon", "avatar", "1x1", "blank", "pixel", ".svg", ".gif"]
    return not any(b in u.lower() for b in bad)

def extract_real_source_image(entry):
    # 1. Check RSS media_content / media_thumbnail / enclosures
    for attr in ["media_content", "media_thumbnail"]:
        if hasattr(entry, attr) and getattr(entry, attr):
            for m in getattr(entry, attr):
                u = m.get("url") or ""
                if is_valid_real_img(u): return u
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            u = enc.get("href") or enc.get("url") or ""
            if is_valid_real_img(u): return u
    # 2. Check HTML img inside summary/description
    html_part = (entry.get("summary") or "") + (entry.get("description") or "")
    if html_part:
        soup = BeautifulSoup(html_part, "html.parser")
        img = soup.find("img")
        if img and is_valid_real_img(img.get("src")): return img.get("src")
    # 3. Scrape exact og:image / twitter:image from the real source webpage!
    link = entry.get("link") or ""
    if "bing.com/news/apiclick" in link and "url=" in link:
        qs = parse_qs(urlparse(link).query)
        if "url" in qs and qs["url"]: link = unquote(qs["url"][0])
    if link.startswith("http") and "news.google.com" not in link:
        try:
            r = requests.get(link, headers=UA, timeout=8)
            if r.status_code == 200:
                sp = BeautifulSoup(r.text, "html.parser")
                for prop in ["og:image", "twitter:image", "og:image:secure_url"]:
                    tag = sp.find("meta", property=prop) or sp.find("meta", attrs={"name": prop})
                    if tag and is_valid_real_img(tag.get("content")):
                        return tag.get("content").strip()
        except Exception:
            pass
    # Return None if NO real image exists so we SKIP this post!
    return None

def build_800w_full_seo_html(title, summary, cat, author):
    clean_sum = BeautifulSoup(summary or title, "html.parser").get_text().strip()
    if len(clean_sum) < 40: clean_sum = title + " official update and comprehensive report."
    prompt = (
        "Write a 900+ word Full-SEO HTML article for '" + cat + "' by journalist '" + author + "' on: '" + title + "'. Context: " + clean_sum + ". "
        "CRITICAL RULES: 1. Must be 850-1000 words. 2. Never mention any third-party website name. 3. Start with <h1 class=\"seo-title\">" + title + "</h1> and <p class=\"intro-text\"><strong>Reported by " + author + " | Fast Job Editorial Desk:</strong>... "
        "4. Include 6 <h3 class=\"article-subheading\"> headings (with 2-3 long paragraphs each), 1 <table class=\"article-table\">, bullet points <ul><li>, 4 SEO FAQs, and <p class=\"hashtags\">. Raw HTML only."
    )
    ai_html = ""
    if O_KEY:
        for m in ["gpt-4o-mini", "gpt-3.5-turbo"]:
            try:
                r = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": "Bearer " + O_KEY}, json={"model": m, "messages": [{"role": "user", "content": prompt}], "max_tokens": 2200}, timeout=55)
                if r.status_code == 200:
                    ai_html = r.json()["choices"][0]["message"]["content"].replace("```html", "").replace("```", "").strip()
                    break
            except Exception:
                pass
    words = len(BeautifulSoup(ai_html, "html.parser").get_text().split()) if ai_html else 0
    if words >= 780:
        return ai_html

    # Guaranteed 850+ Words Full-SEO Article Builder (Used or Appended so EVERY post is 800+ words!)
    seo_block = (
        '<h1 class="seo-title">' + title + '</h1>'
        '<p class="intro-text"><strong>Reported by ' + author + ' | Fast Job Global SEO Desk:</strong> ' + clean_sum + ' Read this comprehensive, fact-checked 2026 special report covering official notifications, key highlights, eligibility parameters, timeline, and expert analysis.</p>'
        '<h3 class="article-subheading">1. Executive Summary & Breaking Developments</h3>'
        '<p>In a landmark development under the <strong>' + cat + '</strong> vertical, official authorities and industry stakeholders have formally released comprehensive details concerning <strong>' + title + '</strong>. Across the national and international landscape in 2026, this update has garnered massive attention from citizens, professionals, job aspirants, and policy analysts alike. According to verified official briefings, the primary objective behind this initiative is to streamline operational transparency, expand accessibility, and establish a modern digital framework that benefits millions of stakeholders directly.</p>'
        '<p>Preliminary assessments from our editorial bureau indicate that <strong>' + title + '</strong> will serve as a major catalyst in shaping upcoming quarterly benchmarks. Whether you are tracking this announcement for career advancement, regulatory compliance, or market awareness, understanding the complete end-to-end specifications is essential before taking action.</p>'
        '<h3 class="article-subheading">2. Official Overview & Key Highlights Table</h3>'
        '<p>To help our readers quickly verify the core parameters of <strong>' + title + '</strong>, our research desk has compiled a structured specification and overview table below based on the latest verified data released in 2026:</p>'
        '<table class="article-table">'
        '<tr><th>Parameter / Metric</th><th>Official Verified Details (2026)</th></tr>'
        '<tr><th>Headline / Notification</th><td>' + title + '</td></tr>'
        '<tr><th>Primary Category Desk</th><td>' + cat + '</td></tr>'
        '<tr><th>Editorial Correspondent</th><td>' + author + '</td></tr>'
        '<tr><th>Current Status</th><td>Officially Active & Verified</td></tr>'
        '<tr><th>Application / Access Mode</th><td>100% Online Digital Portal</td></tr>'
        '<tr><th>Target Audience & Scope</th><td>National & Global Stakeholders (2026 Cycle)</td></tr>'
        '</table>'
        '<h3 class="article-subheading">3. In-Depth Analysis, Eligibility & Core Requirements</h3>'
        '<p>A closer inspection of the official guidelines surrounding <strong>' + title + '</strong> reveals several critical benchmarks that participants and readers must keep in mind. In the context of recruitment drives, policy rollouts, and industry launches, authorities have mandated strict adherence to documentation and verification standards. Applicants and stakeholders must ensure that their educational credentials, identity records, age criteria, and technical specifications align accurately with the prescribed norms.</p>'
        '<ul>'
        '<li><strong>Document Verification Standards:</strong> All submitted records, certificates, and digital forms must be authentic and cross-verified before the final deadline.</li>'
        '<li><strong>Digital Compliance & Security:</strong> The 2026 portal infrastructure uses real-time verification protocols to prevent duplicate entries and ensure fair processing.</li>'
        '<li><strong>Regional & Global Impact:</strong> Experts project a substantial surge in participation and sector growth following the implementation of these updated provisions.</li>'
        '<li><strong>Timely Action Required:</strong> Stakeholders are strongly encouraged to complete all necessary formalities well ahead of the closing window to avoid last-minute server congestion.</li>'
        '</ul>'
        '<h3 class="article-subheading">4. Step-by-Step Procedure & Implementation Guide</h3>'
        '<p>For candidates, consumers, and professionals looking to act on <strong>' + title + '</strong>, following a systematic approach guarantees a smooth experience. First, review the complete official notification and confirm every eligibility or technical parameter listed in the bulletin. Second, gather all required digital documents, photographs, signatures, and supporting proofs in the specified file formats. Third, complete the online registration or verification workflow carefully, double-checking every field before final submission.</p>'
        '<p>Furthermore, retaining a digital PDF copy and reference number of your submission is highly recommended for future tracking, admit card downloads, status checks, or official correspondence throughout the 2026 session.</p>'
        '<h3 class="article-subheading">5. Expert Outlook & Sector Impact in 2026</h3>'
        '<p>Senior analysts and subject-matter specialists tracking the <strong>' + cat + '</strong> sector emphasize that <strong>' + title + '</strong> reflects a broader transformation toward efficiency and accountability. Over the coming months, follow-up notifications, phase-two schedules, and supplementary guidelines are expected to be announced. Our 50+ global correspondents will continue monitoring every official press release to bring you instant, verified updates without delay.</p>'
        '<h3 class="article-subheading">6. Frequently Asked Questions (SEO FAQs)</h3>'
        '<p><strong>Q1: What is the latest official update regarding ' + title + '?</strong><br>Ans: Official authorities have released the latest 2026 update and guidelines for ' + title + ' under the ' + cat + ' section, confirming active status and key compliance parameters for all stakeholders.</p>'
        '<p><strong>Q2: Who is eligible or impacted by this announcement?</strong><br>Ans: All eligible candidates, citizens, and sector professionals who meet the prescribed 2026 criteria and documentation standards outlined in the official notification can participate and benefit.</p>'
        '<p><strong>Q3: How can I check official updates and complete the online process?</strong><br>Ans: You can complete the process online through the respective official portal by verifying your details, uploading required documents, and saving the confirmation receipt, while following Fast Job for real-time alerts.</p>'
        '<p><strong>Q4: Why is this 2026 update considered important by experts?</strong><br>Ans: Analysts highlight that this development introduces transparent digital processing, expanded opportunities, and significant long-term benefits across the ' + cat + ' landscape.</p>'
        '<p class="hashtags">#FastJob #' + cat.replace(" ", "").replace("&", "") + ' #BreakingNews2026 #VerifiedUpdate #LatestNotification #GlobalCoverage</p>'
    )
    return (ai_html + "\n" + seo_block) if ai_html else seo_block

def collect_real_image_posts(urls, cat, target_count, seen):
    out = []
    for u in urls:
        if len(out) >= target_count: break
        try:
            r = requests.get(u, headers=UA, timeout=12)
            entries = feedparser.parse(r.content).entries if r.status_code == 200 else []
        except Exception:
            entries = []
        for e in entries:
            if len(out) >= target_count: break
            t = (e.get("title") or "").rsplit(" - ", 1)[0].strip()
            if not t or len(t) < 15 or t[:35].lower() in seen: continue
            # STRICT CHECK: Only take post if it has a 100% REAL source image! Otherwise SKIP!
            real_img = extract_real_source_image(e)
            if not real_img:
                continue
            seen.add(t[:35].lower())
            out.append((cat, t, e.get("summary") or "", real_img))
    return out

def publish_one(item, idx, total):
    cat, title, summary, img = item
    author = random.choice(AUTHORS)
    slug = "-".join(re.sub(r"[^a-z0-9\s-]", "", title.lower()).split()[:6] or ["post"]) + "-" + str(int(time.time()) % 10000) + str(random.randint(10, 99))
    body = '<div class="post-author-meta" data-author="' + author + '" style="display:none;"></div>\n' + build_800w_full_seo_html(title, summary, cat, author)
    try:
        r = requests.post(S_URL + "/rest/v1/posts", headers=HEADERS, json={"title": title, "slug": slug, "content": body, "category": cat, "image_url": img}, timeout=25)
        if r.status_code in [200, 201, 204]:
            print("OK [" + str(idx) + "/" + str(total) + "] " + cat + " (800+ Words & Real Image): " + title[:45])
            return True
    except Exception as ex:
        print("Err:", ex)
    return False

def run():
    # Clean up old broken picsum test posts so only real posts shine
    try:
        requests.delete(S_URL + "/rest/v1/posts?image_url=like.*picsum.photos*", headers=HEADERS, timeout=15)
        requests.delete(S_URL + "/rest/v1/posts?image_url=like.*source.unsplash.com*", headers=HEADERS, timeout=15)
        requests.delete(S_URL + "/rest/v1/posts?image_url=like.*photo-150000*", headers=HEADERS, timeout=15)
    except Exception:
        pass

    seen = set()
    try:
        r = requests.get(S_URL + "/rest/v1/posts?select=title&order=id.desc&limit=1000", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            seen = {(x.get("title") or "")[:35].lower() for x in r.json() if x.get("title")}
    except Exception:
        pass

    q = []
    # Jobs & Careers gets 25 posts, other categories get 10 real-image posts each
    for cat, urls in FEEDS.items():
        target = 25 if cat == "Jobs & Careers" else 10
        items = collect_real_image_posts(urls, cat, target, seen)
        print("Collected " + str(len(items)) + " REAL-IMAGE posts for " + cat)
        q.extend(items)

    print("Uploading " + str(len(q)) + " Verified Real-Image 800+ Word SEO Posts...")
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(publish_one, it, i + 1, len(q)) for i, it in enumerate(q)]
        for f in as_completed(futs):
            if f.result(): ok += 1
    print("FINISHED! Successfully Published:", ok)

if __name__ == "__main__":
    run()
# DONE
