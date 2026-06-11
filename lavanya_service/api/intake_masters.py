import re
from difflib import SequenceMatcher

import frappe


CATEGORY_DOCTYPE = "Lavanya Product Category"
ITEM_DOCTYPE = "Lavanya Product Item"
BRAND_DOCTYPE = "Brand Service Master"

ALLOWED_CREATE_ROLES = {
	"Lavanya Manager",
	"Lavanya Helpdesk Agent",
	"Lavanya Front Desk",
	"Lavanya Service Coordinator",
	"System Manager",
}

LEGACY_PRODUCT_TYPES = {
	"AC",
	"Refrigerator",
	"Washing Machine",
	"Mixer",
	"Induction Cooker",
	"Chimney",
	"Hob",
	"Gas Stove",
	"TV",
	"Water Purifier",
	"Other",
}


def normalise_lookup_text(value):
	if value is None:
		return ""

	text = str(value).strip().lower()
	text = re.sub(r"[^\w\s]+", " ", text)
	text = re.sub(r"\s+", " ", text)
	return text.strip()


def _require_create_role():
	if frappe.session.user == "Administrator":
		return

	if not set(frappe.get_roles(frappe.session.user)).intersection(ALLOWED_CREATE_ROLES):
		frappe.throw(
			"Only Lavanya staff roles can create intake master records.",
			frappe.PermissionError,
		)


def _is_similar(query_key, candidate_key):
	if not query_key or not candidate_key:
		return False

	if query_key in candidate_key or candidate_key in query_key:
		return True

	query_tokens = set(query_key.split())
	candidate_tokens = set(candidate_key.split())
	if query_tokens and candidate_tokens and query_tokens.intersection(candidate_tokens):
		return True

	return SequenceMatcher(None, query_key, candidate_key).ratio() >= 0.62


def _score(query_key, candidate_key):
	if not query_key or not candidate_key:
		return 0
	return round(SequenceMatcher(None, query_key, candidate_key).ratio(), 3)


def _find_exact_by_normalised(doctype, fieldname, value, filters=None):
	target_key = normalise_lookup_text(value)
	if not target_key:
		return None

	query_filters = dict(filters or {})
	rows = frappe.get_all(
		doctype,
		filters=query_filters,
		fields=["name", fieldname],
		limit=500,
	)

	for row in rows:
		if normalise_lookup_text(row.get(fieldname)) == target_key:
			return row

	return None


def _brand_payload(row, query_key):
	brand_name = row.get("brand_name") or row.name
	key = normalise_lookup_text(brand_name)
	return {
		"name": row.name,
		"brand_name": brand_name,
		"score": _score(query_key, key),
	}


@frappe.whitelist()
def search_similar_brand(query):
	query_key = normalise_lookup_text(query)
	if not query_key:
		return []

	rows = frappe.get_all(
		BRAND_DOCTYPE,
		fields=["name", "brand_name"],
		order_by="name asc",
		limit=500,
	)

	matches = [
		_brand_payload(row, query_key)
		for row in rows
		if _is_similar(query_key, normalise_lookup_text(row.get("brand_name") or row.name))
	]
	return sorted(matches, key=lambda row: (-row["score"], row["name"]))[:10]


@frappe.whitelist()
def create_brand(name):
	_require_create_role()
	brand_name = str(name or "").strip()
	if not brand_name:
		frappe.throw("Brand name is required.")

	existing = _find_exact_by_normalised(BRAND_DOCTYPE, "brand_name", brand_name)
	if existing:
		frappe.throw(f"Brand already exists: {existing.name}")

	doc = frappe.new_doc(BRAND_DOCTYPE)
	doc.brand_name = brand_name
	doc.registration_channel = "Toll Free"
	doc.default_registration_sla_hours = 4
	doc.free_service_supported = 0
	doc.insert(ignore_permissions=True)

	return {
		"name": doc.name,
		"brand_name": doc.brand_name,
		"created": True,
	}


def _category_payload(row, query_key):
	key = normalise_lookup_text(row.category_name or row.name)
	return {
		"name": row.name,
		"category_name": row.category_name,
		"parent_category": row.parent_category,
		"score": _score(query_key, key),
	}


@frappe.whitelist()
def search_similar_category(query):
	query_key = normalise_lookup_text(query)
	if not query_key or not frappe.db.exists("DocType", CATEGORY_DOCTYPE):
		return []

	rows = frappe.get_all(
		CATEGORY_DOCTYPE,
		filters={"disabled": 0},
		fields=["name", "category_name", "parent_category"],
		order_by="name asc",
		limit=500,
	)

	matches = [
		_category_payload(row, query_key)
		for row in rows
		if _is_similar(query_key, normalise_lookup_text(row.category_name or row.name))
	]
	return sorted(matches, key=lambda row: (-row["score"], row["name"]))[:10]


