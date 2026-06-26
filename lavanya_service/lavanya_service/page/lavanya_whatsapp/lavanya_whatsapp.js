frappe.pages['lavanya-whatsapp'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'WhatsApp Inbox',
		single_column: true,
	});

	var $banner = $(
		'<div class="lav-dry-run-banner">' +
		'<span>Live WhatsApp sending is <strong>DISABLED</strong>. ' +
		'All drafts require staff review. Bot is in dry-run mode.</span>' +
		'</div>'
	).prependTo(page.body);

	var $root = $('<div id="lav-whatsapp-root" class="lav-page-root"></div>').appendTo(page.body);

	function mount() {
		if (window.LavanyaService) {
			var app = LavanyaService.mountPage('WhatsAppInbox', $root[0], {
				frappePage: page,
				onOpenTicket: function (name) { frappe.set_route('lavanya-ticket-detail', name); },
				onCreateTicket: function () { frappe.set_route('lavanya-new-ticket'); },
			});
			wrapper.__lav_app = app;
		} else {
			setTimeout(mount, 100);
		}
	}
	mount();

	wrapper.__lav_poll = setInterval(function () {
		if (wrapper.__lav_app && wrapper.__lav_app.refresh) wrapper.__lav_app.refresh();
	}, 60000);
};

frappe.pages['lavanya-whatsapp'].on_page_hide = function (wrapper) {
	if (wrapper.__lav_poll) {
		clearInterval(wrapper.__lav_poll);
		wrapper.__lav_poll = null;
	}
};
