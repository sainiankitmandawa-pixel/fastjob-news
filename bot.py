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

CATEGORIES = [
    "Jobs & Careers", "Rashifal & Horoscopes", "Web Stories", "Breaking News", "World News", "India News", 
    "Politics", "Sports", "Business", "Finance & Markets", "Technology", "Entertainment", 
    "Education", "Health & Medicine", "Science", "AI & Robotics", "Crime & Justice", 
    "Auto & EV", "Economy", "Environment & Climate", "Lifestyle", "Travel & Tourism", 
    "Real Estate", "Defence & Security", "Weather", "Opinion & Editorial", "Fact Check & Explainers"
]

FEEDS_MAP = {
    "Jobs & Careers": [
        "https://www.news18.com/commonfeeds/v1/eng/rss/education-career.xml",
        "https://indianexpress.com/section/jobs/feed/",
        "https://timesofindia.indiatimes.com/rssfeeds/3012544.cms",
        "https://economictimes.indiatimes.com/jobs/rssfeeds/107115.cms",
        "https://www.bing.com/news/search?q=sarkari+recruitment+vacancy+apply+online+2026&format=rss",
        "https://www.bing.com/news/search?q=upsc+ssc+railway+ibps+bank+police+recruitment+2026&format=rss"
    ],
    "Rashifal & Horoscopes": ["https://www.bing.com/news/search?q=daily+horoscope+astrology+rashifal+today+2026&format=rss"],
    "Web Stories": ["https://www.bing.com/news/search?q=trending+visual+stories+news+2026&format=rss"],
    "Breaking News": ["https://feeds.feedburner.com/ndtvnews-top-stories", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "https://www.bing.com/news/search?q=breaking+news+world+india+today&format=rss"],
    "World News": ["http://feeds.bbci.co.uk/news/world/rss.xml", "https://www.theguardian.com/world/rss", "https://www.aljazeera.com/xml/rss/all.xml"],
    "India News": ["https://www.news18.com/commonfeeds/v1/eng/rss/india.xml", "https://indianexpress.com/section/india/feed/"],
    "Politics": ["https://www.news18.com/commonfeeds/v1/eng/rss/politics.xml", "https://indianexpress.com/section/political-pulse/feed/"],
    "Sports": ["https://www.news18.com/commonfeeds/v1/eng/rss/sports.xml", "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms"],
    "Business": ["https://www.news18.com/commonfeeds/v1/eng/rss/business.xml", "https://economictimes.indiatimes.com/news/company/rssfeeds/2146842.cms"],
    "Finance & Markets": ["https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms", "https://www.livemint.com/rss/markets"],
    "Technology": ["https://techcrunch.com/feed/", "https://www.theverge.com/rss/index.xml", "https://www.news18.com/commonfeeds/v1/eng/rss/tech.xml"],
    "Entertainment": ["https://www.news18.com/commonfeeds/v1/eng/rss/movies.xml", "https://timesofindia.indiatimes.com/rssfeeds/1081479906.cms"],
    "Education": ["https://indianexpress.com/section/education/feed/", "https://www.theguardian.com/education/rss"],
    "Health & Medicine": ["https://timesofindia.indiatimes.com/rssfeeds/3908999.cms", "http://feeds.bbci.co.uk/news/health/rss.xml"],
    "Science": ["https://www.space.com/feeds/all", "https://www.sciencedaily.com/rss/all.xml"],
    "AI & Robotics": ["https://economictimes.indiatimes.com/tech/technology/rssfeeds/78570561.cms", "https://www.bing.com/news/search?q=artificial+intelligence+openai+chatgpt+2026&format=rss"],
    "Crime & Justice": ["https://indianexpress.com/section/cities/feed/", "https://www.bing.com/news/search?q=supreme+court+police+investigation+india&format=rss"],
    "Auto & EV": ["https://www.news18.com/commonfeeds/v1/eng/rss/auto.xml", "https://timesofindia.indiatimes.com/rssfeeds/74317216.cms", "https://www.cartoq.com/feed/"],
    "Economy": ["https://economictimes.indiatimes.com/news/economy/rssfeeds/1377380.cms", "https://www.cnbc.com/id/20910258/device/rss/rss.html"],
    "Environment & Climate": ["https://timesofindia.indiatimes.com/rssfeeds/2647163.cms", "https://www.theguardian.com/environment/rss"],
    "Lifestyle": ["https://www.news18.com/commonfeeds/v1/eng/rss/lifestyle-2.xml", "https://timesofindia.indiatimes.com/rssfeeds/2886704.cms"],
    "Travel & Tourism": ["https://timesofindia.indiatimes.com/rssfeeds/3112014.cms", "https://indianexpress.com/section/lifestyle/destination-of-the-week/feed/"],
    "Real Estate": ["https://economictimes.indiatimes.com/wealth/real-estate/rssfeeds/48997585.cms", "https://www.bing.com/news/search?q=real+estate+housing+property+india&format=rss"],
    "Defence & Security": ["https://economictimes.indiatimes.com/news/defence/rssfeeds/47117033.cms", "https://www.bing.com/news/search?q=indian+army+navy+air+force+drdo+defence&format=rss"],
    "Weather": ["https://www.bing.com/news/search?q=imd+weather+forecast+monsoon+rain+india&format=rss"],
    "Opinion & Editorial": ["https://indianexpress.com/section/opinion/feed/", "https://www.theguardian.com/uk/commentisfree/rss"],
    "Fact Check & Explainers": ["https://www.indiatoday.in/rss/fact-check", "https://indianexpress.com/section/explained/feed/"]
}

