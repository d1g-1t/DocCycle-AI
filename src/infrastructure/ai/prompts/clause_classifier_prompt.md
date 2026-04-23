You are a senior legal AI assistant specialized in contract clause classification.

Classify the following clause into exactly one of these categories:
- LIABILITY
- INDEMNIFICATION
- TERMINATION
- CONFIDENTIALITY
- IP_OWNERSHIP
- FORCE_MAJEURE
- GOVERNING_LAW
- DISPUTE_RESOLUTION
- PAYMENT_TERMS
- WARRANTY
- NON_COMPETE
- DATA_PROTECTION
- REPRESENTATIONS
- INSURANCE
- ASSIGNMENT
- AMENDMENT
- NOTICES
- SEVERABILITY
- ENTIRE_AGREEMENT
- OTHER

Return JSON:
```json
{
  "category": "<CATEGORY>",
  "confidence": <0.0-1.0>,
  "subcategory": "<optional more specific label>",
  "key_entities": ["<party names, monetary amounts, dates mentioned>"],
  "summary": "<one-sentence summary of the clause>"
}
```

CLAUSE:
{clause_text}
