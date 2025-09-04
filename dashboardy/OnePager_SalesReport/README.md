# 📊 One-Pager: Sales & Margin Dashboard (Power BI + DAX)

Jednostronicowy dashboard do **monitoringu sprzedaży i marży** w ujęciu czasowym, kategoriach oraz geograficznie.  
Zaprojektowany tak, aby **na jednym raporcie** zobaczyć kluczowe KPI i szybko odpowiedzieć na pytania: *gdzie rośniemy / spadamy, które kategorie dowożą cele i jak wygląda trend miesiąc po miesiącu*.  

---

## 🎯 Cel projektu

- Szybka **ocena realizacji targetów** sprzedażowych i marżowych (ACT vs BDG, ACT vs YTD).  
- Wskazanie **kontrybutorów wzrostu/spadku** (TopN po kategoriach).  
- Podgląd **trendów M/M**: ewolucja sprzedaży i marży oraz **Margin%**.  
- Łatwe **przekroje po miesiącu i kategorii** dzięki parametrom na górze raportu.  

---

## 🖼️ Co znajduje się na One-Pagerze

- **Select a measure & parameters** – wybór miary + parametrów (Month, Category).  
- **Geographical Distribution by wybrana miara** – słupki wg miary po krajach.  
- **TopN Categories by wybrana miara** – ranking kategorii z kontrolą TopN/filtra.  
- **ACT vs BDG / ACT vs YTD** – porównanie realizacji do budżetu i roku bieżącego.  
- **Sales evolution / Margin evolution / Margin%** – trendy czasowe z linią średniej.  
- **YoY% change by wybrana miara** – zmiana r/r.  

---

## 📂 Struktura repo

```text
0. Dashboard/
   └── One-Pager.pdf        # pełny podgląd raportu
1. Data/
   ├── dane.xlsx            # dane transakcyjne / agregaty
2. Przykladowe miary DAX/
   ├── ...                  # opis i założenia
