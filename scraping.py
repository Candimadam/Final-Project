from playwright.sync_api import sync_playwright
import json
import re

# Daftar channel yang akan discrape beserta kategorinya
CHANNELS_URL = [
    {"url": "https://www.youtube.com/@GadgetIn/videos", "category": "Gadgets"},
    {"url": "https://www.youtube.com/@JagatReview/videos", "category": "Gadgets"},
    {"url": "https://www.youtube.com/@GadgetGaul/videos", "category": "Gadgets"},
    {"url": "https://www.youtube.com/@Dhiarcom/videos", "category": "Gadgets"},
    {"url": "https://www.youtube.com/@DKIDchannel/videos", "category": "Gadgets"},
    {"url": "https://www.youtube.com/@PricebookIndonesia/videos", "category": "Gadgets"},
    {"url": "https://www.youtube.com/@Sobat_HAPE/videos", "category": "Gadgets"},
    {"url": "https://www.youtube.com/@projectreview/videos", "category": "Gadgets"},
    {"url": "https://www.youtube.com/@K2G/videos", "category": "Gadgets"},
    {"url": "https://www.youtube.com/@YoutuberCupu/videos", "category": "Gadgets"},
    
    {"url": "https://www.youtube.com/@NexCarlos/videos", "category": "Food"},
    {"url": "https://www.youtube.com/@riasukmawijaya/videos", "category": "Food"},
    {"url": "https://www.youtube.com/@tanboykun/videos", "category": "Food"},
    {"url": "https://www.youtube.com/@KUBILER/videos", "category": "Food"},
    {"url": "https://www.youtube.com/@MamankKuliner/videos", "category": "Food"},
    {"url": "https://www.youtube.com/@Melkibajaj/videos", "category": "Food"},
    {"url": "https://www.youtube.com/@BoengkoesNetwork/videos", "category": "Food"},
    {"url": "https://www.youtube.com/@farida.nurhan/videos", "category": "Food"},
    {"url": "https://www.youtube.com/@Kenandgrat/videos", "category": "Food"},
    {"url": "https://www.youtube.com/@Anak.Kuliner/videos", "category": "Food"},
    
    {"url": "https://www.youtube.com/@Miawaug/videos", "category": "Gaming"},
    {"url": "https://www.youtube.com/@WindahBasudara/videos", "category": "Gaming"},
    {"url": "https://www.youtube.com/@JessNoLimit/videos", "category": "Gaming"},
    {"url": "https://www.youtube.com/@DylandPROS/videos", "category": "Gaming"},
    {"url": "https://www.youtube.com/@rrq_lemon/videos", "category": "Gaming"},
    {"url": "https://www.youtube.com/@BrandonKentEverything/videos", "category": "Gaming"},
    {"url": "https://www.youtube.com/@letdahyper/videos", "category": "Gaming"},
    {"url": "https://www.youtube.com/@MILYHYA/videos", "category": "Gaming"},
    {"url": "https://www.youtube.com/@AfifYulistian/videos", "category": "Gaming"},
    {"url": "https://www.youtube.com/@FrontaLGaming/videos", "category": "Gaming"},
    
    {"url": "https://www.youtube.com/@RansEntertainment/videos", "category": "Entertainment"},
    {"url": "https://www.youtube.com/@corbuzier/videos", "category": "Entertainment"},
    {"url": "https://www.youtube.com/@VINDES/videos", "category": "Entertainment"},
    {"url": "https://www.youtube.com/@radityadika/videos", "category": "Entertainment"},
    {"url": "https://www.youtube.com/@ariefmuhammaddd/videos", "category": "Entertainment"},
    {"url": "https://www.youtube.com/@AttaHalilintar/videos", "category": "Entertainment"},
    {"url": "https://www.youtube.com/@MajelisLucu/videos", "category": "Entertainment"},
    {"url": "https://www.youtube.com/@SPROSULEPRODUCTIONS/videos", "category": "Entertainment"},
    {"url": "https://www.youtube.com/@taulany_tv/videos", "category": "Entertainment"},
    {"url": "https://www.youtube.com/@ybrap/videos", "category": "Entertainment"},
    
    {"url": "https://www.youtube.com/@KokBisa/videos", "category": "Education"},
    {"url": "https://www.youtube.com/@TirtaPengPengPeng/videos", "category": "Education"},
    {"url": "https://www.youtube.com/@SatuPersenIndonesianLifeschool/videos", "category": "Education"},
    {"url": "https://www.youtube.com/@nihongomantappu/videos", "category": "Education"},
    {"url": "https://www.youtube.com/@ZeniusEducation/videos", "category": "Education"},
    {"url": "https://www.youtube.com/@HujanTandaTanya/videos", "category": "Education"},
    {"url": "https://www.youtube.com/@SiKutuBuku/videos", "category": "Education"},
    {"url": "https://www.youtube.com/@BimbelBrilian/videos", "category": "Education"},
    {"url": "https://www.youtube.com/@MalakaProjectid/videos", "category": "Education"},
    {"url": "https://www.youtube.com/@felicia.tjiasaka/videos", "category": "Education"},
    
    {"url": "https://www.youtube.com/@FitraEri/videos", "category": "Automotive"},
    {"url": "https://www.youtube.com/@ridwanhr/videos", "category": "Automotive"},
    {"url": "https://www.youtube.com/@motomobitv/videos", "category": "Automotive"},
    {"url": "https://www.youtube.com/@Otodriver/videos", "category": "Automotive"},
    {"url": "https://www.youtube.com/@AutonetMagz/videos", "category": "Automotive"},
    {"url": "https://www.youtube.com/@Mas-Wahid/videos", "category": "Automotive"},
    {"url": "https://www.youtube.com/@GarasiDrift/videos", "category": "Automotive"},
    {"url": "https://www.youtube.com/@iwanbanaranblog/videos", "category": "Automotive"},
    {"url": "https://www.youtube.com/@carmudiID/videos", "category": "Automotive"},
    {"url": "https://www.youtube.com/@OTOMOTIFTV/videos", "category": "Automotive"},
    
    {"url": "https://www.youtube.com/@PSSITV/videos", "category": "Sports"},
    {"url": "https://www.youtube.com/@IBLTV/videos", "category": "Sports"},
    {"url": "https://www.youtube.com/@officialbaliunited/videos", "category": "Sports"},
    {"url": "https://www.youtube.com/@SportsChannelIndonesia/videos", "category": "Sports"},
    {"url": "https://www.youtube.com/@SPOTV.Indonesia/videos", "category": "Sports"},
    {"url": "https://www.youtube.com/@MNCTV_Sports/videos", "category": "Sports"},
    {"url": "https://www.youtube.com/@CoachJustinl28/videos", "category": "Sports"},
    {"url": "https://www.youtube.com/@ZonaJuaraSports/videos", "category": "Sports"},
    {"url": "https://www.youtube.com/@RCTISports/videos", "category": "Sports"},
    {"url": "https://www.youtube.com/@ArisSportTv/videos", "category": "Sports"},
    
    {"url": "https://www.youtube.com/@MusicaStudios/videos", "category": "Music"},
    {"url": "https://www.youtube.com/@TrinityOptimaProduction/videos", "category": "Music"},
    {"url": "https://www.youtube.com/@NagaswaraOfficial/videos", "category": "Music"},
    {"url": "https://www.youtube.com/@AquariusMusikindo/videos", "category": "Music"},
    {"url": "https://www.youtube.com/@OfficialNoahMusic/videos", "category": "Music"},
    {"url": "https://www.youtube.com/@Judika.Entertainment/videos", "category": "Music"},
    {"url": "https://www.youtube.com/@dennycaknan6996/videos", "category": "Music"},
    {"url": "https://www.youtube.com/@indomusikgram/videos", "category": "Music"},
    {"url": "https://www.youtube.com/@raisa6690/videos", "category": "Music"},
    {"url": "https://www.youtube.com/@Dewa19/videos", "category": "Music"},
    
    {"url": "https://www.youtube.com/@KompasTV/videos", "category": "News"},
    {"url": "https://www.youtube.com/@tvOneNews/videos", "category": "News"},
    {"url": "https://www.youtube.com/@CNNIDOFFICIAL/videos", "category": "News"},
    {"url": "https://www.youtube.com/@metrotvnews/videos", "category": "News"},
    {"url": "https://www.youtube.com/@tribunnews/videos", "category": "News"},
    {"url": "https://www.youtube.com/@OfficialiNews/videos", "category": "News"},
    {"url": "https://www.youtube.com/@liputan6_news/videos", "category": "News"},
    {"url": "https://www.youtube.com/@NarasiNewsroom/videos", "category": "News"},
    {"url": "https://www.youtube.com/@CNBC_ID/videos", "category": "News"},
    {"url": "https://www.youtube.com/@tempovideochannel/videos", "category": "News"},
    
    {"url": "https://www.youtube.com/@PANJIPETUALANG_REAL/videos", "category": "Animals"},
    {"url": "https://www.youtube.com/@AlshadAhmad/videos", "category": "Animals"},
    {"url": "https://www.youtube.com/@deHakimsAviaryIrfanHakim/videos", "category": "Animals"},
    {"url": "https://www.youtube.com/@Audrey-A/videos", "category": "Animals"},
    {"url": "https://www.youtube.com/@LuckyHakimChannel/videos", "category": "Animals"},
    {"url": "https://www.youtube.com/@BeemzAryo/videos", "category": "Animals"},
    {"url": "https://www.youtube.com/@amarpdchannel/videos", "category": "Animals"},
    {"url": "https://www.youtube.com/@Dunia_Alam/videos", "category": "Animals"},
    {"url": "https://www.youtube.com/@deHakims/videos", "category": "Animals"},
    {"url": "https://www.youtube.com/@DuniaBinatangLiar/videos", "category": "Animals"}
]

