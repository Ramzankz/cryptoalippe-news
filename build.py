#!/usr/bin/env python3
"""CryptoAlippe News — static site builder.
Reads the public Telegram channel t.me/s/cryptoalippe_news, keeps every post in data/posts.json,
downloads post images, and writes an SEO-friendly static site into ./site for GitHub Pages.
Runs in GitHub Actions every 2 hours; no secrets needed (the channel is public).
"""
import html, json, os, re, sys, time, urllib.request
from datetime import datetime, timezone, timedelta

CHANNEL = "cryptoalippe_news"
MAIN = "asilekcrypto"
BASE = os.environ.get("SITE_BASE", "https://ramzankz.github.io/cryptoalippe-news").rstrip("/")
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data", "posts.json")
SITE = os.path.join(ROOT, "site")
TZ = timezone(timedelta(hours=5))
UA = {"User-Agent": "Mozilla/5.0 (compatible; CryptoAlippeNewsBuilder/1.0)"}
MONTHS = ["қаңтар", "ақпан", "наурыз", "сәуір", "мамыр", "маусым", "шілде", "тамыз", "қыркүйек", "қазан", "қараша", "желтоқсан"]


def get(url, binary=False):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                b = r.read()
                return b if binary else b.decode("utf-8", "replace")
        except Exception as e:
            if i == 2:
                raise
            time.sleep(3)


def strip(s):
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()


def parse(page):
    posts = []
    for blk in re.split(r'<div class="tgme_widget_message_wrap', page)[1:]:
        m = re.search(r'data-post="%s/(\d+)"' % CHANNEL, blk)
        if not m:
            continue
        pid = int(m.group(1))
        t = re.search(r'<time datetime="([^"]+)"', blk)
        txt = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>', blk, re.S)
        img = re.search(r"tgme_widget_message_photo_wrap[^>]*background-image:url\('([^']+)'\)", blk)
        if not txt:
            continue
        raw = txt.group(1)
        link = re.search(r'<a href="(https?://[^"]+)"', raw)
        text = strip(raw)
        if not text:
            continue
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        posts.append({
            "id": pid,
            "date": t.group(1) if t else "",
            "title": lines[0],
            "body": lines[1:],
            "link": link.group(1) if link and "t.me/" not in link.group(1) else "",
            "img_src": img.group(1) if img else "",
        })
    return posts


def slug_date(iso):
    try:
        d = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(TZ)
        return d, f"{d.day} {MONTHS[d.month-1]} {d.year}, {d:%H:%M}"
    except Exception:
        return None, ""


def clean_title(t):
    return re.sub(r"^[^\wА-Яа-яӘәҒғҚқҢңӨөҰұҮүҺһІі$]+", "", t).strip() or t


def is_news(p):
    # funnel posts that only invite to the main channel are not news articles
    j = " ".join([p["title"]] + p["body"])
    return not ("asilekcrypto" in j or "Assila Crypto" in j) or bool(p["link"])