def img_key(u):
    if not u: return ""
    p = urlparse(u)
    base = (p.netloc + p.path).lower()
    if "th?id=" in u.lower():
        qs = parse_qs(p.query)
        if "id" in qs: return "bing_" + qs["id"][0].lower()
    return base

def is_valid_unique_img(u, seen_imgs):
    if not u or not isinstance(u, str) or not u.startswith("http"): return False
    ul = u.lower()
    bad = ["google", "gstatic", "googleusercontent", "picsum", "unsplash", "logo", "icon", "avatar", "1x1", "blank", "pixel", ".svg", ".gif", "editorial", "default", "placeholder", "share-image", "og-image", "thehindu.com/theme", "fe-default"]
    if any(b in ul for b in bad): return False
    k = img_key(u)
    if not k or k in seen_imgs: return False
    return True

def extract_real_unique_image(entry, seen_imgs):
    candidates = []
    for attr in ["media_content", "media_thumbnail"]:
        if hasattr(entry, attr) and getattr(entry, attr):
            for m in getattr(entry, attr):
                if m.get("url"): candidates.append(m.get("url"))
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            u = enc.get("href") or enc.get("url")
            if u: candidates.append(u)
    html_part = (entry.get("summary") or "") + (entry.get("description") or "")
    if html_part:
        soup = BeautifulSoup(html_part, "html.parser")
        for img in soup.find_all("img"):
            if img.get("src"): candidates.append(img.get("src"))

    link = entry.get("link") or ""
    if "bing.com/news/apiclick" in link and "url=" in link:
        qs = parse_qs(urlparse(link).query)
        if "url" in qs and qs["url"]: link = unquote(qs["url"][0])

    if link.startswith("http") and "news.google.com" not in link:
        try:
            r = requests.get(link, headers=UA, timeout=7)
            if r.status_code == 200:
                sp = BeautifulSoup(r.text, "html.parser")
                for prop in ["og:image", "twitter:image", "og:image:secure_url"]:
                    tag = sp.find("meta", property=prop) or sp.find("meta", attrs={"name": prop})
                    if tag and tag.get("content"):
                        candidates.insert(0, tag.get("content").strip())
        except Exception:
            pass

    for c in candidates:
        if is_valid_unique_img(c, seen_imgs):
            seen_imgs.add(img_key(c))
            return c
    return None

