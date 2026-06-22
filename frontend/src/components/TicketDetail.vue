<template>
  <Transition name="drawer">
    <div v-if="ticketId" class="fixed inset-0 z-50 flex justify-end bg-on-surface/20" @click.self="close">
      <div class="w-full max-w-4xl bg-surface-container-lowest h-full shadow-xl flex flex-col overflow-hidden drawer__panel">
      
      <!-- Main Detail Area -->
      <div class="flex-1 overflow-y-auto border-r border-outline-variant flex flex-col">
        <div v-if="loading" class="p-8 text-center text-on-surface-variant">Loading ticket...</div>
        <div v-else-if="error" class="p-8 text-center text-error">Failed to load ticket.</div>
        <div v-else-if="ticket" class="p-6 md:p-8 flex flex-col gap-8">
          
           <!-- Header -->
           <header class="flex flex-col gap-4 border-b border-outline-variant pb-6">
             <div class="flex items-start justify-between">
               <div>
                 <div class="flex items-center gap-3">
                   <h2 class="font-headline-lg text-headline-lg text-on-surface">{{ ticket.name }}</h2>
                   <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="chip(ticket.status)">{{ ticket.status }}</span>
                   <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="closureGuard.allowed ? { background: 'var(--lav-success)', color: 'white' } : { background: 'var(--lav-danger)', color: 'white' }">
                     {{ closureGuard.allowed ? 'Ready to Close' : 'Closure Blocked' }}
                   </span>
                 </div>
                 <div class="flex flex-wrap gap-x-4 gap-y-1 mt-3 font-body-md text-on-surface-variant">
                   <span>Customer: <span class="font-semibold text-on-surface">{{ ticket.customer?.name || '—' }}</span></span>
                   <span>Mobile: <span class="text-on-surface">{{ ticket.customer?.mobile || '—' }}</span></span>
                   <span>Product: <span class="text-on-surface">{{ ticket.product?.item || '—' }}</span></span>
                   <span>Age: <span class="text-on-surface">{{ ticketAge(ticket.creation) }} days</span></span>
                   <SlaBadge :agreement-status="ticket.sla?.agreement_status" :response-by="ticket.sla?.response_by" :resolution-by="ticket.sla?.resolution_by" />
                 </div>
               </div>
               <button @click="close" class="p-2 rounded hover:bg-surface-container-low" aria-label="Close ticket detail">
                 <span class="material-symbols-outlined" aria-hidden="true">close</span>
               </button>
             </div>
           </header>


            <!-- Do This Now Command Center -->
            <section class="rounded-2xl p-6 mb-8 border-2 border-primary bg-gradient-to-br from-primary-container/40 to-surface-container shadow-sm relative overflow-hidden">
              <!-- Decorative background element -->
              <div class="absolute -right-4 -top-4 w-24 h-24 bg-primary/10 rounded-full blur-2xl"></div>
              
              <div class="flex items-center justify-between mb-4">
                <div class="flex items-center gap-2">
                  <span class="material-symbols-outlined text-primary" style="font-size:28px">bolt</span>
                  <h3 class="font-headline-md text-headline-md text-primary font-bold uppercase tracking-wide">Do This Now</h3>
                </div>
                <span v-if="doThisNow.primaryAction" class="px-2 py-0.5 rounded-full font-label-md text-label-md bg-primary text-on-primary text-xs font-bold uppercase">Priority Action</span>
              </div>

              <div class="mb-6">
                <div class="font-headline-sm text-headline-sm text-on-surface font-bold leading-tight">{{ doThisNow.instruction }}</div>
                <div class="font-body-md text-on-surface-variant mt-2 leading-relaxed">{{ doThisNow.reason }}</div>
              </div>

              <div class="flex flex-wrap gap-3">
                <button v-if="doThisNow.primaryAction" @click="openAction(doThisNow.primaryAction.key)"
                  class="px-6 py-3 rounded-xl font-label-md flex items-center gap-2 bg-primary text-on-primary hover:bg-primary-dark active:scale-[0.97] transition-all shadow-md font-bold">
                  <span class="material-symbols-outlined" style="font-size:20px">{{ doThisNow.primaryAction.icon }}</span>
                  {{ doThisNow.primaryAction.label }}
                </button>
                <button v-if="ticket.customer?.mobile" @click="whatsappCustomer"
                  class="px-6 py-3 rounded-xl font-label-md flex items-center gap-2 bg-surface-container border border-outline-variant text-on-surface hover:bg-surface-container-low active:scale-[0.97] transition-all">
                  <span class="material-symbols-outlined" style="font-size:20px">chat</span> Inform Customer
                </button>
                <button v-if="doThisNow.canReverify" @click="openAction('set_reverification_date')"
                  class="px-6 py-3 rounded-xl font-label-md flex items-center gap-2 bg-surface-container border border-outline-variant text-on-surface hover:bg-surface-container-low active:scale-[0.97] transition-all">
                  <span class="material-symbols-outlined" style="font-size:20px">refresh</span> Set Reverification
                </button>
              </div>
            </section>

            <!-- Action Library — Quick access to all possible workflow moves -->
            <section id="sec-action-library" class="rounded-2xl border border-outline-variant bg-surface-container-lowest p-6 mb-8">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-headline-md text-headline-md text-on-surface font-bold flex items-center gap-2">
                  <span class="material-symbols-outlined text-primary">grid_view</span> Action Library
                </h3>
                <span class="text-label-md text-on-surface-variant italic">Choose a manual workflow move</span>
              </div>
              
              <div class="flex flex-col gap-3">
                <details
                  v-for="g in groupedActions"
                  :key="g.key"
                  open
                  class="rounded-xl border border-outline-variant bg-surface-container/40 overflow-hidden"
                >
                  <summary class="flex items-center gap-2 px-4 py-2.5 cursor-pointer select-none font-label-md font-semibold text-on-surface hover:bg-surface-container-low">
                    <span class="material-symbols-outlined text-primary" style="font-size: 20px">{{ g.icon }}</span>
                    {{ g.label }}
                    <span class="ml-auto text-xs font-label-md text-on-surface-variant px-2 py-0.5 rounded-full bg-surface-container-high">{{ g.items.length }}</span>
                  </summary>
                  <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 p-3 pt-1">
                    <button
                      v-for="item in g.items"
                      :key="item.key"
                      @click="openAction(item.key)"
                      class="flex flex-col items-center justify-center p-3 rounded-xl border border-outline-variant bg-surface-container hover:border-primary hover:bg-primary-container/20 transition-all group active:scale-[0.98]"
                    >
                      <span class="material-symbols-outlined mb-2 text-on-surface-variant group-hover:text-primary transition-colors" style="font-size: 24px">
                        {{ item.def.icon }}
                      </span>
                      <span class="text-xs font-label-md text-center leading-tight text-on-surface-variant group-hover:text-on-surface">
                        {{ item.def.title }}
                      </span>
                    </button>
                  </div>
                </details>
              </div>

              <!-- Special Closure Action (Prominent) -->
              <div v-if="closureGuard.allowed" class="mt-6 pt-6 border-t border-outline-variant flex justify-center">
                <button @click="openAction('close_ticket')" 
                  class="w-full max-w-xs px-6 py-3 bg-error text-on-error rounded-xl font-label-md font-bold flex items-center justify-center gap-2 hover:opacity-90 active:scale-[0.98] transition-all shadow-sm">
                  <span class="material-symbols-outlined" style="font-size: 20px">task_alt</span> Close Ticket
                </button>
              </div>
              <div v-else class="mt-6 pt-6 border-t border-outline-variant flex justify-center">
                <div class="px-4 py-2 rounded-lg bg-error-container text-error border border-error flex items-center gap-2 text-xs font-label-md">
                  <span class="material-symbols-outlined" style="font-size: 16px">lock</span>
                  <span>To close, resolve: {{ closureGuard.reason }}</span>
                </div>
              </div>
            </section>



          <!-- Workflow Timeline — visual stage progression -->
          <LavWorkflowTimeline :ticket="ticket" />

          <!-- Customer Journey Summary Card -->
          <LavCustomerJourneyCard :ticket="ticket" />

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
            <div class="flex items-center gap-2 shrink-0">
              <button @click="openAction('escalate_case')" class="px-3 h-8 rounded-lg bg-warning text-on-warning font-label-md text-label-md hover:opacity-90">Escalate</button>
              <button @click="clearRepeat" class="px-3 h-8 rounded-lg border border-outline-variant text-on-surface-variant font-label-md text-label-md hover:bg-surface-container-low">Clear</button>
            </div>
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
             <h3 class="font-headline-md text-headline-md text-primary mb-3 flex items-center justify-between">
               Service Stage
               <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="{ background: _bg(sectionStatuses['sec-stage'].color), color: sectionStatuses['sec-stage'].color }">
                 {{ sectionStatuses['sec-stage'].label }}
               </span>
             </h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div><span class="block text-label-md text-outline">Service Flow</span> {{ ticket.stage.service_flow_type || '—' }}</div>
              <div><span class="block text-label-md text-outline">Current Service Step</span> {{ ticket.stage.current_service_stage || '—' }}</div>
              <div><span class="block text-label-md text-outline">Recorded Next Action</span> {{ ticket.stage.next_action || '—' }}</div>
              <div><span class="block text-label-md text-outline">Owner</span> {{ ticket.stage.next_action_owner || ticket.stage.next_action_role || '—' }}</div>
              <div><span class="block text-label-md text-outline">Next Follow-up</span> {{ ticket.stage.next_follow_up_date || '—' }}</div>
              <div><span class="block text-label-md text-outline">Stage Due</span> {{ ticket.stage.stage_due_at?.substring(0,16) || '—' }}</div>
              <div>
                <span class="block text-label-md text-outline">Due Status</span>
                <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="dueChip(ticket.stage.overdue_status)">{{ ticket.stage.overdue_status || '—' }}</span>
              </div>
              <div><span class="block text-label-md text-outline">Escalation</span> {{ ticket.stage.escalation_level && ticket.stage.escalation_level !== 'None' ? ticket.stage.escalation_level : '—' }}</div>
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
            <!-- D2/D3: trimmed to the engine's UNIQUE computed projections. The raw
                 Due Status / Escalation / Promise / Next Follow-up / Stage Due /
                 Promised Update live in the Service Stage panel above — not repeated here. -->
            <h3 class="font-headline-md text-headline-md text-primary mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined" style="font-size:20px">smart_toy</span>
              Computed Reminders <span class="font-label-md text-label-md text-outline">(engine — see Service Stage for live values)</span>
            </h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div>
                <span class="block text-label-md text-outline">Customer Update Due</span>
                <span v-if="ticket.reminder.customer_update_due" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="{ color: 'var(--lav-warning)', background: `color-mix(in srgb, var(--lav-warning) 12%, transparent)` }">Due now</span>
                <template v-else>No</template>
              </div>
              <div><span class="block text-label-md text-outline">Reminder Rule</span> {{ ticket.reminder.reminder_rule_applied || 'No rule (fallback)' }}</div>
              <div><span class="block text-label-md text-outline">Due Soon At</span> {{ fmtDT(ticket.reminder.computed_due_soon_at) }}</div>
              <div v-if="reminderShowComputed"><span class="block text-label-md text-outline">Computed Follow-up</span> {{ fmtDT(ticket.reminder.computed_next_followup_at) }}</div>
              <div v-if="ticket.reminder.promise_breach_reason" class="col-span-2">
                <span class="block text-label-md text-outline">Promise Breach Reason</span>
                <span :style="{ color: 'var(--lav-danger)' }">{{ ticket.reminder.promise_breach_reason }}</span>
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
                <span class="block text-label-md text-outline">AI Suggestion (advisory — see “Do This Now” for the action to take)</span>
                <p class="font-body-md text-on-surface mt-0.5">{{ ticket.ai.suggested_next_action }}</p>
              </div>
              <div v-if="ticket.ai.risk_reason">
                <span class="block text-label-md text-outline">Risk Reason</span>
                <p class="font-body-md text-on-surface mt-0.5" :style="{ color: 'var(--lav-danger)' }">{{ ticket.ai.risk_reason }}</p>
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
             <h3 class="font-headline-md text-headline-md text-primary mb-4 flex items-center justify-between">
               <span class="flex items-center gap-2">
                 <span class="material-symbols-outlined" style="font-size:22px">support_agent</span>
                 Follow-up Tracking
               </span>
               <div class="flex gap-2">
                 <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="{ background: _bg(sectionStatuses['sec-followup-tracking'].color), color: sectionStatuses['sec-followup-tracking'].color }">
                   {{ sectionStatuses['sec-followup-tracking'].label }}
                 </span>
                 <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="{ background: _bg(sectionStatuses['sec-verification'].color), color: sectionStatuses['sec-verification'].color }">
                   {{ sectionStatuses['sec-verification'].label }}
                 </span>
               </div>
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
              <div v-if="ticket.stage.part_required" class="rounded-xl p-4 bg-surface-container" :style="{ borderLeft: '4px solid var(--lav-warning)' }">
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
              <div v-if="ticket.stage.estimated_amount || ticket.stage.customer_approved_amount || (ticket.stage.payment_status && ticket.stage.payment_status !== 'Not Applicable')" class="rounded-xl p-4 bg-surface-container" :style="{ borderLeft: '4px solid var(--lav-success)' }">
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
             <h3 class="font-headline-md text-headline-md text-primary mb-3 flex items-center justify-between">
               Customer
               <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="{ background: _bg(sectionStatuses['sec-customer'].color), color: sectionStatuses['sec-customer'].color }">
                 {{ sectionStatuses['sec-customer'].label }}
               </span>
             </h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div><span class="block text-label-md text-outline">Name</span> {{ ticket.customer?.name || '—' }}</div>
              <div><span class="block text-label-md text-outline">Mobile</span> {{ ticket.customer?.mobile || '—' }}</div>
              <div class="col-span-2"><span class="block text-label-md text-outline">Address</span> {{ ticket.customer?.address || '—' }}</div>
              <div><span class="block text-label-md text-outline">Pincode</span> {{ ticket.customer?.pincode || '—' }}</div>
            </div>
            <div class="mt-2">
              <router-link v-if="ticket.customer?.mobile" :to="'/customer-360?mobile=' + ticket.customer.mobile" class="text-primary hover:underline font-label-md text-body-md flex items-center gap-1">
                <span class="material-symbols-outlined" style="font-size:16px">person_search</span>
                View Customer 360
              </router-link>
            </div>
          </section>

          <!-- Product Summary -->
           <section id="sec-product">
             <h3 class="font-headline-md text-headline-md text-primary mb-3 flex items-center justify-between">
               Product
               <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="{ background: _bg(sectionStatuses['sec-product'].color), color: sectionStatuses['sec-product'].color }">
                 {{ sectionStatuses['sec-product'].label }}
               </span>
             </h3>
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

          <!-- H6B: CRM Relationship Card -->
          <section id="sec-crm" v-if="ticket.crm_relationship?.available || ticket.crm_relationship?.warnings?.length">
            <h3 class="font-headline-md text-headline-md text-primary mb-3 flex items-center gap-2">
              <span class="material-symbols-outlined" style="font-size:22px">handshake</span>
              CRM Relationship
            </h3>
            <!-- CRM disabled/unavailable banner -->
            <div v-if="!ticket.crm_relationship.enabled" class="rounded-xl p-4 bg-surface-container border border-outline-variant">
              <div class="flex items-center gap-2 text-on-surface-variant font-body-md">
                <span class="material-symbols-outlined" style="font-size:20px">info</span>
                {{ ticket.crm_relationship.warnings?.[0] || 'CRM integration is disabled.' }}
              </div>
            </div>
            <!-- CRM active card -->
            <div v-else class="rounded-xl bg-surface-container border border-outline-variant p-4">
              <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 font-body-md text-on-surface-variant mb-3">
                <div>
                  <span class="block text-label-md text-outline">Contact</span>
                  <span class="text-on-surface font-semibold">{{ ticket.crm_relationship.contact_linked ? ticket.crm_relationship.contact_name : 'Not linked' }}</span>
                </div>
                <div>
                  <span class="block text-label-md text-outline">Organization</span>
                  <span class="text-on-surface font-semibold">{{ ticket.crm_relationship.organization || '—' }}</span>
                </div>
                <div>
                  <span class="block text-label-md text-outline">Open Deals</span>
                  <span class="text-on-surface font-semibold" :class="ticket.crm_relationship.open_deals > 0 ? 'text-primary' : ''">{{ ticket.crm_relationship.open_deals || 0 }}</span>
                </div>
              </div>
              <!-- Indicators -->
              <div class="flex flex-wrap gap-2">
                <span v-if="ticket.crm_relationship.service_to_sales_opportunity" class="px-2.5 py-0.5 rounded-full font-label-md text-label-md inline-flex items-center gap-1" :style="{ background: 'color-mix(in srgb, var(--lav-secondary) 12%, transparent)', color: 'var(--lav-secondary)' }">
                  <span class="material-symbols-outlined" style="font-size:14px">lightbulb</span> Sales opportunity
                </span>
                <span v-if="ticket.crm_relationship.service_risk" class="px-2.5 py-0.5 rounded-full font-label-md text-label-md inline-flex items-center gap-1" :style="{ background: 'color-mix(in srgb, var(--lav-danger) 12%, transparent)', color: 'var(--lav-danger)' }">
                  <span class="material-symbols-outlined" style="font-size:14px">warning</span> Service risk
                </span>
              </div>
              <div class="mt-3 pt-3 border-t border-outline-variant flex items-center gap-2">
                <span class="font-label-md text-label-md text-on-surface-variant">Mode: {{ ticket.crm_relationship.mode }}</span>
                <span class="text-on-surface-variant">·</span>
                <button disabled class="px-3 py-1 rounded-lg border border-outline-variant text-on-surface-variant font-label-md text-label-md cursor-not-allowed" title="CRM record creation is disabled for safety">Create Opportunity (future)</button>
              </div>
            </div>
          </section>

          <!-- UX-R1: Collapsible lower-priority sections -->
          <div class="mb-3">
            <button @click="showDetails = !showDetails" class="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-outline-variant text-on-surface-variant font-label-md hover:bg-surface-container-low transition-colors">
              <span class="material-symbols-outlined" style="font-size:18px">{{ showDetails ? 'expand_less' : 'expand_more' }}</span>
              {{ showDetails ? 'Hide details' : 'Show more (brand info, CRM, records, technician, appointment, proof)' }}
            </button>
          </div>

          <section id="sec-customer-products" v-if="ticket.customer_products?.length">
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Customer Products ({{ ticket.customer_products.length }})</h3>
            <div class="flex flex-col gap-3">
              <div v-for="cp in ticket.customer_products" :key="cp.name" class="rounded-xl p-4 bg-surface-container border border-outline-variant">
                <div class="flex items-start justify-between gap-3 mb-2">
                  <div class="font-body-md font-semibold text-on-surface">{{ cp.brand }} {{ cp.product_type }} · {{ cp.model_no || '—' }}</div>
                  <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md shrink-0" :style="chip(cp.warranty_status)">{{ cp.warranty_status }}</span>
                </div>
                <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 font-label-md text-label-md text-on-surface-variant">
                  <div>S/N: <span class="text-on-surface">{{ cp.serial_no || '—' }}</span></div>
                  <div>Purchase: <span class="text-on-surface">{{ cp.purchase_date || '—' }}</span></div>
                  <div>Warranty: <span class="text-on-surface">{{ cp.warranty_end_date || '—' }}</span></div>
                  <div>Invoice: <span class="text-on-surface">{{ cp.invoice_number || '—' }}</span></div>
                </div>
                <div v-if="cp.ticket_count > 1" class="mt-2 flex items-center gap-2">
                  <span class="material-symbols-outlined text-warning" style="font-size:16px">repeat</span>
                  <span class="font-label-md text-label-md text-on-surface-variant">{{ cp.ticket_count }} service tickets for this product</span>
                </div>
              </div>
            </div>
          </section>

          <template v-if="showDetails">

          <!-- H5B: Brand Info Card -->
          <section id="sec-brand-info" v-if="ticket.brand_info?.name">
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Brand Info</h3>
            <div class="rounded-xl p-4 bg-surface-container border border-outline-variant">
              <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 font-body-md text-on-surface-variant">
                <div>
                  <span class="block text-label-md text-outline">Toll-free</span>
                  <span class="text-on-surface font-semibold">{{ ticket.brand_info.toll_free || '—' }}</span>
                </div>
                <div>
                  <span class="block text-label-md text-outline">Default SLA</span>
                  <span class="text-on-surface font-semibold">{{ ticket.brand_info.default_sla_hours }}h</span>
                </div>
                <div>
                  <span class="block text-label-md text-outline">Registration Channel</span>
                  <span class="text-on-surface font-semibold">{{ ticket.brand_info.registration_channel || '—' }}</span>
                </div>
                <div>
                  <span class="block text-label-md text-outline">Free Service</span>
                  <span class="text-on-surface font-semibold">{{ ticket.brand_info.free_service_supported ? 'Supported' : 'Not available' }}</span>
                </div>
              </div>
              <div v-if="ticket.brand_info.portal_url" class="mt-3 pt-3 border-t border-outline-variant">
                <a :href="ticket.brand_info.portal_url" target="_blank" class="text-primary hover:underline font-label-md flex items-center gap-1">
                  <span class="material-symbols-outlined" style="font-size:16px">open_in_new</span>
                  Brand Portal
                </a>
              </div>
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
              <!-- H5C: custody closure guard -->
              <div v-if="ticket.receipt?.number" class="col-span-2 mt-2 pt-2 border-t border-outline-variant">
                <span class="block text-label-md text-outline mb-1">Custody Closure Guard</span>
                <span class="font-body-md" :class="custodyGuard.allowed ? 'text-success' : 'text-warning'">{{ custodyGuard.reason }}</span>
              </div>
            </div>
          </section>

          <!-- H5E: Linked Service Records -->
          <section id="sec-linked-records" v-if="hasLinkedRecords">
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Service Records</h3>
            <div class="flex flex-col gap-3">
              <!-- Replacement Record -->
              <div v-if="ticket.linked_records?.replacement?.length" v-for="rec in ticket.linked_records.replacement" :key="rec.name"
                   class="rounded-xl p-4 bg-surface-container border" :style="{ borderLeft: '4px solid var(--lav-secondary)' }">
                <div class="flex items-center gap-2 mb-2">
                  <span class="material-symbols-outlined text-secondary">swap_horiz</span>
                  <span class="font-label-lg text-on-surface font-semibold">Replacement Record</span>
                  <span class="ml-auto font-label-md text-primary">{{ rec.name }}</span>
                </div>
                <div class="grid grid-cols-2 gap-2 font-label-md text-on-surface-variant">
                  <div>Status: <span class="text-on-surface">{{ rec.status || '—' }}</span></div>
                  <div>Old S/N: <span class="text-on-surface">{{ rec.old_serial_no || '—' }}</span></div>
                  <div>New S/N: <span class="text-on-surface">{{ rec.new_serial_no || '—' }}</span></div>
                  <div>Collected: <span class="text-on-surface">{{ rec.old_unit_collected_at?.substring(0,16) || '—' }}</span></div>
                </div>
              </div>
              <!-- Return Record -->
              <div v-if="ticket.linked_records?.return_service?.length" v-for="rec in ticket.linked_records.return_service" :key="rec.name"
                   class="rounded-xl p-4 bg-surface-container border" :style="{ borderLeft: '4px solid var(--lav-warning)' }">
                <div class="flex items-center gap-2 mb-2">
                  <span class="material-symbols-outlined text-warning">keyboard_return</span>
                  <span class="font-label-lg text-on-surface font-semibold">Return Record</span>
                  <span class="ml-auto font-label-md text-primary">{{ rec.name }}</span>
                </div>
                <div class="grid grid-cols-2 gap-2 font-label-md text-on-surface-variant">
                  <div>Refund: <span class="text-on-surface">{{ rec.refund_status || '—' }}</span></div>
                  <div>Reason: <span class="text-on-surface">{{ rec.return_reason || '—' }}</span></div>
                  <div>Requested: <span class="text-on-surface">{{ rec.return_requested_at?.substring(0,10) || '—' }}</span></div>
                </div>
              </div>
              <!-- Stock Complaint Record -->
              <div v-if="ticket.linked_records?.stock_complaint?.length" v-for="rec in ticket.linked_records.stock_complaint" :key="rec.name"
                   class="rounded-xl p-4 bg-surface-container border" :style="{ borderLeft: '4px solid var(--lav-danger)' }">
                <div class="flex items-center gap-2 mb-2">
                  <span class="material-symbols-outlined text-danger">inventory_2</span>
                  <span class="font-label-lg text-on-surface font-semibold">Stock Complaint</span>
                  <span class="ml-auto font-label-md text-primary">{{ rec.name }}</span>
                </div>
                <div class="grid grid-cols-2 gap-2 font-label-md text-on-surface-variant">
                  <div>Supplier: <span class="text-on-surface">{{ rec.supplier || '—' }}</span></div>
                  <div>Notified: <span class="text-on-surface">{{ rec.supplier_notified_at?.substring(0,10) || '—' }}</span></div>
                  <div>Credit Note: <span class="text-on-surface">{{ rec.credit_note_received_at?.substring(0,10) || '—' }}</span></div>
                </div>
              </div>
              <!-- Store Service Record -->
              <div v-if="ticket.linked_records?.store_service?.length" v-for="rec in ticket.linked_records.store_service" :key="rec.name"
                   class="rounded-xl p-4 bg-surface-container border" :style="{ borderLeft: '4px solid var(--lav-primary)' }">
                <div class="flex items-center gap-2 mb-2">
                  <span class="material-symbols-outlined text-primary">store</span>
                  <span class="font-label-lg text-on-surface font-semibold">Store Service</span>
                  <span class="ml-auto font-label-md text-primary">{{ rec.name }}</span>
                </div>
                <div class="grid grid-cols-2 gap-2 font-label-md text-on-surface-variant">
                  <div>Diagnosis: <span class="text-on-surface">{{ rec.diagnosis || '—' }}</span></div>
                  <div>Handed Over: <span class="text-on-surface">{{ rec.product_handed_over_at?.substring(0,16) || '—' }}</span></div>
                  <div>Collected: <span class="text-on-surface">{{ rec.customer_collected_at?.substring(0,16) || '—' }}</span></div>
                </div>
              </div>
              <!-- Communication Log -->
              <div v-if="ticket.linked_records?.communication_log?.length">
                <div class="font-label-md text-label-md text-on-surface-variant mb-2">Communication Log ({{ ticket.linked_records.communication_log.length }})</div>
                <div v-for="entry in ticket.linked_records.communication_log" :key="entry.name"
                     class="flex items-center gap-3 p-3 rounded-lg bg-surface-container-lowest border border-outline-variant">
                  <span class="material-symbols-outlined text-on-surface-variant" style="font-size:20px">
                    {{ entry.communication_type === 'Call' ? 'phone_in_talk' : entry.communication_type === 'WhatsApp' ? 'chat' : entry.communication_type === 'SMS' ? 'sms' : 'mail' }}
                  </span>
                  <div class="flex-1 min-w-0">
                    <div class="font-body-md text-on-surface">{{ entry.summary || '(no summary)' }}</div>
                    <div class="font-label-md text-on-surface-variant">
                      {{ entry.communication_type }} · {{ entry.direction || 'Outbound' }}
                      <template v-if="entry.agent"> · {{ entry.agent }}</template>
                      <template v-if="entry.communication_date"> · {{ entry.communication_date?.substring(0,16) }}</template>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- H5C: Technician Assignment -->
          <section id="sec-technician" v-if="ticket.technicians?.length || ticket.stage?.service_charge_type">
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Technician Assignment</h3>
            <div v-if="ticket.technicians?.length" class="rounded-xl border border-outline-variant bg-surface-container p-4 mb-3">
              <div class="font-label-md text-label-md text-on-surface-variant mb-2">Matching technicians ({{ ticket.technicians.length }})</div>
              <div class="flex flex-col gap-2">
                <div v-for="tech in ticket.technicians.slice(0,5)" :key="tech.name" class="flex items-center justify-between gap-3 p-3 rounded-lg bg-surface-container-lowest border border-outline-variant">
                  <div class="flex-1 min-w-0">
                    <div class="font-body-md font-semibold text-on-surface truncate">{{ tech.technician_name }}</div>
                    <div class="font-label-md text-label-md text-on-surface-variant">
                      {{ tech.phone || 'No phone' }}
                      <template v-if="tech.skills"> · {{ tech.skills }}</template>
                      <template v-if="tech.area"> · {{ tech.area }}</template>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 shrink-0">
                    <span v-if="tech.rating" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="{ background: 'color-mix(in srgb, var(--lav-success) 12%, transparent)', color: 'var(--lav-success)' }">⭐ {{ tech.rating }}</span>
                    <button type="button" @click="assignTechnician(tech)" class="px-3 py-1.5 rounded-lg bg-primary text-on-primary font-label-md text-label-md hover:opacity-90">Assign</button>
                    <a v-if="tech.phone" :href="'tel:' + tech.phone" class="px-3 py-1.5 rounded-lg border border-outline-variant text-primary font-label-md text-label-md hover:bg-surface-container-low">Call</a>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="rounded-xl bg-surface-container p-4 text-on-surface-variant font-body-md">
              No matching technicians found for {{ ticket.product?.type || 'this product type' }}. Assign manually or check area coverage.
            </div>
          </section>

          <!-- H5C: Appointment Flow -->
           <section id="sec-appointment">
             <h3 class="font-headline-md text-headline-md text-primary mb-3 flex items-center justify-between">
               <span class="material-symbols-outlined" style="font-size:22px">event</span>
               Appointment
               <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="{ background: _bg(sectionStatuses['sec-appointment'].color), color: sectionStatuses['sec-appointment'].color }">
                 {{ sectionStatuses['sec-appointment'].label }}
               </span>
              </h3>
             <div v-if="ticket.appointment" class="rounded-xl border border-outline-variant bg-surface-container p-4 mb-3">
              <div class="grid grid-cols-2 gap-3 font-body-md text-on-surface-variant">
                <div>
                  <span class="block text-label-md text-outline">Date/Time</span>
                  <span class="text-on-surface font-semibold">{{ ticket.appointment.appointment_datetime?.substring(0,16) || '—' }}</span>
                </div>
                <div>
                  <span class="block text-label-md text-outline">Technician</span>
                  <span class="text-on-surface font-semibold">{{ ticket.appointment.technician || '—' }}</span>
                </div>
                <div v-if="ticket.appointment.status">
                  <span class="block text-label-md text-outline">Status</span>
                  <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="appointmentStatusChip(ticket.appointment.status)">{{ ticket.appointment.status }}</span>
                </div>
              </div>
              <div class="flex flex-wrap gap-2 mt-3 pt-3 border-t border-outline-variant">
                <button @click="openAction('schedule_appointment')" class="px-3 py-1.5 rounded-lg bg-primary text-on-primary font-label-md text-label-md hover:opacity-90">Schedule</button>
                <button @click="openAction('schedule_appointment')" class="px-3 py-1.5 rounded-lg border border-outline-variant text-on-surface-variant font-label-md text-label-md hover:bg-surface-container-low">Reschedule</button>
                <span class="text-label-md text-on-surface-variant self-center">· Visit actions in quick panel →</span>
              </div>
            </div>
            <div v-else class="rounded-xl bg-surface-container p-4 text-on-surface-variant font-body-md flex items-center justify-between">
              <span>No appointment scheduled.</span>
              <button @click="openAction('schedule_appointment')" class="px-4 py-2 rounded-lg bg-primary text-on-primary font-label-md hover:opacity-90">Schedule Appointment</button>
            </div>
          </section>

          <!-- H5C: Proof / Attachment Categories -->
          <section id="sec-proof" class="rounded-xl border border-outline-variant bg-surface-container-lowest p-4">
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Proof Categories</h3>
            <p class="font-body-md text-on-surface-variant mb-3">Required proof documents by service context. Upload not yet available — reference for staff verification.</p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <div v-for="cat in proofCategories" :key="cat.label" class="flex items-center gap-2 p-2 rounded-lg bg-surface-container">
                <span class="material-symbols-outlined text-on-surface-variant" style="font-size:18px">{{ cat.icon }}</span>
                <div>
                  <div class="font-label-md text-on-surface">{{ cat.label }}</div>
                  <div class="font-label-md text-label-md text-on-surface-variant">{{ cat.context }}</div>
                </div>
              </div>
            </div>
          </section>
          </template>

          <!-- Follow-up history (structured, from tagged log entries) -->
          <!-- Duplicate follow-up timeline removed (Task 9). LavWorkflowTimeline shows log-driven status progression. -->

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
import { chip, dueChip, promiseChip, escChip, stageChip, satisfactionChip, informedChip, fmtDT, ticketAge, relTime, qualityBadge, friendlyLabel } from '@/utils'
import { useToast } from '@/utils/toast'
import { useConfirm } from '@/utils/confirm'
import LavConfirm from '@/components/LavConfirm.vue'
import { resolveActions as resolveEngineActions, ACTION_REGISTRY as ENGINE_REGISTRY, canCloseTicket as engineCanClose } from '@/config/outcome-map.js'

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
const showDetails = ref(false)  // UX-R1: collapsible sections toggle

