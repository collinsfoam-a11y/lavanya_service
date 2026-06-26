frappe.pages['lavanya-customer360'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Customer 360',
		single_column: true,
	});

	var $root = $('<div id="lav-c360-root" class="lav-page-root"></div>').appendTo(page.body);

	function mount() {
		if (window.LavanyaService) {
			var customerId = frappe.utils.get_url_arg('customer') || '';
			var app = LavanyaService.mountPage('Customer360', $root[0], {
				frappePage: page,
				customerId: customerId,
				onOpenTicket: function (ticketName) {
					frappe.set_route('lavanya-ticket-detail', ticketName);
				},
				onNewTicket: function (phone) {
					frappe.set_route('lavanya-new-ticket?phone=' + phone);
				},
			});
			wrapper.__lav_app = app;
		} else {
			setTimeout(mount, 100);
		}
	}
	mount();
};

frappe.pages['lavanya-customer360'].on_page_show = function (wrapper) {
	var customerId = frappe.utils.get_url_arg('customer');
	if (customerId && wrapper.__lav_app) {
		wrapper.__lav_app.loadCustomer && wrapper.__lav_app.loadCustomer(customerId);
	}
};
