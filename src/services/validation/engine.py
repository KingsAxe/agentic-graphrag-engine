import logging
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field
from src.core.config import settings

logger = logging.getLogger(__name__)

class ValidationResult(BaseModel):
    is_contradictory: bool = Field(description="True if the claims clearly contradict each other.")
    explanation: str = Field(description="A brief explanation of why the claims are contradictory or complementary.")
    confidence_score: float = Field(description="A score from 0.0 to 1.0 indicating the overall confidence in the data.")

class ValidationEngine:
    def __init__(self):
        if settings.GROQ_API_KEY:
            self.llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=settings.LLM_MODEL,
                temperature=0
            )
            # Use LangChain structured output for the judge
            self.judge = self.llm.with_structured_output(ValidationResult)
        else:
            self.judge = None
            logger.warning("GROQ_API_KEY not set. ValidationEngine will be disabled.")

    async def detect_contradiction(self, claim_a: str, claim_b: str) -> ValidationResult:
        """Compare two claims and return a ValidationResult."""
        if not self.judge:
            return ValidationResult(is_contradictory=False, explanation="Judge not initialized.", confidence_score=0.5)

        prompt = f"""
        Compare the following two factual claims. 
        Determine if they are contradictory (direct mismatch in facts), complementary (adding different details), or redundant (saying the same thing).
        
        Claim A: "{claim_a}"
        Claim B: "{claim_b}"
        
        Provide a verdict and a brief explanation.
        """

        try:
            result = await self.judge.ainvoke(prompt)
            return result
        except Exception as e:
            logger.error(f"Validation LLM call failed: {e}")
            return ValidationResult(is_contradictory=False, explanation=f"Error: {e}", confidence_score=0.5)

    async def validate_claims(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a list of claims. 
        Expected format: [{"claim": str, "support_count": int, "document_ids": list}]
        """
        if not claims:
            return {"confidence_score": 1.0, "contradictions": []}

        contradictions = []
        total_sources = sum(c.get("support_count", 1) for c in claims)
        llm_scores = []

        # Simple N^2 comparison for now, can be optimized later
        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                res = await self.detect_contradiction(claims[i]["claim"], claims[j]["claim"])
                if res.is_contradictory:
                    contradictions.append({
                        "claim_a": claims[i]["claim"],
                        "claim_b": claims[j]["claim"],
                        "explanation": res.explanation
                    })
                llm_scores.append(res.confidence_score)

        avg_llm_score = sum(llm_scores) / len(llm_scores) if llm_scores else 1.0
        
        final_confidence = self.compute_confidence(
            sources_count=total_sources,
            contradictions_count=len(contradictions),
            average_score=avg_llm_score
        )

        return {
            "confidence_score": round(final_confidence, 2),
            "contradictions": contradictions
        }

    def compute_confidence(self, sources_count: int, contradictions_count: int, average_score: float) -> float:
        """
        Compute a final confidence score based on:
        - Agreement (number of supporting sources)
        - Conflict (number of contradictions)
        - LLM's assessment score
        """
        if sources_count == 0:
            return 0.0
        
        # Base score from sources agreement
        agreement_factor = min(1.0, (sources_count / 5.0)) # Plateau at 5 sources
        
        # Penalty for contradictions
        contradiction_penalty = 0.5 if contradictions_count > 0 else 0.0
        
        final_score = (agreement_factor * 0.4) + (average_score * 0.6) - contradiction_penalty
        return max(0.0, min(1.0, final_score))

# Singleton
validation_engine = None

def get_validation_engine() -> ValidationEngine:
    global validation_engine
    if validation_engine is None:
        validation_engine = ValidationEngine()
    return validation_engine