// Repeat-complaint detection / linking
const repeatCandidates = ref([])

const isClosed = computed(() => ['Closed', 'Cancelled', 'Resolved'].includes(ticket.value?.status))

const doThisNow = computed(() => {
  const s = ticket.value?.stage || {}
  const t = ticket.value || {}
  return {
    instruction: s.next_action || t.next_action || 'Review ticket details',
    reason: s.pending_reason || t.pending_reason || 'Routine follow-up required to ensure service progression.',
    primaryAction: (nextActions.value?.primary || [])[0] || null,
    canReverify: s.followup_stage === 'customer_confirmation_pending' || s.current_service_stage?.includes('Verification'),
  }
})

const sectionStatuses = computed(() => {
  const s = ticket.value?.stage || {}
  const p = ticket.value?.product || {}
  const c = ticket.value?.customer || {}
  const a = ticket.value?.appointment || {}
  const today = new Date().toISOString().split('T')[0]

  return {
    'sec-customer': {
      label: (c.name && c.mobile) ? 'Complete' : 'Missing Info',
      color: (c.name && c.mobile) ? 'var(--lav-success)' : 'var(--lav-warning)',
    },
    'sec-product': {
      label: (p.brand && p.serial_no) ? 'Complete' : 'Missing Info',
      color: (p.brand && p.serial_no) ? 'var(--lav-success)' : 'var(--lav-warning)',
    },
    'sec-stage': {
      label: s.manufacturer_registered === 'Yes' ? 'Done' : 'Pending',
      color: s.manufacturer_registered === 'Yes' ? 'var(--lav-success)' : 'var(--lav-primary)',
    },
    'sec-appointment': {
      label: s.followup_stage === 'no_technician_update' ? 'Missed' : a.appointment_datetime ? 'Scheduled' : a.status === 'Visited' ? 'Visited' : 'Not Scheduled',
      color: s.followup_stage === 'no_technician_update' ? 'var(--lav-danger)' : a.appointment_datetime ? 'var(--lav-primary)' : a.status === 'Visited' ? 'var(--lav-success)' : 'var(--lav-muted)',
    },
    'sec-followup-tracking': {
      label: s.part_required === 'Yes' ? (s.part_expected_date && s.part_expected_date < today ? 'ETA Overdue' : 'Part Pending') : 'Not Required',
      color: s.part_required === 'Yes' ? (s.part_expected_date && s.part_expected_date < today ? 'var(--lav-danger)' : 'var(--lav-warning)') : 'var(--lav-success)',
    },
    'sec-verification': {
      label: s.customer_satisfaction_status === 'Satisfied' ? 'Done' : s.customer_satisfaction_status === 'Not Satisfied' ? 'Blocked' : s.followup_stage === 'customer_confirmation_pending' ? 'Due' : 'Pending',
      color: s.customer_satisfaction_status === 'Satisfied' ? 'var(--lav-success)' : s.customer_satisfaction_status === 'Not Satisfied' ? 'var(--lav-danger)' : s.followup_stage === 'customer_confirmation_pending' ? 'var(--lav-warning)' : 'var(--lav-muted)',
    },
    'sec-actions': {
      label: closureGuard.value.allowed ? 'Ready' : 'Blocked',
      color: closureGuard.value.allowed ? 'var(--lav-success)' : 'var(--lav-danger)',
    },
  }
})