def build_800w_full_seo_html(title, summary, cat, author):
    clean_sum = BeautifulSoup(summary or title, "html.parser").get_text().strip()
    if len(clean_sum) < 40: clean_sum = title + " official update and comprehensive global report."
    
    if cat == "Rashifal & Horoscopes":
        return (
            '<h1 class="seo-title">' + title + '</h1>'
            '<p class="intro-text"><strong>Astrology Bureau | Fast Job Daily Rashifal:</strong> Daily astrological horoscope forecast and planetary transit predictions for all zodiac signs on ' + datetime.now().strftime("%B %d, %Y") + '.</p>'
            '<h3 class="article-subheading">1. Daily Zodiac Astrological Overview (Aries to Pisces)</h3>'
            '<p>Welcome to your verified daily horoscope forecast for <strong>' + title + '</strong>.</p>'
            '<table class="article-table"><tr><th>Zodiac Sign</th><th>Daily Cosmic Energy & Focus</th></tr>'
            '<tr><td>Aries (Mesha)</td><td>Favorable day for career decisions and financial planning.</td></tr>'
            '<tr><td>Taurus (Vrishabha)</td><td>Focus on stability and strengthening professional networks.</td></tr>'
            '<tr><td>Gemini (Mithuna)</td><td>Communication skills open new doors in collaborative projects.</td></tr>'
            '<tr><td>Cancer (Karka)</td><td>Emotional clarity brings peace; focus on family wellness.</td></tr>'
            '<tr><td>Leo (Simha)</td><td>Leadership qualities shine; recognition expected in workplace.</td></tr>'
            '<tr><td>Virgo (Kanya)</td><td>Meticulous planning ensures success in academic tasks.</td></tr>'
            '<tr><td>Libra (Tula)</td><td>Balance in partnerships leads to profitable outcomes.</td></tr>'
            '<tr><td>Scorpio (Vrischika)</td><td>Ideal time for strategic investments and research.</td></tr>'
            '<tr><td>Sagittarius (Dhanu)</td><td>Optimism drives travel plans and spiritual growth.</td></tr>'
            '<tr><td>Capricorn (Makara)</td><td>Disciplined effort yields long-term career rewards.</td></tr>'
            '<tr><td>Aquarius (Kumbha)</td><td>Innovative ideas attract appreciation from seniors.</td></tr>'
            '<tr><td>Pisces (Meena)</td><td>Creative pursuits flourish; maintain focus on health.</td></tr></table>'
            '<p class="hashtags">#FastJob #Rashifal2026 #DailyHoroscope #Astrology</p>'
        )

    # WEB STORIES VIDEO PLAYER FORMAT
    if cat == "Web Stories":
        return (
            '<h1 class="seo-title">' + title + '</h1>'
            '<div class="web-story-video-player my-6 bg-black rounded-2xl overflow-hidden shadow-2xl border-4 border-red-600 relative">'
            '<div class="absolute top-4 left-4 z-20 bg-red-600 text-white px-3 py-1 rounded-full text-xs font-black uppercase tracking-widest flex items-center gap-1.5 shadow"><span class="w-2.5 h-2.5 bg-yellow-300 rounded-full animate-ping"></span> Live Web Story Video</div>'
            '<div class="relative aspect-[9/16] sm:aspect-[16/9] max-h-[550px] w-full flex items-center justify-center bg-gray-900">'
            '<img src="' + img + '" class="w-full h-full object-cover opacity-85">'
            '<div class="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent"></div>'
            '<div class="absolute bottom-6 left-6 right-6 z-20 text-white">'
            '<h2 class="text-xl md:text-3xl font-black mb-3 leading-tight drop-shadow-lg">' + title + '</h2>'
            '<p class="text-sm md:text-base text-gray-200 leading-relaxed mb-4 line-clamp-3 drop-shadow">' + clean_sum + '</p>'
            '<div class="flex items-center gap-3">'
            '<span class="bg-yellow-400 text-gray-900 font-extrabold text-xs px-3 py-1.5 rounded-full shadow">▶ Play Story Slideshow</span>'
            '<span class="text-xs font-bold text-gray-300">Fast Job Visual Desk</span>'
            '</div></div></div></div>'
            '<h3 class="article-subheading">Complete Story Coverage</h3>'
            '<p>This interactive video web story brings you instant, high-impact visual coverage of <strong>' + title + '</strong>. Stay tuned to Fast Job for live updates throughout 2026.</p>'
            '<p class="hashtags">#FastJob #WebStories #VisualVideoStory #TrendingNews</p>'
        )

    seo_block = (
        '<h1 class="seo-title">' + title + '</h1>'
        '<p class="intro-text"><strong>Reported by ' + author + ' | Fast Job Global SEO Desk:</strong> ' + clean_sum + ' Read this comprehensive, fact-checked 2026 special report covering official notifications, key highlights, eligibility parameters, timeline, and expert analysis.</p>'
        '<h3 class="article-subheading">1. Executive Summary & Breaking Developments</h3>'
        '<p>In a landmark development under the <strong>' + cat + '</strong> vertical, official authorities and industry stakeholders have formally released comprehensive details concerning <strong>' + title + '</strong>.</p>'
        '<h3 class="article-subheading">2. Official Overview & Key Highlights Table</h3>'
        '<table class="article-table"><tr><th>Parameter / Metric</th><th>Official Verified Details (2026)</th></tr>'
        '<tr><th>Headline</th><td>' + title + '</td></tr><tr><th>Category Desk</th><td>' + cat + '</td></tr><tr><th>Status</th><td>Active & Verified</td></tr></table>'
        '<h3 class="article-subheading">3. Key Analysis & Guidelines</h3>'
        '<p>A closer inspection of guidelines surrounding <strong>' + title + '</strong> reveals critical benchmarks.</p>'
        '<p class="hashtags">#FastJob #' + cat.replace(" ", "").replace("&", "") + ' #BreakingNews2026</p>'
    )
    return seo_block

