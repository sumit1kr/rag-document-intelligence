import re
import spacy
from typing import Dict, Optional

class QueryInterpreter:
    def __init__(self):
        # self.nlp = spacy.load("en_core_web_sm")
        self.nlp = spacy.load("en_core_web_trf")

        self.procedure_keywords = {
            "knee replacement": ["knee replacement", "knee surgery", "knee operation"],
            "hip replacement": ["hip replacement"],
            "cataract surgery": ["cataract", "eye surgery"],
            "angioplasty": ["angioplasty", "heart stent", "stent placement"],
            "heart bypass": ["bypass surgery", "cabg", "heart bypass"],
            "appendectomy": ["appendix removal", "appendectomy"],
            "delivery": ["childbirth", "delivery", "labour", "normal delivery", "cesarean", "c-section"],
            "fracture": ["bone fracture", "fractured", "broken bone"],
            "ivf": ["ivf", "fertility treatment", "infertility", "insemination"],
            "abortion": ["abortion", "medical termination", "mtp", "ectopic pregnancy"],
            "cosmetic": ["rhinoplasty", "nose job", "cosmetic surgery", "plastic surgery"],
        }

    def parse(self, query: str) -> Dict[str, Optional[str]]:
        query = query.lower().strip()
        doc = self.nlp(query)

        parsed = {
            "age": None,
            "gender": None,
            "procedure": None,
            "location": None,
            "policy_duration": None
        }

        # --- AGE --- (only if tied to "year" or "age")
        age_match = re.search(r'(\d{1,3})\s*(year[- ]?old|yrs?|y/o|age)?', query)
        if age_match:
            keyword = age_match.group(2)
            age = int(age_match.group(1))
            if keyword and 0 < age < 120:
                parsed["age"] = str(age)

        # --- GENDER ---
        gender_match = re.search(r'\b(male|female|m\b|f\b)\b', query)
        if gender_match:
            g = gender_match.group(1)
            parsed["gender"] = "M" if g.startswith("m") else "F"

        # --- POLICY DURATION ---
        dur_match = re.search(r'(\d{1,2})\s*[- ]?(month|months|year|years)\b', query)
        if dur_match:
            value, unit = dur_match.groups()
            parsed["policy_duration"] = f"{value} {unit}"

        # --- LOCATION --- (Named Entities)
        for ent in doc.ents:
            if ent.label_ in ("GPE", "LOC", "FAC"):  # Geo-political entity
                parsed["location"] = ent.text.title()
                break

        # --- PROCEDURE --- (extract medical/noun phrase)
        for proc, aliases in self.procedure_keywords.items():
            for alias in aliases:
                if alias in query:
                    parsed["procedure"] = proc.title()
                    break
            if parsed["procedure"]:
                break

        # --- PROCEDURE fallback: longest noun chunk with medical words
        if not parsed["procedure"]:
            noun_phrases = [
                chunk.text.strip()
                for chunk in doc.noun_chunks
                if any(word in chunk.text.lower() for word in ["surgery", "treatment", "procedure", "operation"])
            ]
            if noun_phrases:
                parsed["procedure"] = max(noun_phrases, key=len).replace("my ", "").strip().title()

        return parsed