const closureGuard = computed(() => {
  if (isClosed.value) return { allowed: true, reason: 'Ticket is already closed or resolved.' }
  return engineCanClose(ticket.value)
})

// H5C: custody closure guard — prevents closure if product is not returned/collected
const custodyGuard = computed(() => {
  const r = ticket.value?.receipt || {}
  if (!r.number) return { allowed: true, reason: 'No product in custody.' }
  const status = r.custody_status || ''
  if (!status || status === 'Ready for Customer Pickup') return { allowed: true, reason: `${status || 'Ready for pickup'}. Can close after handover.` }
  if (status.includes('Sent') || status.includes('Returned from SC')) return { allowed: false, reason: `Product at ${status}. Complete custody chain before closure.` }
  return { allowed: true, reason: `${status}.` }
})

// H5C: appointment status chip
function appointmentStatusChip(status) {
  const map = {
    Scheduled: 'var(--lav-primary)',
    Confirmed: 'var(--lav-success)',
    Rescheduled: 'var(--lav-warning)',
    Visited: 'var(--lav-success)',
    Missed: 'var(--lav-danger)',
    Cancelled: 'var(--lav-muted)',
  }
  const color = map[status] || 'var(--lav-muted)'
  return { background: _bg(color), color }
}

// H5C: assign technician from master data
function assignTechnician(tech) {
  showToast(`Technician ${tech.technician_name} selected. Open Schedule Appointment to set a date.`)
  // Technician assignment is set via the schedule_appointment action modal
  openAction('schedule_appointment')
}

