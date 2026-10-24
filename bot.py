import feedparser, re, random, time, os, requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

S_URL = "https://wioheljpjdcprozqumpv.supabase.co"
S_KEY = (os.environ.get("SUPABASE_KEY") or "").strip() or "sb_publishable_d_ROr-nG6RpIRlVWtIE-Fg_sciaLZXR"
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
    "Matteo Rossi (Milan)", "Sofia Lindqvist (Stockholm)", "Hugo Martinez (Madrid)", "Freya Van Der Berg (Amsterdam)"
]

CATEGORIES = [
    "Automobile", "Technology", "Jobs & Careers", "Rashifal & Horoscopes", "Web Stories", "Breaking News", 
    "World News", "India News", "Politics", "Sports", "Business", "Finance & Markets", 
    "Entertainment", "Education", "Health & Medicine", "Science", "AI & Robotics", "Crime & Justice", 
    "Economy", "Environment & Climate", "Lifestyle", "Travel & Tourism", "Real Estate", 
    "Defence & Security", "Weather", "Opinion & Editorial", "Fact Check & Explainers"
]

FEEDS_MAP = {
    "Automobile": [
        "https://www.cartoq.com/feed/",
        "https://www.news18.com/commonfeeds/v1/eng/rss/auto.xml",
        "https://timesofindia.indiatimes.com/rssfeeds/74317216.cms",
        "https://www.bing.com/news/search?q=bikes+scooters+cars+electric+vehicles+launch+india+2026&format=rss"
    ],
    "Technology": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://www.news18.com/commonfeeds/v1/eng/rss/tech.xml",
        "https://www.bing.com/news/search?q=smartphones+mobile+nokia+feature+button+phones+gadgets+2026&format=rss"
    ],
    "Jobs & Careers": [
        "https://www.news18.com/commonfeeds/v1/eng/rss/education-career.xml",
        "https://indianexpress.com/section/jobs/feed/",
        "https://timesofindia.indiatimes.com/rssfeeds/3012544.cms",
        "https://www.bing.com/news/search?q=sarkari+recruitment+vacancy+apply+online+2026&format=rss"
    ],
    "Rashifal & Horoscopes": ["https://www.bing.com/news/search?q=daily+horoscope+astrology+rashifal+today+2026&format=rss"],
    "Web Stories": ["https://www.bing.com/news/search?q=trending+visual+stories+news+2026&format=rss"],
    "Breaking News": ["https://feeds.feedburner.com/ndtvnews-top-stories", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "https://www.bing.com/news/search?q=breaking+news+world+india+today&format=rss"],
    "World News": ["http://feeds.bbci.co.uk/news/world/rss.xml", "https://www.theguardian.com/world/rss"],
    "India News": ["https://www.news18.com/commonfeeds/v1/eng/rss/india.xml", "https://indianexpress.com/section/india/feed/"],
    "Politics": ["https://www.news18.com/commonfeeds/v1/eng/rss/politics.xml"],
    "Sports": ["https://www.news18.com/commonfeeds/v1/eng/rss/sports.xml", "https://timesofindia.indiatimes.com/rssfeeds/4719148.cms"],
    "Business": ["https://www.news18.com/commonfeeds/v1/eng/rss/business.xml"],
    "Finance & Markets": ["https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"],
    "Entertainment": ["https://www.news18.com/commonfeeds/v1/eng/rss/movies.xml"],
    "Education": ["https://indianexpress.com/section/education/feed/"],
    "Health & Medicine": ["https://timesofindia.indiatimes.com/rssfeeds/3908999.cms"],
    "Science": ["https://www.space.com/feeds/all"],
    "AI & Robotics": ["https://economictimes.indiatimes.com/tech/technology/rssfeeds/78570561.cms"],
    "Crime & Justice": ["https://indianexpress.com/section/cities/feed/"],
    "Economy": ["https://economictimes.indiatimes.com/news/economy/rssfeeds/1377380.cms"],
    "Environment & Climate": ["https://timesofindia.indiatimes.com/rssfeeds/2647163.cms"],
    "Lifestyle": ["https://www.news18.com/commonfeeds/v1/eng/rss/lifestyle-2.xml"],
    "Travel & Tourism": ["https://timesofindia.indiatimes.com/rssfeeds/3112014.cms"],
    "Real Estate": ["https://economictimes.indiatimes.com/wealth/real-estate/rssfeeds/48997585.cms"],
    "Defence & Security": ["https://economictimes.indiatimes.com/news/defence/rssfeeds/47117033.cms"],
    "Weather": ["https://www.bing.com/news/search?q=imd+weather+forecast+monsoon+rain+india&format=rss"],
    "Opinion & Editorial": ["https://indianexpress.com/section/opinion/feed/"],
    "Fact Check & Explainers": ["https://www.indiatoday.in/rss/fact-check"]
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
    bad = ["google", "gstatic", "googleusercontent", "picsum", "unsplash", "logo", "icon", "avatar", "1x1", "blank", "pixel", ".svg", ".gif", "editorial", "default", "placeholder", "share-image", "og-image"]
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

