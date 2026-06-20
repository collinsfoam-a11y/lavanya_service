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
              <button @click="close" class="p-2 rounded hover:bg-surface-container-low" aria-label="Close ticket detail">
                <span class="material-symbols-outlined" aria-hidden="true">close</span>
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
                  class="inline-flex items-center gap-1.5 px-3 h-9 rounded-lg font-label-md text-body-md bg-success text-on-success"
                  :aria-label="'Generate WhatsApp draft for ' + ticket.customer?.name"
                >
                  <span class="material-symbols-outlined" style="font-size:18px" aria-hidden="true">chat</span> WhatsApp Draft
                </button>
              <a :href="'/helpdesk/tickets/' + ticket.name" target="_blank" class="text-primary hover:underline font-label-md">
                Open in Standard Helpdesk ↗
              </a>
            </div>
          </header>

          <!-- Next Action Bar — context-aware primary/secondary/danger actions -->
          <div class="rounded-xl p-4 mb-2 border border-outline-variant bg-surface-container-low">
            <div class="flex items-center gap-2 mb-3">
              <span class="material-symbols-outlined text-primary" style="font-size:20px">flash_on</span>
              <span class="font-label-lg text-label-lg font-semibold text-primary">Next Action</span>
              <LavFollowupQualityBadge v-if="qualityLevel" :ticket="ticket" class="ml-auto" />
            </div>
            <LavActionBar>
              <template #primary>
                <button v-for="action in nextActions.primary" :key="action.key"
                  @click="openAction(action.key)"
                  class="px-4 py-2.5 rounded-lg font-label-md text-left flex items-center gap-2 bg-primary text-on-primary hover:opacity-90 active:scale-[0.97] transition-all">
                  <span class="material-symbols-outlined" style="font-size:18px">{{ action.icon }}</span>
                  {{ action.label }}
                </button>
              </template>
              <template #secondary>
                <button v-for="action in nextActions.secondary" :key="action.key"
                  @click="openAction(action.key)"
                  class="px-4 py-2.5 rounded-lg font-label-md text-left flex items-center gap-2 bg-primary-container text-on-primary hover:opacity-90 active:scale-[0.97] transition-all">
                  <span class="material-symbols-outlined" style="font-size:18px">{{ action.icon }}</span>
                  {{ action.label }}
                </button>
              </template>
              <template #danger>
                <button v-for="action in nextActions.danger" :key="action.key"
                  @click="openAction(action.key)"
                  class="px-4 py-2.5 rounded-lg font-label-md text-left flex items-center gap-2 bg-error text-on-error hover:opacity-90 active:scale-[0.97] transition-all">
                  <span class="material-symbols-outlined" style="font-size:18px">{{ action.icon }}</span>
                  {{ action.label }}
                </button>
              </template>
            </LavActionBar>
            <div v-if="!nextActions.primary.length && !nextActions.secondary.length && !nextActions.danger.length" class="text-on-surface-variant font-body-md py-1">
              No actions available for this ticket state.
            </div>
          </div>

          <!-- Workflow Timeline — visual stage progression -->
          <LavWorkflowTimeline :ticket="ticket" />

          <!-- Customer Journey Summary Card -->
          <LavCustomerJourneyCard :ticket="ticket" />

          <section class="rounded-xl border p-4" :class="closureGuard.allowed ? 'border-success bg-success-container' : 'border-error bg-error-container'">
            <div class="flex items-start gap-3">
              <span class="material-symbols-outlined" :class="closureGuard.allowed ? 'text-success' : 'text-error'" aria-hidden="true">{{ closureGuard.allowed ? 'verified' : 'lock' }}</span>
              <div>
                <h3 class="font-headline-md text-headline-md" :class="closureGuard.allowed ? 'text-success' : 'text-error'">{{ closureGuard.allowed ? 'Closure Allowed' : 'Closure Not Allowed' }}</h3>
                <p class="font-body-md text-on-surface mt-1">Reason: {{ closureGuard.reason }}</p>
              </div>
            </div>
          </section>

          <!-- Communication Preview — P2.2 dry-run notifications only -->
          <section id="sec-communication" class="rounded-xl border border-outline-variant bg-surface-container-lowest p-4">
            <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-4">
              <div>
                <h3 class="font-headline-md text-headline-md text-primary">Communication Preview</h3>
                <p class="font-body-md text-on-surface-variant">Preview WhatsApp/SMS/Internal templates and queue dry-run notifications. No live customer message is sent.</p>
              </div>
              <button @click="openNotificationTemplateModal" class="px-3 h-9 rounded-lg border border-outline-variant text-primary font-label-md hover:bg-surface-container-low">
                Choose Template
              </button>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-[minmax(0,1fr)_minmax(0,1.4fr)] gap-4">
              <div class="flex flex-col gap-3">
                <label class="font-label-md text-label-md text-on-surface-variant">Available templates</label>
                <select v-model="selectedNotificationTemplate" @change="previewNotification" class="w-full rounded-lg border border-outline-variant bg-surface-container-lowest px-3 h-10 text-on-surface">
                  <option value="">Select a template</option>
                  <option v-for="tpl in notificationTemplates" :key="tpl.name" :value="tpl.name">
                    {{ tpl.event_type }} · {{ tpl.channel }}
                  </option>
                </select>
                <div v-if="selectedNotificationTemplateDoc" class="rounded-lg bg-surface-container p-3 font-body-md text-on-surface-variant">
                  <div><span class="font-semibold text-on-surface">Channel:</span> {{ selectedNotificationTemplateDoc.channel }}</div>
                  <div><span class="font-semibold text-on-surface">Approval:</span> {{ selectedNotificationTemplateDoc.requires_approval ? 'Required' : 'Not required' }}</div>
                  <div><span class="font-semibold text-on-surface">Dry-run:</span> Always on</div>
                </div>
                <button :disabled="!selectedNotificationTemplate || notificationBusy" @click="queueSelectedNotification" class="px-4 h-10 rounded-lg bg-primary text-on-primary font-label-md disabled:opacity-50">
                  Queue Dry Run
                </button>
              </div>

              <div class="rounded-xl border border-outline-variant bg-surface-container-low p-4 min-h-[180px]">
                <div class="flex items-center justify-between mb-2">
                  <div class="font-label-md text-label-md text-on-surface-variant">Rendered preview</div>
                  <span v-if="notificationPreview?.channel" class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="notificationChannelChip(notificationPreview.channel)">{{ notificationPreview.channel }}</span>
                </div>
                <div v-if="notificationBusy" class="text-on-surface-variant py-8 text-center">Loading preview...</div>
                <div v-else-if="notificationPreview?.ok" class="rounded-lg bg-surface-container-lowest border border-outline-variant p-3 whitespace-pre-wrap font-body-md text-on-surface">
                  {{ notificationPreview.rendered_message }}
                </div>
                <div v-else-if="notificationPreview" class="rounded-lg bg-error-container text-on-error-container p-3 font-body-md">
                  {{ notificationPreview.error || 'Template could not be rendered safely.' }}
                </div>
                <div v-else class="text-on-surface-variant py-8 text-center">Select a template to preview the message.</div>
              </div>
            </div>

            <div class="mt-5">
              <div class="font-label-md text-label-md text-on-surface-variant mb-2">Past queued messages</div>
              <div v-if="notificationQueue.length === 0" class="text-on-surface-variant font-body-md py-3">No queued notifications for this ticket.</div>
              <div v-else class="overflow-x-auto rounded-lg border border-outline-variant">
                <table class="w-full text-left border-collapse">
                  <thead class="bg-surface-container-low">
                    <tr>
                      <th class="px-3 py-2 font-label-md text-label-md text-on-surface-variant">Event</th>
                      <th class="px-3 py-2 font-label-md text-label-md text-on-surface-variant">Channel</th>
                      <th class="px-3 py-2 font-label-md text-label-md text-on-surface-variant">Status</th>
                      <th class="px-3 py-2 font-label-md text-label-md text-on-surface-variant">Dry Run</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="row in notificationQueue" :key="row.name" class="border-t border-outline-variant">
                      <td class="px-3 py-2 font-body-md text-on-surface">{{ row.event_type }}</td>
                      <td class="px-3 py-2 font-body-md text-on-surface">{{ row.channel }}</td>
                      <td class="px-3 py-2"><span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="notificationStatusChip(row.status)">{{ row.status }}</span></td>
                      <td class="px-3 py-2 font-body-md text-on-surface">{{ row.dry_run ? 'Yes' : 'No' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <!-- Visual Workflow Timeline -->
          <div v-if="workflowTimeline.length" class="overflow-x-auto -mx-1">
            <div class="flex items-center gap-1 min-w-max py-1">
              <template v-for="(s, i) in workflowTimeline" :key="s.key">
                <div class="flex items-center gap-2 px-3 py-2 rounded-full shrink-0 font-label-md text-label-md transition-all"
                  :class="s.status === 'completed' ? 'text-white' : s.status === 'current' ? 'text-white ring-2 ring-offset-1 ring-primary' : s.status === 'waiting' ? 'text-white' : s.status === 'blocked' ? 'text-white' : 'text-on-surface-variant bg-surface-container'"
                  :style="s.status === 'completed' ? { background: COLORS.success } : s.status === 'current' ? { background: COLORS.primary } : s.status === 'waiting' ? { background: COLORS.warning } : s.status === 'blocked' ? { background: COLORS.error } : {}"
                  :title="s.label">
                  <span class="material-symbols-outlined" style="font-size:14px">{{ s.status === 'completed' ? 'check' : s.icon }}</span>
                  <span class="truncate max-w-[120px]">{{ s.label }}</span>
                </div>
                <span v-if="i < workflowTimeline.length - 1" class="w-4 h-0.5 shrink-0 rounded-full"
                  :style="{ background: workflowTimeline[i+1].status === 'pending' ? COLORS.outline : COLORS.success }"></span>
              </template>
            </div>
          </div>

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
              <div><span class="block text-label-md text-outline">Service Flow</span> {{ ticket.stage.service_flow_type || '—' }}</div>
              <div><span class="block text-label-md text-outline">Current Service Step</span> {{ ticket.stage.current_service_stage || '—' }}</div>
              <div><span class="block text-label-md text-outline">Next Action</span> {{ ticket.stage.next_action || '—' }}</div>
              <div><span class="block text-label-md text-outline">Owner</span> {{ ticket.stage.next_action_owner || ticket.stage.next_action_role || '—' }}</div>
              <div><span class="block text-label-md text-outline">Next Follow-up</span> {{ ticket.stage.next_follow_up_date || '—' }}</div>
              <div><span class="block text-label-md text-outline">Stage Due</span> {{ ticket.stage.stage_due_at?.substring(0,16) || '—' }}</div>
              <div>
                <span class="block text-label-md text-outline">Due Status</span>
                <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="dueChip(ticket.stage.overdue_status)">{{ ticket.stage.overdue_status || '—' }}</span>
              </div>
              <div><span class="block text-label-md text-outline">Escalation</span> {{ ticket.stage.escalation_level && ticket.stage.escalation_level !== 'None' ? ticket.stage.escalation_level : '—' }}</div>
              <div><span class="block text-label-md text-outline">Customer Updated?</span> {{ ticket.stage.customer_informed || '—' }}</div>
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
                <span v-if="ticket.reminder.customer_update_due" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="{ color: COLORS.warning, background: hexToRgba(COLORS.warning, 0.12) }">Due now</span>
                <template v-else>No</template>
              </div>
              <div><span class="block text-label-md text-outline">Reminder Rule</span> {{ ticket.reminder.reminder_rule_applied || 'No rule (fallback)' }}</div>
              <div>
                <span class="block text-label-md text-outline">Next Follow-up</span>
                {{ fmtDT(ticket.reminder.next_follow_up_date) }}
                <span v-if="ticket.reminder.manual_followup" class="ml-1 px-1.5 py-0.5 rounded font-label-md text-label-md" :style="{ color: COLORS.secondary, background: hexToRgba(COLORS.secondary, 0.12) }">manual</span>
              </div>
              <div><span class="block text-label-md text-outline">Due Soon At</span> {{ fmtDT(ticket.reminder.computed_due_soon_at) }}</div>
              <div><span class="block text-label-md text-outline">Stage Due At</span> {{ fmtDT(ticket.reminder.computed_stage_due_at) }}</div>
              <div v-if="reminderShowComputed"><span class="block text-label-md text-outline">Computed Follow-up</span> {{ fmtDT(ticket.reminder.computed_next_followup_at) }}</div>
              <div><span class="block text-label-md text-outline">Promised Update At</span> {{ fmtDT(ticket.reminder.customer_promised_update_at) }}</div>
              <div v-if="ticket.reminder.promise_breach_reason" class="col-span-2">
                <span class="block text-label-md text-outline">Promise Breach Reason</span>
                <span :style="{ color: COLORS.error }">{{ ticket.reminder.promise_breach_reason }}</span>
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
                <p class="font-body-md text-on-surface mt-0.5" :style="{ color: COLORS.error }">{{ ticket.ai.risk_reason }}</p>
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
                    <span class="text-on-surface-variant font-body-md">Customer Updated?</span>
                    <span v-if="ticket.stage.customer_informed_status" class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="informedChip(ticket.stage.customer_informed_status)">{{ ticket.stage.customer_informed_status }}</span>
                    <span v-else class="text-outline">—</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-on-surface-variant font-body-md">No-update Count</span>
                    <span class="font-semibold text-on-surface font-body-md">{{ ticket.stage.no_update_count ?? '0' }}</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-on-surface-variant font-body-md">Last SC Follow-up</span>
                    <span class="text-on-surface font-body-md">{{ ticket.stage.last_service_center_followup?.substring(0,16) || '—' }}</span>
                  </div>
                </div>
              </div>

              <!-- Part Tracking (conditional) -->
              <div v-if="ticket.stage.part_required" class="rounded-xl p-4 bg-surface-container" :style="{ borderLeft: '4px solid ' + COLORS.warning }">
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
              <div v-if="ticket.stage.estimated_amount || ticket.stage.customer_approved_amount || (ticket.stage.payment_status && ticket.stage.payment_status !== 'Not Applicable')" class="rounded-xl p-4 bg-surface-container" :style="{ borderLeft: '4px solid ' + COLORS.success }">
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
                  :class="step.status === 'current' ? 'bg-primary text-white ring-4 ring-primary/20' : 'bg-surface-container-highest text-outline'"
                  :style="step.status === 'completed' ? { background: COLORS.success, color: 'white' } : {}">
                  <span v-if="step.status === 'completed'" class="material-symbols-outlined" style="font-size:22px">check</span>
                  <span v-else class="material-symbols-outlined" style="font-size:22px">{{ step.icon }}</span>
                </div>
                <!-- Step content -->
                <div class="flex-1 min-w-0 pt-2">
                  <div class="font-body-md font-semibold"
                    :class="step.status === 'current' ? 'text-primary' : 'text-on-surface-variant'"
                    :style="step.status === 'completed' ? { color: COLORS.success } : {}">
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
                  <div v-else-if="step.status === 'completed' && step.completedLabel" class="font-label-md text-label-md mt-0.5 flex items-center gap-1" :style="{ color: COLORS.success }">
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
  </Transition>

  <!-- Need Invoice Modal -->
  <LavModal :show="modals.needInvoice" title="Need Invoice" :subtitle="'Ticket #' + ticketId + ' - Status Update'" icon="error" icon-bg="bg-error-container text-error" :error="actionError" :loading="submitting" submit-label="Mark Waiting on Customer" submit-icon="schedule_send" :submit-disabled="!form.next_follow_up_date" max-width="lg" @close="modals.needInvoice = false" @submit="submitNeedInvoice">
    <div class="bg-surface-container p-4 rounded-lg flex items-start gap-3 border border-primary-fixed-dim/30">
      <span class="material-symbols-outlined text-primary mt-0.5">info</span>
      <div>
        <p class="text-body-md font-body-md text-on-surface font-medium">Customer document missing</p>
        <p class="text-body-md font-body-md text-on-surface-variant mt-1">This action will change the ticket status to <span class="font-semibold text-secondary">Waiting on Customer</span> and notify the assigned agent.</p>
      </div>
    </div>
    <form class="space-y-5" @submit.prevent="submitNeedInvoice">
      <div class="space-y-1.5">
        <label class="text-label-md font-label-md text-on-surface-variant block">Pending Reason</label>
        <div class="relative">
          <input class="w-full h-10 px-3 bg-surface-variant/30 border border-outline-variant/50 rounded-lg text-on-surface text-body-md font-body-md cursor-not-allowed focus:outline-none focus:ring-0" readonly type="text" :value="form.pending_reason" />
          <span class="material-symbols-outlined absolute right-3 top-2.5 text-on-surface-variant/50 text-[20px]">lock</span>
        </div>
      </div>
      <div class="space-y-1.5">
        <label class="text-label-md font-label-md text-on-surface-variant block" for="followup">Next Follow-up Date <span class="text-error">*</span></label>
        <input class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow" id="followup" required type="date" v-model="form.next_follow_up_date" :min="todayDate()"/>
      </div>
      <div class="space-y-1.5">
        <label class="text-label-md font-label-md text-on-surface-variant block" for="staffNote">Note to Staff (Visible to internal team)</label>
        <textarea class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none" id="staffNote" placeholder="E.g., Customer promised to email it by tomorrow..." rows="3" v-model="form.note"></textarea>
      </div>
    </form>
  </LavModal>

  <!-- Create Product Receipt Modal -->
  <LavModal :show="modals.createReceipt" title="Create Product Receipt" :subtitle="'Ticket #' + ticketId + ' - Intake'" icon="inventory_2" icon-bg="bg-secondary-container text-on-secondary-container" :error="actionError" :loading="submitting" submit-label="Create Receipt" submit-icon="check_circle" :submit-disabled="!formReceipt.accessories_received || !formReceipt.physical_condition" max-width="xl" @close="modals.createReceipt = false" @submit="submitProductReceipt">
    <form class="space-y-5" @submit.prevent="submitProductReceipt">
      <div class="grid grid-cols-2 gap-4">
        <div class="space-y-1.5">
          <label class="text-label-md font-label-md text-on-surface-variant block">Customer Name</label>
          <input class="w-full h-10 px-3 bg-surface-variant/30 border border-outline-variant/50 rounded-lg text-on-surface text-body-md font-body-md cursor-not-allowed" readonly type="text" :value="ticket?.customer?.name || ''" />
        </div>
        <div class="space-y-1.5">
          <label class="text-label-md font-label-md text-on-surface-variant block">Mobile</label>
          <input class="w-full h-10 px-3 bg-surface-variant/30 border border-outline-variant/50 rounded-lg text-on-surface text-body-md font-body-md cursor-not-allowed" readonly type="text" :value="ticket?.customer?.mobile || ''" />
        </div>
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
      <div class="space-y-1.5">
        <label class="text-label-md font-label-md text-on-surface-variant block" for="accessories">Accessories Received <span class="text-error">*</span></label>
        <textarea class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none" id="accessories" required rows="2" v-model="formReceipt.accessories_received" placeholder="E.g. Charger, Original Box..."></textarea>
      </div>
      <div class="space-y-1.5">
        <label class="text-label-md font-label-md text-on-surface-variant block" for="condition">Physical Condition Notes <span class="text-error">*</span></label>
        <textarea class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none" id="condition" required rows="2" v-model="formReceipt.physical_condition" placeholder="E.g. Scratches on screen, dent on corner..."></textarea>
      </div>
    </form>
  </LavModal>

  <!-- Mark Ready for Pickup Modal -->
  <LavModal :show="modals.readyPickup" title="Mark Ready for Pickup" :subtitle="'Ticket #' + ticketId" icon="hail" icon-bg="bg-secondary-container text-on-secondary-container" :error="actionError" :loading="submitting" submit-label="Mark Ready for Pickup" submit-icon="check_circle" max-width="lg" @close="modals.readyPickup = false" @submit="submitReadyPickup">
    <form class="space-y-5" @submit.prevent="submitReadyPickup">
      <div class="grid grid-cols-2 gap-4">
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
  </LavModal>

  <!-- Generic Action Modal (Register Brand / Follow-up SC / Waiting Part / Customer Confirmed / Close) -->
  <LavModal :show="!!actionDef" :title="actionDef?.title || ''" :subtitle="'Ticket #' + ticketId" :icon="actionDef?.icon || ''" :danger="actionDef?.danger || false" :error="actionError" :loading="submitting" :submit-label="actionDef?.submitLabel || ''" :submit-icon="actionDef?.icon || 'check_circle'" :submit-disabled="!actionValid" max-width="lg" @close="closeAction" @submit="submitAction">
    <form class="space-y-5" @submit.prevent="submitAction">
      <div v-for="f in actionDef?.fields || []" :key="f.key" class="space-y-1.5">
        <label class="text-label-md font-label-md text-on-surface-variant block">
          {{ f.label }} <span v-if="f.required" class="text-error">*</span>
        </label>
        <select v-if="f.type === 'select'" v-model="actionForm[f.key]" class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow">
          <option value="" disabled>Select...</option>
          <option v-for="o in f.options" :key="o" :value="o">{{ o }}</option>
        </select>
        <textarea v-else-if="f.type === 'textarea'" v-model="actionForm[f.key]" rows="3" :placeholder="f.placeholder || ''" class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none"></textarea>
        <input v-else v-model="actionForm[f.key]" :type="f.type" :min="f.type === 'date' ? todayDate() : undefined" :placeholder="f.placeholder || ''" class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow" />
        <p v-if="f.hint" class="text-label-md font-label-md text-on-surface-variant">{{ f.hint }}</p>
      </div>
    </form>
  </LavModal>

  <LavModal :show="showNotificationTemplatePicker" title="Select Notification Template" subtitle="Dry-run preview only" icon="forum" icon-bg="bg-primary-container text-on-primary-container" max-width="xl" submit-label="Close" submit-icon="close" @close="showNotificationTemplatePicker = false" @submit="showNotificationTemplatePicker = false">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <button v-for="tpl in notificationTemplates" :key="tpl.name" @click="selectNotificationTemplate(tpl.name)" class="text-left rounded-xl border border-outline-variant bg-surface-container-lowest p-3 hover:border-primary hover:bg-surface-container-low">
        <div class="font-label-lg text-on-surface">{{ tpl.event_type }}</div>
        <div class="font-body-md text-on-surface-variant">{{ tpl.channel }} · {{ tpl.language }} · {{ tpl.requires_approval ? 'Approval required' : 'No approval' }}</div>
      </button>
    </div>
  </LavModal>
  <LavConfirm />
</template>

<script setup>
import { ref, watch, reactive, computed, onMounted, onUnmounted } from 'vue'
import { call, post } from '@/api'
import SlaBadge from '@/components/SlaBadge.vue'
import LavModal from '@/components/LavModal.vue'
import LavActionBar from '@/components/LavActionBar.vue'
import LavWorkflowTimeline from '@/components/lavanya/tickets/LavWorkflowTimeline.vue'
import LavCustomerJourneyCard from '@/components/lavanya/tickets/LavCustomerJourneyCard.vue'
import LavFollowupQualityBadge from '@/components/lavanya/tickets/LavFollowupQualityBadge.vue'
import { chip, dueChip, promiseChip, escChip, stageChip, satisfactionChip, informedChip, fmtDT, ticketAge, relTime, hexToRgba, COLORS, qualityBadge, friendlyLabel } from '@/utils'
import { useToast } from '@/utils/toast'
import { useConfirm } from '@/utils/confirm'
import LavConfirm from '@/components/LavConfirm.vue'

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
const closureGuard = computed(() => {
  const s = ticket.value?.stage || ticket.value || {}
  const satisfaction = s.customer_satisfaction_status
  const confirmed = s.customer_confirmation_received || ticket.value?.customer_confirmation_received
  if (isClosed.value) return { allowed: true, reason: 'Ticket is already closed or resolved.' }
  if (confirmed === 'Yes' || satisfaction === 'Satisfied' || satisfaction === 'Not Required') {
    return { allowed: true, reason: 'Customer confirmed issue solved.' }
  }
  if (satisfaction === 'Not Satisfied') {
    return { allowed: false, reason: 'Customer is not satisfied; follow-up must continue.' }
  }
  return { allowed: false, reason: 'Customer confirmation pending.' }
})

const SECTIONS = [
  { id: 'sec-stage', label: 'Stage' },
  { id: 'sec-reminder', label: 'Reminder' },
  { id: 'sec-ai-advisory', label: 'AI Advisory' },
  { id: 'sec-communication', label: 'Comms' },
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
const { confirm } = useConfirm()
const confirmUid = Math.random().toString(36).slice(2, 9)

const followUpLog = computed(() => activity.value.filter((e) => (e.text || '').startsWith('[Follow-up]')))

// P2.2 dry-run notification preview state
const notificationTemplates = ref([])
const notificationQueue = ref([])
const selectedNotificationTemplate = ref('')
const notificationPreview = ref(null)
const notificationBusy = ref(false)
const showNotificationTemplatePicker = ref(false)

const selectedNotificationTemplateDoc = computed(() => notificationTemplates.value.find(t => t.name === selectedNotificationTemplate.value))

function notificationChannelChip(channel) {
  const color = channel === 'WhatsApp' ? COLORS.success : channel === 'SMS' ? COLORS.primary : channel === 'Internal' ? COLORS.secondary : COLORS.neutral
  return { background: hexToRgba(color, 0.12), color }
}

function notificationStatusChip(status) {
  const map = {
    Queued: COLORS.primary,
    'Approval Pending': COLORS.warning,
    Approved: COLORS.success,
    Skipped: COLORS.neutral,
    Failed: COLORS.error,
    Cancelled: COLORS.neutral,
    Sent: COLORS.success,
  }
  const color = map[status] || COLORS.neutral
  return { background: hexToRgba(color, 0.12), color }
}

async function loadNotificationData() {
  if (!props.ticketId) return
  try {
    const [templates, queue] = await Promise.all([
      call('lavanya_service.api.notifications.get_notification_templates'),
      call('lavanya_service.api.notifications.get_notification_queue', { ticket: props.ticketId }),
    ])
    notificationTemplates.value = templates?.templates || []
    notificationQueue.value = queue?.queue || []
    if (!selectedNotificationTemplate.value && notificationTemplates.value.length) {
      selectedNotificationTemplate.value = notificationTemplates.value[0].name
      await previewNotification()
    }
  } catch (e) {
    notificationTemplates.value = []
    notificationQueue.value = []
  }
}

async function previewNotification() {
  if (!selectedNotificationTemplate.value || !props.ticketId) return
  notificationBusy.value = true
  try {
    notificationPreview.value = await call('lavanya_service.api.notifications.preview_notification', {
      template_name: selectedNotificationTemplate.value,
      ticket: props.ticketId,
    })
  } catch (e) {
    notificationPreview.value = { ok: false, error: e.message || 'Preview failed safely.' }
  } finally {
    notificationBusy.value = false
  }
}

function openNotificationTemplateModal() {
  showNotificationTemplatePicker.value = true
}

async function selectNotificationTemplate(name) {
  selectedNotificationTemplate.value = name
  showNotificationTemplatePicker.value = false
  await previewNotification()
}

async function queueSelectedNotification() {
  if (!selectedNotificationTemplate.value) return
  const ok = await confirm('Queue this notification as dry-run only? No live WhatsApp/SMS will be sent.', 'Queue Notification')
  if (!ok) return
  notificationBusy.value = true
  try {
    const res = await post('lavanya_service.api.notifications.queue_notification', {
      template_name: selectedNotificationTemplate.value,
      ticket: props.ticketId,
    })
    showToast(`Notification ${res.status || 'queued'} (dry-run)`)
    await loadNotificationData()
  } catch (e) {
    showToast(e.message || 'Could not queue notification.', 'error')
  } finally {
    notificationBusy.value = false
  }
}

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
	const map = { Suggested: COLORS.secondary, Accepted: COLORS.success, Ignored: COLORS.neutral, 'Review Needed': COLORS.error }
	const c = map[s] || COLORS.neutral
	return { background: hexToRgba(c, 0.12), color: c }
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
	'Verify Technician Called': { icon: 'phone_in_talk', bg: hexToRgba(COLORS.primary), fg: COLORS.primary },
	'Verify Technician Visit': { icon: 'handyman', bg: hexToRgba(COLORS.secondary), fg: COLORS.secondary },
	'Record SC Follow-up': { icon: 'support_agent', bg: hexToRgba(COLORS.secondary), fg: COLORS.secondary },
	'Inform Customer': { icon: 'campaign', bg: hexToRgba(COLORS.success), fg: COLORS.success },
	'Mark No Update': { icon: 'warning', bg: hexToRgba(COLORS.warning), fg: COLORS.warning },
	'Escalate Case': { icon: 'escalator_warning', bg: hexToRgba(COLORS.error), fg: COLORS.error },
	'Record Satisfaction': { icon: 'sentiment_satisfied', bg: hexToRgba(COLORS.success), fg: COLORS.success },
	'Record Customer Approval': { icon: 'contract', bg: hexToRgba(COLORS.tertiary), fg: COLORS.tertiary },
}
function followupActionStyle(text) {
	for (const [key, style] of Object.entries(FOLLOWUP_ACTION_STYLES)) {
		if (text.includes(key)) return style
	}
	return { icon: 'support_agent', bg: hexToRgba(COLORS.neutral, 0.12), fg: COLORS.neutral }
}
function followupActionIcon(text) { return followupActionStyle(text).icon }
function followupActionBg(text) { return followupActionStyle(text).bg }
function followupActionFg(text) { return followupActionStyle(text).fg }

// Follow-up tracking banner state
const followupBanner = computed(() => {
	const s = ticket.value?.stage || {}
	const _c = (c, a = 0.12) => ({ bg: hexToRgba(c, a), fg: c })
	if (s.customer_satisfaction_status === 'Satisfied' || s.customer_satisfaction_status === 'Not Required')
		return { ..._c(COLORS.success), icon: 'sentiment_satisfied', title: 'Customer Satisfied', sub: 'No further follow-up needed.' }
	if (s.customer_satisfaction_status === 'Not Satisfied')
		return { ..._c(COLORS.error), icon: 'sentiment_dissatisfied', title: 'Customer Not Satisfied', sub: 'Escalate or follow up to resolve concerns.' }
	if (s.escalation_level && s.escalation_level !== 'None')
		return { ..._c(COLORS.error), icon: 'escalator_warning', title: `Escalated — ${s.escalation_level}`, sub: 'Case requires higher-level attention.' }
	if (s.followup_stage === 'no_technician_update')
		return { ..._c(COLORS.warning), icon: 'warning', title: 'No Update from Technician', sub: 'No response from service center — escalation may be needed.' }
	if (s.followup_stage === 'part_pending')
		return { ..._c(COLORS.warning), icon: 'build', title: 'Awaiting Part', sub: s.part_delay_reason || 'Part not yet received.' }
	if (!s.customer_informed_status || s.customer_informed_status === 'Pending')
		return { ..._c(COLORS.warning), icon: 'campaign', title: 'Customer Not Informed', sub: 'Customer needs to be contacted about their service status.' }
	if (s.customer_informed_status === 'Customer Not Reachable')
		return { ..._c(COLORS.error), icon: 'person_off', title: 'Customer Not Reachable', sub: 'Multiple attempts failed — document efforts.' }
	if (s.followup_stage === 'technician_call_pending')
		return { ..._c(COLORS.primary, 0.08), icon: 'phone_in_talk', title: 'Technician Call Pending', sub: 'Verify if technician has called the customer.' }
	if (s.followup_stage === 'technician_visit_pending')
		return { ..._c(COLORS.primary, 0.08), icon: 'handyman', title: 'Technician Visit Pending', sub: 'Verify if technician has visited the customer.' }
	if (s.followup_stage === 'customer_confirmation_pending')
		return { ..._c(COLORS.tertiary), icon: 'how_to_reg', title: 'Awaiting Customer Confirmation', sub: 'Waiting for customer to confirm service completion.' }
	return { ..._c(COLORS.primary, 0.08), icon: 'support_agent', title: 'Follow-up in Progress', sub: 'Ticket is actively being followed up.' }
})

// ── Workflow Timeline Stages ──
const WORKFLOW_STAGES = [
  { key: 'complaint_registered', label: 'Complaint', icon: 'fiber_new', order: 1, check: (s) => true },
  { key: 'brand_registered', label: 'Brand Reg', icon: 'verified', order: 2, check: (s) => !!s.brand_ticket_number },
  { key: 'technician_called', label: 'Tech Called', icon: 'phone_in_talk', order: 3, check: (s) => s.followup_stage === 'technician_called' },
  { key: 'technician_visited', label: 'Tech Visited', icon: 'handyman', order: 4, check: (s) => s.followup_stage === 'technician_visited' },
  { key: 'part_pending', label: 'Part', icon: 'build', order: 5, check: (s) => s.followup_stage === 'part_pending' || s.status === 'Waiting on Part / Approval' },
  { key: 'customer_informed', label: 'Informed', icon: 'campaign', order: 6, check: (s) => s.customer_informed_status && s.customer_informed_status !== 'Pending' },
  { key: 'satisfied', label: 'Satisfied', icon: 'sentiment_satisfied', order: 7, check: (s) => s.customer_satisfaction_status === 'Satisfied' || s.customer_satisfaction_status === 'Not Required' },
  { key: 'closed', label: 'Closed', icon: 'task_alt', order: 8, check: (s) => s.status === 'Closed' || s.status === 'Resolved' },
]

const workflowTimeline = computed(() => {
  const s = ticket.value?.stage || {}
  const ts = ticket.value?.status || ''
  const closed = ts === 'Closed' || ts === 'Resolved'
  let foundCurrent = false
  return WORKFLOW_STAGES.map(stage => {
    const done = stage.check({ ...s, status: ts, closed })
    let status = 'pending'
    if (done && !foundCurrent) {
      status = closed ? 'completed' : 'completed'
      // last completed before a non-completed stage
    }
    if (!done && !foundCurrent && !closed) {
      foundCurrent = true
      status = 'current'
    } else if (!done) {
      status = 'pending'
    }
    return { ...stage, status }
  })
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
		loadNotificationData()
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
  if (def.danger) {
    const ok = await confirm(`Are you sure you want to ${def.submitLabel.toLowerCase()} this ticket?`, 'Confirm Action', true)
    if (!ok) return
  }
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

const qualityLevel = computed(() => ticket.value ? qualityBadge(ticket.value) : '')

const nextActions = computed(() => {
  if (!ticket.value) return { primary: [], secondary: [], danger: [] }
  const s = ticket.value.stage || {}
  const status = ticket.value.status || ''
  const fs = s.followup_stage || ''
  const informed = s.customer_informed_status
  const satisfaction = s.customer_satisfaction_status
  const esc = s.escalation_level

  if (status === 'Closed' || status === 'Cancelled' || status === 'Resolved') {
    return { primary: [], secondary: [], danger: [{ key: 'reopen', label: 'Reopen Ticket', icon: 'restart_alt' }] }
  }

  const primary = []
  const secondary = []
  const danger = []

  // Context-aware action selection
  if (satisfaction === 'Satisfied' || satisfaction === 'Not Required') {
    primary.push({ key: 'close_ticket', label: 'Close Ticket', icon: 'task_alt' })
  } else if (satisfaction === 'Not Satisfied') {
    primary.push({ key: 'record_satisfaction', label: 'Record Satisfaction', icon: 'sentiment_satisfied' })
    danger.push({ key: 'escalate_case', label: 'Escalate', icon: 'escalator_warning' })
  } else if (!satisfaction) {
    if (status === 'Ready for Pickup' || fs === 'customer_satisfied') {
      primary.push({ key: 'record_satisfaction', label: 'Record Satisfaction', icon: 'sentiment_satisfied' })
    }
  }

  if (fs === 'no_technician_update') {
    primary.push({ key: 'record_sc_followup', label: 'Record SC Follow-up', icon: 'support_agent' })
    danger.push({ key: 'escalate_case', label: 'Escalate Case', icon: 'escalator_warning' })
    secondary.push({ key: 'inform_customer', label: 'Inform Customer', icon: 'campaign' })
  }

  if (!informed || informed === 'Pending') {
    if (fs !== 'no_technician_update') {
      primary.push({ key: 'inform_customer', label: 'Inform Customer', icon: 'campaign' })
    }
  }

  if (fs === 'technician_called' || fs === 'technician_visited' || fs === 'sc_followup_done') {
    secondary.push({ key: 'record_sc_followup', label: 'Record SC Follow-up', icon: 'support_agent' })
  }

  if (status === 'Brand Registered') {
    if (!primary.length) primary.push({ key: 'verify_tech_called', label: 'Verify Technician Called', icon: 'phone_in_talk' })
    secondary.push({ key: 'record_sc_followup', label: 'Record SC Follow-up', icon: 'support_agent' })
    if (!informed || informed === 'Pending') secondary.push({ key: 'inform_customer', label: 'Inform Customer', icon: 'campaign' })
  }

  if (status === 'New' || status === 'Open') {
    if (!primary.length) primary.push({ key: 'brand_complaint', label: 'Register Brand Complaint', icon: 'verified' })
  }

  if (status === 'Waiting on Part / Approval' || fs === 'part_pending') {
    primary.push({ key: 'mark_product_ready', label: 'Mark Product Ready', icon: 'hail' })
  }

  if (status === 'Ready for Pickup' && satisfaction !== 'Satisfied' && satisfaction !== 'Not Required') {
    if (!primary.length) primary.push({ key: 'record_satisfaction', label: 'Record Satisfaction', icon: 'sentiment_satisfied' })
  }

  if (s.estimated_amount || s.customer_approved_amount) {
    secondary.push({ key: 'record_approval', label: 'Record Approval', icon: 'contract' })
  }

  // Always-available secondary actions
  if (!secondary.find(a => a.key === 'inform_customer') && (!informed || informed !== 'Informed by Call')) {
    secondary.push({ key: 'inform_customer', label: 'Inform Customer', icon: 'campaign' })
  }

  // Danger actions
  if (!danger.find(a => a.key === 'close_ticket') && status !== 'New') {
    danger.push({ key: 'close_ticket', label: 'Close Ticket', icon: 'task_alt' })
  }

  return { primary, secondary, danger }
})

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
