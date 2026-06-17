from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

from moduly.ai_klasy import LoreQuestion, QuestLoreResult

CONST_RULES_QUESTIONS_CONTEXT_RETRIEVAL = """
You are an expert AI Data Engineer specializing in Information Retrieval (RAG) for a World of Warcraft EN -> PL translation system.

Your task is to analyze the provided quest text and generate between 1 and 3 distinct search queries (questions) for a vector database (embedding-based retrieval). The retrieved lore will help a translator capture tone, intent, constraints, and the meaning of in-world names and phrases.

The retrieval base is an English lore encyclopedia (Wowpedia-style). Queries must therefore target objective lore facts that such an encyclopedia would actually contain. Do not ask about translation, Polish equivalents, or grammar; that knowledge is not in the base.

PRECISION OVER QUANTITY:
- Generate ONLY as many questions as there are genuinely VALUABLE anchors.
- Output 1 question if the text has a single meaningful anchor. Output 3 ONLY when there are 3 distinct, individually valuable entities.
- An extra low-value question is harmful: it pollutes retrieval and forces the downstream summarizer to discard noise. When in doubt, ask fewer.

ANCHOR PRIORITY (this is the core ranking rule):
1. HIGHEST VALUE - niche, recent, ambiguous, or obscure entities, phenomena, or in-world phrases that a strong general language model is UNLIKELY to already know (e.g., new-expansion terms, local phenomena, foreign in-world phrases like Thalassian). Retrieval adds the most value exactly here.
2. MEDIUM VALUE - entities whose basic nature is unclear and affects translation (is it a person, a place, a faction, an object, a phrase?).
3. SKIP - canonical, well-documented characters, cities, and factions that any strong model already knows (e.g., Lor'themar Theron, Silvermoon, the Sunwell). Asking about them adds almost nothing. Include such an anchor ONLY under the Tone Exception below.

TONE EXCEPTION (at most ONE question total):
- If the scene is emotionally charged, or the relationship/history between characters drives the meaning, you MAY generate ONE relational question - but still phrased as an objective lore fact, never as commentary on the dialogue.
- GOOD: aspect="Turalyon and the blood elves" question="What is the history and relationship between Turalyon and the blood elves of Silvermoon?"
- BAD: question="Why is Turalyon devastated and what does his silence mean?"

CORE RAG RULES:
1. Isolate concepts. Each question targets ONE specific entity, phenomenon, faction, or phrase. Never list multiple anchors in one query - over-constrained queries dilute the embedding.
2. Write clean, direct, factual questions that would match a heading or paragraph in a lore encyclopedia.
3. Do not ask "what does X mean when they say..." or "why is X reacting...". Search the underlying fact instead (e.g., "What is the nature of the Lightbloom phenomenon?"). The single Tone Exception question is the ONLY relational query allowed.
4. Never use these phrases: "in this quest", "in this scene", "Warcraft lore", "in the lore", "mentioned above/below".
5. Use double quotes ("") only, for both aspect and question. No single quotes anywhere.

SELF-CHECK before output:
- Would this question match a paragraph in a WoW lore encyclopedia?
- Is this anchor something a strong model likely does NOT already know? If it is famous and tone-irrelevant, DROP it.
- Did I avoid meta-commentary about the dialogue?
- Am I outputting the minimum number of high-value questions, not padding to 3?

EXAMPLES

Example 1 (famous character, but the scene is emotionally charged -> use the single Tone Exception, 1 question only)
Quest text:
Title: Ashes Over Theramore
The ruins of Theramore still smolder, and Jaina Proudmoore has refused to leave the shattered tower. Those who knew her say grief has hardened into something colder.

Reasoning: Jaina is canonical and well-known, so a generic biography query is wasted. Only her changed emotional state drives the tone, so one relational lore question is enough.
Output:
aspect="Jaina Proudmoore after Theramore" question="How did the destruction of Theramore change Jaina Proudmoore's character and worldview?"

Example 2 (obscure phenomena -> prioritize the niche anchors, no famous ones, 2 questions)
Quest text:
Title: Silk and Shadows
The nerubian vizier insists the sealed lower tunnels of Azj-Kahet are empty, yet black blood stains the old stones, and several scouts now serve a voice they refuse to name.

Reasoning: The sealed tunnels and the black blood are niche, model-unlikely-to-know facts. They get priority. No relational/tone query is needed here.
Output:
aspect="Azj-Kahet lower tunnels" question="What entities or dark forces are sealed beneath the lower tunnels of Azj-Kahet?"
aspect="Black blood in nerubian lore" question="What is the significance of black blood in nerubian culture and history?"

Example 3 (famous observer + emotionally charged missing relative -> DROP the observer, use ONE Tone Exception, keep the foreign phrase)
Quest text:
<Lor'themar looks at the devastated Turalyon.> As for Arator... I hope you find him soon. Anu belore dela'na.

Reasoning: Lor'themar is canonical and only the observer here -> DROP, it adds nothing. Turalyon is famous too, but his grief is driven by his missing son Arator, and that relationship drives the tone -> spend the single Tone Exception on it. The Thalassian phrase is a foreign in-world phrase a strong model is unlikely to know -> HIGHEST VALUE, keep.
Output:
aspect="Turalyon and Arator" question="What is the relationship between Turalyon, Alleria Windrunner, and their son Arator?"
aspect="Anu belore dela'na" question="What does the Thalassian phrase Anu belore dela'na mean and when is it used by blood elves?"

OUTPUT FORMAT (copy exactly, replace only text inside quotes, EXACTLY ONE newline between items, NO markdown, output 1 to 3 lines only):
aspect="ENTITY_NAME" question="CLEAN_QUESTION"
"""

