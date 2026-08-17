"""Seed data for QuizArena: questions, shop, achievements, quests, modes, bots, season."""
import uuid
from datetime import timedelta

from core import db, now_utc, CATEGORIES, LEAGUES

AVATAR_POOL = [
    "https://images.pexels.com/photos/7773546/pexels-photo-7773546.jpeg",
    "https://images.unsplash.com/photo-1648736958777-a7a9479d72d8",
    "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde",
    "https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg",
    "https://images.pexels.com/photos/1languages.jpeg",
]


# -------- Questions (Turkish) --------
def _q(text, options, ci, cat, diff, expl, src):
    return {
        "id": f"q_{uuid.uuid4().hex[:12]}",
        "text": text, "options": options, "correctIndex": ci,
        "category": cat, "difficulty": diff, "type": "TEXT",
        "audioUrl": None, "imageUrl": None, "explanation": expl, "source": src,
        "usageCount": 0, "correctRate": 0.0, "reportCount": 0,
        "isActive": True, "verifiedAt": now_utc(), "createdAt": now_utc(),
    }


SEED_QUESTIONS = [
    _q("Türkiye'nin başkenti neresidir?", ["İstanbul", "Ankara", "İzmir", "Bursa"], 1, "GEOGRAPHY", 1, "Ankara 1923'te başkent ilan edildi.", "Coğrafya"),
    _q("Dünyanın en uzun nehri hangisidir?", ["Amazon", "Nil", "Yangtze", "Mississippi"], 1, "GEOGRAPHY", 2, "Nil Nehri yaklaşık 6650 km uzunluğundadır.", "Coğrafya"),
    _q("Hangi ülke 'Doğan Güneşin Ülkesi' olarak bilinir?", ["Çin", "Kore", "Japonya", "Tayland"], 2, "GEOGRAPHY", 2, "Japonya bu lakapla anılır.", "Coğrafya"),
    _q("Everest Dağı hangi sıradağlardadır?", ["Alpler", "And", "Himalaya", "Kayalık Dağlar"], 2, "GEOGRAPHY", 2, "Everest Himalayalar'da yer alır.", "Coğrafya"),

    _q("Işık hızı saniyede yaklaşık kaç km'dir?", ["300.000", "150.000", "1.000.000", "30.000"], 0, "SCIENCE", 2, "Işık boşlukta saniyede ~300.000 km yol alır.", "Fizik"),
    _q("Suyun kimyasal formülü nedir?", ["CO2", "H2O", "O2", "NaCl"], 1, "SCIENCE", 1, "Su iki hidrojen ve bir oksijenden oluşur.", "Kimya"),
    _q("İnsan vücudunda kaç kemik vardır?", ["206", "201", "215", "189"], 0, "SCIENCE", 3, "Yetişkin insanda 206 kemik bulunur.", "Biyoloji"),
    _q("Periyodik tabloda 'O' sembolü neyi ifade eder?", ["Altın", "Oksijen", "Osmiyum", "Oganesson"], 1, "SCIENCE", 1, "O, oksijenin sembolüdür.", "Kimya"),

    _q("İstanbul'u fetheden Osmanlı padişahı kimdir?", ["Yavuz Sultan Selim", "Fatih Sultan Mehmet", "Kanuni", "Orhan Gazi"], 1, "HISTORY", 1, "II. Mehmet 1453'te İstanbul'u fethetti.", "Tarih"),
    _q("Birinci Dünya Savaşı hangi yıl başladı?", ["1914", "1918", "1939", "1905"], 0, "HISTORY", 2, "Savaş 1914'te başladı.", "Tarih"),
    _q("Türkiye Cumhuriyeti hangi yıl kuruldu?", ["1920", "1923", "1919", "1938"], 1, "HISTORY", 1, "Cumhuriyet 29 Ekim 1923'te ilan edildi.", "Tarih"),
    _q("Mısır piramitleri hangi medeniyete aittir?", ["Roma", "Yunan", "Antik Mısır", "Pers"], 2, "HISTORY", 1, "Piramitler Antik Mısır'a aittir.", "Tarih"),

    _q("İlk programlanabilir bilgisayar dillerinden biri hangisidir?", ["Python", "FORTRAN", "Swift", "Kotlin"], 1, "TECHNOLOGY", 3, "FORTRAN 1957'de geliştirildi.", "Teknoloji"),
    _q("HTTP neyin kısaltmasıdır?", ["HyperText Transfer Protocol", "High Transfer Text Protocol", "Hyper Tool Transfer Process", "Home Text Transfer Protocol"], 0, "TECHNOLOGY", 2, "HTTP = HyperText Transfer Protocol.", "Teknoloji"),
    _q("Hangi şirket iPhone'u üretir?", ["Samsung", "Apple", "Google", "Huawei"], 1, "TECHNOLOGY", 1, "iPhone Apple tarafından üretilir.", "Teknoloji"),
    _q("RAM neyin kısaltmasıdır?", ["Random Access Memory", "Read Access Memory", "Rapid Access Module", "Run Access Memory"], 0, "TECHNOLOGY", 2, "RAM = Random Access Memory.", "Teknoloji"),

    _q("Bir futbol takımında sahada kaç oyuncu bulunur?", ["9", "10", "11", "12"], 2, "SPORTS", 1, "Her takımda 11 oyuncu sahada yer alır.", "Spor"),
    _q("Olimpiyat oyunları kaç yılda bir düzenlenir?", ["2", "3", "4", "5"], 2, "SPORTS", 1, "Yaz Olimpiyatları 4 yılda bir yapılır.", "Spor"),
    _q("Basketbolda bir potaya atılan normal sayı kaç puandır?", ["1", "2", "3", "4"], 1, "SPORTS", 1, "Saha içi normal basket 2 puandır.", "Spor"),
    _q("Tenis turnuvası 'Wimbledon' hangi ülkede yapılır?", ["ABD", "Fransa", "İngiltere", "Avustralya"], 2, "SPORTS", 2, "Wimbledon İngiltere'de düzenlenir.", "Spor"),

    _q("Mona Lisa tablosunu kim yapmıştır?", ["Van Gogh", "Picasso", "Leonardo da Vinci", "Michelangelo"], 2, "ART_CULTURE", 1, "Mona Lisa Leonardo da Vinci'nin eseridir.", "Sanat"),
    _q("Hangi sanat akımı Salvador Dali ile özdeşleşmiştir?", ["Kübizm", "Sürrealizm", "Empresyonizm", "Barok"], 1, "ART_CULTURE", 3, "Dali sürrealizmin öncülerindendir.", "Sanat"),

    _q("Beethoven hangi alanda ünlüdür?", ["Resim", "Müzik", "Edebiyat", "Heykel"], 1, "MUSIC", 1, "Beethoven ünlü bir bestecidir.", "Müzik"),
    _q("Bir oktav kaç nota içerir?", ["5", "7", "8", "12"], 2, "MUSIC", 2, "Bir oktav 8 nota içerir (do-do).", "Müzik"),

    _q("'Titanic' filminin yönetmeni kimdir?", ["Steven Spielberg", "James Cameron", "Christopher Nolan", "Ridley Scott"], 1, "CINEMA", 2, "Titanic'i James Cameron yönetti.", "Sinema"),
    _q("Hangi film 'Oscar' ödülünü ilk kazanan animasyondur?", ["Shrek", "Toy Story", "Güzel ve Çirkin", "Aslan Kral"], 0, "CINEMA", 3, "Shrek en iyi animasyon Oscar'ını kazandı.", "Sinema"),

    _q("'Suç ve Ceza' romanının yazarı kimdir?", ["Tolstoy", "Dostoyevski", "Çehov", "Puşkin"], 1, "LITERATURE", 2, "Eser Dostoyevski'ye aittir.", "Edebiyat"),
    _q("'İnce Memed' romanı kimin eseridir?", ["Orhan Pamuk", "Yaşar Kemal", "Sabahattin Ali", "Reşat Nuri"], 1, "LITERATURE", 2, "İnce Memed Yaşar Kemal'in romanıdır.", "Edebiyat"),

    _q("Yunan mitolojisinde tanrıların kralı kimdir?", ["Poseidon", "Zeus", "Hades", "Apollon"], 1, "MYTHOLOGY", 1, "Zeus Olimpos'un kralıdır.", "Mitoloji"),
    _q("Thor hangi mitolojinin tanrısıdır?", ["Yunan", "Roma", "İskandinav", "Mısır"], 2, "MYTHOLOGY", 2, "Thor İskandinav mitolojisinin tanrısıdır.", "Mitoloji"),

    _q("Pizza hangi ülkenin geleneksel yemeğidir?", ["Fransa", "İtalya", "İspanya", "Yunanistan"], 1, "FOOD", 1, "Pizza İtalya kökenlidir.", "Yemek"),
    _q("Sushi hangi ülkeye aittir?", ["Çin", "Kore", "Japonya", "Vietnam"], 2, "FOOD", 1, "Sushi Japon mutfağına aittir.", "Yemek"),

    _q("Dünyanın en büyük memeli hayvanı hangisidir?", ["Fil", "Mavi balina", "Zürafa", "Gergedan"], 1, "NATURE", 2, "Mavi balina en büyük memelidir.", "Doğa"),
    _q("Bal hangi hayvan tarafından üretilir?", ["Karınca", "Arı", "Kelebek", "Sinek"], 1, "NATURE", 1, "Bal arılar tarafından üretilir.", "Doğa"),

    _q("Birleşmiş Milletler kaç yılında kuruldu?", ["1945", "1950", "1939", "1960"], 0, "POLITICS", 3, "BM 1945'te kuruldu.", "Siyaset"),
    _q("Bir ülkenin para politikasını genellikle hangi kurum yönetir?", ["Meclis", "Merkez Bankası", "Belediye", "Mahkeme"], 1, "ECONOMY", 2, "Merkez Bankası para politikasını yürütür.", "Ekonomi"),

    _q("'Minecraft' oyununda ana karakterin adı nedir?", ["Steve", "Mario", "Link", "Kratos"], 0, "GAMING", 1, "Minecraft'ın ikonik karakteri Steve'dir.", "Oyun"),
    _q("'The Legend of Zelda' serisinin kahramanı kimdir?", ["Zelda", "Link", "Ganon", "Mario"], 1, "GAMING", 2, "Oyunun kahramanı Link'tir.", "Oyun"),

    _q("'Naruto' hangi türde bir yapımdır?", ["Disney filmi", "Anime", "Belgesel", "Dizi"], 1, "ANIMATION", 1, "Naruto popüler bir anime serisidir.", "Animasyon"),
    _q("'Tom ve Jerry' çizgi filminde Tom hangi hayvandır?", ["Köpek", "Kedi", "Fare", "Kuş"], 1, "ANIMATION", 1, "Tom bir kedidir.", "Animasyon"),
]