CSS = """
:root{--bg:#f6f4ef;--card:#fff;--ink:#14161f;--muted:#5d6273;--line:#e6e2d8;--acc:#f5a300;--acc2:#12b76a;--tg:#229ed9}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0d0f17;--card:#161927;--ink:#f2f2f5;--muted:#a3a8bb;--line:#262a3c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Montserrat,system-ui,sans-serif;line-height:1.55}
a{color:inherit}.wrap{max-width:760px;margin:0 auto;padding:0 16px}
header{background:linear-gradient(135deg,#5ee7b0,#34c3ff);color:#0b1020}
header .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 16px}
.brand{font-weight:800;font-size:20px;text-decoration:none}.brand b{background:#111;color:#ffd24a;padding:2px 8px;border-radius:8px;margin-left:4px}
.tg{display:inline-flex;align-items:center;gap:8px;background:var(--tg);color:#fff!important;text-decoration:none;font-weight:700;padding:10px 16px;border-radius:999px;white-space:nowrap}
.tg:hover{filter:brightness(1.08)}
.hero{padding:28px 0 8px}.hero h1{font-size:28px;line-height:1.2;margin:0 0 8px}.hero p{color:var(--muted);margin:0}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:18px;overflow:hidden;margin:16px 0;text-decoration:none}
.card img{width:100%;display:block;aspect-ratio:3/2;object-fit:cover}
.card .in{padding:14px 18px 18px}.card h2{font-size:19px;line-height:1.3;margin:4px 0 6px}
.meta{font-size:13px;color:var(--muted)}.card p{margin:0;color:var(--muted)}
article{background:var(--card);border:1px solid var(--line);border-radius:18px;overflow:hidden;margin:20px 0}
article img{width:100%;display:block}article .in{padding:18px 20px 24px}article h1{font-size:24px;line-height:1.25;margin:6px 0 14px}
article p{font-size:17px;margin:0 0 12px}
.cta{background:linear-gradient(135deg,#111827,#1e293b);color:#fff;border-radius:18px;padding:20px;margin:20px 0;display:flex;flex-wrap:wrap;gap:14px;align-items:center;justify-content:space-between}
.cta strong{font-size:18px;display:block}.cta span{opacity:.8;font-size:14px}
.more{display:flex;justify-content:space-between;gap:10px;margin:10px 0 30px;flex-wrap:wrap}
.btn{border:1px solid var(--line);background:var(--card);padding:10px 16px;border-radius:12px;text-decoration:none;font-weight:600}
footer{color:var(--muted);font-size:13px;padding:24px 0 40px;text-align:center}
.src{font-size:14px;color:var(--muted)}
"""

HEAD = """<!doctype html><html lang="kk"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title><meta name="description" content="{desc}"><link rel="canonical" href="{url}">
<meta property="og:type" content="{ogtype}"><meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{image}"><meta property="og:locale" content="kk_KZ">
<meta name="twitter:card" content="summary_large_image"><link rel="alternate" type="application/rss+xml" title="CryptoAlippe News" href="{base}/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800&display=swap" rel="stylesheet">
<style>{css}</style>{ld}</head><body>
<header><div class="wrap"><a class="brand" href="{base}/">CryptoAlippe<b>NEWS</b></a>
<a class="tg" href="https://t.me/{ch}" rel="noopener">✈️ Telegram-ға жазылу</a></div></header><main class="wrap">"""

FOOT = """</main><footer class="wrap">© CryptoAlippe · Крипто жаңалықтар қазақ тілінде · Қаржылық кеңес емес.<br>
<a href="https://t.me/{ch}">Telegram: CryptoAlippe News</a> · <a href="https://t.me/{main}">Assila Crypto</a></footer></body></html>"""

CTA = """<div class="cta"><div><strong>Жаңалықтарды бірінші болып біліңіз 🔔</strong><span>Күн сайын ең маңызды крипто жаңалықтар — қазақ тілінде, қысқа әрі түсінікті.</span></div>
<a class="tg" href="https://t.me/{ch}">✈️ Жазылу</a></div>"""


def e(s):
    return html.escape(s, quote=True)


def page(title, desc, url, image, body, ogtype="website", ld=""):
    return HEAD.format(title=e(title), desc=e(desc), url=url, image=image, base=BASE, css=CSS, ch=CHANNEL, ogtype=ogtype, ld=ld) + body + FOOT.format(ch=CHANNEL, main=MAIN)


