import frappe
from frappe.utils import today, date_diff, getdate, add_days

# A ticket escalates when its follow-up is overdue by at least this many days, or
# its SLA has failed. Default 3 days — adjust here (or move to HD Settings) to suit
# the service desk's policy.
ESCALATION_OVERDUE_DAYS = 3


def get_customer_promise_breach_report():
	"""Active tickets where a customer-promised update time has passed and the
	promise wasn't marked Kept — these must be handled first."""
	if not frappe.get_meta("HD Ticket").has_field("customer_promised_update_at"):
		return []
	return frappe.db.sql(
		"""
		SELECT
			name as ticket, customer_name, phone_1, brand, status,
			current_service_stage, customer_promised_update_at,
			TIMESTAMPDIFF(HOUR, customer_promised_update_at, %s) as hours_late
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Closed', 'Cancelled', 'Resolved')
		  AND customer_promised_update_at IS NOT NULL
		  AND customer_promised_update_at < %s
		  AND IFNULL(customer_promise_status, '') != 'Kept'
		ORDER BY customer_promised_update_at ASC
		""",
		(frappe.utils.now_datetime(), frappe.utils.now_datetime()),
		as_dict=True,
	)


def get_stage_missing_report():
	"""Active tickets without a current_service_stage — they won't follow the stage
	flow until assigned. Cleanup queue for the delta stage rollout."""
	if not frappe.get_meta("HD Ticket").has_field("current_service_stage"):
		return []
	return frappe.db.sql(
		"""
		SELECT
			name as ticket, customer_name, phone_1, brand, ticket_type,
			service_flow_type, status, creation
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Closed', 'Cancelled', 'Resolved')
		  AND (current_service_stage IS NULL OR current_service_stage = '')
		ORDER BY creation DESC
		""",
		as_dict=True,
	)


def get_escalation_report():
	"""Active tickets that need management attention: SLA failed, or follow-up
	overdue by >= ESCALATION_OVERDUE_DAYS days. Worst (oldest) first."""
	return frappe.db.sql(
		"""
		SELECT
			name as ticket, customer_name, phone_1, brand, product_type, status,
			agreement_status, pending_reason, next_follow_up_date,
			DATEDIFF(%s, next_follow_up_date) as overdue_days, priority
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Closed', 'Cancelled', 'Resolved')
		  AND (
			agreement_status = 'Failed'
			OR (next_follow_up_date IS NOT NULL AND DATEDIFF(%s, next_follow_up_date) >= %s)
		  )
		ORDER BY next_follow_up_date ASC
		""",
		(today(), today(), ESCALATION_OVERDUE_DAYS),
		as_dict=True,
	)

def get_daily_follow_up_report():
	return frappe.db.sql("""
		SELECT
			name as ticket, subject, customer_name, phone_1, brand, product_type,
			status, pending_reason, next_follow_up_date,
			DATEDIFF(%s, creation) as age_days, priority
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Closed', 'Cancelled', 'Resolved')
		  AND next_follow_up_date IS NOT NULL
		  AND next_follow_up_date <= %s
		ORDER BY next_follow_up_date ASC
	""", (today(), today()), as_dict=True)

def get_brand_pending_report():
	return frappe.db.sql("""
		SELECT
			name as ticket, customer_name, phone_1, brand, ticket_type, warranty_status,
			manufacturer_registered, brand_ticket_number, registration_date,
			registration_pending_reason, next_follow_up_date
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Closed', 'Cancelled', 'Resolved')
		  AND (
			  status = 'Registration Pending'
			  OR (warranty_status = 'In Warranty' AND IFNULL(manufacturer_registered, '') != 'Yes' AND IFNULL(brand_ticket_number, '') = '' AND IFNULL(brand_registration_override_reason, '') = '')
			  OR (IFNULL(brand_ticket_number, '') != '' AND status IN ('Brand Registered', 'In Progress', 'Waiting on Part / Approval'))
		  )
		ORDER BY creation ASC
	""", as_dict=True)

