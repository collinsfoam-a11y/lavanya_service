/**
 * Lavanya Today's Work — Service Coordinator workspace (Phase 1N-7).
 *
 * Read-only rendering of lavanya_service.api.today_work.get_today_work.
 * The backend is the single source of truth for role-aware grouping and
 * priority ordering; this page only displays what the API returns.
 *
 * Inline quick action buttons are deferred; the existing HD Ticket quick
 * action buttons (HD Form Script) remain the action surface.
 */

frappe.pages["lavanya-today-work"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Lavanya Today's Work"),
		single_column: true,
	});

	const $body = $(wrapper).find(".layout-main-section");

	page.set_secondary_action(__("Refresh"), () => load(), "refresh");

	const STATUS_COLORS = {
		"New": "blue",
		"Registration Pending": "orange",
		"Brand Registered": "cyan",
		"In Progress": "purple",
		"Waiting on Customer": "yellow",
		"Waiting on Part / Approval": "orange",
		"Ready for Pickup": "green",
		"Resolved": "green",
		"Closed": "gray",
		"Cancelled": "red",
	};

	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function load() {
		$body.html(
			`<div class="text-muted" style="padding: 2rem;">${__("Loading Today's Work...")}</div>`
		);

		frappe.call({
			method: "lavanya_service.api.today_work.get_today_work",
			args: { include_counts: 1 },
			callback: (r) => render(r.message || {}),
			error: () => {
				$body.html(
					`<div class="text-danger" style="padding: 2rem;">${__(
						"Could not load Today's Work. Check permissions or contact the manager."
					)}</div>`
				);
			},
		});
	}

	function render(data) {
		const groups = data.groups || [];
		const summary = data.summary || {};
		const parts = [];

		parts.push(renderSummary(summary, data.date));

		if (!groups.length) {
			parts.push(
				`<div class="text-muted" style="padding: 2rem; text-align: center;">${__(
					"No work groups are visible for your role."
				)}</div>`
			);
		} else if ((summary.total || 0) === 0) {
			parts.push(
				`<div style="padding: 2.5rem; text-align: center;">
					<div style="font-size: 2rem;">&#127881;</div>
					<div class="text-muted">${__("All clear — no pending work right now.")}</div>
				</div>`
			);
		}

		for (const group of groups) {
			parts.push(renderGroup(group));
		}

		$body.html(`<div class="lavanya-today-work" style="padding: 0.5rem 0;">${parts.join("")}</div>`);
	}

	function renderSummary(summary, date) {
		const chip = (label, value, color) =>
			`<div style="border: 1px solid var(--border-color); border-radius: 8px; padding: 0.5rem 1rem; min-width: 110px; text-align: center;">
				<div style="font-size: 1.4rem; font-weight: 600; color: ${color};">${esc(value || 0)}</div>
				<div class="text-muted" style="font-size: 0.75rem;">${esc(label)}</div>
			</div>`;

		return `<div style="display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: center; margin-bottom: 1rem;">
			${chip(__("Total Pending"), summary.total, "var(--text-color)")}
			${chip(__("Overdue"), summary.overdue, "var(--red-500, #e03636)")}
			${chip(__("Due Today"), summary.due_today, "var(--orange-500, #e07b00)")}
			<div class="text-muted" style="margin-left: auto; font-size: 0.75rem;">${esc(date || "")}</div>
		</div>`;
	}

	function renderGroup(group) {
		const count = group.count != null ? group.count : (group.tickets || []).length;
		const rows = (group.tickets || []).map(renderRow).join("");
		const body = rows
			? `<div>${rows}</div>`
			: `<div class="text-muted" style="padding: 0.5rem 0.75rem; font-size: 0.8rem;">${__("Nothing here.")}</div>`;

		return `<div style="border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 0.75rem; overflow: hidden;">
			<div style="display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; background: var(--subtle-fg, var(--gray-50)); border-bottom: 1px solid var(--border-color);">
				<span style="font-weight: 600;">${esc(group.label)}</span>
				<span class="indicator-pill ${count ? "blue" : "gray"}" style="margin-left: auto;">${count}</span>
			</div>
			${body}
		</div>`;
	}

	function renderRow(ticket) {
		const statusColor = STATUS_COLORS[ticket.status] || "gray";
		const followUp = formatFollowUp(ticket.next_follow_up_date);
		const product = [ticket.brand, ticket.product_item || ticket.product_type]
			.filter(Boolean)
			.join(" / ");
		const helpdeskUrl = `/helpdesk/tickets/${encodeURIComponent(ticket.name)}`;
		const deskUrl = `/app/hd-ticket/${encodeURIComponent(ticket.name)}`;

		return `<div style="display: flex; gap: 0.75rem; align-items: center; padding: 0.5rem 0.75rem; border-bottom: 1px solid var(--border-color); flex-wrap: wrap;">
			<div style="flex: 2 1 220px; min-width: 200px;">
				<a href="${helpdeskUrl}" target="_blank" rel="noopener" style="font-weight: 500;">
					${esc(ticket.name)} &middot; ${esc(ticket.subject || __("(no subject)"))}
				</a>
				<div class="text-muted" style="font-size: 0.75rem;">
					${esc(ticket.customer_name || "")}${ticket.phone_1 ? " &middot; " + esc(ticket.phone_1) : ""}
					${product ? " &middot; " + esc(product) : ""}
				</div>
			</div>
			<div style="flex: 0 0 auto;">
				<span class="indicator-pill ${statusColor}">${esc(ticket.status || "")}</span>
			</div>
			<div style="flex: 1 1 160px; min-width: 140px; font-size: 0.75rem;" class="text-muted">
				${esc(ticket.pending_reason || "")}
			</div>
			<div style="flex: 0 0 auto; font-size: 0.75rem; ${followUp.style}">${followUp.text}</div>
			<div style="flex: 0 0 auto;">
				<a class="btn btn-xs btn-default" href="${helpdeskUrl}" target="_blank" rel="noopener">${__("Open Ticket")}</a>
				<a class="btn btn-xs btn-default" href="${deskUrl}" target="_blank" rel="noopener" title="${__("Open in Desk")}">&#9881;</a>
			</div>
		</div>`;
	}

	function formatFollowUp(value) {
		if (!value) {
			return { text: `<span class="text-muted">${__("No follow-up date")}</span>`, style: "" };
		}

		const date = frappe.datetime.str_to_obj(String(value).slice(0, 10));
		const todayObj = frappe.datetime.str_to_obj(frappe.datetime.get_today());
		const display = esc(frappe.datetime.str_to_user(String(value).slice(0, 10)));

		if (date < todayObj) {
			return { text: `${__("Overdue")}: ${display}`, style: "color: var(--red-500, #e03636); font-weight: 600;" };
		}
		if (date.getTime() === todayObj.getTime()) {
			return { text: `${__("Due today")}: ${display}`, style: "color: var(--orange-500, #e07b00); font-weight: 600;" };
		}
		return { text: display, style: "" };
	}

	load();
};
