"""H1 workflow consistency hardening tests."""
import frappe
from frappe.tests.utils import FrappeTestCase as IntegrationTestCase
from frappe.utils import now_datetime, add_to_date, today


class TestH1ClosureValidations(IntegrationTestCase):
	"""P0 Fix 1: Linked record completion check before closure."""

	def setUp(self):
		self.ticket = frappe.get_doc({
			"doctype": "HD Ticket",
			"subject": "H1 Test - Closure Validation",
			"description": "Test",
			"ticket_type": "Customer Complaint - Site",
			"customer_name": "H1 Customer",
			"status": "Open",
		}).insert()
		frappe.db.commit()

	def tearDown(self):
		try:
			for doctype in ["Replacement Record", "Return Service Record", "Stock Complaint Record",
							"Store Service Record", "Service Product Receipt"]:
				for rec in frappe.get_all(doctype, filters={"ticket": self.ticket.name}):
					frappe.delete_doc(doctype, rec.name, ignore_permissions=True, force=True)
			if frappe.db.exists("HD Ticket", self.ticket.name):
				frappe.delete_doc("HD Ticket", self.ticket.name, ignore_permissions=True, force=True)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()

	def _set_flow(self, flow_type):
		"""Set service_flow_type using db.set_value to avoid timestamp issues."""
		frappe.db.set_value("HD Ticket", self.ticket.name, "service_flow_type", flow_type)
		frappe.db.commit()

	def test_replacement_cannot_close_without_completed_record(self):
		"""Replacement ticket must have a completed Replacement Record before close."""
		self._set_flow("Replacement / Exchange")
		from lavanya_service.workflow.quick_actions import close_ticket
		with self.assertRaises(frappe.ValidationError):
			close_ticket(self.ticket.name, work_narration="test", closure_type="Resolved by Brand Service",
						customer_confirmation_received="Yes")

	def test_return_cannot_close_without_record(self):
		"""Return ticket must have a completed Return Service Record before close."""
		self._set_flow("Refund Case")
		from lavanya_service.workflow.quick_actions import close_ticket
		with self.assertRaises(frappe.ValidationError):
			close_ticket(self.ticket.name, work_narration="test", closure_type="Customer Collected Product",
						customer_confirmation_received="Yes")

	def test_stock_complaint_cannot_close_without_credit_note(self):
		"""Stock complaint must have completed Stock Complaint Record before close."""
		self._set_flow("Stock Complaint")
		from lavanya_service.workflow.quick_actions import close_ticket
		with self.assertRaises(frappe.ValidationError):
			close_ticket(self.ticket.name, work_narration="test", closure_type="Replacement Completed",
						customer_confirmation_received="Yes")

	def test_store_service_cannot_close_without_handover(self):
		"""Store service must have Service Product Receipt before close."""
		self._set_flow("Customer Product at Store")
		from lavanya_service.workflow.quick_actions import close_ticket
		with self.assertRaises(frappe.ValidationError):
			close_ticket(self.ticket.name, work_narration="test", closure_type="Resolved by Brand Service",
						customer_confirmation_received="Yes")


class TestH1EscalationProtection(IntegrationTestCase):
	"""P0 Fix 3: Scheduler cannot downgrade manual escalation."""

	def test_scheduler_does_not_downgrade_manual_escalation(self):
		"""Manual L3 escalation must not be downgraded to L1 by the scheduler."""
		ticket = frappe.get_doc({
			"doctype": "HD Ticket",
			"subject": "H1 Test - Escalation Protection",
			"description": "Test",
			"ticket_type": "Customer Complaint - Site",
			"customer_name": "H1 Escalation",
			"status": "Open",
			"escalation_level": "L3 - Manager Escalation",
		}).insert()
		frappe.db.commit()

		from lavanya_service.reminder_engine import _persist_state, _ESCALATION_ORDER
		computed = "L1 - Agent Follow-up"
		_persist_state(ticket, None, None, computed, "Not Due", None, False)
		ticket.reload()
		self.assertEqual(ticket.escalation_level, "L3 - Manager Escalation")

		frappe.delete_doc("HD Ticket", ticket.name, ignore_permissions=True, force=True)
		frappe.db.commit()

	def test_scheduler_can_increase_escalation(self):
		"""Scheduler may increase escalation from None to a computed level."""
		ticket = frappe.get_doc({
			"doctype": "HD Ticket",
			"subject": "H1 Test - Escalation Increase",
			"description": "Test",
			"ticket_type": "Customer Complaint - Site",
			"customer_name": "H1 Esc Up",
			"status": "Open",
			"escalation_level": "None",
		}).insert()
		frappe.db.commit()

		from lavanya_service.reminder_engine import _persist_state, _ESCALATION_ORDER
		computed = "L2 - Coordinator Escalation"
		_persist_state(ticket, None, None, computed, "Not Due", None, False)
		ticket.reload()
		self.assertEqual(ticket.escalation_level, "L2 - Coordinator Escalation")

		frappe.delete_doc("HD Ticket", ticket.name, ignore_permissions=True, force=True)
		frappe.db.commit()


