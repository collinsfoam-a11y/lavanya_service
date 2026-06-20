<template>
  <Transition name="drawer">
    <div v-if="ticketId" class="fixed inset-0 z-50 flex justify-end bg-on-surface/20" @click.self="close">
      <div class="w-full max-w-4xl bg-surface-container-lowest h-full shadow-xl flex flex-col md:flex-row overflow-hidden drawer__panel">
      
      <!-- Main Detail Area -->
      <div class="flex-1 overflow-y-auto border-r border-outline-variant flex flex-col">
        <div v-if="loading" class="p-8 text-center text-on-surface-variant">Loading ticket...</div>
        <div v-else-if="error" class="p-8 text-center text-error">Failed to load ticket.</div>
        <div v-else-if="ticket" class="p-6 md:p-8 flex flex-col gap-8">
          
          <!-- Header -->
          <header class="flex flex-col gap-2 border-b border-outline-variant pb-4">
            <div class="flex items-start justify-between">
              <div>
                <h2 class="font-headline-lg text-headline-lg text-on-surface">{{ ticket.name }}</h2>
                <div class="flex flex-wrap gap-2 mt-2">
                  <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="chip(ticket.status)">{{ ticket.status }}</span>
                  <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md bg-surface-variant text-on-surface-variant">{{ ticket.priority }}</span>
                  <SlaBadge :agreement-status="ticket.sla?.agreement_status" :response-by="ticket.sla?.response_by" :resolution-by="ticket.sla?.resolution_by" />
                </div>
              </div>
              <button @click="close" class="p-2 rounded hover:bg-surface-container-low">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>
            <div class="mt-4 font-body-md text-on-surface-variant grid grid-cols-2 gap-y-2">
              <div>Customer: <span class="font-bold text-on-surface">{{ ticket.customer?.name || '—' }}</span></div>
              <div>Mobile: <span class="text-on-surface">{{ ticket.customer?.mobile || '—' }}</span></div>
              <div>Age: <span class="text-on-surface">{{ ticketAge(ticket.creation) }} days</span></div>
              <div>Assigned: <span class="text-on-surface">{{ ticket.assigned_to || 'Unassigned' }}</span></div>
            </div>
            <div class="mt-3 flex items-center gap-3 flex-wrap">
              <button
                v-if="ticket.customer?.mobile"
                @click="whatsappCustomer"
                class="inline-flex items-center gap-1.5 px-3 h-9 rounded-lg font-label-md text-body-md text-on-primary"
                style="background:#25D366"
              >
                <span class="material-symbols-outlined" style="font-size:18px">chat</span> Message on WhatsApp
              </button>
              <a :href="'/helpdesk/tickets/' + ticket.name" target="_blank" class="text-primary hover:underline font-label-md">
                Open in Standard Helpdesk ↗
              </a>
            </div>
          </header>

          <!-- Sticky section nav -->
          <nav class="sticky top-0 z-10 -mx-6 md:-mx-8 px-6 md:px-8 py-2 bg-surface-container-lowest/95 backdrop-blur flex gap-4 border-b border-outline-variant overflow-x-auto">
            <a v-for="s in SECTIONS" :key="s.id" :href="'#' + s.id" class="whitespace-nowrap font-label-md text-label-md text-on-surface-variant hover:text-primary transition-colors" @click.prevent="scrollToSection(s.id)">{{ s.label }}</a>
          </nav>

          <!-- Repeat complaint banner -->
          <div v-if="ticket.repeat?.is_repeat" class="rounded-xl p-4 flex items-center justify-between gap-3"
               style="border:1px solid rgba(113,42,226,0.4); background:rgba(113,42,226,0.08)">
            <div class="flex items-center gap-2 font-body-md text-on-surface">
              <span class="material-symbols-outlined text-secondary">repeat</span>
              Marked as repeat complaint<template v-if="ticket.repeat.previous_ticket"> · linked to <span class="font-semibold text-primary">{{ ticket.repeat.previous_ticket }}</span></template>
            </div>
            <button @click="clearRepeat" class="px-3 h-8 rounded-lg border border-outline-variant text-on-surface-variant font-label-md text-label-md hover:bg-surface-container-low shrink-0">Clear</button>
          </div>
          <div v-else-if="repeatCandidates.length" class="rounded-xl p-4"
               style="border:1px solid rgba(148,55,0,0.4); background:rgba(148,55,0,0.07)">
            <div class="flex items-center gap-2 font-body-md text-on-surface mb-2">
              <span class="material-symbols-outlined text-tertiary">repeat</span>
              Possible repeat — {{ repeatCandidates.length }} earlier ticket(s) for this customer/product
            </div>
            <ul class="flex flex-col gap-1.5">
              <li v-for="c in repeatCandidates" :key="c.ticket" class="flex items-center justify-between gap-2 font-body-md">
                <span class="text-on-surface-variant truncate"><span class="text-primary font-semibold">{{ c.ticket }}</span> · {{ c.subject || '(no subject)' }}</span>
                <button @click="linkRepeat(c.ticket)" class="px-3 h-8 rounded-lg bg-secondary text-on-secondary font-label-md text-label-md shrink-0 hover:opacity-90">Link as repeat</button>
              </li>
            </ul>
          </div>

          <!-- Service Stage (delta Sprint 2) — read display, blank-safe -->
          <section id="sec-stage" v-if="ticket.stage">
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Service Stage</h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div><span class="block text-label-md text-outline">Flow</span> {{ ticket.stage.service_flow_type || '—' }}</div>
              <div><span class="block text-label-md text-outline">Stage</span> {{ ticket.stage.current_service_stage || '—' }}</div>
              <div><span class="block text-label-md text-outline">Next Action</span> {{ ticket.stage.next_action || '—' }}</div>
              <div><span class="block text-label-md text-outline">Owner</span> {{ ticket.stage.next_action_owner || ticket.stage.next_action_role || '—' }}</div>
              <div><span class="block text-label-md text-outline">Next Follow-up</span> {{ ticket.stage.next_follow_up_date || '—' }}</div>
              <div><span class="block text-label-md text-outline">Stage Due</span> {{ ticket.stage.stage_due_at?.substring(0,16) || '—' }}</div>
              <div>
                <span class="block text-label-md text-outline">Due Status</span>
                <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="dueChip(ticket.stage.overdue_status)">{{ ticket.stage.overdue_status || '—' }}</span>
              </div>
              <div><span class="block text-label-md text-outline">Escalation</span> {{ ticket.stage.escalation_level && ticket.stage.escalation_level !== 'None' ? ticket.stage.escalation_level : '—' }}</div>
              <div><span class="block text-label-md text-outline">Customer Informed</span> {{ ticket.stage.customer_informed || '—' }}</div>
              <div><span class="block text-label-md text-outline">Promised Update</span> {{ ticket.stage.customer_promised_update_at?.substring(0,16) || '—' }}</div>
              <div>
                <span class="block text-label-md text-outline">Promise</span>
                <span v-if="ticket.stage.customer_promise_status && ticket.stage.customer_promise_status !== 'None'" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="promiseChip(ticket.stage.customer_promise_status)">{{ ticket.stage.customer_promise_status }}</span>
                <template v-else>—</template>
              </div>
            </div>
          </section>

          <!-- Reminder Intelligence (Step 5) — read-only, blank-safe -->
          <section id="sec-reminder" v-if="ticket.reminder && Object.keys(ticket.reminder).length">
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Reminder Intelligence</h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div>
                <span class="block text-label-md text-outline">Due Status</span>
                <span v-if="ticket.reminder.overdue_status" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="dueChip(ticket.reminder.overdue_status)">{{ ticket.reminder.overdue_status }}</span>
                <template v-else>—</template>
              </div>
              <div>
                <span class="block text-label-md text-outline">Escalation</span>
                <span v-if="reminderEsc !== 'None'" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="escChip(reminderEsc)">{{ reminderEsc }}</span>
                <template v-else>—</template>
              </div>
              <div>
                <span class="block text-label-md text-outline">Customer Promise</span>
                <span v-if="ticket.reminder.customer_promise_status && ticket.reminder.customer_promise_status !== 'None'" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="promiseChip(ticket.reminder.customer_promise_status)">{{ ticket.reminder.customer_promise_status }}</span>
                <template v-else>—</template>
              </div>
              <div>
                <span class="block text-label-md text-outline">Customer Update Due</span>
                <span v-if="ticket.reminder.customer_update_due" class="px-2 py-0.5 rounded-full font-label-md text-label-md" style="color:#943700;background:rgba(148,55,0,0.12)">Due now</span>
                <template v-else>No</template>
              </div>
              <div><span class="block text-label-md text-outline">Reminder Rule</span> {{ ticket.reminder.reminder_rule_applied || 'No rule (fallback)' }}</div>
              <div>
                <span class="block text-label-md text-outline">Next Follow-up</span>
                {{ fmtDT(ticket.reminder.next_follow_up_date) }}
                <span v-if="ticket.reminder.manual_followup" class="ml-1 px-1.5 py-0.5 rounded font-label-md text-label-md" style="color:#0053db;background:rgba(0,83,219,0.12)">manual</span>
              </div>
              <div><span class="block text-label-md text-outline">Due Soon At</span> {{ fmtDT(ticket.reminder.computed_due_soon_at) }}</div>
              <div><span class="block text-label-md text-outline">Stage Due At</span> {{ fmtDT(ticket.reminder.computed_stage_due_at) }}</div>
              <div v-if="reminderShowComputed"><span class="block text-label-md text-outline">Computed Follow-up</span> {{ fmtDT(ticket.reminder.computed_next_followup_at) }}</div>
              <div><span class="block text-label-md text-outline">Promised Update At</span> {{ fmtDT(ticket.reminder.customer_promised_update_at) }}</div>
              <div v-if="ticket.reminder.promise_breach_reason" class="col-span-2">
                <span class="block text-label-md text-outline">Promise Breach Reason</span>
                <span style="color:#ba1a1a">{{ ticket.reminder.promise_breach_reason }}</span>
              </div>
            </div>
          </section>

          <!-- AI Advisory (Step 6) — read-only suggestions from the engine -->
          <section id="sec-ai-advisory" v-if="ticket.ai && ticket.ai.review_status && ticket.ai.review_status !== 'Not Required'">
            <h3 class="font-headline-md text-headline-md text-primary mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined" style="font-size:22px">psychology</span>
              AI Advisory
            </h3>
            <div class="bg-surface-container p-4 rounded-xl space-y-3">
              <div class="flex items-center gap-2">
                <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="aiStatusChip(ticket.ai.review_status)">{{ ticket.ai.review_status }}</span>
                <span v-if="ticket.ai.advisory_source" class="font-label-md text-outline">{{ ticket.ai.advisory_source }}</span>
              </div>
              <div v-if="ticket.ai.suggested_next_action">
                <span class="block text-label-md text-outline">Suggested Next Action</span>
                <p class="font-body-md text-on-surface mt-0.5">{{ ticket.ai.suggested_next_action }}</p>
              </div>
              <div v-if="ticket.ai.risk_reason">
                <span class="block text-label-md text-outline">Risk Reason</span>
                <p class="font-body-md text-on-surface mt-0.5" style="color:#ba1a1a">{{ ticket.ai.risk_reason }}</p>
              </div>
              <div v-if="ticket.ai.manager_summary">
                <span class="block text-label-md text-outline">Manager Summary</span>
                <p class="font-body-md text-on-surface mt-0.5">{{ ticket.ai.manager_summary }}</p>
              </div>
              <div v-if="ticket.ai.suggested_customer_message" class="bg-surface-container-highest p-3 rounded-lg">
                <span class="block text-label-md text-outline mb-1">Suggested Customer Message</span>
                <p class="font-body-md text-on-surface italic">{{ ticket.ai.suggested_customer_message }}</p>
              </div>
              <div v-if="ticket.ai.review_status === 'Suggested'" class="flex gap-2 pt-2">
                <button @click="acceptAiSuggestion" :disabled="aiBusy"
                  class="px-4 py-2 rounded-lg font-label-md flex items-center gap-1.5 bg-tertiary text-on-tertiary transition-all hover:opacity-90 active:scale-[0.97] disabled:opacity-50">
                  <span class="material-symbols-outlined" style="font-size:16px">check</span> Accept
                </button>
                <button @click="ignoreAiSuggestion" :disabled="aiBusy"
                  class="px-4 py-2 rounded-lg font-label-md flex items-center gap-1.5 bg-error-container text-error transition-all hover:opacity-90 active:scale-[0.97] disabled:opacity-50">
                  <span class="material-symbols-outlined" style="font-size:16px">close</span> Ignore
                </button>
              </div>
              <div v-if="ticket.ai.reviewed_by && ticket.ai.last_reviewed_at" class="text-label-md text-outline pt-2 mt-1 border-t border-outline-variant flex gap-4">
                <span>Reviewed by: {{ ticket.ai.reviewed_by }}</span>
                <span>At: {{ fmtDT(ticket.ai.last_reviewed_at) }}</span>
              </div>
            </div>
          </section>

          <!-- Follow-up Tracking (Phase 1N-6B) -->
          <section id="sec-followup-tracking" v-if="ticket.stage && (ticket.stage.service_path || ticket.stage.followup_stage || ticket.stage.service_charge_type)">
            <h3 class="font-headline-md text-headline-md text-primary mb-4 flex items-center gap-2">
              <span class="material-symbols-outlined" style="font-size:22px">support_agent</span>
              Follow-up Tracking
            </h3>

            <!-- Status Banner -->
            <div class="rounded-xl p-4 mb-4 flex items-center gap-3 transition-all" :style="{ background: followupBanner.bg, color: followupBanner.fg, borderLeft: '4px solid ' + followupBanner.fg }">
              <span class="material-symbols-outlined" style="font-size:28px">{{ followupBanner.icon }}</span>
              <div>
                <div class="font-label-lg text-label-lg font-semibold">{{ followupBanner.title }}</div>
                <div class="font-body-md text-body-md" style="opacity:0.8">{{ followupBanner.sub }}</div>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Service Info -->
              <div class="rounded-xl p-4 bg-surface-container">
                <div class="font-label-md text-label-md text-outline mb-3 flex items-center gap-1.5">
                  <span class="material-symbols-outlined" style="font-size:16px">route</span>
                  Service Path
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <span v-if="ticket.stage.service_path" class="px-2.5 py-1 rounded-full font-label-md text-label-md" :style="stageChip(ticket.stage.service_path)">{{ ticket.stage.service_path }}</span>
                  <span v-if="ticket.stage.service_path && ticket.stage.followup_stage" class="text-outline font-label-md">→</span>
                  <span v-if="ticket.stage.followup_stage" class="px-2.5 py-1 rounded-full font-label-md text-label-md" :style="stageChip(ticket.stage.followup_stage)">{{ ticket.stage.followup_stage }}</span>
                  <span v-if="!ticket.stage.service_path && !ticket.stage.followup_stage" class="text-on-surface-variant font-body-md">—</span>
                </div>
                <div v-if="ticket.stage.service_charge_type" class="mt-3 pt-3 border-t border-outline-variant flex items-center gap-2">
                  <span class="material-symbols-outlined text-outline" style="font-size:16px">payments</span>
                  <span class="text-on-surface-variant font-body-md">Charge:</span>
                  <span class="font-semibold text-on-surface font-body-md">{{ ticket.stage.service_charge_type }}</span>
                </div>
              </div>

              <!-- Customer Communication -->
              <div class="rounded-xl p-4 bg-surface-container">
                <div class="font-label-md text-label-md text-outline mb-3 flex items-center gap-1.5">
                  <span class="material-symbols-outlined" style="font-size:16px">contact_support</span>
                  Customer Communication
                </div>
                <div class="space-y-2.5">
                  <div class="flex items-center justify-between">
                    <span class="text-on-surface-variant font-body-md">Satisfaction</span>
                    <span v-if="ticket.stage.customer_satisfaction_status" class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="satisfactionChip(ticket.stage.customer_satisfaction_status)">{{ ticket.stage.customer_satisfaction_status }}</span>
                    <span v-else class="text-outline">—</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-on-surface-variant font-body-md">Informed Status</span>
                    <span v-if="ticket.stage.customer_informed_status" class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="informedChip(ticket.stage.customer_informed_status)">{{ ticket.stage.customer_informed_status }}</span>
                    <span v-else class="text-outline">—</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-on-surface-variant font-body-md">No Update Count</span>
                    <span class="font-semibold text-on-surface font-body-md">{{ ticket.stage.no_update_count ?? '0' }}</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-on-surface-variant font-body-md">Last SC Follow-up</span>
                    <span class="text-on-surface font-body-md">{{ ticket.stage.last_service_center_followup?.substring(0,16) || '—' }}</span>
                  </div>
                </div>
              </div>

              <!-- Part Tracking (conditional) -->
              <div v-if="ticket.stage.part_required" class="rounded-xl p-4 bg-surface-container" style="border-left:4px solid #943700">
                <div class="font-label-md text-label-md text-outline mb-3 flex items-center gap-1.5">
                  <span class="material-symbols-outlined" style="font-size:16px">build</span>
                  Part Tracking
                </div>
                <div class="space-y-2">
                  <div v-if="ticket.stage.part_name" class="flex items-center justify-between">
                    <span class="text-on-surface-variant font-body-md">Part</span>
                    <span class="font-semibold text-on-surface font-body-md">{{ ticket.stage.part_name }}</span>
                  </div>
                  <div v-if="ticket.stage.part_expected_date" class="flex items-center justify-between">
                    <span class="text-on-surface-variant font-body-md">Expected</span>
                    <span class="text-on-surface font-body-md">{{ ticket.stage.part_expected_date }}</span>
                  </div>
                  <div v-if="ticket.stage.part_delay_reason" class="pt-2 border-t border-outline-variant">
                    <span class="text-on-surface-variant font-body-md block">Delay Reason</span>
                    <span class="text-on-surface font-body-md block mt-0.5">{{ ticket.stage.part_delay_reason }}</span>
                  </div>
                  <div v-if="ticket.stage.customer_informed_about_part_delay" class="flex items-center justify-between pt-2 border-t border-outline-variant">
                    <span class="text-on-surface-variant font-body-md">Customer Informed</span>
                    <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="informedChip(ticket.stage.customer_informed_about_part_delay)">{{ ticket.stage.customer_informed_about_part_delay }}</span>
                  </div>
                </div>
              </div>

              <!-- Financial (conditional) -->
              <div v-if="ticket.stage.estimated_amount || ticket.stage.customer_approved_amount || (ticket.stage.payment_status && ticket.stage.payment_status !== 'Not Applicable')" class="rounded-xl p-4 bg-surface-container" style="border-left:4px solid #1a7f37">
                <div class="font-label-md text-label-md text-outline mb-3 flex items-center gap-1.5">
                  <span class="material-symbols-outlined" style="font-size:16px">payments</span>
                  Financial
                </div>
                <div class="space-y-2.5">
                  <div v-if="ticket.stage.estimated_amount" class="flex items-center justify-between">
                    <span class="text-on-surface-variant font-body-md">Estimate</span>
                    <span class="font-semibold text-on-surface font-body-md">₹{{ ticket.stage.estimated_amount }}</span>
                  </div>
                  <div v-if="ticket.stage.customer_approved_amount" class="flex items-center justify-between">
                    <span class="text-on-surface-variant font-body-md">Approved</span>
                    <span class="font-semibold text-on-surface font-body-md">₹{{ ticket.stage.customer_approved_amount }}</span>
                  </div>
                  <div v-if="ticket.stage.technician_payable" class="flex items-center justify-between">
                    <span class="text-on-surface-variant font-body-md">Technician Payable</span>
                    <span class="font-semibold text-on-surface font-body-md">₹{{ ticket.stage.technician_payable }}</span>
                  </div>
                  <div v-if="ticket.stage.payment_status && ticket.stage.payment_status !== 'Not Applicable'" class="flex items-center justify-between pt-2 border-t border-outline-variant">
                    <span class="text-on-surface-variant font-body-md">Payment</span>
                    <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="informedChip(ticket.stage.payment_status)">{{ ticket.stage.payment_status }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Last Follow-up Summary -->
            <div v-if="ticket.stage.last_followup_summary || ticket.stage.last_followup_at" class="mt-4 rounded-xl p-4 bg-surface-container-low border border-outline-variant">
              <div class="flex items-start gap-3">
                <span class="material-symbols-outlined text-outline" style="font-size:20px">history</span>
                <div class="flex-1 min-w-0">
                  <div class="font-label-md text-label-md text-outline">Last Follow-up</div>
                  <div class="text-on-surface font-body-md mt-0.5 break-words">{{ ticket.stage.last_followup_summary || '—' }}</div>
                  <div v-if="ticket.stage.last_followup_at" class="text-on-surface-variant font-label-md text-label-md mt-1 flex items-center gap-1">
                    <span class="material-symbols-outlined" style="font-size:14px">schedule</span>
                    {{ relTime(ticket.stage.last_followup_at) }}
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- Customer Summary -->
          <section id="sec-customer">
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Customer</h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div><span class="block text-label-md text-outline">Name</span> {{ ticket.customer?.name || '—' }}</div>
              <div><span class="block text-label-md text-outline">Mobile</span> {{ ticket.customer?.mobile || '—' }}</div>
              <div class="col-span-2"><span class="block text-label-md text-outline">Address</span> {{ ticket.customer?.address || '—' }}</div>
              <div><span class="block text-label-md text-outline">Pincode</span> {{ ticket.customer?.pincode || '—' }}</div>
            </div>
          </section>

          <!-- Product Summary -->
          <section id="sec-product">
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Product</h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div><span class="block text-label-md text-outline">Type</span> {{ ticket.product?.type || '—' }}</div>
              <div><span class="block text-label-md text-outline">Category/Item</span> {{ ticket.product?.item || '—' }}</div>
              <div><span class="block text-label-md text-outline">Brand</span> {{ ticket.product?.brand || '—' }}</div>
              <div><span class="block text-label-md text-outline">Model</span> {{ ticket.product?.model_number || '—' }}</div>
              <div><span class="block text-label-md text-outline">Serial Number</span> {{ ticket.product?.serial_number || '—' }}</div>
              <div><span class="block text-label-md text-outline">Warranty</span> {{ ticket.product?.warranty_status || '—' }}</div>
              <div><span class="block text-label-md text-outline">Invoice No.</span> {{ ticket.product?.invoice_number || '—' }}</div>
              <div><span class="block text-label-md text-outline">Purchase Date</span> {{ ticket.product?.purchase_date || '—' }}</div>
            </div>
          </section>

          <!-- Workflow Summary -->
          <section id="sec-workflow">
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Workflow</h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div><span class="block text-label-md text-outline">Current Status</span> {{ ticket.workflow?.status || '—' }}</div>
              <div><span class="block text-label-md text-outline">Pending Reason</span> {{ ticket.workflow?.pending_reason || '—' }}</div>
              <div><span class="block text-label-md text-outline">Next Follow-up</span> {{ ticket.workflow?.next_follow_up_date || '—' }}</div>
              <div><span class="block text-label-md text-outline">Service Center</span> {{ ticket.workflow?.service_center || '—' }}</div>
              <div><span class="block text-label-md text-outline">Brand Ticket</span> {{ ticket.workflow?.brand_ticket_number || '—' }}</div>
              <div><span class="block text-label-md text-outline">Brand Reg Date</span> {{ ticket.workflow?.brand_registration_date || '—' }}</div>
              <div>
                <span class="block text-label-md text-outline">SLA</span>
                <SlaBadge v-if="ticket.sla?.agreement_status" :agreement-status="ticket.sla.agreement_status" :response-by="ticket.sla.response_by" :resolution-by="ticket.sla.resolution_by" />
                <template v-else>—</template>
              </div>
              <div><span class="block text-label-md text-outline">Resolution Due</span> {{ ticket.sla?.resolution_by?.substring(0,16) || '—' }}</div>
              <div v-if="ticket.appointment" class="col-span-2">
                <span class="block text-label-md text-outline">Appointment</span>
                <span class="inline-flex items-center gap-1 text-on-surface">
                  <span class="material-symbols-outlined text-primary" style="font-size:16px">event</span>
                  {{ ticket.appointment.appointment_datetime?.substring(0,16) }}<template v-if="ticket.appointment.technician"> · {{ ticket.appointment.technician }}</template>
                </span>
              </div>
            </div>
          </section>

          <!-- Product Receipt Summary -->
          <section id="sec-receipt">
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Product Custody</h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div><span class="block text-label-md text-outline">Receipt No.</span> {{ ticket.receipt?.number || '—' }}</div>
              <div><span class="block text-label-md text-outline">Custody Status</span> {{ ticket.receipt?.custody_status || '—' }}</div>
              <div><span class="block text-label-md text-outline">Last Movement</span> {{ ticket.receipt?.last_movement?.substring(0,10) || '—' }}</div>
              <div><span class="block text-label-md text-outline">Ready for Pickup</span> {{ ticket.receipt?.ready_for_pickup ? 'Yes' : 'No' }}</div>
            </div>
          </section>

          <!-- Follow-up history (structured, from tagged log entries) -->
          <section id="sec-followup" v-if="followUpLog.length" class="border-t border-outline-variant pt-4 mt-4">
            <h3 class="font-headline-md text-headline-md text-on-surface mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined text-on-surface-variant" style="font-size:20px">timeline</span>
              Follow-up history
              <span class="font-body-md text-on-surface-variant font-normal">· {{ followUpLog.length }} attempt{{ followUpLog.length > 1 ? 's' : '' }}</span>
            </h3>
            <div class="relative">
              <!-- Timeline vertical line -->
              <div class="absolute left-[19px] top-3 bottom-3 w-0.5 bg-outline-variant rounded-full"></div>
              <ul class="flex flex-col">
                <li v-for="ev in followUpLog" :key="ev.id" class="flex items-start gap-4 pl-0 pb-5 relative">
                  <!-- Timeline dot + icon -->
                  <div class="relative z-10 flex items-center justify-center w-[38px] h-[38px] rounded-full shrink-0"
                    :style="{ background: followupActionBg(ev.text), color: followupActionFg(ev.text) }">
                    <span class="material-symbols-outlined" style="font-size:18px">{{ followupActionIcon(ev.text) }}</span>
                  </div>
                  <!-- Content -->
                  <div class="flex-1 min-w-0 pt-1">
                    <div class="text-on-surface font-body-md break-words">{{ ev.text.replace('[Follow-up] ', '') }}</div>
                    <div class="font-label-md text-label-md text-on-surface-variant mt-1 flex items-center gap-2">
                      <span class="inline-flex items-center gap-1">
                        <span class="material-symbols-outlined" style="font-size:14px">person</span>
                        {{ ev.by }}
                      </span>
                      <span class="text-outline">·</span>
                      <span class="inline-flex items-center gap-1">
                        <span class="material-symbols-outlined" style="font-size:14px">schedule</span>
                        {{ relTime(ev.on) }}
                      </span>
                    </div>
                  </div>
                </li>
              </ul>
            </div>
          </section>

          <!-- Activity timeline + add note -->
          <section id="sec-activity" class="border-t border-outline-variant pt-4 mt-4">
            <h3 class="font-headline-md text-headline-md text-on-surface mb-3">Activity</h3>

            <!-- Add note -->
            <div class="mb-5">
              <textarea
                v-model="noteText"
                rows="2"
                placeholder="Add an internal note…"
                class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none"
                @keydown.ctrl.enter="addNote"
              ></textarea>
              <div v-if="noteError" class="text-error font-label-md text-label-md mt-1">{{ noteError }}</div>
              <div class="flex justify-end mt-2">
                <button
                  @click="addNote"
                  :disabled="postingNote || !noteText.trim()"
                  class="px-4 h-9 rounded-lg bg-primary text-on-primary font-label-md text-body-md flex items-center gap-1.5 hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50"
                >
                  <span class="material-symbols-outlined" :class="postingNote ? 'animate-spin' : ''" style="font-size: 18px">
                    {{ postingNote ? 'progress_activity' : 'post_add' }}
                  </span>
                  Post note
                </button>
              </div>
            </div>

            <!-- Timeline -->
            <div v-if="activityLoading" class="text-on-surface-variant text-body-md py-4">Loading activity…</div>
            <ul v-else-if="activity.length" class="flex flex-col">
              <li v-for="(ev, i) in activity" :key="ev.id" class="flex gap-3">
                <div class="flex flex-col items-center">
                  <span
                    class="material-symbols-outlined w-8 h-8 rounded-full flex items-center justify-center shrink-0"
                    :class="ev.kind === 'note' ? 'bg-primary-container text-on-primary' : 'bg-surface-container-highest text-on-surface-variant'"
                    style="font-size: 18px"
                  >{{ ev.kind === 'note' ? 'sticky_note_2' : 'history' }}</span>
                  <span v-if="i < activity.length - 1" class="flex-1 w-px bg-outline-variant my-1"></span>
                </div>
                <div class="flex-1 pb-5 -mt-0.5">
                  <div class="font-body-md text-on-surface whitespace-pre-line">{{ ev.text || '—' }}</div>
                  <div class="font-label-md text-label-md text-on-surface-variant mt-0.5">{{ ev.by }} · {{ relTime(ev.on) }}</div>
                </div>
              </li>
            </ul>
            <div v-else class="text-on-surface-variant text-body-md py-2">No activity yet.</div>
          </section>
        </div>
      </div>

      <!-- Quick Action Panel -->
      <div id="sec-actions" class="w-full md:w-80 bg-surface flex flex-col overflow-y-auto border-t md:border-t-0 md:border-l border-outline-variant">
        <div class="p-4 border-b border-outline-variant bg-surface-container-low sticky top-0 z-10">
          <h3 class="font-headline-md text-headline-md text-on-surface">Quick Actions</h3>
        </div>
        <div class="p-4 flex flex-col gap-3">

          <button @click="openAction('brand_complaint')" class="w-full px-4 py-3 bg-primary text-on-primary rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
            <span class="material-symbols-outlined" style="font-size: 18px">verified</span> Register Brand Complaint
          </button>

          <button @click="openNeedInvoice" class="w-full px-4 py-3 bg-primary text-on-primary rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
            <span class="material-symbols-outlined" style="font-size: 18px">receipt_long</span> Need Invoice
          </button>

          <button @click="openAction('follow_up_sc')" class="w-full px-4 py-3 bg-primary-container text-on-primary rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
            <span class="material-symbols-outlined" style="font-size: 18px">support_agent</span> Follow Up Service Center
          </button>

          <button @click="openAction('waiting_part')" class="w-full px-4 py-3 bg-primary-container text-on-primary rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
            <span class="material-symbols-outlined" style="font-size: 18px">build</span> Waiting for Part
          </button>

          <button @click="openAction('schedule_appointment')" class="w-full px-4 py-3 bg-primary-container text-on-primary rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
            <span class="material-symbols-outlined" style="font-size: 18px">event</span> Schedule Appointment
          </button>

          <button @click="openAction('set_promise')" class="w-full px-4 py-3 bg-primary-container text-on-primary rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
            <span class="material-symbols-outlined" style="font-size: 18px">schedule_send</span> Set Customer Promise
          </button>

          <!-- Follow-up Journey Flow (Phase 1N-6B) -->
          <div class="pt-2 mt-1 border-t border-outline-variant font-label-md text-label-md text-on-surface-variant uppercase tracking-wide">Follow-up Journey</div>

          <div class="relative pl-4 mt-3">
            <!-- Vertical connector line -->
            <div class="absolute left-[23px] top-0 bottom-0 w-0.5 bg-outline-variant rounded-full"></div>
            <ul class="flex flex-col gap-0">
              <li v-for="(step, si) in followupFlowSteps" :key="step.key" class="relative flex items-start gap-4 pb-6 last:pb-0">
                <!-- Step indicator -->
                <div class="relative z-10 flex items-center justify-center w-[46px] h-[46px] rounded-full shrink-0 shadow-sm transition-all"
                  :class="step.status === 'completed' ? 'bg-[#1a7f37] text-white' : step.status === 'current' ? 'bg-primary text-white ring-4 ring-primary/20' : 'bg-surface-container-highest text-outline'">
                  <span v-if="step.status === 'completed'" class="material-symbols-outlined" style="font-size:22px">check</span>
                  <span v-else class="material-symbols-outlined" style="font-size:22px">{{ step.icon }}</span>
                </div>
                <!-- Step content -->
                <div class="flex-1 min-w-0 pt-2">
                  <div class="font-body-md font-semibold"
                    :class="step.status === 'completed' ? 'text-[#1a7f37]' : step.status === 'current' ? 'text-primary' : 'text-on-surface-variant'">
                    {{ step.label }}
                  </div>
                  <div v-if="step.status === 'current' && step.action" class="mt-2">
                    <button @click="openAction(step.action)" 
                      class="px-4 py-2 rounded-lg font-label-md text-label-md flex items-center gap-1.5 transition-all hover:opacity-90 active:scale-[0.97]"
                      :class="step.buttonClass || 'bg-primary text-on-primary'">
                      <span class="material-symbols-outlined" style="font-size:16px">{{ step.icon }}</span>
                      {{ step.buttonLabel || step.label }}
                    </button>
                  </div>
                  <div v-else-if="step.status === 'completed' && step.completedLabel" class="font-label-md text-label-md text-[#1a7f37] mt-0.5 flex items-center gap-1">
                    <span class="material-symbols-outlined" style="font-size:14px">done</span>
                    {{ step.completedLabel }}
                  </div>
                </div>
              </li>
            </ul>
          </div>

          <!-- Side note: Mark No Update / Escalate (always shown as alt path) -->
          <div v-if="followupAltActions.length" class="mt-3 pt-3 border-t border-outline-variant">
            <div class="font-label-md text-label-md text-outline mb-2 flex items-center gap-1.5">
              <span class="material-symbols-outlined" style="font-size:16px">alt_route</span>
              Alternative Actions
            </div>
            <div class="flex flex-wrap gap-2">
              <button v-for="alt in followupAltActions" :key="alt.action" @click="openAction(alt.action)"
                class="px-3 py-1.5 rounded-lg font-label-md text-label-md flex items-center gap-1.5 transition-all hover:opacity-90 active:scale-[0.97]"
                :class="alt.buttonClass">
                <span class="material-symbols-outlined" style="font-size:16px">{{ alt.icon }}</span>
                {{ alt.label }}
              </button>
            </div>
          </div>

          <button @click="openProductReceipt" class="w-full px-4 py-3 bg-secondary text-on-secondary rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
            <span class="material-symbols-outlined" style="font-size: 18px">inventory_2</span> Create Product Receipt
          </button>

          <button
            :disabled="!ticket?.receipt?.number"
            @click="ticket?.receipt?.number ? openReadyForPickup() : null"
            class="w-full px-4 py-3 bg-secondary text-on-secondary rounded-lg font-label-md text-left flex items-center gap-2 transition-all group relative"
            :class="ticket?.receipt?.number ? 'hover:opacity-90 active:scale-[0.98]' : 'opacity-50 cursor-not-allowed'"
          >
            <span class="material-symbols-outlined" style="font-size: 18px">hail</span> Mark Ready for Pickup
            <span v-if="!ticket?.receipt?.number" class="absolute hidden group-hover:block bottom-full left-0 mb-2 p-2 bg-inverse-surface text-inverse-on-surface text-xs rounded shadow w-full z-20">Create Product Receipt first.</span>
          </button>

          <button @click="openAction('customer_confirmed')" class="w-full px-4 py-3 bg-tertiary text-on-tertiary rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
            <span class="material-symbols-outlined" style="font-size: 18px">how_to_reg</span> Customer Confirmed
          </button>

          <button @click="openAction('close_ticket')" class="w-full px-4 py-3 bg-error text-on-error rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
            <span class="material-symbols-outlined" style="font-size: 18px">task_alt</span> Close Ticket
          </button>

          <!-- Product custody movements (only when a receipt exists) -->
          <template v-if="ticket?.receipt?.number">
            <div class="pt-2 mt-1 border-t border-outline-variant font-label-md text-label-md text-on-surface-variant uppercase tracking-wide">Product custody</div>
            <button @click="openAction('sent_to_sc')" class="w-full px-4 py-3 bg-surface-container-highest text-on-surface rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
              <span class="material-symbols-outlined" style="font-size: 18px">local_shipping</span> Send to Service Center
            </button>
            <button @click="openAction('returned_from_sc')" class="w-full px-4 py-3 bg-surface-container-highest text-on-surface rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
              <span class="material-symbols-outlined" style="font-size: 18px">assignment_return</span> Returned from SC
            </button>
            <button @click="openAction('delivered')" class="w-full px-4 py-3 bg-surface-container-highest text-on-surface rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
              <span class="material-symbols-outlined" style="font-size: 18px">verified</span> Delivered to Customer
            </button>
          </template>

          <!-- Reopen (only when the ticket is closed/resolved) -->
          <button v-if="isClosed" @click="openAction('reopen')" class="w-full px-4 py-3 bg-tertiary text-on-tertiary rounded-lg font-label-md text-left flex items-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all">
            <span class="material-symbols-outlined" style="font-size: 18px">restart_alt</span> Reopen Ticket
          </button>

        </div>
        <div class="p-4 mt-auto text-xs text-on-surface-variant text-center bg-surface-container-low border-t border-outline-variant">
          Actions are role-gated and validated server-side. You'll see a clear message if your role can't run one.
        </div>
      </div>
      
    </div>
  </div>

  <!-- Need Invoice Modal -->
  <div v-if="modals.needInvoice" class="fixed inset-0 bg-inverse-surface/40 backdrop-blur-sm flex items-center justify-center p-4 z-50" @click.self="modals.needInvoice = false" @keydown.escape="modals.needInvoice = false">
    <div class="bg-surface-container-lowest rounded-xl w-full max-w-lg shadow-[0_10px_15px_-3px_rgba(0,0,0,0.1)] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
      <!-- Modal Header -->
      <div class="px-6 py-5 border-b border-outline-variant/30 flex justify-between items-center bg-surface-bright">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-error-container flex items-center justify-center text-error">
            <span class="material-symbols-outlined icon-fill">error</span>
          </div>
          <div>
            <h2 class="text-headline-md font-headline-md text-on-surface">Need Invoice</h2>
            <p class="text-body-md font-body-md text-on-surface-variant mt-1">Ticket #{{ ticketId }} - Status Update</p>
          </div>
        </div>
        <button @click="modals.needInvoice = false" class="text-on-surface-variant hover:text-on-surface transition-colors rounded-full p-1 hover:bg-surface-variant/50">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <!-- Modal Body -->
      <div class="px-6 py-6 space-y-6 overflow-y-auto">
        <div v-if="actionError" class="p-3 bg-error-container text-on-error-container rounded font-body-sm mb-2">
          {{ actionError }}
        </div>
        <!-- Info Banner -->
        <div class="bg-surface-container p-4 rounded-lg flex items-start gap-3 border border-primary-fixed-dim/30">
          <span class="material-symbols-outlined text-primary mt-0.5">info</span>
          <div>
            <p class="text-body-md font-body-md text-on-surface font-medium">Customer document missing</p>
            <p class="text-body-md font-body-md text-on-surface-variant mt-1">This action will change the ticket status to <span class="font-semibold text-secondary">Waiting on Customer</span> and notify the assigned agent.</p>
          </div>
        </div>
        <form class="space-y-5" @submit.prevent="submitNeedInvoice">
          <!-- Pending Reason -->
          <div class="space-y-1.5">
            <label class="text-label-md font-label-md text-on-surface-variant block">Pending Reason</label>
            <div class="relative">
              <input class="w-full h-10 px-3 bg-surface-variant/30 border border-outline-variant/50 rounded-lg text-on-surface text-body-md font-body-md cursor-not-allowed focus:outline-none focus:ring-0" readonly type="text" :value="form.pending_reason" />
              <span class="material-symbols-outlined absolute right-3 top-2.5 text-on-surface-variant/50 text-[20px]">lock</span>
            </div>
          </div>
          <!-- Next Follow-up Date -->
          <div class="space-y-1.5">
            <label class="text-label-md font-label-md text-on-surface-variant block" for="followup">Next Follow-up Date <span class="text-error">*</span></label>
            <div class="relative">
              <input class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow" id="followup" required type="date" v-model="form.next_follow_up_date" :min="todayDate()"/>
            </div>
          </div>
          <!-- Note to Staff -->
          <div class="space-y-1.5">
            <label class="text-label-md font-label-md text-on-surface-variant block" for="staffNote">Note to Staff (Visible to internal team)</label>
            <textarea class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none" id="staffNote" placeholder="E.g., Customer promised to email it by tomorrow..." rows="3" v-model="form.note"></textarea>
          </div>
        </form>
      </div>
      <!-- Modal Footer -->
      <div class="px-6 py-4 bg-surface-bright border-t border-outline-variant/30 flex justify-end gap-3 rounded-b-xl">
        <button @click="modals.needInvoice = false" :disabled="submitting" class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium text-on-surface-variant hover:bg-surface-variant/50 transition-colors border border-transparent disabled:opacity-50" type="button">
          Cancel
        </button>
        <button @click="submitNeedInvoice" :disabled="submitting || !form.next_follow_up_date" class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium bg-primary text-on-primary hover:bg-on-primary-fixed-variant transition-colors shadow-sm flex items-center gap-2 disabled:opacity-50" type="button">
          <span v-if="submitting" class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
          <span v-else class="material-symbols-outlined text-[18px]">schedule_send</span>
          Mark Waiting on Customer
        </button>
      </div>
    </div>
  </div>
  <!-- Create Product Receipt Modal -->
  <div v-if="modals.createReceipt" class="fixed inset-0 bg-inverse-surface/40 backdrop-blur-sm flex items-center justify-center p-4 z-50" @click.self="modals.createReceipt = false" @keydown.escape="modals.createReceipt = false">
    <div class="bg-surface-container-lowest rounded-xl w-full max-w-2xl shadow-[0_10px_15px_-3px_rgba(0,0,0,0.1)] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200 max-h-[90vh]">
      <!-- Modal Header -->
      <div class="px-6 py-5 border-b border-outline-variant/30 flex justify-between items-center bg-surface-bright">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container">
            <span class="material-symbols-outlined icon-fill">inventory_2</span>
          </div>
          <div>
            <h2 class="text-headline-md font-headline-md text-on-surface">Create Product Receipt</h2>
            <p class="text-body-md font-body-md text-on-surface-variant mt-1">Ticket #{{ ticketId }} - Intake</p>
          </div>
        </div>
        <button @click="modals.createReceipt = false" class="text-on-surface-variant hover:text-on-surface transition-colors rounded-full p-1 hover:bg-surface-variant/50">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <!-- Modal Body -->
      <div class="px-6 py-6 space-y-6 overflow-y-auto">
        <div v-if="actionError" class="p-3 bg-error-container text-on-error-container rounded font-body-sm mb-2">
          {{ actionError }}
        </div>
        
        <form class="space-y-5" @submit.prevent="submitProductReceipt">
          <div class="grid grid-cols-2 gap-4">
            <!-- Customer info -->
            <div class="space-y-1.5">
              <label class="text-label-md font-label-md text-on-surface-variant block">Customer Name</label>
              <input class="w-full h-10 px-3 bg-surface-variant/30 border border-outline-variant/50 rounded-lg text-on-surface text-body-md font-body-md cursor-not-allowed" readonly type="text" :value="ticket?.customer?.name || ''" />
            </div>
            <div class="space-y-1.5">
              <label class="text-label-md font-label-md text-on-surface-variant block">Mobile</label>
              <input class="w-full h-10 px-3 bg-surface-variant/30 border border-outline-variant/50 rounded-lg text-on-surface text-body-md font-body-md cursor-not-allowed" readonly type="text" :value="ticket?.customer?.mobile || ''" />
            </div>
            
            <!-- Product info -->
            <div class="space-y-1.5">
              <label class="text-label-md font-label-md text-on-surface-variant block">Product Type</label>
              <input class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow" type="text" v-model="formReceipt.product_type" />
            </div>
            <div class="space-y-1.5">
              <label class="text-label-md font-label-md text-on-surface-variant block">Brand</label>
              <input class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow" type="text" v-model="formReceipt.brand" />
            </div>
            <div class="space-y-1.5">
              <label class="text-label-md font-label-md text-on-surface-variant block">Model Number</label>
              <input class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow" type="text" v-model="formReceipt.model_no" />
            </div>
            <div class="space-y-1.5">
              <label class="text-label-md font-label-md text-on-surface-variant block">Serial Number</label>
              <input class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow" type="text" v-model="formReceipt.serial_no" />
            </div>
          </div>
          
          <!-- Notes -->
          <div class="space-y-1.5">
            <label class="text-label-md font-label-md text-on-surface-variant block" for="accessories">Accessories Received <span class="text-error">*</span></label>
            <textarea class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none" id="accessories" required rows="2" v-model="formReceipt.accessories_received" placeholder="E.g. Charger, Original Box..."></textarea>
          </div>
          
          <div class="space-y-1.5">
            <label class="text-label-md font-label-md text-on-surface-variant block" for="condition">Physical Condition Notes <span class="text-error">*</span></label>
            <textarea class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none" id="condition" required rows="2" v-model="formReceipt.physical_condition" placeholder="E.g. Scratches on screen, dent on corner..."></textarea>
          </div>
        </form>
      </div>
      <!-- Modal Footer -->
      <div class="px-6 py-4 bg-surface-bright border-t border-outline-variant/30 flex justify-end gap-3 rounded-b-xl">
        <button @click="modals.createReceipt = false" :disabled="submitting" class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium text-on-surface-variant hover:bg-surface-variant/50 transition-colors border border-transparent disabled:opacity-50" type="button">
          Cancel
        </button>
        <button @click="submitProductReceipt" :disabled="submitting || !formReceipt.accessories_received || !formReceipt.physical_condition" class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium bg-secondary text-on-secondary hover:bg-secondary-fixed-variant transition-colors shadow-sm flex items-center gap-2 disabled:opacity-50" type="button">
          <span v-if="submitting" class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
          <span v-else class="material-symbols-outlined text-[18px]">check_circle</span>
          Create Receipt
        </button>
      </div>
    </div>
  </div>

  <!-- Mark Ready for Pickup Modal -->
  <div v-if="modals.readyPickup" class="fixed inset-0 bg-inverse-surface/40 backdrop-blur-sm flex items-center justify-center p-4 z-50" @click.self="modals.readyPickup = false" @keydown.escape="modals.readyPickup = false">
    <div class="bg-surface-container-lowest rounded-xl w-full max-w-lg shadow-[0_10px_15px_-3px_rgba(0,0,0,0.1)] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
      <!-- Modal Header -->
      <div class="px-6 py-5 border-b border-outline-variant/30 flex justify-between items-center bg-surface-bright">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container">
            <span class="material-symbols-outlined icon-fill">hail</span>
          </div>
          <div>
            <h2 class="text-headline-md font-headline-md text-on-surface">Mark Ready for Pickup</h2>
            <p class="text-body-md font-body-md text-on-surface-variant mt-1">Ticket #{{ ticketId }}</p>
          </div>
        </div>
        <button @click="modals.readyPickup = false" class="text-on-surface-variant hover:text-on-surface transition-colors rounded-full p-1 hover:bg-surface-variant/50">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <!-- Modal Body -->
      <div class="px-6 py-6 space-y-6 overflow-y-auto">
        <div v-if="actionError" class="p-3 bg-error-container text-on-error-container rounded font-body-sm mb-2">
          {{ actionError }}
        </div>
        <form class="space-y-5" @submit.prevent="submitReadyPickup">
          <div class="grid grid-cols-2 gap-4">
            <!-- Ticket info -->
            <div class="space-y-1.5">
              <label class="text-label-md font-label-md text-on-surface-variant block">Ticket ID</label>
              <input class="w-full h-10 px-3 bg-surface-variant/30 border border-outline-variant/50 rounded-lg text-on-surface text-body-md font-body-md cursor-not-allowed" readonly type="text" :value="ticket?.name || ''" />
            </div>
            <div class="space-y-1.5">
              <label class="text-label-md font-label-md text-on-surface-variant block">Receipt Number</label>
              <input class="w-full h-10 px-3 bg-surface-variant/30 border border-outline-variant/50 rounded-lg text-on-surface text-body-md font-body-md cursor-not-allowed" readonly type="text" :value="ticket?.receipt?.number || ''" />
            </div>
          </div>
          
          <div class="space-y-1.5">
            <label class="text-label-md font-label-md text-on-surface-variant block" for="readyDate">Ready Date</label>
            <input class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow" id="readyDate" type="date" v-model="formReady.ready_date" :min="todayDate()"/>
          </div>

          <div class="space-y-1.5">
            <label class="text-label-md font-label-md text-on-surface-variant block" for="readyNote">Ready Note</label>
            <textarea class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none" id="readyNote" placeholder="Instructions for front desk / customer" rows="3" v-model="formReady.ready_note"></textarea>
          </div>
        </form>
      </div>
      <!-- Modal Footer -->
      <div class="px-6 py-4 bg-surface-bright border-t border-outline-variant/30 flex justify-end gap-3 rounded-b-xl">
        <button @click="modals.readyPickup = false" :disabled="submitting" class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium text-on-surface-variant hover:bg-surface-variant/50 transition-colors border border-transparent disabled:opacity-50" type="button">
          Cancel
        </button>
        <button @click="submitReadyPickup" :disabled="submitting" class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium bg-primary text-on-primary hover:bg-on-primary-fixed-variant transition-colors shadow-sm flex items-center gap-2 disabled:opacity-50" type="button">
          <span v-if="submitting" class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
          <span v-else class="material-symbols-outlined text-[18px]">check_circle</span>
          Mark Ready for Pickup
        </button>
      </div>
    </div>
  </div>

  <!-- Generic Action Modal (Register Brand / Follow-up SC / Waiting Part / Customer Confirmed / Close) -->
  <div v-if="actionDef" class="fixed inset-0 bg-inverse-surface/40 backdrop-blur-sm flex items-center justify-center p-4 z-50" @click.self="closeAction" @keydown.escape="closeAction">
    <div class="bg-surface-container-lowest rounded-xl w-full max-w-lg shadow-[0_10px_15px_-3px_rgba(0,0,0,0.1)] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200 max-h-[90vh]">
      <div class="px-6 py-5 border-b border-outline-variant/30 flex justify-between items-center bg-surface-bright">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full flex items-center justify-center"
               :class="actionDef.danger ? 'bg-error-container text-error' : 'bg-primary-container text-on-primary'">
            <span class="material-symbols-outlined">{{ actionDef.icon }}</span>
          </div>
          <div>
            <h2 class="text-headline-md font-headline-md text-on-surface">{{ actionDef.title }}</h2>
            <p class="text-body-md font-body-md text-on-surface-variant mt-1">Ticket #{{ ticketId }}</p>
          </div>
        </div>
        <button @click="closeAction" class="text-on-surface-variant hover:text-on-surface transition-colors rounded-full p-1 hover:bg-surface-variant/50">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>

      <div class="px-6 py-6 space-y-5 overflow-y-auto">
        <div v-if="actionError" class="p-3 bg-error-container text-on-error-container rounded font-body-md">{{ actionError }}</div>

        <form class="space-y-5" @submit.prevent="submitAction">
          <div v-for="f in actionDef.fields" :key="f.key" class="space-y-1.5">
            <label class="text-label-md font-label-md text-on-surface-variant block">
              {{ f.label }} <span v-if="f.required" class="text-error">*</span>
            </label>

            <select
              v-if="f.type === 'select'"
              v-model="actionForm[f.key]"
              class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow"
            >
              <option value="" disabled>Select…</option>
              <option v-for="o in f.options" :key="o" :value="o">{{ o }}</option>
            </select>

            <textarea
              v-else-if="f.type === 'textarea'"
              v-model="actionForm[f.key]"
              rows="3"
              :placeholder="f.placeholder || ''"
              class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none"
            ></textarea>

            <input
              v-else
              v-model="actionForm[f.key]"
              :type="f.type"
              :min="f.type === 'date' ? todayDate() : undefined"
              :placeholder="f.placeholder || ''"
              class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow"
            />

            <p v-if="f.hint" class="text-label-md font-label-md text-on-surface-variant">{{ f.hint }}</p>
          </div>
        </form>
      </div>

      <div class="px-6 py-4 bg-surface-bright border-t border-outline-variant/30 flex justify-end gap-3 rounded-b-xl">
        <button @click="closeAction" :disabled="submitting" class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium text-on-surface-variant hover:bg-surface-variant/50 transition-colors disabled:opacity-50" type="button">
          Cancel
        </button>
        <button
          @click="submitAction"
          :disabled="submitting || !actionValid"
          class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium text-on-primary hover:opacity-90 transition-all shadow-sm flex items-center gap-2 disabled:opacity-50"
          :class="actionDef.danger ? 'bg-error' : 'bg-primary'"
          type="button"
        >
          <span v-if="submitting" class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
          <span v-else class="material-symbols-outlined text-[18px]">{{ actionDef.icon }}</span>
          {{ actionDef.submitLabel }}
        </button>
      </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch, reactive, computed, onMounted, onUnmounted } from 'vue'
