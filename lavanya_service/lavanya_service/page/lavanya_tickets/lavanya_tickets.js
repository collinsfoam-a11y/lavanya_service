frappe.pages['lavanya-tickets'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Tickets',
		single_column: true,
	});

	var statusFilter = page.add_field({
		label: 'Status',
		fieldtype: 'Select',
		options: ['', 'New', 'Registered', 'In Follow-up', 'Waiting',
		          'Resolved by Brand', 'Customer Confirmation Pending', 'Closed', 'Reopened'],
		change: function () {
			if (wrapper.__lav_app) wrapper.__lav_app.setFilter('status', this.value);
		},
	});

	page.set_primary_action(__('New Ticket'), function () {
		frappe.set_route('lavanya-new-ticket');
	}, 'add');

	var $root = $('<div id="lav-tickets-root" class="lav-page-root"></div>').appendTo(page.body);

	function mount() {
		if (window.LavanyaService) {
			wrapper.__lav_app = LavanyaService.mountPage('Tickets', $root[0], { frappePage: page });
		} else {
			setTimeout(mount, 100);
		}
	}
	mount();
};

frappe.pages['lavanya-tickets'].on_page_show = function (wrapper) {
	if (wrapper.__lav_app && wrapper.__lav_app.refresh) wrapper.__lav_app.refresh();
};
