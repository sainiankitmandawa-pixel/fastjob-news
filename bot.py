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

CATEGORY_HIERARCHY = {
    "Jobs & Careers": [
        "Sarkari Naukri & Govt Vacancies", "UPSC & Civil Services", "SSC CGL CHSL MTS", "Railway RRB NTPC Group D",
        "Banking SBI IBPS PO Clerk", "Police & Defence Bharti", "State PSC & Teacher Jobs", "India Post GDS Recruitment",
        "PSU & Engineering Jobs", "International Visa Jobs", "Remote & Work From Home", "Admit Cards & Hall Tickets",
        "Exam Results & Merit Lists", "Answer Keys & Cut-Offs", "Apprentice & Trainee Openings"
    ],
    "Rashifal & Horoscopes": [
        "Daily Aries Horoscope", "Daily Taurus Horoscope", "Daily Gemini Horoscope", "Daily Cancer Horoscope",
        "Daily Leo Horoscope", "Daily Virgo Horoscope", "Daily Libra Horoscope", "Daily Scorpio Horoscope",
        "Daily Sagittarius Horoscope", "Daily Capricorn Horoscope", "Daily Aquarius Horoscope", "Daily Pisces Horoscope",
        "Weekly Astrological Forecast", "Monthly Planetary Movements", "Career & Wealth Rashifal"
    ],
    "Breaking News": ["National Flash", "Global Breaking", "Top Headlines", "Live Updates", "Urgent Bulletins", "Editor's Pick", "Exclusive Reports", "In The Spotlight", "Major Announcements", "Day's Summary", "Speed News", "Flash Bulletins", "Editorials Live", "Special Dispatch", "24x7 Wire"],
    "World News": ["US & Americas", "Europe & UK", "Middle East & GCC", "Asia Pacific", "Africa Desk", "UN & Global Diplomacy", "Cross-Border Affairs", "International Security", "Global Human Rights", "Foreign Policy", "Global Economy", "Transatlantic Relations", "Indo-Pacific Alliance", "Latin America Briefs", "Eurasia Monitor"],
    "India News": ["National Capital Region", "North India States", "South India Bureau", "Western India Updates", "Eastern & Northeast", "Central India Affairs", "Government Schemes", "Public Welfare", "Social Initiatives", "National Infrastructure", "Rural Development", "Urban Affairs", "State Legislative Updates", "Cultural Heritage", "National Security"],
    "Politics": ["Parliament & Cabinet", "Election Commission", "State Assemblies", "Opposition Updates", "Policy & Legislation", "Political Debates", "Campaign Trails", "Constitutional Affairs", "Party Strategies", "Governance Reforms", "Political Speeches", "Diplomatic Summits", "Cabinet Decisions", "Electoral Analysis", "Policy Watch"],
    "Sports": ["Cricket & IPL", "Football & ISL", "Badminton & Tennis", "Olympics & Athletics", "Hockey & Kabaddi", "Motorsports & F1", "Chess & Esports", "Match Analysis", "Player Transfers", "Tournament Schedules", "Domestic Leagues", "Women's Sports", "Interviews & Profiles", "Sports Science", "Fitness & Training"],
    "Business": ["Startup Ecosystem", "Corporate Earnings", "Mergers & Acquisitions", "Retail & FMCG", "Logistics & Supply Chain", "MSME & Small Business", "Manufacturing Hubs", "Telecom & Energy", "Aviation & Tourism Biz", "Industrial Growth", "Venture Capital", "Corporate Governance", "Export Houses", "E-Commerce Trends", "Consumer Insights"],
    "Finance & Markets": ["Sensex & Nifty", "Wall Street & Global", "Mutual Funds & SIP", "Gold & Silver Rates", "RBI Monetary Policy", "Cryptocurrency & Web3", "Taxation & Budget", "Insurance & Banking", "IPO & Share Market", "Foreign Institutional Flows", "Personal Finance", "Debt & Bonds", "Commodities Market", "Forex Rates", "Wealth Management"],
    "Technology": ["Smartphones & Gadgets", "Consumer Electronics", "Software & Cloud", "Cybersecurity & Privacy", "Semiconductors & Chips", "Telecom & 6G", "Internet & Social Media", "Tech Policy & Antitrust", "Gadget Reviews", "Open Source & Dev", "Enterprise Tech", "Data Centers", "Web Development", "Hardware Innovations", "Tech Startups"],
    "Entertainment": ["Bollywood Box Office", "Hollywood & Global", "OTT & Web Series", "Music & Albums", "Celebrity News", "Television Serials", "Film Festivals", "Awards & Honours", "Trailers & Teasers", "Art & Theatre", "Fashion & Cinema", "Regional Cinema", "Streaming Analytics", "Voice & Podcast", "Media Industry"],
    "Education": ["CBSE & State Boards", "NEET & JEE Main", "University Exams", "UGC NET & Ph.D.", "Study Abroad Guides", "Scholarships & Grants", "EdTech & Online Learning", "Skill Development", "Vocational Training", "Academic Policies", "Higher Education", "School Curriculum", "Entrance Tests", "Research Fellowships", "Student Success"],
    "Health & Medicine": ["Medical Breakthroughs", "Fitness & Nutrition", "Mental Wellness", "Diseases & Prevention", "Hospital & Pharma", "Ayurveda & Yoga", "Public Health Advisories", "Pediatric Care", "Healthcare Policies", "Clinical Trials", "Dietary Science", "Alternative Medicine", "Global Health", "Nursing & Care", "Medical Technology"],
    "Science": ["Space Exploration", "NASA & ISRO Updates", "Astronomy & Universe", "Physics & Quantum", "Biology & Genetics", "Earth Sciences", "Archaeology & History", "Research Journals", "Scientific Innovations", "Laboratory Discoveries", "Climate Research", "Oceanography", "Paleontology", "Neuroscience", "Nanotechnology"],
    "AI & Robotics": ["Generative AI & LLMs", "OpenAI & Anthropic", "Humanoid Robotics", "Machine Learning", "AI Ethics & Law", "Automation in Industry", "Computer Vision", "Neural Networks", "AI Chips & Hardware", "Future of Work", "Natural Language Processing", "Autonomous Systems", "Edge AI", "Robotic Surgery", "AI Research"],
    "Crime & Justice": ["Supreme Court Verdicts", "High Court Rulings", "Police Investigations", "Cyber Crime Alerts", "Legal Reforms", "CBI & ED Actions", "Forensic Science", "Human Rights Law", "Prison & Corrections", "Landmark Judgments", "Trial Court Updates", "Anti-Corruption", "White Collar Crime", "Civil Rights", "Legal Aid"],
    "Auto & EV": ["Electric Vehicles (EV)", "New SUV Launches", "Bikes & Scooters", "Car Price & Mileage", "Battery & Charging Tech", "Hybrid Vehicles", "Commercial Vehicles", "Luxury & Supercars", "Auto Component Industry", "Road Safety & Tests", "Concept Cars", "Two-Wheeler News", "EV Infrastructure", "Motorsport Auto", "Aftermarket Trends"],
    "Economy": ["GDP Growth & Forecast", "Inflation & CPI", "Fiscal & Revenue Deficit", "Export & Import", "Agriculture Economy", "Employment & Labor", "Foreign Direct Investment", "Rural Economy", "Economic Surveys", "Global Trade Pacts", "Microeconomics", "Macro Trends", "Public Debt", "Currency Valuation", "Economic Policy"],
    "Environment & Climate": ["Climate Change & IPCC", "Renewable Energy", "Solar & Wind Power", "Wildlife Conservation", "Pollution Control", "Water Resources", "Forest & Ecology", "Green Hydrogen", "Carbon Emissions", "Sustainable Living", "Biodiversity", "Waste Management", "Green Tech", "Environmental Law", "Eco Tourism"],
    "Lifestyle": ["Fashion & Trends", "Interior Design", "Food & Culinary", "Relationships", "Parenting & Family", "Luxury & Living", "Astrology & Horoscope", "Pet Care & Animals", "Personal Growth", "Festivals & Culture", "Wellness & Spa", "Home Decor", "Gardening", "Hobbies & Craft", "Modern Etiquette"],
    "Travel & Tourism": ["Destination Guides", "Airlines & Aviation", "Indian Tourism", "International Travel", "Railway Tourism", "Hotel & Hospitality", "Visa Rules & Passports", "Adventure & Trekking", "Budget Travel", "Heritage Sites", "Cruise Holidays", "Travel Insurance", "Eco Tourism", "Pilgrimage Tours", "Travel Gadgets"],
    "Real Estate": ["Housing & Apartments", "Commercial Property", "Smart Cities", "RERA Regulations", "Home Loans & Interest", "Architecture & Design", "Land & Plots", "Rental Markets", "Urban Infrastructure", "Property Investment", "Affordable Housing", "Real Estate Tech", "Interior Planning", "Township Projects", "Property Law"],
    "Defence & Security": ["Indian Army Updates", "Indian Navy & Maritime", "Indian Air Force", "DRDO & Missile Tech", "Border Security", "Global Military & NATO", "Defense Procurement", "Indigenization & Make in India", "Counter-Terrorism", "Cyber Warfare", "Military Exercises", "Strategic Affairs", "Aerospace Defense", "Naval Fleet", "Soldier Welfare"],
    "Weather": ["IMD Forecasts", "Monsoon Updates", "Heatwave Alerts", "Cyclone & Storms", "Winter & Fog Reports", "Rainfall Statistics", "Global Climate Alerts", "Air Quality Index (AQI)", "Agricultural Weather", "Satellite Imaging", "Severe Weather", "Temperature Trends", "El Nino & La Nina", "Weather Radar", "Seasonal Outlook"],
    "Opinion & Editorial": ["Editor's Desk", "Geopolitical Analysis", "Economic Viewpoints", "Social Commentaries", "Guest Columns", "Policy Critiques", "Historical Perspectives", "Philosophical Essays", "Letters to Editor", "Expert Roundtables", "Media Critique", "Public Debates", "Think Tank Briefs", "Global Dialogues", "Future Outlook"],
    "Fact Check & Explainers": ["Viral Rumours Debunked", "Policy Explainers", "Historical Context", "Data Visualizations", "Scientific Myths", "Deepfake Verification", "Economic Terminology", "Legal Rights Explained", "How Things Work", "In-Depth Q&A", "Health Fact Check", "Tech Myths Busted", "Geopolitics Explained", "Statistical Insights", "News Verification"]
}

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
            '<p class="intro-text"><strong>Astrology Bureau | Fast Job Daily Rashifal:</strong> Daily astrological horoscope forecast and planetary transit predictions for all zodiac signs on ' + datetime.now().strftime("%B %d, %Y") + '. Discover what the stars hold for your career, wealth, health, and relationships.</p>'
            '<h3 class="article-subheading">1. Daily Zodiac Astrological Overview (Aries to Pisces)</h3>'
            '<p>Welcome to your verified daily horoscope forecast for <strong>' + title + '</strong>. Astrological alignments and planetary transits indicate significant shifts in professional energy, financial opportunities, and personal well-being across all zodiac signs today.</p>'
            '<table class="article-table">'
            '<tr><th>Zodiac Sign</th><th>Daily Cosmic Energy & Focus (2026)</th></tr>'
            '<tr><td>Aries (Mesha)</td><td>High vitality; favorable day for career decisions and financial planning.</td></tr>'
            '<tr><td>Taurus (Vrishabha)</td><td>Focus on stability, savings, and strengthening professional networks.</td></tr>'
            '<tr><td>Gemini (Mithuna)</td><td>Excellent communication skills will open new doors in collaborative projects.</td></tr>'
            '<tr><td>Cancer (Karka)</td><td>Emotional clarity brings peace; focus on family bonding and wellness.</td></tr>'
            '<tr><td>Leo (Simha)</td><td>Leadership qualities shine; recognition expected in workplace ventures.</td></tr>'
            '<tr><td>Virgo (Kanya)</td><td>Meticulous planning ensures success in academic and financial tasks.</td></tr>'
            '<tr><td>Libra (Tula)</td><td>Balance in partnerships leads to harmony and profitable outcomes.</td></tr>'
            '<tr><td>Scorpio (Vrischika)</td><td>Intuition is strong; ideal time for strategic investments and research.</td></tr>'
            '<tr><td>Sagittarius (Dhanu)</td><td>Optimism drives travel plans, higher learning, and spiritual growth.</td></tr>'
            '<tr><td>Capricorn (Makara)</td><td>Disciplined effort yields tangible long-term career rewards.</td></tr>'
            '<tr><td>Aquarius (Kumbha)</td><td>Innovative ideas attract appreciation from peers and seniors.</td></tr>'
            '<tr><td>Pisces (Meena)</td><td>Creative pursuits flourish; maintain mindful focus on physical health.</td></tr>'
            '</table>'
            '<h3 class="article-subheading">2. Detailed Career, Wealth & Relationship Guidance</h3>'
            '<p>Astrologers emphasize that aligning daily tasks with your natural zodiac strengths helps mitigate stress and maximize productivity.</p>'
            '<p class="hashtags">#FastJob #Rashifal2026 #DailyHoroscope #Astrology #ZodiacSigns #CareerHoroscope</p>'
        )

    seo_block = (
        '<h1 class="seo-title">' + title + '</h1>'
        '<p class="intro-text"><strong>Reported by ' + author + ' | Fast Job Global SEO Desk:</strong> ' + clean_sum + ' Read this comprehensive, fact-checked 2026 special report covering official notifications, key highlights, eligibility parameters, timeline, and expert analysis.</p>'
        '<h3 class="article-subheading">1. Executive Summary & Breaking Developments</h3>'
        '<p>In a landmark development under the <strong>' + cat + '</strong> vertical, official authorities and industry stakeholders have formally released comprehensive details concerning <strong>' + title + '</strong>. Across the national and international landscape in 2026, this update has garnered massive attention from citizens, professionals, job aspirants, and policy analysts alike.</p>'
        '<h3 class="article-subheading">2. Official Overview & Key Highlights Table</h3>'
        '<table class="article-table">'
        '<tr><th>Parameter / Metric</th><th>Official Verified Details (2026)</th></tr>'
        '<tr><th>Headline / Notification</th><td>' + title + '</td></tr>'
        '<tr><th>Primary Category Desk</th><td>' + cat + '</td></tr>'
        '<tr><th>Editorial Correspondent</th><td>' + author + '</td></tr>'
        '<tr><th>Current Status</th><td>Officially Active & Verified</td></tr>'
        '</table>'
        '<h3 class="article-subheading">3. In-Depth Analysis, Eligibility & Core Requirements</h3>'
        '<p>A closer inspection of the official guidelines surrounding <strong>' + title + '</strong> reveals several critical benchmarks that participants and readers must keep in mind.</p>'
        '<ul>'
        '<li><strong>Document Verification Standards:</strong> All submitted records and digital forms must be authentic and verified.</li>'
        '<li><strong>Digital Compliance & Security:</strong> The 2026 portal infrastructure uses real-time verification protocols.</li>'
        '<li><strong>Regional & Global Impact:</strong> Experts project a substantial surge in participation and sector growth.</li>'
        '</ul>'
        '<h3 class="article-subheading">4. Step-by-Step Procedure & Implementation Guide</h3>'
        '<p>For candidates, consumers, and professionals looking to act on <strong>' + title + '</strong>, following a systematic approach guarantees a smooth experience.</p>'
        '<h3 class="article-subheading">5. Expert Outlook & Sector Impact in 2026</h3>'
        '<p>Senior analysts tracking the <strong>' + cat + '</strong> sector emphasize that <strong>' + title + '</strong> reflects a broader transformation toward efficiency and accountability.</p>'
        '<h3 class="article-subheading">6. Frequently Asked Questions (SEO FAQs)</h3>'
        '<p><strong>Q1: What is the latest official update regarding ' + title + '?</strong><br>Ans: Official authorities have released the latest 2026 update and guidelines for ' + title + '.</p>'
        '<p><strong>Q2: Who is eligible or impacted by this announcement?</strong><br>Ans: All eligible candidates and professionals meeting prescribed criteria.</p>'
        '<p><strong>Q3: How can I check official updates and complete the process?</strong><br>Ans: Through the respective official portal while following Fast Job.</p>'
        '<p class="hashtags">#FastJob #' + cat.replace(" ", "").replace("&", "") + ' #BreakingNews2026 #VerifiedUpdate #LatestNotification #GlobalCoverage</p>'
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
        astral_img = "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=1000&q=80"
        return [(cat, t, "Daily horoscope predictions for all zodiac signs.", astral_img)]

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

def publish_story(item):
    cat, title, summary, img = item
    story_slug = "story-" + "-".join(re.sub(r"[^a-z0-9\s-]", "", title.lower()).split()[:4] or ["news"]) + "-" + str(int(time.time()) % 10000)
    story_content = (
        '<div class="web-story-card" style="background:#111;color:#fff;padding:30px;border-radius:12px;">'
        '<span style="background:#d10000;color:#fff;padding:4px 10px;font-size:12px;font-weight:bold;text-transform:uppercase;">Visual Web Story</span>'
        '<h2 style="font-size:24px;margin-top:15px;margin-bottom:15px;">' + title + '</h2>'
        '<img src="' + img + '" style="width:100%;max-height:400px;object-fit:cover;border-radius:8px;margin-bottom:15px;">'
        '<p style="font-size:16px;line-height:1.6;">' + summary + '</p>'
        '</div>'
    )
    try:
        requests.post(S_URL + "/rest/v1/posts", headers=HEADERS, json={"title": "⚡ Story: " + title, "slug": story_slug, "content": story_content, "category": "Web Stories", "image_url": img}, timeout=20)
    except Exception:
        pass

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
    for cat in CATEGORY_HIERARCHY.keys():
        urls = FEEDS_MAP.get(cat, FEEDS_MAP["Breaking News"])
        target = 20 if cat == "Jobs & Careers" else (1 if cat == "Rashifal & Horoscopes" else 8)
        items = collect_unique_posts(urls, cat, target, seen_titles, seen_imgs)
        q.extend(items)

    print("Publishing " + str(len(q)) + " Unique Posts & Web Stories...")
    ok = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(publish_one, it, i + 1, len(q)) for i, it in enumerate(q)]
        for f in as_completed(futs):
            if f.result(): ok += 1
        # Auto-publish Web Stories for top items
        for it in q[:25]:
            ex.submit(publish_story, it)
    print("FINISHED! Published " + str(ok) + " Posts & Web Stories!")

if __name__ == "__main__":
    run()
# DONE
