frappe.pages['lavanya-new-ticket'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'New Ticket',
		single_column: true,
	});

	page.add_breadcrumb?.('Tickets', function () {
		frappe.set_route('lavanya-tickets');
	}) || page.set_title?.('New Ticket');

	var $root = $('<div id="lav-new-ticket-root" class="lav-page-root"></div>').appendTo(page.body);

	function mount() {
		if (window.LavanyaService) {
			var prefillPhone = frappe.utils.get_url_arg('phone') || '';
			var prefillCustomer = frappe.utils.get_url_arg('customer') || '';
			var app = LavanyaService.mountPage('NewTicket', $root[0], {
				frappePage: page,
				prefillPhone: prefillPhone,
				prefillCustomer: prefillCustomer,
				onSuccess: function (ticketName) {
					frappe.show_alert({ message: __('Ticket {0} created', [ticketName]), indicator: 'green' });
					frappe.set_route('lavanya-ticket-detail', ticketName);
				},
			});
			wrapper.__lav_app = app;
		} else {
			setTimeout(mount, 100);
		}
	}
	mount();
};