import { call, post } from '@/api'
import SlaBadge from '@/components/SlaBadge.vue'
import { chip, dueChip, promiseChip, escChip, stageChip, satisfactionChip, informedChip, fmtDT, ticketAge, relTime } from '@/utils'
import { useToast } from '@/utils/toast'

const props = defineProps({
  ticketId: { type: String, default: null }
})

const emit = defineEmits(['close', 'refresh'])

const { show: showToast } = useToast()

const ticket = ref(null)
const loading = ref(false)
const error = ref(false)

// Activity timeline + add-note state
const activity = ref([])
const activityLoading = ref(false)
const noteText = ref('')
const noteError = ref('')
const postingNote = ref(false)

// Repeat-complaint detection / linking
const repeatCandidates = ref([])

const isClosed = computed(() => ['Closed', 'Cancelled', 'Resolved'].includes(ticket.value?.status))

const SECTIONS = [
  { id: 'sec-stage', label: 'Stage' },
  { id: 'sec-reminder', label: 'Reminder' },
  { id: 'sec-ai-advisory', label: 'AI Advisory' },
  { id: 'sec-followup-tracking', label: 'Follow-up Tracking' },
  { id: 'sec-customer', label: 'Customer' },
  { id: 'sec-product', label: 'Product' },
  { id: 'sec-workflow', label: 'Workflow' },
  { id: 'sec-receipt', label: 'Custody' },
  { id: 'sec-followup', label: 'Follow-ups' },
  { id: 'sec-activity', label: 'Activity' },
  { id: 'sec-actions', label: 'Actions' },
]
function scrollToSection(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// Structured follow-up history — derived from the tagged activity entries.
const followUpLog = computed(() => activity.value.filter((e) => (e.text || '').startsWith('[Follow-up]')))

// Follow-up journey flow stepper — served by AI engine on the server.
const followupFlowSteps = ref([])
const followupAltActions = ref([])

const loadFollowupFlow = async () => {
	if (!props.ticketId) { followupFlowSteps.value = []; followupAltActions.value = []; return }
	try {
		const res = await call('lavanya_service.ai_advisory.get_followup_flow', { ticket_name: props.ticketId })
		followupFlowSteps.value = res?.steps || []
		followupAltActions.value = res?.alt_actions || []
	} catch (e) {
		followupFlowSteps.value = []
		followupAltActions.value = []
	}
}
const aiBusy = ref(false)
function aiStatusChip(s) {
	if (s === 'Suggested') return { background: 'rgba(0,83,219,0.12)', color: '#0053db' }
	if (s === 'Accepted') return { background: 'rgba(26,127,55,0.12)', color: '#1a7f37' }
	if (s === 'Ignored') return { background: 'rgba(67,70,85,0.12)', color: '#434655' }
	if (s === 'Review Needed') return { background: 'rgba(186,26,26,0.12)', color: '#ba1a1a' }
	return { background: 'rgba(67,70,85,0.08)', color: '#434655' }
}
async function acceptAiSuggestion() {
	aiBusy.value = true
	try {
		await post('lavanya_service.ai_advisory.accept_ai_suggestion', { ticket_name: props.ticketId, accepted_field: 'ai_suggested_next_action' })
		await loadTicket()
		showToast('AI suggestion accepted')
	} catch (e) {
		showToast(e.message || 'Could not accept suggestion.', 'error')
	} finally {
		aiBusy.value = false
	}
}
async function ignoreAiSuggestion() {
	aiBusy.value = true
	try {
		await post('lavanya_service.ai_advisory.ignore_ai_suggestion', { ticket_name: props.ticketId })
		await loadTicket()
		showToast('AI suggestion ignored')
	} catch (e) {
		showToast(e.message || 'Could not ignore suggestion.', 'error')
	} finally {
		aiBusy.value = false
	}
}

const FOLLOWUP_ACTION_STYLES = {
	'Verify Technician Called': { icon: 'phone_in_talk', bg: 'rgba(0,74,198,0.12)', fg: '#004ac6' },
	'Verify Technician Visit': { icon: 'handyman', bg: 'rgba(37,99,235,0.12)', fg: '#2563eb' },
	'Record SC Follow-up': { icon: 'support_agent', bg: 'rgba(0,83,219,0.12)', fg: '#0053db' },
	'Inform Customer': { icon: 'campaign', bg: 'rgba(26,127,55,0.12)', fg: '#1a7f37' },
	'Mark No Update': { icon: 'warning', bg: 'rgba(148,55,0,0.12)', fg: '#943700' },
	'Escalate Case': { icon: 'escalator_warning', bg: 'rgba(186,26,26,0.12)', fg: '#ba1a1a' },
	'Record Satisfaction': { icon: 'sentiment_satisfied', bg: 'rgba(26,127,55,0.12)', fg: '#1a7f37' },
	'Record Customer Approval': { icon: 'contract', bg: 'rgba(113,42,226,0.12)', fg: '#712ae2' },
}
function followupActionStyle(text) {
	for (const [key, style] of Object.entries(FOLLOWUP_ACTION_STYLES)) {
		if (text.includes(key)) return style
	}
	return { icon: 'support_agent', bg: 'rgba(67,70,85,0.12)', fg: '#434655' }
}
function followupActionIcon(text) { return followupActionStyle(text).icon }
function followupActionBg(text) { return followupActionStyle(text).bg }
function followupActionFg(text) { return followupActionStyle(text).fg }

// Follow-up tracking banner state
const followupBanner = computed(() => {
	const s = ticket.value?.stage || {}
	if (s.customer_satisfaction_status === 'Satisfied' || s.customer_satisfaction_status === 'Not Required')
		return { bg: 'rgba(26,127,55,0.12)', fg: '#1a7f37', icon: 'sentiment_satisfied', title: 'Customer Satisfied', sub: 'No further follow-up needed.' }
	if (s.customer_satisfaction_status === 'Not Satisfied')
		return { bg: 'rgba(186,26,26,0.12)', fg: '#ba1a1a', icon: 'sentiment_dissatisfied', title: 'Customer Not Satisfied', sub: 'Escalate or follow up to resolve concerns.' }
	if (s.escalation_level && s.escalation_level !== 'None')
		return { bg: 'rgba(186,26,26,0.12)', fg: '#ba1a1a', icon: 'escalator_warning', title: `Escalated — ${s.escalation_level}`, sub: 'Case requires higher-level attention.' }
	if (s.followup_stage === 'no_technician_update')
		return { bg: 'rgba(148,55,0,0.12)', fg: '#943700', icon: 'warning', title: 'No Update from Technician', sub: 'No response from service center — escalation may be needed.' }
	if (s.followup_stage === 'part_pending')
		return { bg: 'rgba(148,55,0,0.12)', fg: '#943700', icon: 'build', title: 'Awaiting Part', sub: s.part_delay_reason || 'Part not yet received.' }
	if (!s.customer_informed_status || s.customer_informed_status === 'Pending')
		return { bg: 'rgba(148,55,0,0.12)', fg: '#943700', icon: 'campaign', title: 'Customer Not Informed', sub: 'Customer needs to be contacted about their service status.' }
	if (s.customer_informed_status === 'Customer Not Reachable')
		return { bg: 'rgba(186,26,26,0.12)', fg: '#ba1a1a', icon: 'person_off', title: 'Customer Not Reachable', sub: 'Multiple attempts failed — document efforts.' }
	if (s.followup_stage === 'technician_call_pending')
		return { bg: 'rgba(0,74,198,0.08)', fg: '#004ac6', icon: 'phone_in_talk', title: 'Technician Call Pending', sub: 'Verify if technician has called the customer.' }
	if (s.followup_stage === 'technician_visit_pending')
		return { bg: 'rgba(0,74,198,0.08)', fg: '#004ac6', icon: 'handyman', title: 'Technician Visit Pending', sub: 'Verify if technician has visited the customer.' }
	if (s.followup_stage === 'customer_confirmation_pending')
		return { bg: 'rgba(113,42,226,0.12)', fg: '#712ae2', icon: 'how_to_reg', title: 'Awaiting Customer Confirmation', sub: 'Waiting for customer to confirm service completion.' }
	return { bg: 'rgba(0,74,198,0.08)', fg: '#004ac6', icon: 'support_agent', title: 'Follow-up in Progress', sub: 'Ticket is actively being followed up.' }
})

async function loadRepeat() {
  repeatCandidates.value = []
  if (!props.ticketId) return
  try {
    const res = await call('lavanya_service.api.repeat_complaints.find_repeat_candidates', { ticket_name: props.ticketId })
    repeatCandidates.value = res?.candidates || []
  } catch (e) {
    repeatCandidates.value = []
  }
}

async function linkRepeat(previous) {
  try {
    await post('lavanya_service.api.repeat_complaints.confirm_repeat_complaint', {
      ticket_name: props.ticketId,
      previous_ticket_link: previous,
    })
    emit('refresh')
    await loadTicket()
  } catch (e) {
    actionError.value = e.message || 'Could not link the repeat complaint.'
  }
}

async function clearRepeat() {
  try {
    await post('lavanya_service.api.repeat_complaints.clear_repeat_complaint', { ticket_name: props.ticketId })
    emit('refresh')
    await loadTicket()
  } catch (e) {
    actionError.value = e.message || 'Could not clear the repeat flag.'
  }
}

const loadActivity = async () => {
  if (!props.ticketId) return
  activityLoading.value = true
  try {
    const res = await call('lavanya_service.api.stitch_console.get_ticket_activity', { ticket_id: props.ticketId })
    activity.value = res?.events || []
  } catch (e) {
    activity.value = []
  } finally {
    activityLoading.value = false
  }
}

async function addNote() {
  const text = noteText.value.trim()
  if (!text) return
  postingNote.value = true
  noteError.value = ''
  try {
    const ev = await post('lavanya_service.api.stitch_console.add_ticket_note', {
      ticket_id: props.ticketId,
      note: text,
    })
    activity.value = [ev, ...activity.value]
    noteText.value = ''
    showToast('Note added')
  } catch (err) {
    noteError.value = err.message || 'Could not post note.'
    showToast(err.message || 'Could not post note.', 'error')
  } finally {
    postingNote.value = false
  }
}

const loadTicket = async () => {
  if (props.ticketId) {
    loading.value = true
    error.value = false
    noteText.value = ''
    noteError.value = ''
    try {
      ticket.value = await call('lavanya_service.api.stitch_console.get_ticket_detail', { ticket_id: props.ticketId })
    } catch (e) {
      error.value = true
    } finally {
      loading.value = false
    }
    loadActivity()
    loadRepeat()
    loadFollowupFlow()
  }
}

watch(() => props.ticketId, loadTicket)

function close() {
  emit('close')
}

onMounted(() => document.addEventListener('keydown', onKeyDown))
onUnmounted(() => document.removeEventListener('keydown', onKeyDown))
function onKeyDown(e) {
  if (e.key === 'Escape' && props.ticketId) close()
}

// WhatsApp the customer via a wa.me link (no gateway needed — opens WhatsApp with
// the number + a status-appropriate pre-filled message; staff press send).
function whatsappCustomer() {
  const t = ticket.value
  if (!t?.customer?.mobile) return
  const digits = String(t.customer.mobile).replace(/\D/g, '')
  const intl = digits.length === 10 ? '91' + digits : digits // default India country code
  const product = [t.product?.brand, t.product?.item || t.product?.type].filter(Boolean).join(' ') || 'product'
  const name = t.customer?.name ? `Hello ${t.customer.name}, ` : 'Hello, '
  const byStatus = {
    'Ready for Pickup': `your ${product} is repaired and ready for pickup.`,
    'Waiting on Customer': `we need some information to proceed with your ${product} service.`,
    Resolved: `your ${product} service is complete.`,
    Closed: `your ${product} service is complete.`,
  }
  const tail = byStatus[t.status] || `here's an update on your ${product} service: ${t.status}.`
  const msg = `${name}${tail} (Ticket ${t.name}) — Lavanya eMart Service`
  window.open(`https://wa.me/${intl}?text=${encodeURIComponent(msg)}`, '_blank')
}

// Action state
const modals = reactive({
  needInvoice: false,
  createReceipt: false,
  readyPickup: false
})
const form = reactive({
  pending_reason: 'Need Invoice',
  next_follow_up_date: '',
  note: ''
})
const submitting = ref(false)
const actionError = ref('')

function todayDate() {
  return new Date().toISOString().slice(0, 10)
}

function openNeedInvoice() {
  actionError.value = ''
  form.pending_reason = 'Need Invoice'
  form.next_follow_up_date = ''
  form.note = ''
  modals.needInvoice = true
}

async function submitNeedInvoice() {
  if (!form.next_follow_up_date) {
    actionError.value = "Next follow-up date is required."
    return
  }
  submitting.value = true
  actionError.value = ''
  try {
    await post('lavanya_service.api.workflow_actions.need_invoice_from_customer', {
      ticket_name: props.ticketId,
      next_follow_up_date: form.next_follow_up_date,
      note: form.note
    })
    modals.needInvoice = false
    emit('refresh')
    await loadTicket()
  } catch (err) {
    actionError.value = err.message || 'An error occurred while saving.'
  } finally {
    submitting.value = false
  }
}

const formReceipt = reactive({
  product_type: '',
  brand: '',
  model_no: '',
  serial_no: '',
  accessories_received: '',
  physical_condition: ''
})

function openProductReceipt() {
  actionError.value = ''
  formReceipt.product_type = ticket.value?.product?.type || ''
  formReceipt.brand = ticket.value?.product?.brand || ''
  formReceipt.model_no = ticket.value?.product?.model_number || ''
  formReceipt.serial_no = ticket.value?.product?.serial_number || ''
  formReceipt.accessories_received = ''
  formReceipt.physical_condition = ''
  modals.createReceipt = true
}

async function submitProductReceipt() {
  if (!formReceipt.accessories_received || !formReceipt.physical_condition) {
    actionError.value = "Accessories and condition are required."
    return
  }
  submitting.value = true
  actionError.value = ''
  try {
    await post('lavanya_service.api.workflow_actions.create_product_receipt', {
      ticket_name: props.ticketId,
      accessories_received: formReceipt.accessories_received,
      physical_condition: formReceipt.physical_condition,
      product_type: formReceipt.product_type,
      brand: formReceipt.brand,
      model_no: formReceipt.model_no,
      serial_no: formReceipt.serial_no
    })
    modals.createReceipt = false
    emit('refresh')
    await loadTicket()
  } catch (err) {
    actionError.value = err.message || 'An error occurred while saving.'
  } finally {
    submitting.value = false
  }
}

const formReady = reactive({
  ready_date: '',
  ready_note: ''
})

function openReadyForPickup() {
  actionError.value = ''
  formReady.ready_date = todayDate()
  formReady.ready_note = ''
  modals.readyPickup = true
}

async function submitReadyPickup() {
  submitting.value = true
  actionError.value = ''
  try {
    await post('lavanya_service.api.product_receipt_actions.mark_ready_for_pickup', {
      receipt_name: ticket.value.receipt.number,
      next_follow_up_date: formReady.ready_date,
      notes: formReady.ready_note
    })
    modals.readyPickup = false
    emit('refresh')
    await loadTicket()
  } catch (err) {
    actionError.value = err.message || 'An error occurred while saving.'
  } finally {
    submitting.value = false
  }
}

// ── Generic quick-action modal ──────────────────────────────────────────────
// Option lists mirror the backend constants in setup/hd_ticket_fields.py and
// workflow/quick_actions.py. The server re-validates every value and the role,
// so these are only for a good dropdown UX — drift surfaces as a clear error.
const FOLLOW_UP_RESULTS = [
  'Service center contacted',
  'Technician assigned',
  'Customer not reachable',
  'Service completed',
  'Part pending',
  'Approval pending',
]
const PENDING_REASONS = [
  'Invoice Proof Pending', 'Invoice Pending', 'Brand Registration Recommended',
  'Manufacturer Registration Pending', 'Service Follow-up Required', 'Brand Ticket Number Pending',
  'Customer Details Missing', 'Technician Not Visited', 'Service Center Delayed',
  'Service Center Out of Area', 'Customer Not Reachable', 'Customer Reappointed', 'Part Pending',
  'Part Warranty Pending', 'Replacement Approval Pending', 'Supplier Approval Pending',
  'Customer Pickup Pending', 'Manager Escalation Pending', 'Local Technician Pending',
  'Local Service Transfer Pending', 'Estimate Approval Pending', 'Brand Line Busy',
  'Service Center Unreachable', 'Other',
]
const CLOSURE_TYPES = [
  'Resolved by Brand Service', 'Resolved by Local Technician', 'Replacement Completed',
  'Customer Collected Product', 'Customer Cancelled', 'Duplicate Ticket',
  'Not Purchased From Lavanya - Guided Only', 'Brand Denied Warranty', 'Customer Not Responding',
  'Closed After Manager Approval', 'Other',
]

const ACTIONS = {
  brand_complaint: {
    title: 'Register Brand Complaint', icon: 'verified', submitLabel: 'Register',
    endpoint: 'lavanya_service.api.workflow_actions.register_brand_complaint',
    fields: [
      { key: 'brand_ticket_number', label: 'Brand Ticket Number', type: 'text', required: true },
      { key: 'registration_date', label: 'Registration Date', type: 'date', required: true },
      { key: 'next_follow_up_date', label: 'Next Follow-up Date', type: 'date', required: true },
      { key: 'service_center', label: 'Service Center (optional)', type: 'text', required: false },
    ],
  },
  follow_up_sc: {
    title: 'Follow Up Service Center', icon: 'support_agent', submitLabel: 'Record Follow-up',
    endpoint: 'lavanya_service.api.workflow_actions.follow_up_service_center',
    fields: [
      { key: 'follow_up_result', label: 'Follow-up Result', type: 'select', required: true, options: FOLLOW_UP_RESULTS },
      {
        key: 'next_follow_up_date', label: 'Next Follow-up Date', type: 'date',
        required: (f) => f.follow_up_result !== 'Service completed',
        hint: 'Required unless the result is “Service completed”.',
      },
    ],
  },
  waiting_part: {
    title: 'Waiting for Part', icon: 'build', submitLabel: 'Mark Waiting on Part',
    endpoint: 'lavanya_service.api.workflow_actions.waiting_for_part',
    fields: [
      { key: 'pending_reason', label: 'Pending Reason', type: 'select', required: true, options: PENDING_REASONS },
      { key: 'next_follow_up_date', label: 'Next Follow-up Date', type: 'date', required: true },
    ],
  },
  customer_confirmed: {
    title: 'Customer Confirmed', icon: 'how_to_reg', submitLabel: 'Confirm & Close',
    endpoint: 'lavanya_service.api.workflow_actions.customer_confirmed',
    fields: [
      { key: 'work_narration', label: 'Work Narration', type: 'textarea', required: true, placeholder: 'Summary of the work done…' },
      { key: 'closure_type', label: 'Closure Type', type: 'select', required: true, options: CLOSURE_TYPES },
    ],
  },
  close_ticket: {
    title: 'Close Ticket', icon: 'task_alt', submitLabel: 'Close Ticket', danger: true,
    endpoint: 'lavanya_service.api.workflow_actions.close_ticket',
    fields: [
      { key: 'work_narration', label: 'Work Narration', type: 'textarea', required: true, placeholder: 'Summary of the work done…' },
      { key: 'closure_type', label: 'Closure Type', type: 'select', required: true, options: CLOSURE_TYPES },
      { key: 'customer_confirmation_received', label: 'Customer Confirmation Received', type: 'select', required: true, options: ['Yes', 'No'] },
    ],
  },
  // Product-custody movements — operate on the linked Service Product Receipt.
  sent_to_sc: {
    title: 'Send to Service Center', icon: 'local_shipping', submitLabel: 'Mark Sent', target: 'receipt',
    endpoint: 'lavanya_service.api.product_receipt_actions.mark_product_sent_to_sc',
    fields: [
      { key: 'expected_return_date', label: 'Expected Return Date', type: 'date', required: false },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  returned_from_sc: {
    title: 'Returned from Service Center', icon: 'assignment_return', submitLabel: 'Mark Returned', target: 'receipt',
    endpoint: 'lavanya_service.api.product_receipt_actions.mark_product_returned_from_sc',
    fields: [
      { key: 'actual_return_date', label: 'Actual Return Date', type: 'date', required: false },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  delivered: {
    title: 'Delivered to Customer', icon: 'verified', submitLabel: 'Mark Delivered', target: 'receipt',
    endpoint: 'lavanya_service.api.product_receipt_actions.mark_delivered_to_customer',
    fields: [{ key: 'notes', label: 'Handover notes', type: 'textarea', required: false }],
  },
  reopen: {
    title: 'Reopen Ticket', icon: 'restart_alt', submitLabel: 'Reopen', danger: true, target: 'ticket',
    endpoint: 'lavanya_service.api.product_receipt_actions.reopen_ticket',
    fields: [{ key: 'reopen_reason', label: 'Reason for reopening', type: 'textarea', required: true, placeholder: 'e.g. Customer reports the issue persists' }],
  },
  schedule_appointment: {
    title: 'Schedule Appointment', icon: 'event', submitLabel: 'Schedule', target: 'ticket',
    endpoint: 'lavanya_service.api.stitch_console.schedule_appointment',
    fields: [
      { key: 'appointment_datetime', label: 'Date & Time', type: 'datetime-local', required: true },
      { key: 'technician', label: 'Technician', type: 'text', required: false, placeholder: 'Name of the technician' },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  set_promise: {
    title: 'Set Customer Promise', icon: 'schedule_send', submitLabel: 'Save Promise', target: 'ticket',
    endpoint: 'lavanya_service.api.stitch_console.set_customer_promise',
    fields: [{ key: 'promised_at', label: 'Promised an update by', type: 'datetime-local', required: true }],
  },
  // Follow-up tracking actions (Phase 1N-6B)
  verify_tech_called: {
    title: 'Verify Technician Called', icon: 'phone_in_talk', submitLabel: 'Verify Called',
    endpoint: 'lavanya_service.api.workflow_actions.verify_technician_called',
    fields: [
      { key: 'technician_name', label: 'Technician Name', type: 'text', required: false },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  verify_tech_visit: {
    title: 'Verify Technician Visit', icon: 'handyman', submitLabel: 'Verify Visit',
    endpoint: 'lavanya_service.api.workflow_actions.verify_technician_visit',
    fields: [
      { key: 'technician_name', label: 'Technician Name', type: 'text', required: false },
      { key: 'visit_result', label: 'Visit Result', type: 'text', required: false },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  record_sc_followup: {
    title: 'Record SC Follow-up', icon: 'support_agent', submitLabel: 'Record',
    endpoint: 'lavanya_service.api.workflow_actions.record_sc_followup',
    fields: [
      { key: 'follow_up_result', label: 'Follow-up Result', type: 'select', required: true, options: FOLLOW_UP_RESULTS },
      { key: 'next_follow_up_date', label: 'Next Follow-up Date', type: 'date', required: false },
      { key: 'customer_informed_status', label: 'Customer Informed', type: 'select', required: true, options: ['Informed by Call', 'Informed by WhatsApp', 'Informed by SMS', 'Pending', 'Customer Not Reachable', 'Not Required'] },
    ],
  },
  inform_customer: {
    title: 'Inform Customer', icon: 'campaign', submitLabel: 'Mark Informed',
    endpoint: 'lavanya_service.api.workflow_actions.inform_customer',
    fields: [
      { key: 'channel', label: 'Channel', type: 'select', required: true, options: ['Phone', 'WhatsApp', 'Direct', 'SMS', 'Email'] },
      { key: 'message', label: 'Message', type: 'textarea', required: false },
    ],
  },
  mark_no_update: {
    title: 'Mark No Update', icon: 'warning', submitLabel: 'Mark & Escalate',
    endpoint: 'lavanya_service.api.workflow_actions.mark_no_update',
    fields: [
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  escalate_case: {
    title: 'Escalate Case', icon: 'escalator_warning', submitLabel: 'Escalate',
    endpoint: 'lavanya_service.api.workflow_actions.escalate_case',
    fields: [
      { key: 'reason', label: 'Reason', type: 'textarea', required: true, placeholder: 'Why is this being escalated?' },
    ],
  },
  record_satisfaction: {
    title: 'Record Satisfaction', icon: 'sentiment_satisfied', submitLabel: 'Record',
    endpoint: 'lavanya_service.api.workflow_actions.record_satisfaction',
    fields: [
      { key: 'satisfaction_status', label: 'Satisfaction Status', type: 'select', required: true, options: ['Satisfied', 'Not Satisfied', 'Customer Not Reachable', 'Not Required'] },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  record_approval: {
    title: 'Record Customer Approval', icon: 'contract', submitLabel: 'Record Approval',
    endpoint: 'lavanya_service.api.workflow_actions.record_customer_approval',
    fields: [
      { key: 'approved_amount', label: 'Approved Amount', type: 'number', required: true },
      { key: 'payment_status', label: 'Payment Status', type: 'select', required: false, options: ['Not Applicable', 'Pending', 'Approved', 'Paid'] },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
}

const actionKey = ref(null)
const actionDef = computed(() => (actionKey.value ? ACTIONS[actionKey.value] : null))
const actionForm = reactive({}); watch(actionForm, () => { if (actionError.value) actionError.value = '' })

function isRequired(f) {
  return typeof f.required === 'function' ? f.required(actionForm) : !!f.required
}
const actionValid = computed(() => {
  const def = actionDef.value
  if (!def) return false
  return def.fields.every((f) => !isRequired(f) || String(actionForm[f.key] ?? '').trim() !== '')
})

function openAction(key) {
  actionError.value = ''
  Object.keys(actionForm).forEach((k) => delete actionForm[k])
  for (const f of ACTIONS[key].fields) actionForm[f.key] = ''
  actionKey.value = key
}
function closeAction() {
  actionKey.value = null
}
async function submitAction() {
  if (!actionValid.value) return
  const def = actionDef.value
  if (def.danger && !confirm(`Are you sure you want to ${def.submitLabel.toLowerCase()} this ticket?`)) return
  // Receipt-targeted actions (custody movements) need the linked receipt.
  if (def.target === 'receipt' && !ticket.value?.receipt?.number) {
    actionError.value = 'This action needs a Product Receipt. Create one first.'
    return
  }
  submitting.value = true
  actionError.value = ''
  try {
    const payload = def.target === 'receipt'
      ? { receipt_name: ticket.value.receipt.number }
      : { ticket_name: props.ticketId }
    for (const f of def.fields) {
      const v = String(actionForm[f.key] ?? '').trim()
      if (v) payload[f.key] = v
    }
    await post(def.endpoint, payload)
    actionKey.value = null
    emit('refresh')
    await loadTicket()
    showToast(def.submitLabel + ' completed')
  } catch (err) {
    actionError.value = err.message || 'An error occurred while saving.'
    showToast(err.message || 'Action failed', 'error')
  } finally {
    submitting.value = false
  }
}

const reminderEsc = computed(() => ticket.value?.reminder?.escalation_level || 'None')
const reminderShowComputed = computed(() => !!ticket.value?.reminder?.manual_followup)
const lastFollowupText = computed(() => {
  const stage = ticket.value?.stage
  if (!stage?.last_followup_at && !stage?.last_followup_summary) return '—'
  const dt = stage.last_followup_at ? stage.last_followup_at.substring(0, 16) : ''
  const summary = stage.last_followup_summary ? stage.last_followup_summary.substring(0, 80) : ''
  return (dt ? dt + ' · ' : '') + summary || '—'
})
</script>

<style scoped>
.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.25s ease;
}
.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}
.drawer__panel {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.drawer-enter-from .drawer__panel,
.drawer-leave-to .drawer__panel {
  transform: translateX(100%);
}
</style>