// H5C: proof categories (read-only reference for staff)
const proofCategories = [
  { label: 'Invoice Copy', icon: 'receipt_long', context: 'All service types' },
  { label: 'Warranty Card', icon: 'verified', context: 'Warranty claims' },
  { label: 'Product / Serial Photo', icon: 'photo_camera', context: 'All service types' },
  { label: 'Brand Ticket Screenshot', icon: 'screenshot', context: 'Brand warranty' },
  { label: 'Service Center Job Sheet', icon: 'assignment', context: 'Product at store' },
  { label: 'Technician Visit Proof', icon: 'handyman', context: 'Technician visits' },
  { label: 'Customer Approval Proof', icon: 'how_to_reg', context: 'Estimates / paid service' },
  { label: 'Payment Receipt', icon: 'payments', context: 'Paid / local service' },
  { label: 'Closure Confirmation', icon: 'task_alt', context: 'All closed tickets' },
  { label: 'Returned Product Photo', icon: 'inventory_2', context: 'Return / replacement' },
  { label: 'Showroom Receipt', icon: 'store', context: 'Product at store' },
  { label: 'WhatsApp Screenshot Import', icon: 'chat', context: 'Customer communication' },
]

// H5E: linked service records summary
const hasLinkedRecords = computed(() => {
  const r = ticket.value?.linked_records || {}
  return Object.values(r).some(arr => (arr || []).length > 0)
})

