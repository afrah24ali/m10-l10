"""spaCy NLP helpers for entity extraction."""

import spacy
from spacy.language import Language

from .models import Entity


_NLP: Language | None = None


def load_pipeline(model_name: str = "en_core_web_sm") -> Language:
    global _NLP

    if _NLP is None:
        _NLP = spacy.load(model_name)

    return _NLP


def extract_entities(text: str, nlp: Language | None = None) -> list[Entity]:
    pipeline=nlp or _NLP

    if pipeline is None:
        raise RuntimeError("spaCy pipeline has not been loaded")

    doc = pipeline(text)

    entities = [
        Entity(
            text=ent.text,
            label=ent.label_,
            start=ent.start_char,
            end=ent.end_char,
        )
        for ent in doc.ents
    ]

    return sorted(entities, key=lambda entity: entity.start)