def build_800w_full_seo_html(title, summary, cat, author, img_url):
    clean_sum = BeautifulSoup(summary or title, "html.parser").get_text().strip()
    if len(clean_sum) < 40: clean_sum = title + " official update and comprehensive global report."
    
    if cat == "Rashifal & Horoscopes":
        today_date = datetime.now().strftime("%B %d, %Y")
        return (
            '<h1 class="seo-title">' + title + '</h1>'
            '<p class="intro-text"><strong>Astrology Bureau | Fast Job Daily Rashifal (' + today_date + '):</strong> Daily astrological horoscope forecast and planetary transit predictions for all 12 zodiac signs.</p>'
            '<h3 class="article-subheading">1. Introduction to Daily Planetary Alignments (2026)</h3>'
            '<p>Welcome to your comprehensive astrological forecast for <strong>' + title + '</strong>.</p>'
            '<p class="hashtags">#FastJob #Rashifal2026 #DailyHoroscope #Astrology</p>'
        )

    if cat == "Web Stories":
        durations = [10, 30, 40, 60]
        selected_duration = random.choice(durations)
        return (
            '<h1 class="seo-title">' + title + '</h1>'
            '<div class="web-story-reel-container my-6 mx-auto max-w-[360px] bg-black rounded-[24px] overflow-hidden shadow-2xl border-4 border-red-600 relative aspect-[9/16] flex flex-col justify-between p-5 text-white">'
            '<div class="absolute inset-0 z-0"><video autoplay muted loop playsinline class="w-full h-full object-cover opacity-90"><source src="https://assets.mixkit.co/videos/preview/mixkit-digital-animation-of-screens-and-numbers-31917-large.mp4" type="video/mp4"></video><div class="absolute inset-0 bg-gradient-to-t from-black via-black/30 to-black/60"></div></div>'
            '<div class="flex justify-between items-center z-10"><span class="bg-red-600 text-white text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-wider flex items-center gap-1.5 shadow"><span class="w-2 h-2 bg-yellow-300 rounded-full animate-ping"></span> 9:16 Video Story (' + str(selected_duration) + 's)</span><span class="text-xs text-yellow-400 font-bold">Fast Job Reel</span></div>'
            '<div class="z-10 my-auto text-center"><img src="' + img_url + '" class="w-24 h-24 mx-auto rounded-full object-cover border-2 border-yellow-400 shadow-xl mb-3 animate-bounce"></div>'
            '<div class="z-10 bg-black/70 backdrop-blur-md p-4 rounded-xl border border-white/20"><h3 class="text-base font-black leading-snug text-white mb-2">' + title + '</h3><p class="text-xs text-gray-300 line-clamp-2 mb-3">' + clean_sum + '</p>'
            '<a href="#" class="block bg-[#d10000] text-white font-black text-xs uppercase text-center py-2 rounded-full shadow-lg">🔗 Read More (Puri Post Dekhein)</a></div>'
            '</div>'
            '<h3 class="article-subheading">Complete Video Story Coverage</h3>'
            '<p>This 9:16 vertical video story (' + str(selected_duration) + ' seconds loop) provides instant visual insights into <strong>' + title + '</strong>.</p>'
            '<p class="hashtags">#FastJob #WebStories #VerticalVideo #Reels2026</p>'
        )

    return (
        '<h1 class="seo-title">' + title + '</h1>'
        '<p class="intro-text"><strong>Reported by ' + author + ' | Fast Job Global SEO Desk:</strong> ' + clean_sum + ' Read this comprehensive, fact-checked report covering official notifications, key highlights, and expert analysis.</p>'
        '<h3 class="article-subheading">1. Executive Summary & Breaking Developments</h3>'
        '<p>In a landmark development under the <strong>' + cat + '</strong> vertical, official authorities and industry stakeholders have formally released comprehensive details concerning <strong>' + title + '</strong>.</p>'
        '<h3 class="article-subheading">2. Official Overview & Key Highlights Table</h3>'
        '<table class="article-table">'
        '<tr><th>Parameter / Metric</th><th>Official Verified Details (2026)</th></tr>'
        '<tr><th>Headline / Notification</th><td>' + title + '</td></tr>'
        '<tr><th>Primary Category Desk</th><td>' + cat + '</td></tr>'
        '<tr><th>Editorial Correspondent</th><td>' + author + '</td></tr>'
        '</table>'
        '<h3 class="article-subheading">3. In-Depth Analysis & Core Requirements</h3>'
        '<p>A closer inspection of the guidelines surrounding <strong>' + title + '</strong> reveals several critical benchmarks.</p>'
        '<p class="hashtags">#FastJob #' + cat.replace(" ", "").replace("&", "") + ' #BreakingNews2026</p>'
    )

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
    body = '<div class="post-author-meta" data-author="' + author + '" style="display:none;"></div>\n' + build_800w_full_seo_html(title, summary, cat, author, img)
    try:
        r = requests.post(S_URL + "/rest/v1/posts", headers=HEADERS, json={"title": title, "slug": slug, "content": body, "category": cat, "image_url": img}, timeout=25)
        if r.status_code in [200, 201, 204]:
            print("OK [" + str(idx) + "/" + str(total) + "] " + cat + ": " + title[:45])
            
            if cat != "Web Stories":
                story_slug = "story-" + slug
                story_title = "⚡ Story: " + title
                story_body = build_800w_full_seo_html(title, summary, "Web Stories", author, img)
                requests.post(S_URL + "/rest/v1/posts", headers=HEADERS, json={"title": story_title, "slug": story_slug, "content": story_body, "category": "Web Stories", "image_url": img}, timeout=15)

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
        if cat == "Web Stories": continue
        urls = FEEDS_MAP.get(cat, FEEDS_MAP["Breaking News"])
        if cat in ["Automobile", "Technology"]:
            target = 5
        elif cat == "Jobs & Careers":
            target = 10
        elif cat == "Rashifal & Horoscopes":
            target = 1
        else:
            target = 4
        
        items = collect_unique_posts(urls, cat, target, seen_titles, seen_imgs)
        q.extend(items)

    print("Publishing Hourly Batch with 9:16 Video Web Stories...")
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(publish_one, it, i + 1, len(q)) for i, it in enumerate(q)]
        for f in as_completed(futs):
            if f.result(): ok += 1
    print("FINISHED! Published " + str(ok) + " Posts & Stories!")

if __name__ == "__main__":
    run()
