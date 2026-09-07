"""
sentinel/core/masking.py
========================
High-Performance Regex-based Sensitive Data Masking Engine for OpenSRE.

Detects, redacts, and partially masks sensitive credentials, PCI-DSS payment data,
PII (SSN, Aadhaar, National IDs, Passports), tokens, and private keys IF AND ONLY IF
they contain sensitive data, while leaving safe business variables completely untouched.
"""

import re
from typing import Any, Dict, List, Union, Optional


# ==============================================================================
# 1. KEY-BASED SENSITIVE NAME PATTERNS (Case-insensitive)
# ==============================================================================
SENSITIVE_KEY_PATTERNS = [
    # Passwords & Authentication
    re.compile(r"^(password|passwd|pwd|passphrase)$", re.IGNORECASE),
    re.compile(r".*(password|passwd|pwd|passphrase).*", re.IGNORECASE),
    re.compile(r".*(secret|secretkey|client_secret|clientsecret).*", re.IGNORECASE),
    re.compile(r".*(api_?key|apikey|auth_?token|accesstoken|access_token|refresh_token|refreshtoken).*", re.IGNORECASE),
    re.compile(r".*(bearer|jwt|session_?id|session_?token|private_?key|privkey).*", re.IGNORECASE),
    re.compile(r".*(credential|credentials|authorization|auth_header).*", re.IGNORECASE),
    
    # Financial & PCI-DSS
    re.compile(r".*(card_?number|cardnumber|credit_?card|debit_?card|card_?no|cc_?num).*", re.IGNORECASE),
    re.compile(r".*(cvv|cvc|cvv2|cvc2|security_?code|card_?code).*", re.IGNORECASE),
    re.compile(r".*(iban|account_?number|bank_?account|routing_?number).*", re.IGNORECASE),
    re.compile(r"^(pan|pin|pin_code)$", re.IGNORECASE),

    # PII & National Identity
    re.compile(r".*(ssn|social_?security|national_?id|aadhaar|aadhar|passport_?no|tax_?id|ein).*", re.IGNORECASE),
    re.compile(r".*(otp|verification_?code|mfa_?code).*", re.IGNORECASE),
]


# ==============================================================================
# 2. VALUE-BASED STRICT REGEX PATTERNS (Matching Actual Content)
# ==============================================================================

# Private Key Blocks (RSA, EC, OPENSSH, PGP, etc.)
REGEX_PRIVATE_KEY = re.compile(
    r"-----BEGIN[ A-Z0-9_-]+PRIVATE KEY-----[\s\S]+?-----END[ A-Z0-9_-]+PRIVATE KEY-----",
    re.MULTILINE
)

# JSON Web Tokens (JWT)
REGEX_JWT = re.compile(
    r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
)

# Authorization Headers (Bearer & Basic)
REGEX_BEARER_AUTH = re.compile(
    r"\b(Bearer\s+)[A-Za-z0-9\-._~+/]+=*\b",
    re.IGNORECASE
)
REGEX_BASIC_AUTH = re.compile(
    r"\b(Basic\s+)[A-Za-z0-9+/=]{12,}\b",
    re.IGNORECASE
)

# Cloud & Developer API Keys
REGEX_AWS_ACCESS_KEY = re.compile(r"\b(AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b")
REGEX_GOOGLE_API_KEY = re.compile(r"\bAIza[0-9A-Za-z\-_]{25,40}\b")
REGEX_GITHUB_TOKEN = re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{30,}\b")
REGEX_SLACK_TOKEN = re.compile(r"\bxox[baprs]-[0-9a-zA-Z]{10,48}\b")
REGEX_STRIPE_SECRET_KEY = re.compile(r"\b(?:sk|rk)_(?:test|live)_[0-9a-zA-Z]{20,}\b")
REGEX_GENERIC_INLINE_SECRET = re.compile(
    r"(?i)\b((?:api_?key|secret_?token|auth_?token|secret_?key)\s*[:=\s]+['\"]?)([A-Za-z0-9\-_]{12,64})(['\"]?)"
)

# Credit Card Numbers (Luhn-candidate 13 to 19 digits, plain or hyphen/space separated)
REGEX_CREDIT_CARD = re.compile(
    r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|2[2-7][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12})\b"
)
REGEX_CREDIT_CARD_DELIMITED = re.compile(
    r"\b(?:\d{4}[ -]){3}\d{4}\b|\b\d{4}[ -]\d{6}[ -]\d{5}\b"
)

# US Social Security Number (SSN: XXX-XX-XXXX)
REGEX_US_SSN = re.compile(
    r"\b(?!000|666|9\d{2})\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b"
)

