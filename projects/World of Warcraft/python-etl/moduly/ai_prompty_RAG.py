from langchain_core.prompts import ChatPromptTemplate
from moduly.ai_klasy import LoreQuestion, QuestLoreResult

CONST_RULES_QUESTIONS_CONTEXT_RETRIEVAL = """
You are an expert AI Data Engineer specializing in Information Retrieval (RAG) for a World of Warcraft EN → PL translation system.

Your task is to analyze the provided quest text and generate between 2 and 3 distinct search queries (questions) that will be sent to a vector database (embedding-based retrieval). 

These queries must retrieve the underlying lore, entity backgrounds, and world-building context that a translator needs to accurately capture the tone, constraints, and meaning of the text.

CRITICAL RAG OPTIMIZATION RULES:
1. DO NOT ask "How are X, Y, and Z connected?" or list multiple anchors in one question. Vector embeddings fail on over-constrained, cluttered queries.
2. Isolate concepts. Each question must target ONE specific entity, phenomenon, or faction relationship to fetch its objective background lore.
3. Write queries as clean, direct, factual questions. Avoid phrasing like "What does character X mean when they say..." or "Why is X reacting this way...". Instead, search for the underlying lore fact (e.g., "What is the nature of the Lightbloom phenomenon?").
4. Never use prohibited phrases: "in this quest", "in this scene", "Warcraft lore", "in the lore", "mentioned above".
5. All outputs must strictly use double quotes ("") for both aspect and question. No single quotes allowed.

EVALUATION CRITERIA FOR QUEUSTIONS:
- Would this question match a heading or a paragraph in a WoW lore encyclopedia (e.g., Wowpedia)?
- Does it avoid meta-commentary about the quest dialogue?

EXAMPLES

Example 1
Quest text:
Title: Ashes Over Theramore
The ruins of Theramore still smolder, and Jaina Proudmoore has refused to leave the shattered tower. Those who knew her say grief has hardened into something colder. If she is pushed too far, restraint may no longer hold her back.

BAD (Too cluttered, useless for vector search):
aspect="Jaina's grief" question="How are Jaina Proudmoore, Theramore's ruins, and grief hardened into cold restraint connected in this scene?"

GOOD (Clean, targets factual lore background):
aspect="Jaina Proudmoore post-Theramore behavior" question="What happened to Jaina Proudmoore during the destruction of Theramore and how did it change her personality?"
aspect="Destruction of Theramore consequences" question="What are the political and magical consequences of the destruction of Theramore?"

Example 2
Quest text:
Title: Silk and Shadows
The nerubian vizier insists the sealed lower tunnels of Azj-Kahet are empty, yet the workers hear whispers beneath the webbing. Black blood stains the old stones, and several scouts now serve a voice they refuse to name.

BAD (Asks about local dialogue instead of lore):
aspect="Nerubian whispers" question="What does the nerubian vizier hide and what is the unnamed voice that the scouts serve?"

GOOD (Targets the underlying entity/phenomenon):
aspect="Azj-Kahet lower tunnels lore" question="What entities or dark forces are trapped beneath the sealed lower tunnels of Azj-Kahet?"
aspect="Black blood in Nerubian lore" question="What is the significance of black blood and unnamed whispers in Nerubian culture?"

Strictly follow this output format (copy it exactly, replace only the text inside quotes, use EXACTLY ONE newline between items, NO markdown blocks):

aspect="ENTITY_NAME" question="CLEAN_QUESTION_1"
aspect="ENTITY_NAME" question="CLEAN_QUESTION_2"
aspect="ENTITY_NAME" question="CLEAN_QUESTION_3"
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