import hashlib
import re
from src.models.graph import Claim, Entity, GraphExtraction


def mock_embed_texts(texts: list[str], vector_size: int = 1024) -> list[list[float]]:
    vectors = []
    for text in texts:
        vector = [0.0] * vector_size
        for token in re.findall(r"\w+", text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
            index = int(digest[:8], 16) % vector_size
            vector[index] += 1.0

        norm = sum(value * value for value in vector) ** 0.5
        if norm:
            vector = [value / norm for value in vector]
        vectors.append(vector)
    return vectors


def extract_graph_from_text(text: str) -> GraphExtraction:
    entities = []
    claims = []
    seen = set()

    matches = re.findall(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b", text)
    for match in matches[:8]:
        entity_id = re.sub(r"[^A-Z0-9]+", "_", match.upper()).strip("_")
        if not entity_id or entity_id in seen:
            continue
        seen.add(entity_id)
        entity_type = "ORGANIZATION" if any(word in match for word in ["Corp", "Inc", "Ltd", "Company"]) else "PERSON"
        entities.append(
            Entity(
                id=entity_id,
                type=entity_type,
                description=f"Mock extracted entity for '{match}'.",
            )
        )

    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
    for sentence in sentences[:8]:
        subject = next((entity.id for entity in entities if entity.id.replace("_", " ") in sentence.upper()), None)
        if subject is None and entities:
            subject = entities[0].id
        if subject:
            claims.append(Claim(subject_entity_id=subject, claim=sentence))

    return GraphExtraction(entities=entities, relationships=[], claims=claims)


def detect_contradiction(claim_a: str, claim_b: str) -> tuple[bool, str, float]:
    numbers_a = re.findall(r"\d+(?:\.\d+)?", claim_a)
    numbers_b = re.findall(r"\d+(?:\.\d+)?", claim_b)
    if numbers_a and numbers_b and numbers_a != numbers_b:
        return True, "Mock validator found differing numeric values across the two claims.", 0.6

    negation_words = {"not", "never", "no"}
    tokens_a = set(re.findall(r"\w+", claim_a.lower()))
    tokens_b = set(re.findall(r"\w+", claim_b.lower()))
    if (tokens_a & negation_words) ^ (tokens_b & negation_words):
        return True, "Mock validator found a likely negation mismatch between the two claims.", 0.55

    overlap = len(tokens_a & tokens_b) / max(1, len(tokens_a | tokens_b))
    if overlap > 0.35:
        return False, "Mock validator considers the claims related or supportive.", 0.7

    return False, "Mock validator considers the claims complementary.", 0.65
