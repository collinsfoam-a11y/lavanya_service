import frappe

from lavanya_service.workflow.today_work import get_today_work_data


@frappe.whitelist()
def get_today_work(owner=None, include_counts=True, limit=50):
	return get_today_work_data(
		user=frappe.session.user,
		owner=owner,
		include_counts=_as_bool(include_counts),
		limit=limit,
	)


def _as_bool(value):
	if isinstance(value, str):
		return value.strip().lower() not in {"0", "false", "no", "off"}
	return bool(value)
