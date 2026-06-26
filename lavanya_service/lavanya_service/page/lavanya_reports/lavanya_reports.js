frappe.pages['lavanya-reports'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper, title: 'Reports', single_column: true,
	});

	var reportField = page.add_field({
		label: 'Report', fieldtype: 'Select',
		options: [
			'Open Tickets by Stage', 'Overdue Follow-ups', 'Brand-wise Delay',
			'Technician Performance', 'Customer Not Informed', 'Part Pending Aging',
			'Satisfaction Summary', 'Staff Compliance', 'Repeat Complaints',
			'WhatsApp Coverage', 'Service-to-CRM Opportunities',
		],
		change: function () {
			if (wrapper.__lav_app) wrapper.__lav_app.setReport && wrapper.__lav_app.setReport(this.value);
		},
	});

	var periodField = page.add_field({
		label: 'Period', fieldtype: 'Select',
		options: ['Today', 'This Week', 'This Month', 'Last 3 Months', 'Custom'],
		default: 'This Month',
		change: function () {
			if (wrapper.__lav_app) wrapper.__lav_app.setPeriod && wrapper.__lav_app.setPeriod(this.value);
		},
	});

	page.set_primary_action(__('Export CSV'), function () {
		if (wrapper.__lav_app) wrapper.__lav_app.exportCSV && wrapper.__lav_app.exportCSV();
	}, 'download');

	var $root = $('<div id="lav-reports-root" class="lav-page-root"></div>').appendTo(page.body);

	function mount() {
		if (window.LavanyaService) {
			var app = LavanyaService.mountPage('Reports', $root[0], { frappePage: page });
			wrapper.__lav_app = app;
		} else {
			setTimeout(mount, 100);
		}
	}
	mount();
};