SHOP_ITEMS = [
    {"id": "frame_gold", "name": "Altın Çerçeve", "description": "Şampiyonlara özel altın çerçeve", "type": "FRAME", "imageUrl": "https://images.unsplash.com/photo-1513346940221-6f673d962e97", "animationUrl": None, "coinPrice": 500, "isActive": True},
    {"id": "frame_neon", "name": "Neon Çerçeve", "description": "Parlayan neon çerçeve", "type": "FRAME", "imageUrl": "https://images.pexels.com/photos/2248589/pexels-photo-2248589.jpeg", "animationUrl": None, "coinPrice": 350, "isActive": True},
    {"id": "frame_fire", "name": "Ateş Çerçevesi", "description": "Alev alev bir görünüm", "type": "FRAME", "imageUrl": "https://images.unsplash.com/photo-1490750967868-88aa4486c946", "animationUrl": None, "coinPrice": 400, "isActive": True},
    {"id": "avatar_neon", "name": "Neon Oyuncu", "description": "Neon tarzı avatar", "type": "AVATAR", "imageUrl": "https://images.pexels.com/photos/7773546/pexels-photo-7773546.jpeg", "animationUrl": None, "coinPrice": 250, "isActive": True},
    {"id": "avatar_red", "name": "Kırmızı Ceket", "description": "Stil sahibi avatar", "type": "AVATAR", "imageUrl": "https://images.unsplash.com/photo-1648736958777-a7a9479d72d8", "animationUrl": None, "coinPrice": 250, "isActive": True},
    {"id": "card_galaxy", "name": "Galaksi Kartı", "description": "Profil kartı arka planı", "type": "CARD", "imageUrl": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564", "animationUrl": None, "coinPrice": 300, "isActive": True},
    {"id": "effect_confetti", "name": "Konfeti Efekti", "description": "Galibiyette konfeti", "type": "VICTORY_ANIMATION", "imageUrl": "https://images.pexels.com/photos/6532364/pexels-photo-6532364.jpeg", "animationUrl": None, "coinPrice": 200, "isActive": True},
    {"id": "effect_entry", "name": "Giriş Efekti", "description": "Maça görkemli giriş", "type": "ENTRY_EFFECT", "imageUrl": "https://images.unsplash.com/photo-1534224039826-c7a0eda0e6b3", "animationUrl": None, "coinPrice": 180, "isActive": True},
    {"id": "title_legend", "name": "Efsane Ünvanı", "description": "'Efsane' ünvanı", "type": "TITLE", "imageUrl": "https://images.unsplash.com/photo-1578269174936-2709b6aeb913", "animationUrl": None, "coinPrice": 600, "isActive": True},
    {"id": "title_master", "name": "Usta Ünvanı", "description": "'Usta' ünvanı", "type": "TITLE", "imageUrl": "https://images.unsplash.com/photo-1578269174936-2709b6aeb913", "animationUrl": None, "coinPrice": 450, "isActive": True},
    {"id": "badge_crown", "name": "Taç Rozeti", "description": "Kraliyet rozeti", "type": "BADGE", "imageUrl": "https://images.pexels.com/photos/6532364/pexels-photo-6532364.jpeg", "animationUrl": None, "coinPrice": 320, "isActive": True},
    {"id": "emoji_pack_1", "name": "Emoji Paketi", "description": "Maç içi emoji seti", "type": "EMOJI_PACK", "imageUrl": "https://images.unsplash.com/photo-1535378620166-273708d44e4c", "animationUrl": None, "coinPrice": 150, "isActive": True},
]


ACHIEVEMENTS = [
    {"id": "ach_first_blood", "key": "first_blood", "title": "İlk Kan", "description": "İlk maçı kazan", "iconUrl": "https://images.unsplash.com/photo-1578269174936-2709b6aeb913", "coinReward": 50, "xpReward": 50},
    {"id": "ach_wise", "key": "wise", "title": "Bilge", "description": "100 soruyu doğru cevapla", "iconUrl": "https://images.unsplash.com/photo-1578269174936-2709b6aeb913", "coinReward": 200, "xpReward": 50},
    {"id": "ach_legend", "key": "legend", "title": "Efsane", "description": "50 maç kazan", "iconUrl": "https://images.unsplash.com/photo-1578269174936-2709b6aeb913", "coinReward": 500, "xpReward": 50},
    {"id": "ach_speed_demon", "key": "speed_demon", "title": "Hız Şeytanı", "description": "3 saniyeden kısa sürede doğru cevap ver", "iconUrl": "https://images.unsplash.com/photo-1578269174936-2709b6aeb913", "coinReward": 100, "xpReward": 50},
    {"id": "ach_streak_killer", "key": "streak_killer", "title": "Seri Katil", "description": "10 maç üst üste kazan", "iconUrl": "https://images.unsplash.com/photo-1578269174936-2709b6aeb913", "coinReward": 300, "xpReward": 50},
    {"id": "ach_collector", "key": "collector", "title": "Koleksiyoncu", "description": "10 mağaza ürünü satın al", "iconUrl": "https://images.unsplash.com/photo-1578269174936-2709b6aeb913", "coinReward": 150, "xpReward": 50},
    {"id": "ach_social", "key": "social_butterfly", "title": "Sosyal Kelebek", "description": "10 arkadaş edin", "iconUrl": "https://images.unsplash.com/photo-1578269174936-2709b6aeb913", "coinReward": 100, "xpReward": 50},
]


QUESTS = [
    {"id": "quest_d1", "title": "5 soru doğru cevapla", "description": "Herhangi bir maçta 5 soruyu doğru bil", "type": "DAILY", "target": 5, "coinReward": 30, "xpReward": 20, "isActive": True},
    {"id": "quest_d2", "title": "1 maç kazan", "description": "Bugün 1 maç kazan", "type": "DAILY", "target": 1, "coinReward": 50, "xpReward": 30, "isActive": True},
    {"id": "quest_d3", "title": "Bilim kategorisinden 3 soru cevapla", "description": "Bilim sorularını cevapla", "type": "DAILY", "target": 3, "coinReward": 25, "xpReward": 15, "isActive": True},
    {"id": "quest_w1", "title": "10 maç tamamla", "description": "Bu hafta 10 maç oyna", "type": "WEEKLY", "target": 10, "coinReward": 150, "xpReward": 100, "isActive": True},
    {"id": "quest_w2", "title": "Arkadaşınla özel oda kur", "description": "Bir özel oda oluştur", "type": "WEEKLY", "target": 1, "coinReward": 80, "xpReward": 50, "isActive": True},
    {"id": "quest_w3", "title": "Dereceli modda 3 galibiyet", "description": "Ranked modda 3 maç kazan", "type": "WEEKLY", "target": 3, "coinReward": 200, "xpReward": 150, "isActive": True},
]


GAME_MODES = [
    {"id": "CLASSIC", "name": "Klasik", "description": "10 soruluk standart düello", "icon": "flash", "minLevel": 1, "ranked": False},
    {"id": "RANKED", "name": "Dereceli", "description": "Puanların için savaş", "icon": "trophy", "minLevel": 3, "ranked": True},
    {"id": "QUICK", "name": "Hızlı Maç", "description": "Anında eşleşme", "icon": "rocket", "minLevel": 1, "ranked": False},
    {"id": "SURVIVAL", "name": "Hayatta Kalma", "description": "Yanlış yaparsan elenirsin", "icon": "heart", "minLevel": 5, "ranked": False},
    {"id": "CATEGORY", "name": "Kategori", "description": "Tek kategoride düello", "icon": "grid", "minLevel": 2, "ranked": False},
    {"id": "PRIVATE", "name": "Özel Oda", "description": "Arkadaşınla oyna", "icon": "people", "minLevel": 1, "ranked": False},
    {"id": "DAILY_TOURNAMENT", "name": "Günlük Turnuva", "description": "Günün şampiyonu ol", "icon": "calendar", "minLevel": 4, "ranked": True},
    {"id": "WEEKLY_LEAGUE", "name": "Haftalık Lig", "description": "Lig sıralamasında yüksel", "icon": "podium", "minLevel": 6, "ranked": True},
    {"id": "TEAM_BATTLE", "name": "Takım Savaşı", "description": "Takımınla zafere ulaş", "icon": "shield", "minLevel": 8, "ranked": False},
    {"id": "SEASONAL", "name": "Sezon Etkinliği", "description": "Özel sezon ödülleri", "icon": "star", "minLevel": 5, "ranked": False},
]


BOT_NAMES = [
    ("trivia_master", "Trivia Master", 1850),
    ("quiz_king", "Quiz Kralı", 2100),
    ("brainiac", "Beyin Fırtınası", 1450),
    ("the_oracle", "Kahin", 2750),
    ("smarty", "Akıllı Tilki", 1200),
    ("genius_99", "Dahi 99", 3200),
    ("nova_player", "Nova", 950),
    ("rapid_mind", "Şimşek Zeka", 1650),
]


async def seed_all():
    # Questions
    if await db.questions.count_documents({}) == 0:
        await db.questions.insert_many([dict(q) for q in SEED_QUESTIONS])
    # Shop
    if await db.shop_items.count_documents({}) == 0:
        await db.shop_items.insert_many([dict(s) for s in SHOP_ITEMS])
    # Achievements
    if await db.achievements.count_documents({}) == 0:
        await db.achievements.insert_many([dict(a) for a in ACHIEVEMENTS])
    # Quests
    if await db.quests.count_documents({}) == 0:
        await db.quests.insert_many([dict(q) for q in QUESTS])
    # Modes
    if await db.game_modes.count_documents({}) == 0:
        await db.game_modes.insert_many([dict(m) for m in GAME_MODES])
    # Bot users
    if await db.users.count_documents({"isBot": True}) == 0:
        bots = []
        for i, (uname, dname, rp) in enumerate(BOT_NAMES):
            bots.append({
                "user_id": f"bot_{uname}",
                "username": uname,
                "displayName": dname,
                "email": f"{uname}@bot.quizarena",
                "googleId": f"bot_{uname}",
                "avatarUrl": AVATAR_POOL[i % len(AVATAR_POOL)],
                "gender": "UNSPECIFIED",
                "level": max(1, rp // 250),
                "currentXP": 0, "totalXP": rp * 5, "coins": 500,
                "rankPoints": rp, "isPremium": False, "premiumExpiresAt": None,
                "activeTitle": None, "activeFrameId": None, "activeCardId": None,
                "totalMatches": 80 + i * 7, "wins": 40 + i * 5, "losses": 30 + i * 2,
                "currentStreak": 0, "longestStreak": 5 + i, "loginStreak": 0,
                "lastLoginDate": None, "countryCode": "TR",
                "isBot": True, "skill": 0.45 + (rp / 8000),
                "createdAt": now_utc(), "lastSeenAt": now_utc(),
            })
        await db.users.insert_many(bots)
    # Season + Leagues
    if await db.seasons.count_documents({}) == 0:
        start = now_utc()
        await db.seasons.insert_one({
            "id": f"season_{uuid.uuid4().hex[:8]}", "number": 1, "name": "Sezon 1: Yükseliş",
            "startDate": start, "endDate": start + timedelta(weeks=8), "isActive": True,
        })
        for lg in LEAGUES:
            await db.leagues.insert_one({
                "id": f"league_{lg['tier'].lower()}", "name": lg["tier"].capitalize(),
                "tier": lg["tier"], "minPoints": lg["min"],
                "maxPoints": lg["max"] if lg["max"] < 10 ** 9 else 99999, "seasonId": "season_1",
            })