# Indian Identity (Aadhaar: 12 digits, PAN: 5 letters + 4 digits + 1 letter)
REGEX_AADHAAR = re.compile(
    r"\b[2-9]{1}[0-9]{3}[ -][0-9]{4}[ -][0-9]{4}\b"
)
REGEX_PAN_CARD = re.compile(
    r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b"
)

# Passwords inside Connection URIs (e.g. postgres://user:password@host:5432/db)
REGEX_URI_PASSWORD = re.compile(
    r"(?P<prefix>(?:mongodb|postgres|postgresql|mysql|redis|amqp|http|https)://[^:]+:)(?P<pass>[^@/]+)(?P<suffix>@[^/\s]+)",
    re.IGNORECASE
)

# Standard Email Address
REGEX_EMAIL = re.compile(
    r"\b([A-Za-z0-9._%+-]{1,3})[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)

# International & US Phone Numbers
REGEX_PHONE = re.compile(
    r"\b(?:\+?(\d{1,3}))?[-.\s]?\(?(\d{3})\)?[-.\s]?\d{3}[-.\s]?(\d{4})\b"
)


# ==============================================================================
# 3. HELPER MASKING FUNCTIONS
# ==============================================================================

def _is_luhn_valid(card_num: str) -> bool:
    """Verifies Luhn checksum algorithm for potential credit card numbers."""
    digits = [int(d) for d in re.sub(r"\D", "", card_num)]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0


def mask_credit_card(card_str: str) -> str:
    """Masks a credit card preserving only the last 4 digits (e.g. ****-****-****-1234)."""
    digits_only = re.sub(r"\D", "", card_str)
    if len(digits_only) >= 4:
        last4 = digits_only[-4:]
        return f"****-****-****-{last4}"
    return "****-****-****-****"


def mask_ssn(ssn_str: str) -> str:
    """Masks a US SSN preserving only the last 4 digits (e.g. ***-**-6789)."""
    digits_only = re.sub(r"\D", "", ssn_str)
    if len(digits_only) == 9:
        return f"***-**-{digits_only[-4:]}"
    return "***-**-****"


def mask_aadhaar(aadhaar_str: str) -> str:
    """Masks an Aadhaar number preserving only the last 4 digits (e.g. ****-****-1234)."""
    digits_only = re.sub(r"\D", "", aadhaar_str)
    if len(digits_only) == 12:
        return f"****-****-{digits_only[-4:]}"
    return "****-****-****"


def mask_email(email_str: str) -> str:
    """Partially masks email address (e.g. j***@domain.com)."""
    m = REGEX_EMAIL.search(email_str)
    if m:
        prefix, domain = m.group(1), m.group(2)
        return f"{prefix}***@{domain}"
    return "********"


# ==============================================================================
# 4. CORE VALUE MASKING LOGIC
# ==============================================================================

def is_sensitive_key(key: str) -> bool:
    """Checks if a variable key name inherently indicates sensitive data."""
    if not key or not isinstance(key, str):
        return False
    clean_key = key.strip()
    return any(pattern.match(clean_key) for pattern in SENSITIVE_KEY_PATTERNS)


def mask_string_value(val: str, key_hint: str = "") -> str:
    """
    Scans a string value and masks sensitive data matching strict regex patterns.
    If key_hint is inherently sensitive, masks the entire value safely.
    Leaves non-sensitive content completely unchanged.
    """
    if not isinstance(val, str) or not val.strip():
        return val

    # If key indicates strict secret/password/token/cvv/card/ssn, mask with clean asterisks
    if key_hint and is_sensitive_key(key_hint):
        if val.lower() in ("null", "none", "undefined", ""):
            return val
        
        low_key = key_hint.lower()
        
        # Credit / Debit Cards
        if any(w in low_key for w in ["card", "credit", "debit", "pan"]):
            return mask_credit_card(val)
        
        # Social Security Numbers
        if any(w in low_key for w in ["ssn", "social"]):
            return mask_ssn(val)
            
        # Indian Aadhaar
        if any(w in low_key for w in ["aadhaar", "aadhar"]):
            return mask_aadhaar(val)
            
        # CVV / Security Code / PIN
        if any(w in low_key for w in ["cvv", "cvc", "pin", "security_code", "card_code"]):
            return "***"

        # Passwords, Secrets, API Keys, Tokens
        return "********"

    masked = val

    # 1. Private Keys
    masked = REGEX_PRIVATE_KEY.sub("********", masked)

    # 2. Database / Broker Connection URI Passwords
    masked = REGEX_URI_PASSWORD.sub(r"\g<prefix>********\g<suffix>", masked)

    # 3. JWT Tokens
    masked = REGEX_JWT.sub("********", masked)

    # 4. Authorization Headers
    masked = REGEX_BEARER_AUTH.sub(r"\g<1>********", masked)
    masked = REGEX_BASIC_AUTH.sub(r"\g<1>********", masked)

    # 5. Cloud & Developer API Keys & Inline Secrets
    masked = REGEX_AWS_ACCESS_KEY.sub("********", masked)
    masked = REGEX_GOOGLE_API_KEY.sub("********", masked)
    masked = REGEX_GITHUB_TOKEN.sub("********", masked)
    masked = REGEX_SLACK_TOKEN.sub("********", masked)
    masked = REGEX_STRIPE_SECRET_KEY.sub("********", masked)
    masked = REGEX_GENERIC_INLINE_SECRET.sub(r"\g<1>********\g<3>", masked)

    # 6. Credit Card Numbers (with Luhn validation)
    for match in list(REGEX_CREDIT_CARD_DELIMITED.finditer(masked)) + list(REGEX_CREDIT_CARD.finditer(masked)):
        card_candidate = match.group(0)
        if _is_luhn_valid(card_candidate):
            masked = masked.replace(card_candidate, mask_credit_card(card_candidate))

    # 7. US SSN
    for match in REGEX_US_SSN.finditer(masked):
        ssn_candidate = match.group(0)
        masked = masked.replace(ssn_candidate, mask_ssn(ssn_candidate))

    # 8. Indian Identity (Aadhaar & PAN)
    for match in REGEX_AADHAAR.finditer(masked):
        aadhaar_cand = match.group(0)
        masked = masked.replace(aadhaar_cand, mask_aadhaar(aadhaar_cand))

    for match in REGEX_PAN_CARD.finditer(masked):
        pan_cand = match.group(0)
        masked = masked.replace(pan_cand, f"{pan_cand[:2]}****{pan_cand[-2:]}")

    return masked


def mask_sensitive_value(value: Any, key_hint: str = "") -> Any:
    """
    Recursively inspects and masks sensitive data inside any primitive, dict, or list.
    Preserves exact data types for numbers, booleans, and non-sensitive strings.
    """
    if value is None:
        return None

    if isinstance(value, str):
        return mask_string_value(value, key_hint=key_hint)

    if isinstance(value, dict):
        return {
            k: mask_sensitive_value(v, key_hint=str(k))
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [mask_sensitive_value(item, key_hint=key_hint) for item in value]

    # If key indicates sensitivity for numeric pins/cvvs (e.g. cvv: 123)
    if isinstance(value, (int, float)) and key_hint and is_sensitive_key(key_hint):
        return "***"

    return value


def mask_variables(variables: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Main entry point to mask Camunda process variables dictionary.
    Safe variables (customerId, orderId, amount, status) are 100% preserved.
    Sensitive variables (password, token, creditCard, ssn, private keys) are masked.
    """
    if not variables or not isinstance(variables, dict):
        return {}

    return {
        key: mask_sensitive_value(val, key_hint=str(key))
        for key, val in variables.items()
    }


def mask_incident_payload(payload: Any) -> Any:
    """
    Masks sensitive data across all fields of an IncidentAlert / ErrorEvent payload or dict,
    including variables, logs, error message, and timeline context.
    """
    if payload is None:
        return payload

    # Support Pydantic model (IncidentAlert, ErrorEvent)
    if hasattr(payload, "model_copy"):
        updates: Dict[str, Any] = {}
        if hasattr(payload, "variables") and payload.variables:
            updates["variables"] = mask_variables(payload.variables)
        if hasattr(payload, "error_message") and payload.error_message:
            updates["error_message"] = mask_string_value(payload.error_message)
        if hasattr(payload, "logs") and payload.logs:
            updates["logs"] = [mask_string_value(l) for l in payload.logs]
        if hasattr(payload, "timeline") and payload.timeline:
            updates["timeline"] = [mask_string_value(t) for t in payload.timeline]
        return payload.model_copy(update=updates)

    if isinstance(payload, dict):
        sanitized = dict(payload)
        if "variables" in sanitized and isinstance(sanitized["variables"], dict):
            sanitized["variables"] = mask_variables(sanitized["variables"])
        if "error_message" in sanitized and isinstance(sanitized["error_message"], str):
            sanitized["error_message"] = mask_string_value(sanitized["error_message"])
        elif "errorMessage" in sanitized and isinstance(sanitized["errorMessage"], str):
            sanitized["errorMessage"] = mask_string_value(sanitized["errorMessage"])
        if "logs" in sanitized and isinstance(sanitized["logs"], list):
            sanitized["logs"] = [
                mask_string_value(log) if isinstance(log, str) else log
                for log in sanitized["logs"]
            ]
        if "timeline" in sanitized and isinstance(sanitized["timeline"], list):
            sanitized["timeline"] = [
                mask_string_value(t) if isinstance(t, str) else t
                for t in sanitized["timeline"]
            ]
        return sanitized

    return payload
