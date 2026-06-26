frappe.pages['lavanya-manager'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Manager Dashboard',
		single_column: true,
	});

	if (!frappe.user.has_role(['Service Manager', 'Lavanya Owner'])) {
		page.body.html('<div class="lav-no-access"><p>Manager access required</p></div>');
		return;
	}

	var periodField = page.add_field({
		label: 'Period',
		fieldtype: 'Select',
		options: ['Today', 'This Week', 'This Month'],
		default: 'Today',
		change: function () {
			if (wrapper.__lav_app) wrapper.__lav_app.setPeriod && wrapper.__lav_app.setPeriod(this.value);
		},
	});

	page.set_secondary_action(__('Export'), function () {
		frappe.call({
			method: 'lavanya_service.api.dashboard.export_report',
			callback: function (r) {
				if (r.message) window.open(r.message);
			},
		});
	}, 'download');

	var $root = $('<div id="lav-manager-root" class="lav-page-root"></div>').appendTo(page.body);

	function mount() {
		if (window.LavanyaService) {
			var app = LavanyaService.mountPage('ManagerDashboard', $root[0], { frappePage: page });
			wrapper.__lav_app = app;
		} else {
			setTimeout(mount, 100);
		}
	}
	mount();
};
