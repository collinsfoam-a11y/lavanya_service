app_name = "lavanya_service"
app_title = "Lavanya Service"
app_publisher = "Lavanya eMart"
app_description = "Lavanya eMart Helpdesk customization app"
app_email = "admin@example.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "lavanya_service",
# 		"logo": "/assets/lavanya_service/logo.png",
# 		"title": "Lavanya Service",
# 		"route": "/lavanya_service",
# 		"has_permission": "lavanya_service.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/lavanya_service/css/lavanya_service.css"
# app_include_js = "/assets/lavanya_service/js/lavanya_service.js"

# include js, css files in header of web template
# web_include_css = "/assets/lavanya_service/css/lavanya_service.css"
# web_include_js = "/assets/lavanya_service/js/lavanya_service.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "lavanya_service/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "lavanya_service/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "lavanya_service.utils.jinja_methods",
# 	"filters": "lavanya_service.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "lavanya_service.install.before_install"
# after_install = "lavanya_service.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "lavanya_service.uninstall.before_uninstall"
# after_uninstall = "lavanya_service.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "lavanya_service.utils.before_app_install"
# after_app_install = "lavanya_service.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "lavanya_service.utils.before_app_uninstall"
# after_app_uninstall = "lavanya_service.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "lavanya_service.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"lavanya_service.tasks.all"
# 	],
# 	"daily": [
# 		"lavanya_service.tasks.daily"
# 	],
# 	"hourly": [
# 		"lavanya_service.tasks.hourly"
# 	],
# 	"weekly": [
# 		"lavanya_service.tasks.weekly"
# 	],
# 	"monthly": [
# 		"lavanya_service.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "lavanya_service.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "lavanya_service.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "lavanya_service.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["lavanya_service.utils.before_request"]
# after_request = ["lavanya_service.utils.after_request"]

# Job Events
# ----------
# before_job = ["lavanya_service.utils.before_job"]
# after_job = ["lavanya_service.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"lavanya_service.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


# Lavanya Service fixtures
# Export only explicitly approved metadata/config records.
fixtures = [
	{
		"dt": "DocType",
		"filters": [
			[
				"name",
				"in",
				[
					"Brand Service Master",
					"Service Center Master",
					"Local Technician Master",
					"Free Service Rule",
					"Service Product Receipt",
					"Custody Log Entry",
				],
			],
		],
	},
	{
		"dt": "Custom Field",
		"filters": [
			["dt", "=", "HD Ticket"],
			[
				"fieldname",
				"in",
				[
					"lavanya_customer_section",
					"complaint_source",
					"customer_name",
					"phone_1",
					"phone_2",
					"address",
					"pincode",
					"lavanya_product_section",
					"product_type",
					"product_subtype",
					"brand",
					"model_no",
					"serial_no",
					"lavanya_purchase_section",
					"purchased_from_lavanya",
					"invoice_source",
					"old_erp_reference",
					"purchase_date",
					"warranty_status",
					"lavanya_brand_service_section",
					"manufacturer_registration_required",
					"manufacturer_registered",
					"brand_ticket_number",
					"registration_date",
					"registration_pending_reason",
					"service_center",
					"local_technician",
					"lavanya_followup_section",
					"is_repeated_complaint",
					"previous_ticket_link",
					"pending_reason",
					"next_follow_up_date",
					"closure_type",
					"service_product_receipt",
					"work_narration",
					"customer_confirmation_received",
					"closed_by",
					"closure_date",
				],
			],
		],
	},
	{
		"dt": "HD Ticket Status",
		"filters": [
			[
				"name",
				"in",
				[
					"New",
					"Registration Pending",
					"Brand Registered",
					"In Progress",
					"Waiting on Customer",
					"Waiting on Part / Approval",
					"Ready for Pickup",
					"Resolved",
					"Closed",
					"Cancelled",
				],
			],
		],
	},
	{
		"dt": "HD Ticket Priority",
		"filters": [
			["name", "in", ["Urgent", "High", "Medium", "Low"]],
		],
	},
	{
		"dt": "HD Ticket Type",
		"filters": [
			[
				"name",
				"in",
				[
					"Customer Complaint - Site",
					"Customer Product at Store",
					"Stock Complaint",
					"Installation / Demo",
					"Replacement / DOA",
					"Out of Warranty Local Service",
					"Free Service",
				],
			],
		],
	},
	{
		"dt": "HD Service Level Agreement",
		"filters": [
			["name", "in", ["Lavanya Default", "Default"]],
		],
	},
	{
		"dt": "Brand Service Master",
		"filters": [
			[
				"name",
				"in",
				[
					"LG",
					"Samsung",
					"Whirlpool",
					"Voltas",
					"Preethi",
					"Bajaj",
					"Prestige",
					"Crompton",
					"Kent",
					"Faber",
				],
			],
		],
	},
]


# Lavanya Service validation hooks
doc_events = {
	"HD Ticket": {
		"before_validate": "lavanya_service.validations.hd_ticket.normalize_ticket_phone_numbers",
		"validate": "lavanya_service.validations.hd_ticket.validate_ticket",
	},
	"Service Product Receipt": {
		"validate": "lavanya_service.validations.service_receipt.validate_service_product_receipt",
	},
}


# Lavanya Service ticket template fixtures
fixtures.extend(
	[
		{
			"dt": "HD Ticket Template",
			"filters": [
				["name", "=", "Default"],
			],
		},
		{
			"dt": "HD Ticket Template Field",
			"filters": [
				["parenttype", "=", "HD Ticket Template"],
				["parent", "=", "Default"],
				[
					"fieldname",
					"in",
					[
						"complaint_source",
						"customer_name",
						"phone_1",
						"phone_2",
						"address",
						"pincode",
						"product_type",
						"product_subtype",
						"brand",
						"model_no",
						"serial_no",
						"purchased_from_lavanya",
						"invoice_source",
						"old_erp_reference",
						"purchase_date",
						"warranty_status",
					],
				],
			],
		},
	]
)


# Lavanya Service runtime settings fixtures
fixtures.extend(
	[
		{
			"dt": "HD Settings",
			"filters": [
				["name", "=", "HD Settings"],
			],
		},
	]
)
