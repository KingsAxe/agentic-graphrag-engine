from pydantic import BaseModel, Field

class Entity(BaseModel):
    id: str = Field(description="A unique, uppercase identifier for the entity (e.g., PERSON_NAME, COMPANY_NAME).")
    type: str = Field(description="The type of the entity (e.g., PERSON, ORGANIZATION, CONCEPT, TOOL).")
    description: str = Field(description="A short, factual description of the entity derived from the text.")

class Relationship(BaseModel):
    source_entity_id: str = Field(description="The source entity ID.")
    target_entity_id: str = Field(description="The target entity ID.")
    relation_type: str = Field(description="A strict uppercase relationship type (e.g., ACQUIRED, WORKS_FOR, CONTRADICTS).")
    description: str = Field(description="A short explanation of why this relationship exists based on the text.")

class Claim(BaseModel):
    subject_entity_id: str = Field(description="The main entity this claim is about.")
    claim: str = Field(description="A concrete, factual statement extracted from the text.")

class GraphExtraction(BaseModel):
    entities: list[Entity] = Field(default_factory=list, description="All key entities found.")
    relationships: list[Relationship] = Field(default_factory=list, description="All relationships between entities.")
    claims: list[Claim] = Field(default_factory=list, description="Core factual claims contained in the text.")
