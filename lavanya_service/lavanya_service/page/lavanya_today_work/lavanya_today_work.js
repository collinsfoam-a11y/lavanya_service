/**
 * Lavanya Today's Work — Service Coordinator workspace.
 *
 * Read-only rendering of lavanya_service.api.today_work.get_today_work.
 * The backend is the single source of truth for role-aware grouping and
 * priority ordering; this page only displays what the API returns.
 *
 * Visual language follows the Stitch "Lavanya Service Framework" reference
 * (docs/ui_references/.../lavanya_service_framework/DESIGN.md): Lavanya Purple
 * primary, Inter type scale, base-8 spacing, work-priority cards (big count +
 * colored accent), collapsible panels with a chevron, and pill status chips.
 * Styles are scoped to `.lv-tw` so nothing leaks into the Desk shell.
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

	// Per-bucket accent colour (Stitch palette) used for the card left-accent
	// and the count badge. Keys match the API group keys.
	const GROUP_ACCENT = {
		overdue_follow_up: "#ba1a1a",
		due_today: "#b86e00",
		registration_recommended: "#5412dd",
		registration_pending: "#6d3df5",
		waiting_on_customer: "#2f6fed",
		waiting_on_part: "#a84900",
		ready_for_pickup: "#1a7f37",
		product_receipt_missing: "#823700",
		closure_pending: "#545f73",
		new_complaints: "#5412dd",
	};

	// Status chip colours: full-saturation text on a 12% tint of the same hue.
	const STATUS_HUE = {
		"New": "#2f6fed",
		"Registration Pending": "#6d3df5",
		"Brand Registered": "#0e7490",
		"In Progress": "#5412dd",
		"Waiting on Customer": "#b86e00",
		"Waiting on Part / Approval": "#a84900",
		"Ready for Pickup": "#1a7f37",
		"Resolved": "#1a7f37",
		"Closed": "#545f73",
		"Cancelled": "#ba1a1a",
	};

	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function tint(hex, alpha) {
		const h = hex.replace("#", "");
		const r = parseInt(h.slice(0, 2), 16);
		const g = parseInt(h.slice(2, 4), 16);
		const b = parseInt(h.slice(4, 6), 16);
		return `rgba(${r}, ${g}, ${b}, ${alpha})`;
	}

	function styleBlock() {
		return `<style>
		.lv-tw { font-family: Inter, var(--font-stack, -apple-system, sans-serif); padding: 8px 0 24px; color: #1c1a24; }
		.lv-tw a { color: #5412dd; }
		.lv-tw .lv-summary { display: flex; gap: 16px; flex-wrap: wrap; align-items: stretch; margin-bottom: 24px; }
		.lv-tw .lv-metric { flex: 1 1 150px; min-width: 140px; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
		.lv-tw .lv-metric.lv-accent { border: 2px solid #5412dd; background: #f7f1ff; }
		.lv-tw .lv-metric .lv-num { font-size: 28px; line-height: 34px; font-weight: 700; letter-spacing: -0.02em; }
		.lv-tw .lv-metric .lv-cap { font-size: 12px; line-height: 16px; color: #494456; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.04em; }
		.lv-tw .lv-date { margin-left: auto; align-self: center; font-size: 12px; color: #7a7487; }
		.lv-tw .lv-card { background: #fff; border: 1px solid #e2e8f0; border-left-width: 4px; border-radius: 8px; margin-bottom: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
		.lv-tw .lv-head { display: flex; align-items: center; gap: 12px; padding: 12px 16px; cursor: pointer; user-select: none; }
		.lv-tw .lv-head:hover { background: #f7f1ff; }
		.lv-tw .lv-badge { min-width: 34px; height: 34px; padding: 0 8px; border-radius: 9999px; display: inline-flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 700; color: #fff; }
		.lv-tw .lv-label { font-size: 18px; line-height: 24px; font-weight: 600; }
		.lv-tw .lv-chev { margin-left: auto; transition: transform 0.2s; color: #7a7487; font-size: 18px; }
		.lv-tw .lv-card.lv-open .lv-chev { transform: rotate(90deg); }
		.lv-tw .lv-rows { display: none; border-top: 1px solid #ece6f4; }
		.lv-tw .lv-card.lv-open .lv-rows { display: block; }
		.lv-tw .lv-row { display: flex; gap: 12px; align-items: center; padding: 10px 16px; border-bottom: 1px solid #f2ebfa; flex-wrap: wrap; }
		.lv-tw .lv-row:last-child { border-bottom: 0; }
		.lv-tw .lv-row .lv-main { flex: 2 1 220px; min-width: 200px; }
		.lv-tw .lv-row .lv-sub { font-size: 12px; color: #494456; margin-top: 2px; }
		.lv-tw .lv-chip { display: inline-block; padding: 2px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; }
		.lv-tw .lv-reason { flex: 1 1 150px; min-width: 130px; font-size: 12px; color: #494456; }
		.lv-tw .lv-fu { flex: 0 0 auto; font-size: 12px; }
		.lv-tw .lv-empty { padding: 10px 16px; font-size: 13px; color: #7a7487; }
		.lv-tw .btn-lv { font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 4px; border: 1px solid #e2e8f0; background: #fff; color: #5412dd; text-decoration: none; }
		.lv-tw .btn-lv:hover { background: #f7f1ff; }
		.lv-tw .lv-allclear { padding: 40px; text-align: center; }
		.lv-tw .lv-allclear .em { font-size: 32px; }
		</style>`;
	}

	function load() {
		$body.html(
			`<div class="lv-tw"><div class="lv-empty" style="padding: 32px;">${__(
				"Loading Today's Work…"
			)}</div></div>`
		);

		frappe.call({
			method: "lavanya_service.api.today_work.get_today_work",
			args: { include_counts: 1 },
			callback: (r) => render(r.message || {}),
			error: () => {
				$body.html(
					`<div class="lv-tw"><div style="padding: 32px; color: #ba1a1a;">${__(
						"Could not load Today's Work. Check permissions or contact the manager."
					)}</div></div>`
				);
			},
		});
	}

	function render(data) {
		const groups = data.groups || [];
		const summary = data.summary || {};
		const parts = [styleBlock(), renderSummary(summary, data.date)];

		if (!groups.length) {
			parts.push(
				`<div class="lv-empty" style="text-align: center; padding: 32px;">${__(
					"No work groups are visible for your role."
				)}</div>`
			);
		} else if ((summary.total || 0) === 0) {
			parts.push(
				`<div class="lv-allclear"><div class="em">&#127881;</div>
				<div class="lv-empty">${__("All clear — no pending work right now.")}</div></div>`
			);
		}

		for (const group of groups) {
			parts.push(renderGroup(group));
		}

		$body.html(`<div class="lv-tw">${parts.join("")}</div>`);

		// Collapsible behaviour (DESIGN.md: chevron on collapsible panels).
		$body.find(".lv-head").on("click", function () {
			$(this).closest(".lv-card").toggleClass("lv-open");
		});
	}

	function renderSummary(summary, date) {
		const metric = (label, value, accent) =>
			`<div class="lv-metric${accent ? " lv-accent" : ""}">
				<div class="lv-num" style="${accent ? "color:#5412dd;" : ""}">${esc(value || 0)}</div>
				<div class="lv-cap">${esc(label)}</div>
			</div>`;

		return `<div class="lv-summary">
			${metric(__("Total Pending"), summary.total, true)}
			${metric(__("Overdue"), summary.overdue, false)}
			${metric(__("Due Today"), summary.due_today, false)}
			<div class="lv-date">${esc(date || "")}</div>
		</div>`;
	}

	function renderGroup(group) {
		const accent = GROUP_ACCENT[group.key] || "#5412dd";
		const count = group.count != null ? group.count : (group.tickets || []).length;
		const rows = (group.tickets || []).map(renderRow).join("");
		const body = rows
			? rows
			: `<div class="lv-empty">${__("Nothing here.")}</div>`;
		const open = count > 0 ? " lv-open" : "";
		const badgeColor = count > 0 ? accent : "#cac3d9";

		return `<div class="lv-card${open}" style="border-left-color: ${accent};">
			<div class="lv-head">
				<span class="lv-badge" style="background: ${badgeColor};">${count}</span>
				<span class="lv-label">${esc(group.label)}</span>
				<span class="lv-chev">&#9656;</span>
			</div>
			<div class="lv-rows">${body}</div>
		</div>`;
	}

	function renderRow(ticket) {
		const hue = STATUS_HUE[ticket.status] || "#545f73";
		const followUp = formatFollowUp(ticket.next_follow_up_date);
		const product = [ticket.brand, ticket.product_item || ticket.product_type]
			.filter(Boolean)
			.join(" / ");
		const helpdeskUrl = `/helpdesk/tickets/${encodeURIComponent(ticket.name)}`;
		const deskUrl = `/app/hd-ticket/${encodeURIComponent(ticket.name)}`;

		return `<div class="lv-row">
			<div class="lv-main">
				<a href="${helpdeskUrl}" target="_blank" rel="noopener" style="font-weight: 500;">
					${esc(ticket.name)} &middot; ${esc(ticket.subject || __("(no subject)"))}
				</a>
				<div class="lv-sub">
					${esc(ticket.customer_name || "")}${ticket.phone_1 ? " &middot; " + esc(ticket.phone_1) : ""}
					${product ? " &middot; " + esc(product) : ""}
				</div>
			</div>
			<span class="lv-chip" style="color: ${hue}; background: ${tint(hue, 0.12)};">${esc(
			ticket.status || ""
		)}</span>
			<div class="lv-reason">${esc(ticket.pending_reason || "")}</div>
			<div class="lv-fu" style="${followUp.style}">${followUp.text}</div>
			<div style="flex: 0 0 auto;">
				<a class="btn-lv" href="${helpdeskUrl}" target="_blank" rel="noopener">${__("Open Ticket")}</a>
				<a class="btn-lv" href="${deskUrl}" target="_blank" rel="noopener" title="${__("Open in Desk")}">&#9881;</a>
			</div>
		</div>`;
	}

	function formatFollowUp(value) {
		if (!value) {
			return { text: `<span style="color:#7a7487;">${__("No follow-up date")}</span>`, style: "" };
		}

		const date = frappe.datetime.str_to_obj(String(value).slice(0, 10));
		const todayObj = frappe.datetime.str_to_obj(frappe.datetime.get_today());
		const display = esc(frappe.datetime.str_to_user(String(value).slice(0, 10)));

		if (date < todayObj) {
			return { text: `${__("Overdue")}: ${display}`, style: "color: #ba1a1a; font-weight: 600;" };
		}
		if (date.getTime() === todayObj.getTime()) {
			return { text: `${__("Due today")}: ${display}`, style: "color: #b86e00; font-weight: 600;" };
		}
		return { text: display, style: "" };
	}

	load();
};