@frappe.whitelist()
def create_category(category_name, parent_category=None):
	_require_create_role()
	category_name = str(category_name or "").strip()
	parent_category = str(parent_category or "").strip() or None

	if not category_name:
		frappe.throw("Category name is required.")

	existing = _find_exact_by_normalised(CATEGORY_DOCTYPE, "category_name", category_name)
	if existing:
		frappe.throw(f"Product category already exists: {existing.name}")

	if parent_category and not frappe.db.exists(CATEGORY_DOCTYPE, parent_category):
		frappe.throw(f"Parent category does not exist: {parent_category}")

	doc = frappe.new_doc(CATEGORY_DOCTYPE)
	doc.category_name = category_name
	doc.parent_category = parent_category
	doc.disabled = 0
	doc.insert(ignore_permissions=True)

	return {
		"name": doc.name,
		"category_name": doc.category_name,
		"parent_category": doc.parent_category,
		"created": True,
	}


def _item_duplicate(item_name, brand=None, model_no=None):
	target_name = normalise_lookup_text(item_name)
	target_brand = normalise_lookup_text(brand)
	target_model = normalise_lookup_text(model_no)

	rows = frappe.get_all(
		ITEM_DOCTYPE,
		fields=["name", "item_name", "brand", "model_no"],
		limit=1000,
	)

	for row in rows:
		same_name = normalise_lookup_text(row.item_name or row.name) == target_name
		same_brand = normalise_lookup_text(row.brand) == target_brand
		same_model = normalise_lookup_text(row.model_no) == target_model
		if same_name and same_brand and same_model:
			return row

	return None


def _item_payload(row, query_key):
	key = normalise_lookup_text(" ".join([row.item_name or row.name, row.brand or "", row.model_no or ""]))
	return {
		"name": row.name,
		"item_name": row.item_name,
		"item_type": row.item_type,
		"brand": row.brand,
		"model_no": row.model_no,
		"default_warranty_months": row.default_warranty_months,
		"score": _score(query_key, key),
	}


@frappe.whitelist()
def search_similar_item(query, brand=None, category=None, model_no=None):
	query_key = normalise_lookup_text(" ".join([str(query or ""), str(model_no or "")]))
	if not query_key or not frappe.db.exists("DocType", ITEM_DOCTYPE):
		return []

	filters = {"disabled": 0}
	if brand:
		filters["brand"] = brand
	if category:
		filters["item_type"] = category

	rows = frappe.get_all(
		ITEM_DOCTYPE,
		filters=filters,
		fields=[
			"name",
			"item_name",
			"item_type",
			"brand",
			"model_no",
			"default_warranty_months",
		],
		order_by="modified desc",
		limit=500,
	)

	matches = [
		_item_payload(row, query_key)
		for row in rows
		if _is_similar(
			query_key,
			normalise_lookup_text(" ".join([row.item_name or row.name, row.brand or "", row.model_no or ""])),
		)
	]
	return sorted(matches, key=lambda row: (-row["score"], row["name"]))[:10]


@frappe.whitelist()
def create_item(
	item_name,
	brand=None,
	item_type=None,
	model_no=None,
	default_warranty_months=0,
):
	_require_create_role()
	item_name = str(item_name or "").strip()
	brand = str(brand or "").strip() or None
	item_type = str(item_type or "").strip() or None
	model_no = str(model_no or "").strip() or None

	if not item_name:
		frappe.throw("Item name is required.")

	if brand and not frappe.db.exists(BRAND_DOCTYPE, brand):
		frappe.throw(f"Brand does not exist: {brand}")

	if item_type and not frappe.db.exists(CATEGORY_DOCTYPE, item_type):
		frappe.throw(f"Product category does not exist: {item_type}")

	existing = _item_duplicate(item_name, brand=brand, model_no=model_no)
	if existing:
		frappe.throw(f"Product item already exists: {existing.name}")

	doc = frappe.new_doc(ITEM_DOCTYPE)
	doc.item_name = item_name
	doc.item_type = item_type
	doc.brand = brand
	doc.model_no = model_no
	doc.default_warranty_months = int(default_warranty_months or 0)
	doc.disabled = 0
	doc.insert(ignore_permissions=True)

	return {
		"name": doc.name,
		"item_name": doc.item_name,
		"item_type": doc.item_type,
		"brand": doc.brand,
		"model_no": doc.model_no,
		"default_warranty_months": doc.default_warranty_months,
		"created": True,
	}


@frappe.whitelist()
def get_item_defaults(item):
	if not item:
		return {"found": False}

	if not frappe.db.exists(ITEM_DOCTYPE, item):
		return {"found": False, "name": item}

	doc = frappe.get_doc(ITEM_DOCTYPE, item)
	product_type = doc.item_type if doc.item_type in LEGACY_PRODUCT_TYPES else None

	return {
		"found": True,
		"name": doc.name,
		"item_name": doc.item_name,
		"item_type": doc.item_type,
		"product_category": doc.item_type,
		"product_type": product_type,
		"brand": doc.brand,
		"model_no": doc.model_no,
		"default_warranty_months": doc.default_warranty_months,
	}
