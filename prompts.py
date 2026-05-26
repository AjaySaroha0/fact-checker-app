"""
prompts.py
Contains all prompt templates for the AI Fact Checker.
"""

FACT_CHECK_SYSTEM_PROMPT = """You are an expert AI fact-checking analyst. Your role is to verify claims by analyzing evidence from web search results and providing accurate, neutral, and well-reasoned assessments.

CORE RULES:
1. Use ONLY evidence from the provided search results - never hallucinate or invent facts
2. Maintain strict political neutrality and objectivity
3. Clearly distinguish between verified facts, opinions, and speculation
4. Detect manipulated context, misleading framing, and logical fallacies
5. Mark claims as UNVERIFIED when evidence is insufficient
6. Consider recency, source credibility, and consensus among sources
7. Be transparent about limitations in the available evidence

VERDICT DEFINITIONS:
- TRUE: The claim is fully supported by reliable evidence
- FALSE: The claim is directly contradicted by reliable evidence
- MISLEADING: The claim contains some truth but is distorted, taken out of context, or omits crucial information
- PARTIALLY TRUE: The claim is partially accurate but contains significant inaccuracies or overgeneralizations
- UNVERIFIED: There is insufficient reliable evidence to confirm or deny the claim
- SATIRE: The claim is from a satirical or parody source and not intended as factual

OUTPUT FORMAT:
You must respond in the following exact format:

Verdict: [ONE OF: TRUE/FALSE/MISLEADING/PARTIALLY TRUE/UNVERIFIED/SATIRE]
Confidence Score: [0-100]
Summary: [2-3 sentence summary]
Detailed Explanation: [Thorough analysis with reasoning]
Key Evidence: [Bullet points of most relevant evidence]
Source Reliability Assessment: [Assessment of source quality and consensus]
Final Conclusion: [Clear final statement]
Sources: [List of key sources used]
"""
def build_fact_check_prompt(claim: str, search_results: list) -> str:
    """
    Build the user prompt for fact-checking.
    """

    prompt = f"""CLAIM TO VERIFY:
"{claim}"

SEARCH EVIDENCE:
"""

    for i, result in enumerate(search_results, 1):

        title = result.get('title', 'No title')
        content = result.get('snippet', 'No content')
        source = result.get('source', 'Unknown source')

        prompt += f"""
[{i}] Title: {title}
Source: {source}
Content: {content[:500]}
"""

    prompt += """

INSTRUCTIONS:
1. Analyze the claim against the search evidence above
2. Use ONLY the provided evidence
3. Keep response concise and factual
4. Follow the exact output format
"""

    return prompt
# def build_fact_check_prompt(claim: str, search_results: list) -> str:
#     """
#     Build the user prompt for fact-checking.

#     Args:
#         claim: The user's claim to verify
#         search_results: List of search result dictionaries

#     Returns:
#         Formatted prompt string
#     """
#     prompt = f"""CLAIM TO VERIFY:
# "{claim}"

# SEARCH EVIDENCE:
# """

#     for i, result in enumerate(search_results, 1):
#         title = result.get('title', 'No title')
#         content = result.get('content', result.get('snippet', 'No content'))
#         url = result.get('url', 'No URL')
#         source = result.get('source', 'Unknown source')

#         prompt += f"""
# [{i}] Title: {title}
# Source: {source}
# Content: {content[:700]}
# """

#     prompt += """

# INSTRUCTIONS:
# 1. Analyze the claim against the search evidence above
# 2. Consider all perspectives and evidence quality
# 3. Provide your assessment following the exact output format specified in your system instructions
# 4. Be thorough but concise in your reasoning
# 5. If sources contradict each other, explain the conflict and which side has stronger evidence
# 6. Note any gaps in the available evidence
# """

#     return prompt


def build_summary_prompt(claim: str, verdict: str, confidence: int, explanation: str) -> str:
    """
    Build prompt for generating a concise summary card.

    Args:
        claim: Original claim
        verdict: AI verdict
        confidence: Confidence score
        explanation: Detailed explanation

    Returns:
        Summary prompt string
    """
    return f"""Based on the following fact-check analysis, create a very concise 1-2 sentence summary suitable for a quick-read card:

Claim: "{claim}"
Verdict: {verdict}
Confidence: {confidence}%
Explanation: {explanation}

Provide only the summary text, nothing else."""