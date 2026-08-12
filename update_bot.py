import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

BASE_URL = "https://fixbettv83.com/"
CHANNEL_IDS = {
    "zirve": "Bein Sports 1",
    "b2": "Bein Sports 2",
    # ... diğer tüm kanal ID'leri
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9"
}

def fetch_page(url):
    """Sayfayı indir ve BeautifulSoup nesnesi döndür."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "lxml")
    except Exception as e:
        print(f"⚠️ Hata ({url}): {e}")
        return None

def parse_stream_url(soup):
    """
    Kanal sayfasından gerçek m3u8 linkini çıkar.
    Örnek: <iframe src="...m3u8..."> veya <video src="...">
    """
    if not soup:
        return None

    # 1. Yöntem: iframe içinde ara
    iframe = soup.find("iframe")
    if iframe and iframe.get("src"):
        src = iframe["src"]
        if ".m3u8" in src:
            return src
        # Eğer iframe başka bir sayfaya gidiyorsa, o sayfayı da çek
        if src.startswith("http"):
            nested_soup = fetch_page(src)
            return parse_stream_url(nested_soup)

    # 2. Yöntem: video etiketinde ara
    video = soup.find("video")
    if video and video.get("src"):
        return video["src"]

    # 3. Yöntem: script içinde m3u8 patterni ara
    import re
    pattern = re.compile(r'(https?://\S+\.m3u8[^\s"\']*)')
    scripts = soup.find_all("script")
    for script in scripts:
        if script.string:
            match = pattern.search(script.string)
            if match:
                return match.group(1)

    return None

def parse_matches(soup):
    """
    Günün maç listesini çıkar.
    Sitenin maç listesi yapısına göre uyarlayın.
    """
    matches = []
    # Örnek: her maç .match-card sınıfında olabilir
    cards = soup.select(".match-card") if soup else []
    for card in cards:
        home = card.select_one(".home-team").get_text(strip=True)
        away = card.select_one(".away-team").get_text(strip=True)
        time_ = card.select_one(".match-time").get_text(strip=True)
        league = card.select_one(".league").get_text(strip=True)
        channel = card.select_one(".channel").get_text(strip=True)
        matches.append({
            "home": home,
            "away": away,
            "time": time_,
            "league": league,
            "channel": channel
        })
    return matches

def update_streams():
    """Tüm kanallar için stream linklerini topla ve streams.json'a yaz."""
    streams = {}
    for channel_id, channel_name in CHANNEL_IDS.items():
        print(f"🔄 {channel_name} kontrol ediliyor...")
        soup = fetch_page(f"{BASE_URL}channel?id={channel_id}")
        url = parse_stream_url(soup)
        if url:
            streams[channel_id] = {
                "name": channel_name,
                "url": url,
                "updated_at": datetime.utcnow().isoformat() + "Z"
            }
            print(f"   ✅ Link bulundu: {url[:60]}...")
        else:
            print(f"   ❌ Link bulunamadı")
        time.sleep(2)  # Sunucuyu yormamak için bekleme

    with open("streams.json", "w", encoding="utf-8") as f:
        json.dump(streams, f, ensure_ascii=False, indent=2)
    print(f"💾 streams.json güncellendi ({len(streams)} kanal)")

def update_matches():
    """Günün maçlarını çek ve matches.json'a yaz."""
    print("⚽ Maçlar kontrol ediliyor...")
    soup = fetch_page(BASE_URL)  # veya maçların olduğu sayfa
    matches = parse_matches(soup)
    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "matches": matches
    }
    with open("matches.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 matches.json güncellendi ({len(matches)} maç)")

if __name__ == "__main__":
    update_streams()
    update_matches()