# Batas maksimal video yang ingin diambil per channel
JUMLAH_VIDEO = 100
# Nama file keluaran JSON
OUTPUT_JSON = "data_video.json"

def parse_views(view_str: str) -> int:
        if not view_str:
                return 0

        view_str = view_str.lower().strip()

        # Ganti koma desimal (format ID) menjadi titik
        if "," in view_str and "." not in view_str:
                view_str = view_str.replace(",", ".")

        # Hapus koma ribuan (format EN)
        view_str = view_str.replace(",", "")

        match = re.search(r"([\d.]+)", view_str)
        if not match:
                return 0

        num = float(match.group(1))

        if "jt" in view_str or "m" in view_str or "million" in view_str:
                num *= 1_000_000
        elif "rb" in view_str or "k" in view_str or "thousand" in view_str:
                num *= 1_000

        return int(num)


def scrape_dataset():
        # Gunakan Playwright sync API untuk membuka browser dan mengendalikan halaman
        with sync_playwright() as p:
                # Launch browser Chromium; headless=False agar terlihat saat debugging
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

                # Menyimpan semua data video dari semua channel
                all_data = []
                # ID unik bertambah untuk tiap video yang diambil
                global_id = 1

                # Loop untuk tiap channel di daftar CHANNELS_URL
                for idx, ch in enumerate(CHANNELS_URL, start=1):
                        channel_url = ch.get("url")
                        category = ch.get("category", "")
                        # Informasi progress scraping ke console
                        print(f"\n🚀 Mulai scraping channel {idx}/{len(CHANNELS_URL)}: {channel_url} (kategori: {category})\n")

                        # Buka halaman videos dari channel
                        page.goto(channel_url, wait_until="networkidle")

                        print("Mulai scroll dan ambil data...\n")

                        # Menyimpan jumlah elemen video sebelum scroll terakhir
                        previous_count = 0
                        # Hitung berapa kali scroll dilakukan
                        scroll_round = 0

                        # Scroll terus sampai mencapai jumlah video yang diinginkan atau tidak ada konten baru
                        while True:
                                scroll_round += 1
                                # Scroll ke bawah sampai ke akhir halaman untuk memicu lazy-load YouTube
                                page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
                                # Tunggu sampai network idle untuk memastikan resource dimuat
                                page.wait_for_load_state("networkidle")
                                # Tambahan jeda singkat agar elemen DOM sempat muncul
                                page.wait_for_timeout(1000)

                                # Hitung jumlah elemen video (selector ytd-rich-grid-media)
                                current_count = len(page.query_selector_all("ytd-rich-grid-media"))
                                print(f"🔁 Scroll ke-{scroll_round}: {current_count} video ditemukan")

                                # Berhenti jika sudah lebih dari batas yang diinginkan
                                if current_count > JUMLAH_VIDEO:
                                        print(f"\n✅ Tercapai {current_count} video (> {JUMLAH_VIDEO}), berhenti scroll.\n")
                                        break

                                # Jika tidak ada perubahan jumlah elemen setelah scroll, berhenti juga
                                if current_count == previous_count:
                                        print("\n⚠️ Tidak ada video baru yang dimuat, berhenti.\n")
                                        break

                                previous_count = current_count

                        # Ambil semua elemen video yang ada dan batasi sesuai JUMLAH_VIDEO
                        video_elements = page.locator("ytd-rich-grid-media").all()[:JUMLAH_VIDEO]

                        # Ambil nama channel dari header; gunakan try/except karena selector bisa berubah
                        try:
                                channel_name = page.locator("yt-content-metadata-view-model div:nth-child(1)").inner_text()
                        except Exception:
                                channel_name = ""  # Fallback jika selector tidak ditemukan

                        # Ambil jumlah pelanggan (subscriber); selector spesifik dan rentan berubah
                        try:
                                subscriber_count = page.locator(
                                        "#page-header > yt-page-header-renderer > yt-page-header-view-model > div > div.yt-page-header-view-model__page-header-headline > div > yt-content-metadata-view-model > div:nth-child(3) > span:nth-child(1)"
                                ).text_content()
                        except Exception:
                                subscriber_count = None  # Fallback ke None jika error

                        # Loop untuk setiap elemen video yang ditemukan pada halaman
                        for video in video_elements:
                                # Ambil judul video dengan aman (handle exception jika selector tidak sesuai)
                                try:
                                        title = video.locator("yt-formatted-string#video-title").inner_text()
                                except Exception:
                                        title = ""

                                # Ambil link video; normalisasi jika href relatif (dimulai dengan "/")
                                try:
                                        href = video.locator("a#video-title-link").get_attribute("href")
                                        link = "https://www.youtube.com" + href if href and href.startswith("/") else href
                                except Exception:
                                        link = None

                                # Metadata seperti jumlah tayangan dan waktu upload biasanya berada di span.inline-metadata-item
                                try:
                                        meta_items = video.locator("span.inline-metadata-item").all()
                                        views_text = meta_items[0].inner_text() if len(meta_items) > 0 else "0"
                                        upload_text = meta_items[1].inner_text() if len(meta_items) > 1 else ""
                                except Exception:
                                        # Jika gagal mengambil metadata, gunakan nilai default
                                        views_text = "0"
                                        upload_text = ""

                                # Tambahkan data video ke list all_data dalam bentuk dict (tanpa thumbnail)
                                all_data.append(
                                        {
                                                "id": global_id,
                                                "link_channel": channel_url,
                                                "nama_channel": channel_name,
                                                "kategori": category,
                                                # parse_views digunakan untuk normalisasi teks jumlah (contoh. "1,2 rb" -> angka)
                                                "jumlah_pelanggan": parse_views(subscriber_count) if subscriber_count else None,
                                                "judul": title,
                                                "link": link,
                                                # parse_views juga dipakai untuk jumlah tayangan
                                                "jumlah_tayangan": parse_views(views_text) if views_text else None,
                                                "tanggal_upload": upload_text,
                                        }
                                )

                                # Informasi log setiap video yang berhasil diambil
                                print(f"📥 [{channel_name}] Mengambil data video id-{global_id}: {title}")
                                global_id += 1

                # Tutup browser setelah selesai scraping semua channel
                browser.close()

                return all_data


if __name__ == "__main__":
        data_hasil = scrape_dataset()

        # Simpan hasil scraping ke file JSON jika ada data
        if data_hasil:
                with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                        json.dump(data_hasil, f, ensure_ascii=False, indent=4)
                print(f"\n🎉 Berhasil! Data telah disimpan ke file '{OUTPUT_JSON}'")
        else:
                # Jika tidak ada data yang berhasil, tampilkan pesan
                print("\nTidak ada data yang berhasil diambil.")
