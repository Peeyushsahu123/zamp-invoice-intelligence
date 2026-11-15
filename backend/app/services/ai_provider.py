"""Isolated AI/LLM provider for invoice data extraction."""
import os
import json
import re
import logging

logger = logging.getLogger(__name__)


class AIProviderUnavailable(Exception):
    """Raised when no AI provider API key is configured."""
    pass


class AIProvider:
    """Abstracted AI provider that supports OpenAI, Anthropic, or Gemini."""

    EXTRACTION_PROMPT = """You are an invoice data extraction assistant. Extract the following fields from the invoice text below and return ONLY a valid JSON object with these keys:

- invoice_number: string
- vendor_name: string
- vendor_tax_id: string or null
- po_reference: string or null (purchase order number)
- invoice_date: string (in YYYY-MM-DD format)
- currency: string (e.g., "USD")
- subtotal: number
- tax_amount: number
- total_amount: number
- line_items: array of objects with keys: description, quantity, unit_price, amount

Invoice text:
{text}

Return ONLY the JSON object, no markdown formatting or explanation."""

    def __init__(self):
        self.api_key = (
            os.environ.get("OPENAI_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
        )
        self.provider = self._detect_provider()

    def _detect_provider(self) -> str | None:
        """Detect which AI provider is configured."""
        if os.environ.get("OPENAI_API_KEY"):
            return "openai"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            return "anthropic"
        elif os.environ.get("GEMINI_API_KEY"):
            return "gemini"
        return None

    def extract_invoice_data(self, text: str) -> dict:
        """Call LLM with structured output prompt. Return extracted data dict."""
        if not self.api_key or not self.provider:
            raise AIProviderUnavailable(
                "No AI provider API key configured. "
                "Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or GEMINI_API_KEY."
            )

        prompt = self.EXTRACTION_PROMPT.format(text=text)

        try:
            if self.provider == "openai":
                return self._call_openai(prompt)
            elif self.provider == "anthropic":
                return self._call_anthropic(prompt)
            elif self.provider == "gemini":
                return self._call_gemini(prompt)
        except AIProviderUnavailable:
            raise
        except Exception as e:
            logger.error(f"AI provider call failed: {e}")
            raise AIProviderUnavailable(f"AI provider call failed: {e}")

    def _call_openai(self, prompt: str) -> dict:
        """Call OpenAI API."""
        import httpx

        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return self._parse_json_response(content)

    def _call_anthropic(self, prompt: str) -> dict:
        """Call Anthropic API."""
        import httpx

        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 2048,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["content"][0]["text"]
        return self._parse_json_response(content)

    def _call_gemini(self, prompt: str) -> dict:
        """Call Google Gemini API."""
        import httpx

        response = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.api_key}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return self._parse_json_response(content)

    @staticmethod
    def _parse_json_response(content: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            # Remove opening fence (possibly ```json)
            content = re.sub(r"^```(?:json)?\s*\n?", "", content)
            content = re.sub(r"\n?```\s*$", "", content)

        return json.loads(content)
