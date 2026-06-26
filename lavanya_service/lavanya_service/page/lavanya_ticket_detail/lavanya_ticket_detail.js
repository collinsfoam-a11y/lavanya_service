frappe.pages['lavanya-ticket-detail'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Ticket',
		single_column: true,
	});

	page.add_breadcrumb?.('Tickets', function () {
		frappe.set_route('lavanya-tickets');
	}) || page.set_title?.('Ticket');

	page.set_secondary_action(__('Refresh'), function () {
		if (wrapper.__lav_app && wrapper.__lav_app.refresh) wrapper.__lav_app.refresh();
	}, 'refresh');

	var $root = $('<div id="lav-ticket-detail-root" class="lav-page-root"></div>').appendTo(page.body);

	function mount() {
		if (window.LavanyaService) {
			var ticketId = frappe.utils.get_url_arg('name') || frappe.get_route()[1];
			var app = LavanyaService.mountPage('TicketDetail', $root[0], {
				frappePage: page,
				ticketId: ticketId,
			});
			wrapper.__lav_app = app;
			if (ticketId) page.set_title('#' + ticketId);
		} else {
			setTimeout(mount, 100);
		}
	}
	mount();
};

frappe.pages['lavanya-ticket-detail'].on_page_show = function (wrapper) {
	var ticketId = frappe.utils.get_url_arg('name') || frappe.get_route()[1];
	if (wrapper.__lav_app) {
		wrapper.__lav_app.setTicket && wrapper.__lav_app.setTicket(ticketId);
	}
};
