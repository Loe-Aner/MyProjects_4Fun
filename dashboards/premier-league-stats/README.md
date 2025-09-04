# ⚽ Premier League Top 6 Dashboard (Power BI + Analizy SQL)

Projekt do analizy i wizualizacji wyników oraz statystyk **TOP6 klubów Premier League**.  
Dane źródłowe pochodzą z [Kaggle – Premier League Top 6 Teams Match Statistics](https://www.kaggle.com/datasets/ensarakbas/premier-league-top-6-teams-match-statistics).  
Dashboard pokazuje najważniejsze informacje o klubach, ich osiągnięcia, statystyki meczowe oraz dynamikę wyników w ostatnich sezonach.

---

## 🎯 Cel projektu

Celem tego dashboardu jest szybka i przejrzysta analiza **TOP6 klubów Premier League**.  
Dzięki temu możliwe jest:
- porównanie osiągnięć zespołów w różnych sezonach,  
- śledzenie kluczowych statystyk (gole, posiadanie piłki, celność strzałów, skuteczność),  
- przegląd informacji o klubach (historia, stadion, trener, trofea),  
- analiza najczęściej stosowanych formacji oraz przykładowych jedenastek.

---

## 📂 Struktura projektu

- **0. Dashboard - przykładowe zdjęcie/**  
  - `man_city_dashboard.png`  
  - `...`

- **1. Data/**  
  - **Info o klubie/** – podstawowe dane (rok założenia, stadion, trener, liczba trofeów)  
  - **Jedenastki/** – jedenastki oraz współrzędne na wykres punktowy (boisko) 
  - **Obrazki/** – loga klubów  
  - **Statystyki/** – pliki ze wskaźnikami (gole, posiadanie piłki, win ratio, celność strzałów, skuteczność strzelecka, średnia punktów na mecz itd.)

- **2. Zadania - SQL/**  
  - zapytania SQL analizujące dane źródłowe

- **3. Przykładowe miary w DAX/**  
  - przykłady metryk wykorzystywanych w dashboardzie Power BI

- **Opis kolumn/**  
  - szczegółowy opis wszystkich pól z datasetu Kaggle (np. `Goals`, `ShotsOnTarget`, `Possession`, `WinRatio`, itd.)
