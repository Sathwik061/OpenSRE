/**
 * Incident Insights Hub / src/lib/masking.ts
 * ==========================================
 * Client-side Regex-based Sensitive Data Masking Engine.
 * Masks passwords, API keys, JWT tokens, credit cards, SSNs, and private keys
 * IF AND ONLY IF they contain sensitive data, while leaving safe business variables untouched.
 */

// 1. Key-based Sensitive Name Patterns
const SENSITIVE_KEY_REGEX =
  /^(password|passwd|pwd|passphrase|secret|secretkey|client_secret|clientsecret|api_?key|apikey|auth_?token|accesstoken|access_token|refresh_token|refreshtoken|bearer|jwt|session_?id|session_?token|private_?key|privkey|credential|credentials|authorization|auth_header|card_?number|cardnumber|credit_?card|debit_?card|card_?no|cc_?num|cvv|cvc|cvv2|cvc2|security_?code|card_?code|iban|account_?number|bank_?account|routing_?number|pan|pin|pin_code|ssn|social_?security|national_?id|aadhaar|aadhar|passport_?no|tax_?id|ein|otp|verification_?code|mfa_?code)$/i;

// 2. Strict Value-based Regex Patterns
const REGEX_PRIVATE_KEY = /-----BEGIN[ A-Z0-9_-]+PRIVATE KEY-----[\s\S]+?-----END[ A-Z0-9_-]+PRIVATE KEY-----/g;
const REGEX_JWT = /\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g;
const REGEX_BEARER_AUTH = /\b(Bearer\s+)[A-Za-z0-9\-._~+/]+=*\b/gi;
const REGEX_BASIC_AUTH = /\b(Basic\s+)[A-Za-z0-9+/=]{12,}\b/gi;
const REGEX_AWS_ACCESS_KEY = /\b(AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b/g;
const REGEX_GOOGLE_API_KEY = /\bAIza[0-9A-Za-z\-_]{25,45}\b/g;
const REGEX_GITHUB_TOKEN = /\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{30,}\b/g;
const REGEX_GENERIC_INLINE_SECRET = /\b((?:api_?key|secret_?token|auth_?token|secret_?key)\s*[:=\s]+['"]?)([A-Za-z0-9\-_]{12,64})(['"]?)/gi;
const REGEX_CREDIT_CARD_DELIMITED = /\b(?:\d{4}[ -]){3}\d{4}\b|\b\d{4}[ -]\d{6}[ -]\d{5}\b/g;
const REGEX_US_SSN = /\b(?!000|666|9\d{2})\d{3}[- ](?!00)\d{2}[- ](?!0000)\d{4}\b/g;
const REGEX_AADHAAR = /\b[2-9]{1}[0-9]{3}[ -][0-9]{4}[ -][0-9]{4}\b/g;
const REGEX_URI_PASSWORD = /((?:mongodb|postgres|postgresql|mysql|redis|amqp|http|https):\/\/[^:]+:)([^@/]+)(@[^/\s]+)/gi;

function isLuhnValid(cardNum: string): boolean {
  const digits = cardNum.replace(/\D/g, "").split("").map(Number);
  if (digits.length < 13 || digits.length > 19) return false;
  let checksum = 0;
  const reversed = digits.reverse();
  for (let i = 0; i < reversed.length; i++) {
    let d = reversed[i];
    if (i % 2 === 1) {
      d *= 2;
      checksum += d > 9 ? d - 9 : d;
    } else {
      checksum += d;
    }
  }
  return checksum % 10 === 0;
}

export function isSensitiveKey(key: string): boolean {
  if (!key) return false;
  return SENSITIVE_KEY_REGEX.test(key.trim());
}

export function maskStringValue(val: string, keyHint: string = ""): string {
  if (!val || typeof val !== "string") return val;

  // Key-based check
  if (keyHint && isSensitiveKey(keyHint)) {
    if (["null", "none", "undefined", ""].includes(val.toLowerCase().trim())) {
      return val;
    }
    const lowKey = keyHint.toLowerCase();
    const digits = val.replace(/\D/g, "");

    if (["card", "credit", "debit", "pan"].some((w) => lowKey.includes(w))) {
      return digits.length >= 4 ? `****-****-****-${digits.slice(-4)}` : "****-****-****-****";
    }
    if (["ssn", "social"].some((w) => lowKey.includes(w))) {
      return digits.length === 9 ? `***-**-${digits.slice(-4)}` : "***-**-****";
    }
    if (["aadhaar", "aadhar"].some((w) => lowKey.includes(w))) {
      return digits.length === 12 ? `****-****-${digits.slice(-4)}` : "****-****-****";
    }
    if (["cvv", "cvc", "pin", "security_code"].some((w) => lowKey.includes(w))) {
      return "***";
    }
    return "********";
  }

  let masked = val;

  // Value-based regex checks
  masked = masked.replace(REGEX_PRIVATE_KEY, "********");
  masked = masked.replace(REGEX_URI_PASSWORD, "$1********$3");
  masked = masked.replace(REGEX_JWT, "********");
  masked = masked.replace(REGEX_BEARER_AUTH, "$1********");
  masked = masked.replace(REGEX_BASIC_AUTH, "$1********");
  masked = masked.replace(REGEX_AWS_ACCESS_KEY, "********");
  masked = masked.replace(REGEX_GOOGLE_API_KEY, "********");
  masked = masked.replace(REGEX_GITHUB_TOKEN, "********");
  masked = masked.replace(REGEX_GENERIC_INLINE_SECRET, "$1********$3");

  // Credit Cards
  masked = masked.replace(REGEX_CREDIT_CARD_DELIMITED, (cand) => {
    if (isLuhnValid(cand)) {
      const digits = cand.replace(/\D/g, "");
      return `****-****-****-${digits.slice(-4)}`;
    }
    return cand;
  });

  // SSN
  masked = masked.replace(REGEX_US_SSN, (cand) => {
    const digits = cand.replace(/\D/g, "");
    return `***-**-${digits.slice(-4)}`;
  });

  // Aadhaar
  masked = masked.replace(REGEX_AADHAAR, (cand) => {
    const digits = cand.replace(/\D/g, "");
    return `****-****-${digits.slice(-4)}`;
  });

  return masked;
}

export function maskVariables(variables: Record<string, any> | null | undefined): Record<string, any> {
  if (!variables || typeof variables !== "object") return {};

  const result: Record<string, any> = {};
  for (const [k, v] of Object.entries(variables)) {
    if (typeof v === "string") {
      result[k] = maskStringValue(v, k);
    } else if (typeof v === "number" && isSensitiveKey(k)) {
      result[k] = "***";
    } else if (v && typeof v === "object") {
      result[k] = maskVariables(v);
    } else {
      result[k] = v;
    }
  }
  return result;
}
