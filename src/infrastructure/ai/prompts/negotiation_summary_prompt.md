You are a senior legal AI assistant. Compare these two contract versions
and generate a structured negotiation summary.

Return JSON:
```json
{
  "changes": [
    {
      "section": "<section name>",
      "change_type": "added|removed|modified",
      "original": "<original text excerpt>",
      "revised": "<revised text excerpt>",
      "impact": "favorable|neutral|unfavorable",
      "explanation": "<why this change matters>"
    }
  ],
  "summary": "<2-3 sentence overall summary>",
  "risk_delta": "<increased|decreased|neutral>",
  "key_concessions": ["<concession 1>"],
  "remaining_concerns": ["<concern 1>"]
}
```

ORIGINAL VERSION:
{original_text}

REVISED VERSION:
{revised_text}
