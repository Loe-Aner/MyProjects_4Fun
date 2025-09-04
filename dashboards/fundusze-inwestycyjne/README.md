# 📊 Funds Dashboard (Python + Power BI + Analizy SQL)

Projekt do analizy i wizualizacji rentowności funduszy inwestycyjnych.  
Dane źródłowe pochodzą z plików Excel/CSV oraz kart funduszu (PDF), które następnie są przetwarzane i wizualizowane w Power BI.  
Część informacji jest pozyskiwana automatycznie z plików PDF za pomocą **Gemini API**.

---

## 🎯 Cel projektu

Celem tego dashboardu jest ułatwienie podjęcia decyzji **w który fundusz warto zainwestować**.  
Analiza uwzględnia nie tylko **stopy zwrotu** (zarówno narastające, jak i kroczące w różnych horyzontach),  
ale także **ryzyko** oraz **kluczowe parametry** takie jak wielkość aktywów netto, struktura aktywów, alokacja sektorowa, geograficzna i walutowa.  

Dzięki temu możliwe jest pełniejsze spojrzenie na fundusze – nie tylko „ile zarobiły”,  
ale także **jak stabilnie się rozwijają i w jakich warunkach rynkowych funkcjonują**.  

---

## 📂 Struktura projektu

- **fundusze_get_data.ipynb** - główny notebook Jupyter
- **0. Dasboard - przyklady** - jak wygladaja poszczegolne strony
- **1. Aktywa netto/**
  - `aktywa.xlsx`  
- **2. Benchmark/**
  - `benchmark.xlsx`  
- **3. Struktura aktywow/**
  - `struktura_aktywow.xlsx`  
- **4. Struktura geograficzna/**
  - `struktura_geograficzna.xlsx`  
- **5. Najwieksze pozycje w portfelu/**
  - `najw_poz_w_porfelu.xlsx`  
- **6. Alokacja sektorowa/**
  - `alokacja_sektorowa.xlsx`  
- **7. Waluty/**
  - `waluty.xlsx`  
- **Additional Tables/**
  - `extraInfo.csv`  
- **Karty funduszu/** - podfoldery = tickery funduszy  
  - `MIL27/2025-04-30.pdf`  
  - `ING43/2025-07-31.pdf`
  - `.../....pdf`
- **Notowania/**
  - `dane.csv`
- **Przykładowe Miary w DAX/** - jak niektóre parametry są liczone
- **Przykładowe klauzule SQL (analizy)/** - analizy zbiorów z wykorzystaniem SQL'a
- **Zwrot od Gemini/** - odpowiedzi Gemini (per ticker)  
  - `MIL27/...`  
  - `ING43/...`
  - `.../...`