class TestH1CustomerInformedCanonical(IntegrationTestCase):
	"""P0 Fix 2: customer_informed_status is canonical; customer_informed derived."""

	def test_inform_customer_sets_canonical_field(self):
		"""inform_customer sets customer_informed_status and synced customer_informed."""
		ticket = frappe.get_doc({
			"doctype": "HD Ticket",
			"subject": "H1 Test - Customer Informed",
			"description": "Test",
			"ticket_type": "Customer Complaint - Site",
			"customer_name": "H1 Informed",
			"status": "Open",
		}).insert()
		frappe.db.commit()

		from lavanya_service.workflow.quick_actions import inform_customer
		inform_customer(ticket.name, message="Test message", channel="Phone")
		ticket.reload()
		self.assertEqual(ticket.customer_informed, "Yes")
		self.assertEqual(ticket.customer_informed_status, "Informed by Call")
		self.assertIsNotNone(ticket.customer_informed_at)

		frappe.delete_doc("HD Ticket", ticket.name, ignore_permissions=True, force=True)
		frappe.db.commit()


class TestH1StageBridge(IntegrationTestCase):
	"""P0 Fix 4: followup_stage bridges to current_service_stage where applicable."""

	def test_followup_stage_bridge_constants_exist(self):
		"""The sync constants are defined and importable."""
		from lavanya_service.workflow.quick_actions import _FOLLOWUP_STAGE_SYNC
		self.assertIn("technician_called", _FOLLOWUP_STAGE_SYNC)
		self.assertIn("technician_visited", _FOLLOWUP_STAGE_SYNC)
		self.assertTrue(len(_FOLLOWUP_STAGE_SYNC) >= 4)

	def test_stage_rules_bridge_mapping_exists(self):
		"""The FOLLOWUP_STAGE_TO_SERVICE_STAGE mapping exists in stage_rules."""
		from lavanya_service.stage_rules import FOLLOWUP_STAGE_TO_SERVICE_STAGE, derive_stage_from_followup
		self.assertIn("registration_done", FOLLOWUP_STAGE_TO_SERVICE_STAGE)
		self.assertEqual(derive_stage_from_followup("registration_done"), "Brand Registered")
		self.assertEqual(derive_stage_from_followup("part_pending"), "Spare Pending")


class TestH1StageOptionsPermanence(IntegrationTestCase):
	"""H1 Fix 1: Stage options persist after migrate."""

	def test_current_service_stage_has_all_stages(self):
		"""The current_service_stage field must have all 52 stages."""
		meta = frappe.get_meta("HD Ticket")
		field = meta.get_field("current_service_stage")
		self.assertIsNotNone(field, "current_service_stage field must exist")
		opts = str(field.options).split("\n")
		# 52 stages + 1 leading blank = 53 lines
		self.assertGreaterEqual(len(opts), 52,
			f"Expected at least 52 stage options, got {len(opts)}")
		for stage in ["Old Unit Collected", "Return Reason Verified",
					   "Brand Notified for Return", "New Unit Dispatched",
					   "Customer Refund Processed", "Reimbursement Received"]:
			self.assertIn(stage, opts, f"Stage '{stage}' missing from options")


class TestH1BrandFieldStandardization(IntegrationTestCase):
	"""H1 Fix 6: Reports use 'brand' not 'lavanya_brand'."""

	def test_no_lavanya_brand_in_source(self):
		"""No Python source files should reference lavanya_brand (except tests)."""
		import os
		app_path = frappe.get_app_path("lavanya_service")
		violations = []
		for root, dirs, files in os.walk(app_path):
			for fname in files:
				if not fname.endswith(".py") or "test" in fname.lower():
					continue
				fpath = os.path.join(root, fname)
				with open(fpath, 'r') as f:
					content = f.read()
				if "lavanya_brand" in content:
					violations.append(fpath)
		self.assertEqual(violations, [], f"lavanya_brand still used in: {violations}")
