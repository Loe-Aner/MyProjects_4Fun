from scraper_wowhead_kolejnosc import zbuduj_kolejnosc

zbuduj_kolejnosc(
    ["https://www.wowhead.com/storylines?filter=2;12;0"],
    rozmiar_paczki=100,
    pauza_sekundy=120,
)