const SECTIONS = [
  { id: 'sec-stage', label: 'Stage' },
  { id: 'sec-reminder', label: 'Reminder' },
  { id: 'sec-ai-advisory', label: 'AI Advisory' },
  { id: 'sec-communication', label: 'Comms' },
  { id: 'sec-followup-tracking', label: 'Tracking' },
  { id: 'sec-customer', label: 'Customer' },
  { id: 'sec-product', label: 'Product' },
  { id: 'sec-customer-products', label: 'History' },
  { id: 'sec-brand-info', label: 'Brand' },
  { id: 'sec-crm', label: 'CRM' },
  { id: 'sec-workflow', label: 'Workflow' },
  { id: 'sec-receipt', label: 'Custody' },
  { id: 'sec-technician', label: 'Technician' },
  { id: 'sec-appointment', label: 'Appointment' },
  { id: 'sec-linked-records', label: 'Records' },
  { id: 'sec-proof', label: 'Proof' },
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

// CSS-var-safe background tint helper (replaces hexToRgba for theme responsiveness)
function _bg(colorVar, alpha = 0.12) {
  return `color-mix(in srgb, ${colorVar} ${Math.round(alpha * 100)}%, transparent)`
}

function notificationChannelChip(channel) {
  const color = channel === 'WhatsApp' ? 'var(--lav-success)' : channel === 'SMS' ? 'var(--lav-primary)' : channel === 'Internal' ? 'var(--lav-secondary)' : 'var(--lav-muted)'
  return { background: _bg(color), color }
}

function notificationStatusChip(status) {
  const map = {
    Queued: 'var(--lav-primary)',
    'Approval Pending': 'var(--lav-warning)',
    Approved: 'var(--lav-success)',
    Skipped: 'var(--lav-muted)',
    Failed: 'var(--lav-danger)',
    Cancelled: 'var(--lav-muted)',
    Sent: 'var(--lav-success)',
  }
  const color = map[status] || 'var(--lav-muted)'
  return { background: _bg(color), color }
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
	const map = { Suggested: 'var(--lav-secondary)', Accepted: 'var(--lav-success)', Ignored: 'var(--lav-muted)', 'Review Needed': 'var(--lav-danger)' }
	const c = map[s] || 'var(--lav-muted)'
	return { background: _bg(c), color: c }
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
	'Verify Technician Called': { icon: 'phone_in_talk', bg: _bg('var(--lav-primary)'), fg: 'var(--lav-primary)' },
	'Verify Technician Visit': { icon: 'handyman', bg: _bg('var(--lav-secondary)'), fg: 'var(--lav-secondary)' },
	'Record SC Follow-up': { icon: 'support_agent', bg: _bg('var(--lav-secondary)'), fg: 'var(--lav-secondary)' },
	'Inform Customer': { icon: 'campaign', bg: _bg('var(--lav-success)'), fg: 'var(--lav-success)' },
	'Mark No Update': { icon: 'warning', bg: _bg('var(--lav-warning)'), fg: 'var(--lav-warning)' },
	'Escalate Case': { icon: 'escalator_warning', bg: _bg('var(--lav-danger)'), fg: 'var(--lav-danger)' },
	'Record Satisfaction': { icon: 'sentiment_satisfied', bg: _bg('var(--lav-success)'), fg: 'var(--lav-success)' },
	'Record Customer Approval': { icon: 'contract', bg: _bg('var(--lav-tertiary)'), fg: 'var(--lav-tertiary)' },
}
function followupActionStyle(text) {
	for (const [key, style] of Object.entries(FOLLOWUP_ACTION_STYLES)) {
		if (text.includes(key)) return style
	}
	return { icon: 'support_agent', bg: _bg('var(--lav-muted)', 0.12), fg: 'var(--lav-muted)' }
}
function followupActionIcon(text) { return followupActionStyle(text).icon }
function followupActionBg(text) { return followupActionStyle(text).bg }
function followupActionFg(text) { return followupActionStyle(text).fg }

// Follow-up tracking banner state
const followupBanner = computed(() => {
	const s = ticket.value?.stage || {}
	const _c = (colorVar, a = 0.12) => ({ bg: _bg(colorVar, a), fg: colorVar })
	if (s.customer_satisfaction_status === 'Satisfied' || s.customer_satisfaction_status === 'Not Required')
		return { ..._c('var(--lav-success)'), icon: 'sentiment_satisfied', title: 'Customer Satisfied', sub: 'No further follow-up needed.' }
	if (s.customer_satisfaction_status === 'Not Satisfied')
		return { ..._c('var(--lav-danger)'), icon: 'sentiment_dissatisfied', title: 'Customer Not Satisfied', sub: 'Escalate or follow up to resolve concerns.' }
	if (s.escalation_level && s.escalation_level !== 'None')
		return { ..._c('var(--lav-danger)'), icon: 'escalator_warning', title: `Escalated — ${s.escalation_level}`, sub: 'Case requires higher-level attention.' }
	if (s.followup_stage === 'no_technician_update')
		return { ..._c('var(--lav-warning)'), icon: 'warning', title: 'No Update from Technician', sub: 'No response from service center — escalation may be needed.' }
	if (s.followup_stage === 'part_pending')
		return { ..._c('var(--lav-warning)'), icon: 'build', title: 'Awaiting Part', sub: s.part_delay_reason || 'Part not yet received.' }
	if (!s.customer_informed_status || s.customer_informed_status === 'Pending')
		return { ..._c('var(--lav-warning)'), icon: 'campaign', title: 'Customer Not Informed', sub: 'Customer needs to be contacted about their service status.' }
	if (s.customer_informed_status === 'Customer Not Reachable')
		return { ..._c('var(--lav-danger)'), icon: 'person_off', title: 'Customer Not Reachable', sub: 'Multiple attempts failed — document efforts.' }
	if (s.followup_stage === 'technician_call_pending')
		return { ..._c('var(--lav-primary)', 0.08), icon: 'phone_in_talk', title: 'Technician Call Pending', sub: 'Verify if technician has called the customer.' }
	if (s.followup_stage === 'technician_visit_pending')
		return { ..._c('var(--lav-primary)', 0.08), icon: 'handyman', title: 'Technician Visit Pending', sub: 'Verify if technician has visited the customer.' }
	if (s.followup_stage === 'customer_confirmation_pending')
		return { ..._c('var(--lav-tertiary)'), icon: 'how_to_reg', title: 'Awaiting Customer Confirmation', sub: 'Waiting for customer to confirm service completion.' }
	return { ..._c('var(--lav-primary)', 0.08), icon: 'support_agent', title: 'Follow-up in Progress', sub: 'Ticket is actively being followed up.' }
})

// Task 9: the manual WORKFLOW_STAGES / workflowTimeline computed was dead code —
// the visual timeline is now rendered solely by the log-driven <LavWorkflowTimeline>
// component (see template). Removed to eliminate the duplicate timeline source.

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
  // P0: Appointment handlers
  confirm_appointment: {
    title: 'Confirm Appointment', icon: 'event_available', submitLabel: 'Confirm',
    endpoint: 'lavanya_service.api.workflow_actions.confirm_appointment',
    fields: [
      { key: 'appointment_datetime', label: 'Date & Time', type: 'datetime-local', required: false },
      { key: 'technician', label: 'Technician', type: 'text', required: false },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  mark_appointment_missed: {
    title: 'Mark Appointment Missed', icon: 'event_busy', submitLabel: 'Mark Missed',
    endpoint: 'lavanya_service.api.workflow_actions.mark_appointment_missed',
    fields: [
      { key: 'reason', label: 'Reason', type: 'textarea', required: true, placeholder: 'Why was the appointment missed?' },
      { key: 'reschedule_date', label: 'Reschedule Date', type: 'date', required: false },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  mark_technician_visited: {
    title: 'Mark Technician Visited', icon: 'handyman', submitLabel: 'Record Visit',
    endpoint: 'lavanya_service.api.workflow_actions.mark_technician_visited',
    fields: [
      { key: 'visit_result', label: 'Visit Result', type: 'text', required: false, placeholder: 'Repaired / PCBs required / Revisit needed' },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  verify_customer_after_visit: {
    title: 'Verify Customer After Visit', icon: 'contact_phone', submitLabel: 'Record Verification',
    endpoint: 'lavanya_service.api.workflow_actions.verify_customer_after_appointment',
    fields: [
      { key: 'confirmed', label: 'Customer Confirms', type: 'select', required: true, options: ['Yes', 'Cleared', 'Satisfied', 'No', 'Not Cleared', 'Still Issue', 'Part Pending'] },
      { key: 'satisfaction', label: 'Satisfaction (optional)', type: 'select', required: false, options: ['Satisfied', 'Not Satisfied', 'Customer Not Reachable', 'Not Required'] },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  // P0: Part-pending actions
  record_part_required: {
    title: 'Record Part Required', icon: 'build', submitLabel: 'Mark Part Pending',
    endpoint: 'lavanya_service.api.workflow_actions.record_part_required',
    fields: [
      { key: 'part_name', label: 'Part Name', type: 'text', required: true, placeholder: 'e.g. PCB, Compressor' },
      { key: 'part_expected_date', label: 'Part ETA', type: 'date', required: true },
      { key: 'next_follow_up_date', label: 'Next Follow-up', type: 'date', required: true },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  update_part_eta: {
    title: 'Update Part ETA', icon: 'schedule', submitLabel: 'Update ETA',
    endpoint: 'lavanya_service.api.workflow_actions.update_part_eta',
    fields: [
      { key: 'new_eta', label: 'New ETA Date', type: 'date', required: true },
      { key: 'delay_reason', label: 'Delay Reason', type: 'text', required: false, placeholder: 'Supplier delayed / Out of stock' },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
  // P0: Reverification loop
  set_reverification_date: {
    title: 'Set Reverification Date', icon: 'event_repeat', submitLabel: 'Set Date',
    endpoint: 'lavanya_service.api.workflow_actions.set_reverification_date',
    fields: [
      { key: 'reverify_at', label: 'Reverify Date', type: 'date', required: true },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },
}

// Task 5: group the Action Library into labelled, collapsible sections instead of
// one flat 24-button grid. The grouping is a key→category map; a catch-all bucket
// guarantees no action is ever dropped, and `close_ticket` stays as the separate
// prominent closure button below the grid.
const ACTION_GROUPS = [
  { key: 'brand_sc', label: 'Brand / Service Center', icon: 'verified',
    keys: ['brand_complaint', 'follow_up_sc', 'record_sc_followup', 'mark_no_update', 'set_reverification_date'] },
  { key: 'customer', label: 'Customer Communication', icon: 'campaign',
    keys: ['inform_customer', 'set_promise', 'record_satisfaction', 'verify_customer_after_visit'] },
  { key: 'tech_appt', label: 'Technician / Appointment', icon: 'handyman',
    keys: ['schedule_appointment', 'confirm_appointment', 'mark_appointment_missed', 'verify_tech_called', 'verify_tech_visit', 'mark_technician_visited'] },
  { key: 'part_product', label: 'Part / Product', icon: 'build',
    keys: ['record_part_required', 'update_part_eta', 'waiting_part', 'sent_to_sc', 'returned_from_sc', 'delivered'] },
  { key: 'closure_mgr', label: 'Closure / Manager', icon: 'gavel',
    keys: ['customer_confirmed', 'escalate_case', 'record_approval', 'reopen'] },
]

// Stage-progression rule: a one-time stage action disappears once its stage is
// passed (it must not be done again). Driven by followup_stage/status (the engine
// source of truth). Recurring actions (inform, follow-up, escalate, set-reverify,
// no-update) have NO entry here, so they always stay available.
const _fs = () => ticket.value?.stage?.followup_stage || ticket.value?.followup_stage || ''
const _afterCall = ['technician_called', 'technician_visit_pending', 'technician_visited', 'sc_followup_done', 'customer_informed', 'part_pending', 'customer_confirmation_pending', 'customer_satisfied', 'customer_not_satisfied']
const _afterVisit = ['technician_visited', 'customer_confirmation_pending', 'customer_satisfied', 'customer_not_satisfied']
const ACTION_DONE = {
  // Register Brand Complaint: done once the brand is registered (followup_stage set, or status advanced past intake).
  brand_complaint: () => !!_fs() || !['New', 'Open', 'Registration Pending', ''].includes(ticket.value?.status || ''),
  // Technician-call verification: done once the call/visit is recorded.
  verify_tech_called: () => _afterCall.includes(_fs()),
  // Technician-visit verification: done once a visit is recorded.
  verify_tech_visit: () => _afterVisit.includes(_fs()),
  mark_technician_visited: () => _afterVisit.includes(_fs()),
  // Record Part Required: done once a part is already logged (use Update Part ETA instead).
  record_part_required: () => !!ticket.value?.stage?.part_required,
}
function isActionDone(key) {
  const fn = ACTION_DONE[key]
  try { return fn ? !!fn() : false } catch { return false }
}

const groupedActions = computed(() => {
  const assigned = new Set()
  const groups = ACTION_GROUPS.map((g) => {
    const items = g.keys
      .filter((k) => ACTIONS[k] && !isActionDone(k))
      .map((k) => { assigned.add(k); return { key: k, def: ACTIONS[k] } })
    return { ...g, items }
  })
  // Catch-all: any action not explicitly grouped (close_ticket is rendered separately).
  const leftover = Object.keys(ACTIONS)
    .filter((k) => !assigned.has(k) && k !== 'close_ticket' && !isActionDone(k))
    .map((k) => ({ key: k, def: ACTIONS[k] }))
  if (leftover.length) groups.push({ key: 'other', label: 'Other Actions', icon: 'more_horiz', items: leftover })
  return groups.filter((g) => g.items.length)
})

const actionKey = ref(null)
const actionDef = computed(() => {
  if (!actionKey.value) return null
  const localDef = ACTIONS[actionKey.value]
  const engineDef = ENGINE_REGISTRY[actionKey.value]
  if (localDef) return localDef
  if (engineDef) return {
    title: engineDef.label || actionKey.value,
    icon: engineDef.icon || 'touch_app',
    submitLabel: engineDef.label || actionKey.value,
    danger: false,
    endpoint: engineDef.endpoint,
    fields: engineDef.fields || [],
  }
  return null
})
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
  const localDef = ACTIONS[key]
  const engineDef = ENGINE_REGISTRY[key]
  const fields = localDef?.fields || engineDef?.fields || []
  if (!localDef && !engineDef) {
    actionError.value = `Unknown action: ${key}`
    return
  }
  for (const f of fields) actionForm[f.key] = ''
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

// Engine-driven action resolution using OUTCOME_MAP config (UI-ENGINE-R1)
const nextActions = computed(() => {
  if (!ticket.value) return { primary: [], secondary: [], danger: [] }
  const status = ticket.value.status || ''

  // Terminal states — no actions
  if (status === 'Closed' || status === 'Cancelled') {
    return { primary: [], secondary: [], danger: [] }
  }

  // Use engine-driven resolution from OUTCOME_MAP config
  return resolveEngineActions(ticket.value)
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
