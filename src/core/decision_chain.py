# chains/decision_chain.py

from .query_interpreter import QueryInterpreter
from .qa_chain import QAChain  # your existing class
from src.utils.conv_mem import ConversationMemory
class DecisionChain:
    def __init__(self, config):
        self.memory = ConversationMemory()
        self.interpreter = QueryInterpreter()
        self.qa_chain = QAChain(config)

    def __getattr__(self, name):
        return getattr(self.qachain, name)
    
    def run(self, query: str, retriever, session_id: str):
        structured_query = self.interpreter.parse(query)

        # Optionally, inject structured_query into logs or context
        print(f"🔍 Parsed Query: {structured_query}")

        # You could even enrich the query before passing to QAChain
        enriched_query = self._enrich_query(query, structured_query)

        return self.qa_chain.run(enriched_query, retriever, session_id)

    def _enrich_query(self, original: str, parsed: dict) -> str:
        additions = []

        if parsed.get("age") and parsed.get("gender"):
            additions.append(f"I am a {parsed['age']}-year-old {parsed['gender'].lower()}.")
        elif parsed.get("age"):
            additions.append(f"I am {parsed['age']} years old.")
        elif parsed.get("gender"):
            additions.append(f"My gender is {parsed['gender'].lower()}.")

        if parsed.get("procedure"):
            additions.append(f"I am undergoing {parsed['procedure'].lower()}.")

        if parsed.get("location"):
            additions.append(f"The treatment is in {parsed['location']}.")

        if parsed.get("policy_duration"):
            additions.append(f"My policy has been active for {parsed['policy_duration']}.")

        context_sentence = " ".join(additions)
        return f"{original.strip()}\n\n{context_sentence.strip()}"
