"""Bounded cloud requests and actionable, credential-free error messages."""
import os


def create_client(polish=False):
    import httpx
    from groq import Groq
    key = os.environ.get("GROQ_API_KEY", "")
    if not key or key == "your_groq_api_key_here":
        raise RuntimeError("Add a valid GROQ_API_KEY to the .env file beside ALTWISP, or choose Local in Settings.")
    return Groq(api_key=key, timeout=httpx.Timeout(8.0 if polish else 15.0, connect=4.0),
                max_retries=0 if polish else 1)


def describe_error(exc):
    from groq import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError, APIStatusError
    if isinstance(exc, APITimeoutError):
        return "The speech server took too long to respond. Check your connection and retry the recording."
    if isinstance(exc, APIConnectionError):
        return "Could not connect securely to Groq. Check your internet, VPN or proxy, then retry. Local transcription works offline after its model is downloaded."
    if isinstance(exc, AuthenticationError):
        return "Groq rejected the API key. Update GROQ_API_KEY in .env and restart ALTWISP."
    if isinstance(exc, RateLimitError):
        return "Groq's usage limit was reached. Wait before retrying, or switch to Local transcription."
    if isinstance(exc, APIStatusError):
        return f"Groq returned HTTP {exc.status_code}. Please retry shortly."
    return str(exc) if isinstance(exc, (RuntimeError, ValueError)) else f"{type(exc).__name__}: the operation could not complete. See the local diagnostic log."
