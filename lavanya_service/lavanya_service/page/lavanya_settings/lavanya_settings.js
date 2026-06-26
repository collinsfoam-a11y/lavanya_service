frappe.pages['lavanya-settings'].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper, title: 'Settings', single_column: true,
	});

	if (!frappe.user.has_role(['Service Manager','Lavanya Owner'])) {
		page.body.html('<div class="lav-no-access"><p>Manager or Owner access required</p></div>');
		return;
	}

	page.set_primary_action(__('Save Settings'), function () {
		if (wrapper.__lav_app) wrapper.__lav_app.saveSettings && wrapper.__lav_app.saveSettings();
	}, 'save');

	page.set_secondary_action(__('Reset to Defaults'), function () {
		frappe.confirm(
			'Reset all settings to safe defaults? This will disable live sending and enable closure guard.',
			function () {
				if (wrapper.__lav_app) wrapper.__lav_app.resetDefaults && wrapper.__lav_app.resetDefaults();
			}
		);
	}, 'restore_page');

	var $root = $('<div id="lav-settings-root" class="lav-page-root"></div>').appendTo(page.body);

	function mount() {
		if (window.LavanyaService) {
			var isOwner = frappe.user.has_role('Lavanya Owner');
			var app = LavanyaService.mountPage('Settings', $root[0], {
				frappePage: page,
				isOwner: isOwner,
			});
			wrapper.__lav_app = app;
		} else {
			setTimeout(mount, 100);
		}
	}
	mount();
};