def get_waiting_on_customer_report():
	return frappe.db.sql("""
		SELECT
			name as ticket, customer_name, phone_1, pending_reason, next_follow_up_date,
			DATEDIFF(%s, creation) as age_days, modified as last_modified
		FROM `tabHD Ticket`
		WHERE status = 'Waiting on Customer'
		ORDER BY modified DESC
	""", (today(),), as_dict=True)

def get_waiting_on_part_report():
	return frappe.db.sql("""
		SELECT
			name as ticket, customer_name, brand, product_type, product_item,
			pending_reason, next_follow_up_date, DATEDIFF(%s, creation) as age_days
		FROM `tabHD Ticket`
		WHERE status = 'Waiting on Part / Approval'
		ORDER BY modified DESC
	""", (today(),), as_dict=True)

def get_product_at_store_aging_report():
	return frappe.db.sql("""
		SELECT
			r.name as receipt, r.ticket, t.customer_name, t.phone_1, t.brand,
			t.product_type, t.product_item, r.current_custody_status, r.receipt_date,
			DATEDIFF(%s, r.receipt_date) as age_days, r.name as service_product_receipt,
			t.status as ticket_status
		FROM `tabService Product Receipt` r
		LEFT JOIN `tabHD Ticket` t ON r.ticket = t.name
		WHERE r.current_custody_status IN ('Received at Store', 'Handed to Service Center', 'With Local Technician', 'Returned to Store')
		ORDER BY r.receipt_date ASC
	""", (today(),), as_dict=True)

def get_ready_for_pickup_report():
	return frappe.db.sql("""
		SELECT
			name as ticket, customer_name, phone_1, brand, product_type,
			service_product_receipt, next_follow_up_date, modified
		FROM `tabHD Ticket`
		WHERE status = 'Ready for Pickup'
		ORDER BY modified DESC
	""", as_dict=True)

def get_closure_report(from_date=None, to_date=None):
	filters = "status IN ('Closed', 'Resolved')"
	args = []
	if from_date:
		filters += " AND DATE(modified) >= %s"
		args.append(from_date)
	if to_date:
		filters += " AND DATE(modified) <= %s"
		args.append(to_date)
	
	if not from_date and not to_date:
		filters += " AND DATE(modified) = %s"
		args.append(today())
		
	return frappe.db.sql(f"""
		SELECT
			name as ticket, customer_name, brand, product_type, status,
			closure_type, customer_confirmation_received, closed_by, modified as closure_date,
			work_narration
		FROM `tabHD Ticket`
		WHERE {filters}
		ORDER BY modified DESC
	""", tuple(args), as_dict=True)

def get_repeat_complaint_report():
	return frappe.db.sql("""
		SELECT
			name as ticket, previous_ticket_link, customer_name, phone_1,
			brand, product_type, model_no, serial_no, status, closure_type
		FROM `tabHD Ticket`
		WHERE is_repeated_complaint = 'Yes'
		ORDER BY creation DESC
	""", as_dict=True)

def get_warranty_override_report():
	return frappe.db.sql("""
		SELECT
			name as ticket, customer_name, phone_1, brand, ticket_type, warranty_status,
			manufacturer_registered, brand_ticket_number, brand_registration_override_reason,
			registration_pending_reason, status
		FROM `tabHD Ticket`
		WHERE warranty_status = 'In Warranty'
		  AND (
			IFNULL(brand_registration_override_reason, '') != ''
			OR IFNULL(manufacturer_registered, '') != 'Yes'
		  )
		ORDER BY creation DESC
	""", as_dict=True)

def get_cancelled_tickets_report(from_date=None, to_date=None):
	filters = "status = 'Cancelled'"
	args = []
	if from_date:
		filters += " AND DATE(modified) >= %s"
		args.append(from_date)
	if to_date:
		filters += " AND DATE(modified) <= %s"
		args.append(to_date)
		
	if not from_date and not to_date:
		filters += " AND DATE(modified) = %s"
		args.append(today())

	return frappe.db.sql(f"""
		SELECT
			name as ticket, customer_name, phone_1, brand, product_type,
			closure_type, work_narration, modified
		FROM `tabHD Ticket`
		WHERE {filters}
		ORDER BY modified DESC
	""", tuple(args), as_dict=True)
