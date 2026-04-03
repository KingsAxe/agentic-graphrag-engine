import asyncio
import os
import sys

# Ensure src is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.validation.engine import get_validation_engine

async def test_validation():
    print("--- Testing Validation Engine ---")
    engine = get_validation_engine()
    
    # 1. Test Contradiction Detection
    claim1 = "The revenue of Acme Corp in 2023 was $10 million."
    claim2 = "Acme Corp reported a revenue of $15 million for the 2023 fiscal year."
    
    print(f"\nComparing:\nA: {claim1}\nB: {claim2}")
    result = await engine.detect_contradiction(claim1, claim2)
    print(f"Is Contradictory: {result.is_contradictory}")
    print(f"Explanation: {result.explanation}")
    print(f"Confidence Score: {result.confidence_score}")

    # 2. Test Complementary Claims
    claim3 = "Acme Corp is headquartered in San Francisco."
    claim4 = "Acme Corp was founded by Alice Smith in 2020."
    
    print(f"\nComparing:\nA: {claim3}\nB: {claim4}")
    result = await engine.detect_contradiction(claim3, claim4)
    print(f"Is Contradictory: {result.is_contradictory}")
    print(f"Explanation: {result.explanation}")

    # 3. Test Batch Validation with Confidence Scoring
    print("\n--- Testing Batch Validation ---")
    mock_claims = [
        {"claim": "The CEO of Acme Corp is Alice Smith.", "support_count": 3, "document_ids": ["doc1"]},
        {"claim": "Alice Smith has been the CEO since 2020.", "support_count": 2, "document_ids": ["doc2"]},
        {"claim": "Bob Jones was appointed CEO of Acme Corp in 2023.", "support_count": 1, "document_ids": ["doc3"]}
    ]
    
    validation_summary = await engine.validate_claims(mock_claims)
    print(f"Overall Confidence Score: {validation_summary['confidence_score']}")
    print(f"Contradictions Found: {len(validation_summary['contradictions'])}")
    for c in validation_summary['contradictions']:
        print(f"Conflict: '{c['claim_a']}' VS '{c['claim_b']}'")
        print(f"Reason: {c['explanation']}")

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY must be set to run this test.")
    else:
        asyncio.run(test_validation())
