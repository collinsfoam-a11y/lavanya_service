frappe.pages['lavanya-today'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Today's Work",
		single_column: true,
	});

	page.set_secondary_action(__('Refresh'), function () {
		if (wrapper.__lav_app && wrapper.__lav_app.refresh) {
			wrapper.__lav_app.refresh();
		}
	}, 'refresh');

	var $root = $('<div id="lav-today-root" class="lav-page-root"></div>').appendTo(page.body);

	function mount() {
		if (window.LavanyaService) {
			wrapper.__lav_app = LavanyaService.mountPage('TodaysWork', $root[0], {
				frappePage: page,
			});
		} else {
			setTimeout(mount, 100);
		}
	}
	mount();
};

frappe.pages['lavanya-today'].on_page_show = function (wrapper) {
	if (wrapper.__lav_app && wrapper.__lav_app.refresh) {
		wrapper.__lav_app.refresh();
	}
};
