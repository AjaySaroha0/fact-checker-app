"""
verifier.py
Handles AI-powered fact verification using Groq API.
"""

import os
import re
from typing import Dict, List, Optional
from groq import Groq

from prompts import FACT_CHECK_SYSTEM_PROMPT, build_fact_check_prompt


class FactVerifier:
    """AI-powered fact verification engine."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.1-8b-instant"
    ):
        """
        Initialize the fact verifier.

        Args:
            api_key: Groq API key.
            model: Groq model to use.
        """

        self.api_key = api_key or os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Groq API key not found. Please set GROQ_API_KEY in your .env file."
            )

        self.client = Groq(api_key=self.api_key)
        self.model = model

    def verify(self, claim: str, search_results: List[Dict]) -> Dict:
        """
        Verify a claim using AI analysis of search evidence.
        """

        if not search_results:
            return self._create_unverified_response(
                claim,
                "No search results available to verify this claim."
            )

        # Build prompt
        user_prompt = build_fact_check_prompt(claim, search_results)

        try:
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": FACT_CHECK_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0.2,
                max_tokens=2000
            )

            raw_output = response.choices[0].message.content

            # Parse response
            parsed = self._parse_response(raw_output)

            parsed["claim"] = claim
            parsed["raw_sources"] = search_results

            return parsed

        except Exception as e:
            return self._create_error_response(claim, str(e))

    def _parse_response(self, raw_output: str) -> Dict:
        """
        Parse structured AI response.
        """

        result = {
            "verdict": "UNVERIFIED",
            "confidence": 0,
            "summary": "",
            "detailed_explanation": "",
            "key_evidence": [],
            "source_reliability": "",
            "final_conclusion": "",
            "sources": [],
            "raw_output": raw_output
        }

        # Verdict
        verdict_match = re.search(
            r'Verdict:\s*(.+?)(?:\n|$)',
            raw_output,
            re.IGNORECASE
        )

        if verdict_match:
            result["verdict"] = verdict_match.group(1).strip().upper()

        # Confidence
        confidence_match = re.search(
            r'Confidence Score:\s*(\d+)',
            raw_output,
            re.IGNORECASE
        )

        if confidence_match:
            result["confidence"] = int(confidence_match.group(1))

        # Summary
        summary_match = re.search(
            r'Summary:\s*(.+?)(?=\n\w+:|$)',
            raw_output,
            re.IGNORECASE | re.DOTALL
        )

        if summary_match:
            result["summary"] = summary_match.group(1).strip()

        # Detailed explanation
        explanation_match = re.search(
            r'Detailed Explanation:\s*(.+?)(?=Key Evidence:|$)',
            raw_output,
            re.IGNORECASE | re.DOTALL
        )

        if explanation_match:
            result["detailed_explanation"] = explanation_match.group(1).strip()

        # Key evidence
        evidence_section = re.search(
            r'Key Evidence:\s*(.+?)(?=Source Reliability|$)',
            raw_output,
            re.IGNORECASE | re.DOTALL
        )

        if evidence_section:
            evidence_text = evidence_section.group(1)

            bullets = re.findall(
                r'[-•*]\s*(.+?)(?=\n[-•*]|\Z)',
                evidence_text,
                re.DOTALL
            )

            result["key_evidence"] = [
                b.strip() for b in bullets if b.strip()
            ]

        # Source reliability
        reliability_match = re.search(
            r'Source Reliability Assessment:\s*(.+?)(?=Final Conclusion:|$)',
            raw_output,
            re.IGNORECASE | re.DOTALL
        )

        if reliability_match:
            result["source_reliability"] = reliability_match.group(1).strip()

        # Final conclusion
        conclusion_match = re.search(
            r'Final Conclusion:\s*(.+?)(?=Sources:|$)',
            raw_output,
            re.IGNORECASE | re.DOTALL
        )

        if conclusion_match:
            result["final_conclusion"] = conclusion_match.group(1).strip()

        # Sources
        sources_section = re.search(
            r'Sources:\s*(.+)',
            raw_output,
            re.IGNORECASE | re.DOTALL
        )

        if sources_section:
            sources_text = sources_section.group(1)

            source_items = re.findall(
                r'(?:\d+\.\s*|[-•*]\s*)(.+?)(?=\n(?:\d+\.\s*|[-•*]\s*)|\Z)',
                sources_text,
                re.DOTALL
            )

            result["sources"] = [
                s.strip() for s in source_items if s.strip()
            ]

        return result

    def _create_unverified_response(
        self,
        claim: str,
        reason: str
    ) -> Dict:

        return {
            "claim": claim,
            "verdict": "UNVERIFIED",
            "confidence": 0,
            "summary": reason,
            "detailed_explanation": reason,
            "key_evidence": [],
            "source_reliability": "No sources available.",
            "final_conclusion": reason,
            "sources": [],
            "raw_sources": [],
            "raw_output": ""
        }

    def _create_error_response(
        self,
        claim: str,
        error_msg: str
    ) -> Dict:

        return {
            "claim": claim,
            "verdict": "UNVERIFIED",
            "confidence": 0,
            "summary": f"Error: {error_msg}",
            "detailed_explanation": error_msg,
            "key_evidence": [],
            "source_reliability": "Unable to assess.",
            "final_conclusion": "Verification failed.",
            "sources": [],
            "raw_sources": [],
            "raw_output": "",
            "error": error_msg
        }


class VerificationError(Exception):
    """Custom verification exception."""
    pass


def verify_claim(
    claim: str,
    search_results: List[Dict],
    api_key: Optional[str] = None
) -> Dict:

    verifier = FactVerifier(api_key=api_key)

    return verifier.verify(claim, search_results)