def main():
    os.makedirs(os.path.dirname(DATA), exist_ok=True)
    store = {}
    if os.path.exists(DATA):
        store = {str(p["id"]): p for p in json.load(open(DATA, encoding="utf-8"))}
    # newest page, then walk back until we reach posts we already have (or 15 pages on first run)
    url = f"https://t.me/s/{CHANNEL}"
    for _ in range(15):
        got = parse(get(url))
        if not got:
            break
        new = [p for p in got if str(p["id"]) not in store]
        for p in got:
            old = store.get(str(p["id"]), {})
            p["img"] = old.get("img", "")
            store[str(p["id"])] = p
        if store and not new and len(store) > len(got):
            break
        url = f"https://t.me/s/{CHANNEL}?before={min(p['id'] for p in got)}"
        time.sleep(1)

    os.makedirs(os.path.join(SITE, "p"), exist_ok=True)
    os.makedirs(os.path.join(SITE, "img"), exist_ok=True)
    img_dir = os.path.join(ROOT, "img")
    os.makedirs(img_dir, exist_ok=True)
    for p in store.values():
        if p.get("img_src") and not p.get("img"):
            fn = f"{p['id']}.jpg"
            try:
                open(os.path.join(img_dir, fn), "wb").write(get(p["img_src"], binary=True))
                p["img"] = fn
            except Exception as ex:
                print("img fail", p["id"], ex, file=sys.stderr)
    json.dump(sorted(store.values(), key=lambda p: p["id"]), open(DATA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # copy images into site
    for fn in os.listdir(img_dir):
        src, dst = os.path.join(img_dir, fn), os.path.join(SITE, "img", fn)
        if not os.path.exists(dst):
            open(dst, "wb").write(open(src, "rb").read())

    posts = sorted([p for p in store.values() if is_news(p)], key=lambda p: p["id"], reverse=True)
    default_img = f"{BASE}/img/{posts[0]['img']}" if posts and posts[0].get("img") else ""

    def card(p):
        d, ds = slug_date(p["date"])
        im = f'<img loading="lazy" src="{BASE}/img/{p["img"]}" alt="{e(clean_title(p["title"]))}">' if p.get("img") else ""
        return f'<a class="card" href="{BASE}/p/{p["id"]}.html">{im}<div class="in"><div class="meta">{ds}</div><h2>{e(p["title"])}</h2><p>{e(p["body"][0] if p["body"] else "")}</p></div></a>'

    # article pages
    for i, p in enumerate(posts):
        d, ds = slug_date(p["date"])
        t = clean_title(p["title"])
        desc = " ".join(p["body"])[:155]
        img = f"{BASE}/img/{p['img']}" if p.get("img") else default_img
        u = f"{BASE}/p/{p['id']}.html"
        ld = '<script type="application/ld+json">' + json.dumps({
            "@context": "https://schema.org", "@type": "NewsArticle", "headline": t[:110], "inLanguage": "kk",
            "datePublished": p["date"], "dateModified": p["date"], "image": [img] if img else [],
            "author": {"@type": "Organization", "name": "CryptoAlippe"},
            "publisher": {"@type": "Organization", "name": "CryptoAlippe News"},
            "mainEntityOfPage": u, "description": desc}, ensure_ascii=False) + "</script>"
        paras = "".join(f"<p>{e(x)}</p>" for x in p["body"])
        src = f'<p class="src">Дереккөз: <a href="{e(p["link"])}" rel="nofollow noopener">түпнұсқа мақала</a></p>' if p["link"] else ""
        im = f'<img src="{img}" alt="{e(t)}">' if p.get("img") else ""
        nav = '<div class="more">'
        if i + 1 < len(posts):
            nav += f'<a class="btn" href="{BASE}/p/{posts[i+1]["id"]}.html">← Алдыңғы жаңалық</a>'
        nav += f'<a class="btn" href="{BASE}/">Барлық жаңалықтар</a>'
        if i > 0:
            nav += f'<a class="btn" href="{BASE}/p/{posts[i-1]["id"]}.html">Келесі жаңалық →</a>'
        nav += "</div>"
        body = f'<article>{im}<div class="in"><div class="meta">{ds}</div><h1>{e(p["title"])}</h1>{paras}{src}</div></article>' + CTA.format(ch=CHANNEL) + nav
        body += "<h2>Тағы оқыңыз</h2>" + "".join(card(q) for q in posts[max(0, i-2):i] + posts[i+1:i+4])
        open(os.path.join(SITE, "p", f"{p['id']}.html"), "w", encoding="utf-8").write(
            page(f"{t} — крипто жаңалық қазақша | CryptoAlippe", desc, u, img, body, "article", ld))

    # index pages (30 per page)
    per = 30
    pages = max(1, (len(posts) + per - 1) // per)
    for n in range(pages):
        chunk = posts[n*per:(n+1)*per]
        hero = ('<section class="hero"><h1>Крипто жаңалықтар қазақ тілінде</h1>'
                '<p>Биткоин, Ethereum, биржалар, Қазақстандағы реттеу — ең маңызды жаңалықтар күн сайын, қысқа әрі түсінікті.</p></section>' + CTA.format(ch=CHANNEL)) if n == 0 else f"<section class='hero'><h1>Крипто жаңалықтар — {n+1}-бет</h1></section>"
        nav = '<div class="more">'
        if n > 0:
            nav += f'<a class="btn" href="{BASE}/{"index" if n == 1 else f"page{n}"}.html">← Жаңарақ</a>'
        if n + 1 < pages:
            nav += f'<a class="btn" href="{BASE}/page{n+2}.html">Ескірек →</a>'
        nav += "</div>"
        fn = "index.html" if n == 0 else f"page{n+1}.html"
        open(os.path.join(SITE, fn), "w", encoding="utf-8").write(page(
            "Крипто жаңалықтар қазақша — биткоин, Ethereum, биржалар | CryptoAlippe News" if n == 0 else f"Крипто жаңалықтар қазақша — {n+1}-бет | CryptoAlippe News",
            "Крипто жаңалықтар қазақ тілінде: биткоин, Ethereum, биржалар, Қазақстандағы криптовалюта реттеуі. Күн сайын жаңартылады.",
            f"{BASE}/" if n == 0 else f"{BASE}/{fn}", default_img, hero + "".join(card(p) for p in chunk) + nav))

    # sitemap, robots, rss, 404
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', f"<url><loc>{BASE}/</loc><lastmod>{now}</lastmod><changefreq>hourly</changefreq></url>"]
    sm += [f"<url><loc>{BASE}/p/{p['id']}.html</loc><lastmod>{p['date'] or now}</lastmod></url>" for p in posts]
    sm.append("</urlset>")
    open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(sm))
    open(os.path.join(SITE, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    items = "".join(
        f"<item><title>{e(clean_title(p['title']))}</title><link>{BASE}/p/{p['id']}.html</link><guid>{BASE}/p/{p['id']}.html</guid>"
        f"<pubDate>{slug_date(p['date'])[0].strftime('%a, %d %b %Y %H:%M:%S %z') if slug_date(p['date'])[0] else ''}</pubDate><description>{e(' '.join(p['body']))}</description></item>"
        for p in posts[:50])
    open(os.path.join(SITE, "feed.xml"), "w", encoding="utf-8").write(
        f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>CryptoAlippe News — крипто жаңалықтар қазақша</title><link>{BASE}/</link><description>Крипто жаңалықтар қазақ тілінде</description><language>kk</language>{items}</channel></rss>')
    open(os.path.join(SITE, "404.html"), "w", encoding="utf-8").write(page("Бет табылмады | CryptoAlippe News", "Бет табылмады", f"{BASE}/404.html", default_img,
        f'<section class="hero"><h1>Бет табылмады 😕</h1><p><a href="{BASE}/">Барлық жаңалықтарға оралу</a></p></section>' + CTA.format(ch=CHANNEL)))
    open(os.path.join(SITE, ".nojekyll"), "w").write("")
    print(f"built {len(posts)} articles, {pages} index pages")


if __name__ == "__main__":
    main()
