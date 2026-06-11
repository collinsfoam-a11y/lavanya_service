import re


VALID_MOBILE_START_DIGITS = {"6", "7", "8", "9"}


def normalize_phone(value):
	"""Return canonical Indian mobile details for a raw phone value.

	Canonical mobile values are stored as 10 digits. Raw-only values are preserved
	by callers but are not used for uniqueness or customer-profile matching.
	"""

	raw = "" if value is None else str(value)
	clean_raw = raw.strip()

	result = {
		"raw": raw,
		"normalized": None,
		"is_valid_mobile": False,
		"reason": "blank",
	}

	if not clean_raw:
		result["raw"] = ""
		return result

	digits = re.sub(r"\D+", "", clean_raw)
	if not digits:
		result["reason"] = "too_short"
		return result

	candidate = None
	prefixed_with_zero = False

	if len(digits) == 10:
		candidate = digits
	elif len(digits) == 12 and digits.startswith("91"):
		candidate = digits[2:]
	elif len(digits) == 11 and digits.startswith("0"):
		candidate = digits[1:]
		prefixed_with_zero = True
	else:
		if len(digits) < 10:
			result["reason"] = "too_short"
		elif len(digits) in {11, 12}:
			result["reason"] = "not_indian_mobile"
		else:
			result["reason"] = "too_long"
		return result

	if len(set(candidate)) == 1:
		result["reason"] = "repeated_junk"
		return result

	if candidate[0] not in VALID_MOBILE_START_DIGITS:
		result["reason"] = "not_indian_mobile" if prefixed_with_zero else "invalid_mobile_range"
		return result

	result["normalized"] = candidate
	result["is_valid_mobile"] = True
	result["reason"] = "valid"
	return result


def normalized_mobile(value):
	return normalize_phone(value).get("normalized") or ""


def is_mobile_number_name(value):
	result = normalize_phone(value)
	return bool(result["is_valid_mobile"] and result["raw"].strip() == result["normalized"])
