frappe.pages['lavanya-service-centers'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Service Centers & Brands',
		single_column: true,
	});

	var tabField = page.add_field({
		label: 'View',
		fieldtype: 'Select',
		options: ['Brands', 'Service Centers', 'Technicians'],
		change: function () {
			if (wrapper.__lav_app) wrapper.__lav_app.setTab && wrapper.__lav_app.setTab(this.value);
		},
	});

	page.set_primary_action(__('Add New'), function () {
		if (wrapper.__lav_app) wrapper.__lav_app.openAddModal && wrapper.__lav_app.openAddModal();
	}, 'add');

	var $root = $('<div id="lav-sc-root" class="lav-page-root"></div>').appendTo(page.body);

	function mount() {
		if (window.LavanyaService) {
			var app = LavanyaService.mountPage('ServiceCenters', $root[0], { frappePage: page });
			wrapper.__lav_app = app;
		} else {
			setTimeout(mount, 100);
		}
	}
	mount();
};