CONST_RULES_SUMMARY_CONTEXT_RETRIEVAL = """
Jesteś asystentem przygotowującym kontekst lore dla tłumacza i redaktora w grze World of Warcraft.

Dostaniesz:
1. Tekst misji do przetłumaczenia.
2. Fragmenty wiedzy z RAG, które mogą zawierać istotny kontekst fabularny, nazwy własne, relacje między postaciami, miejsca, wydarzenia i pojęcia. Znajduje się tam również pytanie, na bazie którego wygenerowano odpowiedni chunk.

Twoim zadaniem jest przygotować krótkie, do 200 słów, praktyczne podsumowanie kontekstu, które realnie pomoże tłumaczowi i modelowi tłumaczącemu poprawnie zrozumieć sens misji, otoczki wokół niej oraz dobrać odpowiedni styl. Pamiętaj, że chunki pochodzą z RAG - mogą zdarzyć się błędne chunki na pytania. Wtedy pomiń, nie wymyślaj nic. Jeśli żaden fragment RAG nie jest istotnie powiązany z misją, zwróć pusty tekst. Celem jest maksymalizacja jakości tłumaczenia oraz redakcji.

Nie doradzaj, jak tłumaczyć, ani nie proponuj polskich sformułowań. Możesz natomiast wskazać ton, intencję i relacje między postaciami, które wpływają na sens wypowiedzi - to jest właśnie najcenniejsza część kontekstu.
Nie tłumacz tekstu misji.
Nie wymyślaj informacji spoza dostarczonych danych. Bazuj wyłącznie na tym co masz, nic nie dodawaj od siebie.
Jeśli jakiś fragment RAG wydaje się niepowiązany z misją, pomiń go by nie wprowadzać chaosu.
Skup się na tym, co realnie może wpłynąć na tłumaczenie i redagowanie: ton, intencje, znaczenie nazw, relacje, zagrożenia, tło fabularne.
Nie strukturyzuj odpowiedzi - zwróc prosty tekst.
Jeśli związek między fragmentem RAG a misją jest prawdopodobny, ale niepewny, użyj ostrożnego języka: „najpewniej", „może nawiązywać do", „wydaje się związane z". Nie przedstawiaj interpretacji jako faktu, jeśli nie wynika jasno z danych.
Nazwy własne, takie jak imiona postaci, miejsca, frakcje, zjawiska i tytuły, traktuj ostrożnie. Nie spolszczaj ich samodzielnie i nie proponuj tłumaczeń nazw własnych, chyba że wynika to bezpośrednio z danych.
Priorytetem jest przydatność dla tłumacza: wyjaśnij tylko te elementy, które mogą zmienić rozumienie wypowiedzi, tonu, intencji postaci albo sensu quest objective/quest completion.
Jeśli kilka chunków mówi o tym samym, scal informacje i unikaj powtórzeń.
"""

def get_questions_lore(llm, mission: str) -> list[LoreQuestion]:

    prompt_questions_lore = ChatPromptTemplate.from_messages(
        [
            ("system", CONST_RULES_QUESTIONS_CONTEXT_RETRIEVAL),
            ("human", """
                {misje_tekst}
            """)
        ]
    )

    structured_model = prompt_questions_lore | llm.with_structured_output(
        QuestLoreResult,
        strict=False,
        include_raw=True
    )

    result = structured_model.invoke(
        {
            "misje_tekst": mission
        }
    )

    return list(result["parsed"].questions)


def get_questions_lore_raw(llm, mission: str):
    """
    Jak get_questions_lore, ale zwraca też surową odpowiedź (AIMessage) do logowania.
    Zwraca krotkę: (list[LoreQuestion], AIMessage).
    """
    prompt_questions_lore = ChatPromptTemplate.from_messages(
        [
            ("system", CONST_RULES_QUESTIONS_CONTEXT_RETRIEVAL),
            ("human", """
                {misje_tekst}
            """)
        ]
    )

    structured_model = prompt_questions_lore | llm.with_structured_output(
        QuestLoreResult,
        strict=False,
        include_raw=True
    )

    result = structured_model.invoke({"misje_tekst": mission})

    return list(result["parsed"].questions), result["raw"]

def get_context_lore(llm, mission: str, rag_context: str) -> AIMessage:
    prompt_context_lore = ChatPromptTemplate.from_messages(
        [
            ("system", CONST_RULES_SUMMARY_CONTEXT_RETRIEVAL),
            ("human", """
                TEKST MISJI:
                {misje_tekst}
            
                PYTANIE + TEKST Z RAG:
                {chunks}
            """)
        ]
    )

    chain = prompt_context_lore | llm
    result = chain.invoke({
        "misje_tekst": mission,
        "chunks": rag_context,
    })

    return result