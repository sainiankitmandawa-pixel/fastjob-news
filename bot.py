import feedparser, re, random, time, os, requests, json
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.oauth2 import service_account
from googleapiclient.discovery import build

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

def notify_google_indexing(url):
    try:
        sa_json = os.environ.get("GCP_SA_KEY")
        if not sa_json:
            return
        service_account_info = json.loads(sa_json)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=["https://www.googleapis.com/auth/indexing"]
        )
        service = build('indexing', 'v3', credentials=credentials)
        body = {"url": url, "type": "URL_UPDATED"}
        service.urlNotifications().publish(body=body).execute()
        print("Instant Indexed:", url)
    except Exception as e:
        print("Indexing Error:", e)

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
            '<p class="intro-text"><strong>Astrology Bureau | Fast Job Daily Rashifal (' + today_date + '):</strong> Daily astrological horoscope forecast and planetary transit predictions for all 12 zodiac signs. Discover what the cosmos holds for your career, wealth, health, and personal relationships today.</p>'
            '<h3 class="article-subheading">1. Introduction to Daily Planetary Alignments (2026)</h3>'
            '<p>Welcome to your comprehensive astrological forecast for <strong>' + title + '</strong>. As planetary transits shift across the celestial sphere, individuals across all zodiac signs will experience distinct energetic influences. Whether you are navigating important career crossroads, financial investments, or family dynamics, understanding these cosmic currents provides invaluable clarity and foresight.</p>'
            '<p>Astrologers emphasize that daily horoscopes act as navigational maps rather than rigid decrees. By aligning your daily efforts with favorable cosmic windows, you can maximize productivity, mitigate stress, and attract positive outcomes in both professional and personal spheres.</p>'
            '<h3 class="article-subheading">2. Comprehensive Zodiac-Wise Horoscope Forecast (Aries to Pisces)</h3>'
            '<p>Our expert astrological desk has synthesized planetary movements to bring you detailed daily insights across all twelve zodiac signs for ' + today_date + ':</p>'
            '<table class="article-table">'
            '<tr><th>Zodiac Sign (Rashi)</th><th>Cosmic Focus & Detailed Astrological Prediction (2026)</th></tr>'
            '<tr><td><strong>Aries (Mesha)</strong></td><td>High vitality and dynamic energy define your day. Favorable celestial alignments make this an ideal time for launching new career projects, negotiating contracts, and making proactive financial decisions. Maintain patience in interpersonal relationships.</td></tr>'
            '<tr><td><strong>Taurus (Vrishabha)</strong></td><td>Focus shifts toward stability, asset consolidation, and long-term financial planning. Professional networks will offer unexpected support. Prioritize mental wellness and avoid overexertion in daily routines.</td></tr>'
            '<tr><td><strong>Gemini (Mithuna)</strong></td><td>Communication is your greatest asset today. Collaborative projects, team presentations, and academic pursuits will yield stellar results. Networking with industry leaders opens rewarding doors.</td></tr>'
            '<tr><td><strong>Cancer (Karka)</strong></td><td>Emotional clarity brings profound inner peace. Dedicate quality time to family bonding and domestic harmony. Financial prudence is advised; review your budget before committing to major expenses.</td></tr>'
            '<tr><td><strong>Leo (Simha)</strong></td><td>Your natural leadership qualities shine brightly. Workplace recognition and appreciation from superiors are on the horizon. Stay humble and continue fostering collaborative team spirit.</td></tr>'
            '<tr><td><strong>Virgo (Kanya)</strong></td><td>Meticulous planning and analytical rigor ensure success in complex tasks. Health and vitality remain robust. A great day for organizing workspace environments and setting new fitness goals.</td></tr>'
            '<tr><td><strong>Libra (Tula)</strong></td><td>Equilibrium and diplomacy guide your interactions today. Partnerships—both personal and business—flourish under harmonious planetary aspects. Creative expression brings immense joy.</td></tr>'
            '<tr><td><strong>Scorpio (Vrischika)</strong></td><td>Intuition reaches a peak, guiding you through strategic decisions and confidential matters. Favorable time for research, investments, and introspective personal growth.</td></tr>'
            '<tr><td><strong>Sagittarius (Dhanu)</strong></td><td>Optimism and adventurous spirit drive your day. Opportunities for higher learning, travel, and expanding your professional horizon emerge. Keep an open mind to diverse perspectives.</td></tr>'
            '<tr><td><strong>Capricorn (Makara)</strong></td><td>Disciplined effort and unwavering focus yield tangible career milestones. Senior mentors recognize your dedication. Maintain work-life balance to sustain long-term stamina.</td></tr>'
            '<tr><td><strong>Aquarius (Kumbha)</strong></td><td>Innovative concepts and forward-thinking ideas attract appreciation from peers. Collaborative community projects thrive. Embrace technological tools to streamline daily tasks.</td></tr>'
            '<tr><td><strong>Pisces (Meena)</strong></td><td>Spiritual awareness and artistic creativity flourish. Trust your inner voice in navigating creative projects. Prioritize restorative rest and mindful relaxation in the evening.</td></tr>'
            '</table>'
            '<h3 class="article-subheading">3. Key Astrological Remedies & Auspicious Timings</h3>'
            '<p>To harness positive planetary vibrations and ward off malefic influences, practitioners recommend engaging in charitable acts, practicing morning meditation, and reciting traditional mantras associated with your ruling planet. Staying hydrated and spending mindful moments in nature further enhances grounded energy throughout the day.</p>'
            '<h3 class="article-subheading">4. Frequently Asked Questions (Rashifal FAQs)</h3>'
            '<p><strong>Q1: How accurate are daily horoscope predictions?</strong><br>Ans: Daily horoscopes are formulated based on traditional Vedic and Western astrological transit calculations, offering general cosmic guidance and psychological insights for personal reflection.</p>'
            '<p><strong>Q2: Can planetary transits impact financial decisions?</strong><br>Ans: While astrology highlights favorable or cautious periods, financial decisions should always be combined with practical market research and professional planning.</p>'
            '<p><strong>Q3: How often is the Rashifal updated on Fast Job?</strong><br>Ans: Our astrological desk publishes verified daily horoscope forecasts every morning at precisely 4:00 AM.</p>'
            '<p class="hashtags">#FastJob #Rashifal2026 #DailyHoroscope #AstrologyForecast #ZodiacSigns #CosmicGuidance</p>'
        )

    if cat == "Web Stories":
        durations = [10, 30, 40, 60]
        selected_duration = random.choice(durations)
        return (
            '<h1 class="seo-title">' + title + '</h1>'
            '<div class="web-story-reel-container my-6 mx-auto max-w-[360px] bg-black rounded-[24px] overflow-hidden shadow-2xl border-4 border-red-600 relative aspect-[9/16] flex flex-col justify-between p-5 text-white">'
            '<div class="absolute inset-0 z-0"><img src="' + img_url + '" class="w-full h-full object-cover opacity-90"><div class="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-black/70"></div></div>'
            '<div class="flex justify-between items-center z-10"><span class="bg-red-600 text-white text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-wider flex items-center gap-1.5 shadow"><span class="w-2 h-2 bg-yellow-300 rounded-full animate-ping"></span> 9:16 Video Story (' + str(selected_duration) + 's)</span><span class="text-xs text-yellow-400 font-bold">Fast Job Reel</span></div>'
            '<div class="z-10 my-auto text-center"><img src="' + img_url + '" class="w-24 h-24 mx-auto rounded-full object-cover border-2 border-yellow-400 shadow-xl mb-3 animate-bounce"></div>'
            '<div class="z-10 bg-black/75 backdrop-blur-md p-4 rounded-xl border border-white/20"><h3 class="text-base font-black leading-snug text-white mb-2">' + title + '</h3><p class="text-xs text-gray-300 line-clamp-2 mb-3">' + clean_sum + '</p>'
            '<a href="#" class="block bg-[#d10000] text-white font-black text-xs uppercase text-center py-2 rounded-full shadow-lg">🔗 Read More (Puri Post Dekhein)</a></div>'
            '</div>'
            '<h3 class="article-subheading">Complete Video Story Coverage</h3>'
            '<p>This 9:16 vertical video story (' + str(selected_duration) + ' seconds loop) provides instant visual insights into <strong>' + title + '</strong>. Stay tuned to Fast Job for live updates throughout 2026.</p>'
            '<p class="hashtags">#FastJob #WebStories #VerticalVideo #Reels2026</p>'
        )

    return (
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
        '<p>A closer inspection of the official guidelines surrounding <strong>' + title + '</strong> reveals several critical benchmarks that participants and readers must keep in mind. In the context of recruitment drives, policy rollouts, and industry launches, authorities have mandated strict adherence to documentation and verification standards.</p>'
        '<ul>'
        '<li><strong>Document Verification Standards:</strong> All submitted records, certificates, and digital forms must be authentic and cross-verified before the final deadline.</li>'
        '<li><strong>Digital Compliance & Security:</strong> The 2026 portal infrastructure uses real-time verification protocols to prevent duplicate entries and ensure fair processing.</li>'
        '<li><strong>Regional & Global Impact:</strong> Experts project a substantial surge in participation and sector growth following the implementation of these updated provisions.</li>'
        '<li><strong>Timely Action Required:</strong> Stakeholders are strongly encouraged to complete all necessary formalities well ahead of the closing window.</li>'
        '</ul>'
        '<h3 class="article-subheading">4. Step-by-Step Procedure & Implementation Guide</h3>'
        '<p>For candidates, consumers, and professionals looking to act on <strong>' + title + '</strong>, following a systematic approach guarantees a smooth experience. First, review the complete official notification and confirm every eligibility or technical parameter listed in the bulletin. Second, gather all required digital documents, photographs, signatures, and supporting proofs in the specified file formats. Third, complete the online registration or verification workflow carefully.</p>'
        '<h3 class="article-subheading">5. Expert Outlook & Sector Impact in 2026</h3>'
        '<p>Senior analysts and subject-matter specialists tracking the <strong>' + cat + '</strong> sector emphasize that <strong>' + title + '</strong> reflects a broader transformation toward efficiency and accountability. Over the coming months, follow-up notifications, phase-two schedules, and supplementary guidelines are expected to be announced.</p>'
        '<h3 class="article-subheading">6. Frequently Asked Questions (SEO FAQs)</h3>'
        '<p><strong>Q1: What is the latest official update regarding ' + title + '?</strong><br>Ans: Official authorities have released the latest 2026 update and guidelines for ' + title + ' under the ' + cat + ' section.</p>'
        '<p><strong>Q2: Who is eligible or impacted by this announcement?</strong><br>Ans: All eligible candidates, citizens, and sector professionals who meet the prescribed 2026 criteria and documentation standards.</p>'
        '<p><strong>Q3: How can I check official updates and complete the process?</strong><br>Ans: You can complete the process online through the respective official portal by verifying your details and saving the confirmation receipt.</p>'
        '<p><strong>Q4: Why is this 2026 update considered important by experts?</strong><br>Ans: Analysts highlight that this development introduces transparent digital processing and expanded opportunities.</p>'
        '<p class="hashtags">#FastJob #' + cat.replace(" ", "").replace("&", "") + ' #BreakingNews2026 #VerifiedUpdate #LatestNotification #GlobalCoverage</p>'
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
            notify_google_indexing(f"https://fastjob.online/{slug}")
            
            if cat != "Web Stories":
                story_slug = "story-" + slug
                story_title = "⚡ Story: " + title
                story_body = build_800w_full_seo_html(title, summary, "Web Stories", author, img)
                res_story = requests.post(S_URL + "/rest/v1/posts", headers=HEADERS, json={"title": story_title, "slug": story_slug, "content": story_body, "category": "Web Stories", "image_url": img}, timeout=15)
                if res_story.status_code in [200, 201, 204]:
                    notify_google_indexing(f"https://fastjob.online/{story_slug}")

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

    print("Publishing Hourly Batch with Instant Google Indexing & Image Web Stories...")
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(publish_one, it, i + 1, len(q)) for i, it in enumerate(q)]
        for f in as_completed(futs):
            if f.result(): ok += 1
    print("FINISHED! Published " + str(ok) + " Posts & Stories with Instant Indexing!")

if __name__ == "__main__":
    run()