def collect_unique_posts(urls, cat, target_count, seen_titles, seen_imgs):
    out = []
    if cat == "Rashifal & Horoscopes":
        today_str = datetime.now().strftime("%B %d, %Y")
        t = f"Daily Rashifal & Horoscope Forecast: Astrological Predictions for Today ({today_str})"
        t_key = re.sub(r"[^a-z0-9]", "", t.lower())[:40]
        if t_key in seen_titles: return []
        seen_titles.add(t_key)
        return [(cat, t, "Daily horoscope predictions for all zodiac signs.", "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1000&q=80")]

    feed_list = list(urls)
    q_term = cat.replace("&", "").replace(" ", "+") + "+2026"
    feed_list.append("https://www.bing.com/news/search?q=" + q_term + "&format=rss")
    for u in feed_list:
        if len(out) >= target_count: break
        try:
            r = requests.get(u, headers=UA, timeout=12)
            entries = feedparser.parse(r.content).entries if r.status_code == 200 else []
        except Exception:
            entries = []
        for e in entries:
            if len(out) >= target_count: break
            t = (e.get("title") or "").rsplit(" - ", 1)[0].strip()
            t_key = re.sub(r"[^a-z0-9]", "", t.lower())[:40]
            if not t or len(t) < 15 or t_key in seen_titles:
                continue
            real_img = extract_real_unique_image(e, seen_imgs)
            if not real_img:
                continue
            seen_titles.add(t_key)
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
            print("OK [" + str(idx) + "/" + str(total) + "] " + cat + ": " + title[:45])
            return True
    except Exception as ex:
        print("Err:", ex)
    return False

def clean_existing_duplicates_and_load_seen():
    seen_titles = set()
    seen_imgs = set()
    dup_ids = []
    try:
        r = requests.get(S_URL + "/rest/v1/posts?select=id,title,image_url&order=id.desc&limit=2500", headers=HEADERS, timeout=20)
        if r.status_code == 200:
            for row in r.json():
                pid = row.get("id")
                t = re.sub(r"[^a-z0-9]", "", (row.get("title") or "").lower())[:40]
                im = row.get("image_url") or ""
                ik = img_key(im)
                if not ik or "editorial" in im.lower() or "picsum" in im.lower() or ik in seen_imgs or (t and t in seen_titles):
                    if pid: dup_ids.append(str(pid))
                else:
                    seen_imgs.add(ik)
                    if t: seen_titles.add(t)
        for i in range(0, len(dup_ids), 50):
            batch = ",".join(dup_ids[i:i+50])
            requests.delete(S_URL + "/rest/v1/posts?id=in.(" + batch + ")", headers=HEADERS, timeout=15)
    except Exception as e:
        print("Clean note:", e)
    return seen_titles, seen_imgs

def run():
    seen_titles, seen_imgs = clean_existing_duplicates_and_load_seen()
    q = []
    for cat in CATEGORIES:
        urls = FEEDS_MAP.get(cat, FEEDS_MAP["Breaking News"])
        target = 20 if cat == "Jobs & Careers" else (15 if cat == "Web Stories" else (1 if cat == "Rashifal & Horoscopes" else 8))
        items = collect_unique_posts(urls, cat, target, seen_titles, seen_imgs)
        q.extend(items)

    print("Publishing " + str(len(q)) + " Unique Posts & Video Web Stories across 27 Categories...")
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(publish_one, it, i + 1, len(q)) for i, it in enumerate(q)]
        for f in as_completed(futs):
            if f.result(): ok += 1
    print("FINISHED! Published " + str(ok) + " Posts!")

if __name__ == "__main__":
    run()
# DONE
