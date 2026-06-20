<!--
  Reports Center — Manager Dashboard. Polish phase: executive summary cards,
  brand delay, supplier control, follow-up quality, aging, filters, drill-down.
-->
<template>
  <AppShell>
    <!-- Tab bar -->
    <div class="flex items-center gap-1 mb-gutter overflow-x-auto pb-1" role="tablist" aria-label="Dashboard views">
      <button v-for="tab in TABS" :key="tab.key"
        role="tab"
        :aria-selected="activeTab === tab.key"
        :aria-label="tab.label"
        class="px-4 py-2 rounded-lg font-label-md text-body-md whitespace-nowrap transition-colors"
        :class="activeTab === tab.key
          ? 'bg-primary text-on-primary'
          : 'text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface'"
        @click="activeTab = tab.key"
      >{{ tab.label }}</button>
    </div>

    <!-- ====== OVERVIEW TAB ====== -->
    <template v-if="activeTab === 'overview'">
      <!-- Trend + breakdowns -->
      <section v-if="overview.allowed" class="mb-6 flex flex-col gap-4">
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-headline-md text-headline-md text-on-surface">Last {{ overview.days }} days</h3>
            <div class="flex items-center gap-4 font-label-md text-label-md text-on-surface-variant">
              <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full" :style="{ background: COLORS.primary }"></span> Created {{ overview.totals?.created ?? 0 }}</span>
              <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full" :style="{ background: COLORS.success }"></span> Resolved {{ overview.totals?.resolved ?? 0 }}</span>
            </div>
          </div>
          <div v-if="trend" class="bg-surface-container-lowest rounded-lg overflow-hidden">
            <svg :viewBox="`0 0 ${trend.W} ${trend.H}`" class="w-full" style="height: 130px" preserveAspectRatio="none">
              <path :d="trend.created" fill="none" :stroke="COLORS.primary" stroke-width="2" vector-effect="non-scaling-stroke" />
              <path :d="trend.resolved" fill="none" :stroke="COLORS.success" stroke-width="2" vector-effect="non-scaling-stroke" />
            </svg>
          </div>
          <div v-if="trend" class="flex justify-between font-label-md text-label-md text-on-surface-variant mt-1">
            <span>{{ trend.first }}</span><span>{{ trend.last }}</span>
          </div>
        </div>
      </section>

      <!-- Executive Summary Cards -->
      <section class="mb-6">
        <h3 class="font-headline-md text-headline-md text-on-surface mb-3">Executive Summary</h3>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <div v-for="card in execCards" :key="card.key"
            class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4 hover:-translate-y-0.5 hover:shadow-md transition cursor-pointer"
            :style="{ borderLeft: '4px solid ' + (card.color === 'error' ? COLORS.error : card.color === 'warning' ? COLORS.warning : card.color === 'secondary' ? COLORS.secondary : COLORS.primary) }"
            @click="handleCardClick(card.key)"
            role="button" :tabindex="0"
            :aria-label="card.label + ': ' + card.count"
            @keydown.enter="handleCardClick(card.key)"
            @keydown.space.prevent="handleCardClick(card.key)"
          >
            <div class="flex items-center justify-between mb-1">
              <span class="material-symbols-outlined text-on-surface-variant" style="font-size: 22px">{{ card.icon }}</span>
              <span class="font-headline-sm text-on-surface font-bold">{{ card.count }}</span>
            </div>
            <div class="font-label-md text-label-md text-on-surface-variant">{{ card.label }}</div>
          </div>
        </div>
      </section>

      <!-- By status / closure type -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4" v-if="overview.allowed">
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-3">By status</h3>
          <div v-for="b in overview.by_status" :key="b.label" class="flex items-center gap-2 mb-1.5">
            <span class="font-label-md text-label-md text-on-surface-variant w-36 truncate" :title="b.label">{{ b.label }}</span>
            <div class="flex-1 h-3 bg-surface-container rounded-full overflow-hidden">
              <div class="h-full bg-primary rounded-full" :style="{ width: barPct(b.count, overview.by_status) }"></div>
            </div>
            <span class="font-label-md text-label-md w-7 text-right text-on-surface">{{ b.count }}</span>
          </div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-3">By closure type</h3>
          <div v-if="!overview.by_closure_type?.length" class="font-body-md text-on-surface-variant">No closed tickets yet.</div>
          <div v-for="b in overview.by_closure_type" :key="b.label" class="flex items-center gap-2 mb-1.5">
            <span class="font-label-md text-label-md text-on-surface-variant w-36 truncate" :title="b.label">{{ b.label }}</span>
            <div class="flex-1 h-3 bg-surface-container rounded-full overflow-hidden">
              <div class="h-full rounded-full" :style="{ background: COLORS.success, width: barPct(b.count, overview.by_closure_type) }"></div>
            </div>
            <span class="font-label-md text-label-md w-7 text-right text-on-surface">{{ b.count }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ====== BRAND DELAY TAB ====== -->
    <template v-if="activeTab === 'brand_delay'">
      <div class="mb-gutter">
        <h2 class="font-headline-lg text-headline-lg text-on-surface">Brand / Service Center Delay</h2>
        <p class="font-body-md text-on-surface-variant">Which brand/service center is delaying customer complaints</p>
      </div>
      <div v-if="loadingBrand" class="text-on-surface-variant font-body-md py-8 text-center">Loading...</div>
      <div v-else-if="brandData.brands?.length === 0" class="py-12 text-center">
        <div class="text-5xl mb-2">✅</div>
        <div class="text-on-surface-variant font-body-lg">No brand delays to report.</div>
      </div>
      <div v-else class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-low">
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Brand</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Open</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Overdue</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">No Update</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Avg Days</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Escalated</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Part Pending</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in brandData.brands" :key="b.brand"
              class="border-t border-outline-variant hover:bg-surface-container-low">
              <td class="px-4 py-3 font-body-md text-on-surface font-semibold">{{ b.brand }}</td>
              <td class="px-4 py-3 font-body-md text-on-surface">{{ b.open_cases }}</td>
              <td class="px-4 py-3 font-body-md" :class="b.overdue > 0 ? 'text-error font-semibold' : 'text-on-surface'">{{ b.overdue }}</td>
              <td class="px-4 py-3 font-body-md" :class="b.no_tech_update > 0 ? 'text-warning font-semibold' : 'text-on-surface'">{{ b.no_tech_update }}</td>
              <td class="px-4 py-3 font-body-md text-on-surface">{{ b.avg_days }}d</td>
              <td class="px-4 py-3 font-body-md" :class="b.escalated > 0 ? 'text-error font-semibold' : 'text-on-surface'">{{ b.escalated }}</td>
              <td class="px-4 py-3 font-body-md text-on-surface">{{ b.part_pending }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ====== SUPPLIER CONTROL TAB ====== -->
    <template v-if="activeTab === 'supplier'">
      <div class="mb-gutter">
        <h2 class="font-headline-lg text-headline-lg text-on-surface">Supplier Control</h2>
        <p class="font-body-md text-on-surface-variant">Supplier compliance, stock complaints, payment blocks</p>
      </div>
      <div v-if="loadingSupplier" class="text-on-surface-variant font-body-md py-8 text-center">Loading...</div>
      <div v-else-if="supplierData.suppliers?.length === 0" class="py-12 text-center">
        <div class="text-5xl mb-2">📋</div>
        <div class="text-on-surface-variant font-body-lg">No supplier data available.</div>
      </div>
      <div v-else class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-x-auto mb-6">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-low">
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Supplier</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Stock Complaints</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Overdue</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Escalated</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">SLA Breaches</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Payment</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Block Reason</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in supplierData.suppliers" :key="s.brand"
              class="border-t border-outline-variant hover:bg-surface-container-low">
              <td class="px-4 py-3 font-body-md text-on-surface font-semibold">{{ s.brand }}</td>
              <td class="px-4 py-3 font-body-md text-on-surface">{{ s.active_stock_complaints }}</td>
              <td class="px-4 py-3 font-body-md" :class="s.overdue_complaints > 0 ? 'text-error font-semibold' : 'text-on-surface'">{{ s.overdue_complaints }}</td>
              <td class="px-4 py-3 font-body-md" :class="s.escalated > 0 ? 'text-error font-semibold' : 'text-on-surface'">{{ s.escalated }}</td>
              <td class="px-4 py-3 font-body-md" :class="s.sla_breaches > 0 ? 'text-warning font-semibold' : 'text-on-surface'">{{ s.sla_breaches }}</td>
              <td class="px-4 py-3">
                <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md"
                  :class="s.payment_blocked ? 'bg-error text-on-error' : 'bg-surface-container-highest text-on-surface-variant'">
                  {{ s.payment_blocked ? 'Blocked' : 'Clear' }}
                </span>
              </td>
              <td class="px-4 py-3 font-body-md text-on-surface-variant max-w-[200px] truncate" :title="s.block_reason">{{ s.block_reason || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ====== FOLLOW-UP QUALITY TAB ====== -->
    <template v-if="activeTab === 'followup_quality'">
      <div class="mb-gutter">
        <h2 class="font-headline-lg text-headline-lg text-on-surface">Follow-up Quality</h2>
        <p class="font-body-md text-on-surface-variant">Measure whether Lavanya is proving follow-up properly</p>
      </div>
      <div v-if="loadingFQ" class="text-on-surface-variant font-body-md py-8 text-center">Loading...</div>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4"
          :style="{ borderLeft: fqData.no_followup > 0 ? '4px solid ' + COLORS.error : '4px solid ' + COLORS.outline }">
          <div class="font-headline-sm text-on-surface mb-1">{{ fqData.no_followup || 0 }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant">Tickets without follow-up</div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4"
          :style="{ borderLeft: fqData.customer_not_informed > 0 ? '4px solid ' + COLORS.warning : '4px solid ' + COLORS.outline }">
          <div class="font-headline-sm text-on-surface mb-1">{{ fqData.customer_not_informed || 0 }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant">Customer not informed</div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4"
          :style="{ borderLeft: fqData.promise_breach > 0 ? '4px solid ' + COLORS.error : '4px solid ' + COLORS.outline }">
          <div class="font-headline-sm text-on-surface mb-1">{{ fqData.promise_breach || 0 }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant">Promise breached</div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4"
          :style="{ borderLeft: fqData.no_technician_update > 0 ? '4px solid ' + COLORS.warning : '4px solid ' + COLORS.outline }">
          <div class="font-headline-sm text-on-surface mb-1">{{ fqData.no_technician_update || 0 }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant">No technician update</div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4"
          :style="{ borderLeft: '4px solid ' + COLORS.success }">
          <div class="font-headline-sm text-on-surface mb-1">{{ fqData.closed_with_satisfaction || 0 }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant">Closed with satisfaction</div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4"
          :style="{ borderLeft: '4px solid ' + COLORS.secondary }">
          <div class="font-headline-sm text-on-surface mb-1">{{ fqData.satisfaction_pct || 0 }}%</div>
          <div class="font-label-md text-label-md text-on-surface-variant">Satisfaction rate</div>
        </div>
      </div>
    </template>

    <!-- ====== PENALTY TAB ====== -->
    <template v-if="activeTab === 'penalty'">
      <div class="mb-gutter">
        <h2 class="font-headline-lg text-headline-lg text-on-surface">Supplier Penalty</h2>
        <p class="font-body-md text-on-surface-variant">Computed penalty exposure — advisory, no accounting posting</p>
      </div>

      <!-- Summary Cards -->
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-6" v-if="penaltySummary">
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4" :style="{ borderLeft: '4px solid ' + COLORS.error }">
          <div class="font-headline-sm text-error">{{ formatCurrency(penaltySummary.total_computed) }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant">Computed Total</div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4" :style="{ borderLeft: '4px solid ' + COLORS.warning }">
          <div class="font-headline-sm text-on-surface">{{ penaltySummary.manager_review_count || 0 }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant">Manager Review</div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4" :style="{ borderLeft: '4px solid ' + COLORS.success }">
          <div class="font-headline-sm text-on-surface">{{ formatCurrency(penaltySummary.approved_amount) }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant">Approved</div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4" :style="{ borderLeft: '4px solid ' + COLORS.secondary }">
          <div class="font-headline-sm text-on-surface">{{ formatCurrency(penaltySummary.waived_amount) }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant">Waived</div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4" :style="{ borderLeft: '4px solid ' + COLORS.error }">
          <div class="font-headline-sm text-on-surface">{{ penaltySummary.highest_supplier || '—' }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant">Highest Supplier</div>
        </div>
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4" :style="{ borderLeft: '4px solid ' + COLORS.warning }">
          <div class="font-headline-sm text-on-surface">{{ penaltySummary.oldest_breach_days || 0 }}d</div>
          <div class="font-label-md text-label-md text-on-surface-variant">Oldest Breach</div>
        </div>
      </div>

      <!-- Penalty Table -->
      <div v-if="loadingPenaltyList" class="text-on-surface-variant font-body-md py-8 text-center">Loading...</div>
      <div v-else-if="penaltyList.length === 0" class="py-12 text-center">
        <div class="text-5xl mb-2">✅</div>
        <div class="text-on-surface-variant font-body-lg">No penalty computations found.</div>
      </div>
      <div v-else class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-low">
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Ticket</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Supplier</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Breach Type</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Breach Days</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Final Amount</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Status</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in penaltyList" :key="p.name" class="border-t border-outline-variant hover:bg-surface-container-low">
              <td class="px-4 py-3 font-body-md text-primary font-semibold">{{ p.ticket }}</td>
              <td class="px-4 py-3 font-body-md text-on-surface">{{ p.brand || p.supplier || '—' }}</td>
              <td class="px-4 py-3 font-body-md text-on-surface">{{ p.breach_type }}</td>
              <td class="px-4 py-3 font-body-md text-on-surface">{{ p.breach_days }}d</td>
              <td class="px-4 py-3 font-body-md font-semibold" :class="(p.final_penalty_amount || 0) > 0 ? 'text-error' : 'text-on-surface'">{{ formatCurrency(p.final_penalty_amount) }}</td>
              <td class="px-4 py-3">
                <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="penaltyStatusChip(p.status)">{{ p.status }}</span>
              </td>
              <td class="px-4 py-3">
                <div class="flex flex-wrap items-center gap-1">
                  <button type="button"
                    @click="viewPenaltyDetail(p.name)" class="px-2 py-1 rounded font-label-md text-label-md border border-outline-variant text-primary hover:bg-surface-container-low">View Details</button>
                  <span v-if="p.status === 'Computed' || p.status === 'Manager Review'" class="w-px h-6 bg-outline-variant mx-1" aria-hidden="true"></span>
                  <button v-if="p.status === 'Computed' || p.status === 'Manager Review'"
                    type="button" @click="openPenaltyAction('approve', p.name)" class="px-2 py-1 rounded font-label-md text-label-md bg-success text-on-success hover:opacity-90">Approve</button>
                  <button v-if="p.status === 'Computed' || p.status === 'Manager Review'"
                    type="button" @click="openPenaltyAction('waive', p.name)" class="px-2 py-1 rounded font-label-md text-label-md bg-tertiary text-on-tertiary hover:opacity-90">Waive</button>
                  <button v-if="p.status === 'Computed' || p.status === 'Manager Review'"
                    type="button" @click="openPenaltyAction('reject', p.name)" class="px-2 py-1 rounded font-label-md text-label-md bg-error text-on-error hover:opacity-90">Reject</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ====== NOTIFICATIONS TAB ====== -->
    <template v-if="activeTab === 'notifications'">
      <div class="mb-gutter">
        <h2 class="font-headline-lg text-headline-lg text-on-surface">Notifications</h2>
        <p class="font-body-md text-on-surface-variant">Dry-run WhatsApp/SMS/Internal queue. Live sending is disabled.</p>
      </div>

      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        <div v-for="card in notificationCards" :key="card.label" class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4" :style="{ borderLeft: '4px solid ' + card.color }">
          <div class="font-headline-sm text-on-surface">{{ card.count }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant">{{ card.label }}</div>
        </div>
      </div>

      <div v-if="loadingNotifications" class="text-on-surface-variant font-body-md py-8 text-center">Loading notifications...</div>
      <div v-else-if="notificationQueue.length === 0" class="py-12 text-center">
        <div class="text-5xl mb-2">✅</div>
        <div class="text-on-surface-variant font-body-lg">No queued notifications yet.</div>
      </div>
      <div v-else class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-low">
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Ticket</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Customer</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Channel</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Event</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Status</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Dry Run</th>
              <th class="font-label-md text-label-md uppercase text-on-surface-variant px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in notificationQueue" :key="row.name" class="border-t border-outline-variant hover:bg-surface-container-low">
              <td class="px-4 py-3 font-body-md text-primary font-semibold">{{ row.ticket || '—' }}</td>
              <td class="px-4 py-3 font-body-md text-on-surface">{{ row.customer_name || '—' }}</td>
              <td class="px-4 py-3 font-body-md text-on-surface">{{ row.channel }}</td>
              <td class="px-4 py-3 font-body-md text-on-surface max-w-[240px] truncate" :title="row.event_type">{{ row.event_type }}</td>
              <td class="px-4 py-3"><span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="notificationStatusChip(row.status)">{{ row.status }}</span></td>
              <td class="px-4 py-3 font-body-md text-on-surface">{{ row.dry_run ? 'Yes' : 'No' }}</td>
              <td class="px-4 py-3">
                <div class="flex flex-wrap gap-1">
                  <button v-if="row.status === 'Approval Pending' || row.status === 'Queued'" @click="approveNotification(row.name)" class="px-2 py-1 rounded font-label-md text-label-md bg-success text-on-success hover:opacity-90">Approve</button>
                  <button v-if="row.status !== 'Cancelled' && row.status !== 'Sent'" @click="cancelNotification(row.name)" class="px-2 py-1 rounded font-label-md text-label-md bg-error text-on-error hover:opacity-90">Cancel</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <!-- ====== AGING TAB ====== -->
    <template v-if="activeTab === 'aging'">
      <div class="mb-gutter">
        <h2 class="font-headline-lg text-headline-lg text-on-surface">Aging Reports</h2>
        <p class="font-body-md text-on-surface-variant">Ticket age distribution by category</p>
      </div>
      <div v-if="loadingAging" class="text-on-surface-variant font-body-md py-8 text-center">Loading...</div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="cat in agingCategories" :key="cat.key"
          class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4">
          <h3 class="font-headline-md text-headline-md text-on-surface mb-3">{{ cat.label }}</h3>
          <div v-for="b in (agingData.aging?.[cat.key] || [])" :key="b.label"
            class="flex items-center gap-2 mb-1.5">
            <span class="font-label-md text-label-md text-on-surface-variant w-20">{{ b.label }}</span>
            <div class="flex-1 h-3 bg-surface-container rounded-full overflow-hidden">
              <div class="h-full rounded-full" :style="{ background: b.label === '15+ days' ? COLORS.error : b.label.includes('8-15') ? COLORS.warning : COLORS.primary, width: agingBarPct(b.count, cat.key) }"></div>
            </div>
            <span class="font-label-md text-label-md w-7 text-right text-on-surface">{{ b.count }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ====== REPORTS CATALOG TAB ====== -->
    <template v-if="activeTab === 'reports'">
      <template v-if="!reportActive">
        <div v-if="loadingCatalog" class="text-on-surface-variant font-body-md py-12 text-center">
          Loading reports...
        </div>
        <div v-else-if="catalogError" class="text-error font-body-md py-12 text-center">
          Could not load reports.
        </div>
        <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <button v-for="r in catalog" :key="r.key"
            class="group text-left bg-surface-container-lowest border border-outline-variant rounded-xl p-4
                   transition hover:-translate-y-1 hover:border-primary hover:shadow-md flex flex-col gap-2"
            @click="openReport(r.key)">
            <div class="flex items-start justify-between">
              <span class="material-symbols-outlined text-primary" style="font-size: 28px">{{ r.icon }}</span>
              <span class="min-w-[28px] h-7 px-2 inline-flex items-center justify-center rounded-full font-label-md text-label-md"
                :class="r.count ? 'bg-primary text-on-primary' : 'bg-surface-container-highest text-on-surface-variant'">{{ r.count ?? '—' }}</span>
            </div>
            <div class="font-headline-md text-headline-md text-on-surface">{{ r.title }}</div>
            <div class="font-body-md text-on-surface-variant flex-1">{{ r.description }}</div>
            <div class="font-label-md text-label-md text-primary flex items-center gap-1 mt-1">
              Open report
              <span class="material-symbols-outlined transition-transform group-hover:translate-x-1" style="font-size: 16px">arrow_forward</span>
            </div>
          </button>
        </div>
      </template>
      <!-- Drilled-in report table -->
      <template v-else>
        <button class="flex items-center gap-1 font-label-md text-body-md text-primary mb-3 hover:underline" @click="reportActive = null">
          <span class="material-symbols-outlined" style="font-size: 18px">arrow_back</span> Back to reports
        </button>
        <div class="mb-gutter flex items-center gap-3">
          <span class="material-symbols-outlined text-primary" style="font-size: 28px">{{ reportActive.icon }}</span>
          <div class="flex-1">
            <h2 class="font-headline-lg text-headline-lg text-on-surface">
              {{ reportActive.title }}
              <span class="font-body-md text-on-surface-variant">· {{ reportActive.count }}</span>
            </h2>
            <p class="font-body-md text-on-surface-variant">{{ reportActive.description }}</p>
          </div>
          <button v-if="reportActive.count > 0" @click="exportCsv"
            class="flex items-center gap-1.5 px-4 h-9 rounded-lg border border-outline-variant text-primary font-label-md text-body-md hover:bg-surface-container-low">
            <span class="material-symbols-outlined" style="font-size: 18px">download</span> Export CSV
          </button>
        </div>
        <div v-if="loadingReport" class="text-on-surface-variant font-body-md py-12 text-center">Loading...</div>
        <div v-else-if="reportActive.count === 0" class="py-16 text-center">
          <div class="text-5xl mb-2">✅</div>
          <div class="text-on-surface-variant font-body-lg">Nothing in this report right now.</div>
        </div>
        <div v-else class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-surface-container-low">
                <th v-for="c in reportActive.columns" :key="c.key"
                  class="font-label-md text-label-md uppercase tracking-wide text-on-surface-variant px-4 py-3 whitespace-nowrap">{{ c.label }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in reportActive.rows" :key="i"
                class="border-t border-outline-variant cursor-pointer hover:bg-surface-container-low"
                @click="row.ticket && (selectedTicket = row.ticket)">
                <td v-for="c in reportActive.columns" :key="c.key"
                  class="px-4 py-3 font-body-md whitespace-nowrap"
                  :class="c.key === 'ticket' ? 'text-primary font-semibold' : 'text-on-surface'">
                  {{ cell(row, c.key) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </template>

    <LavModal
      :show="penaltyDetailOpen"
      title="Penalty Detail"
      :subtitle="selectedPenaltyDetail?.name || 'Loading penalty computation'"
      icon="receipt_long"
      icon-bg="bg-primary-container text-on-primary-container"
      :error="penaltyDetailError"
      :loading="loadingPenaltyDetail"
      :show-footer="false"
      max-width="2xl"
      @close="closePenaltyDetail"
      @backdrop="closePenaltyDetail"
    >
      <div v-if="loadingPenaltyDetail" class="font-body-md text-on-surface-variant">Loading penalty detail...</div>
      <div v-else-if="selectedPenaltyDetail" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div v-for="field in penaltyDetailFields" :key="field.key" class="rounded-lg border border-outline-variant bg-surface-container-lowest p-3">
          <div class="font-label-md text-label-md text-on-surface-variant">{{ field.label }}</div>
          <div class="font-body-md text-on-surface mt-1 whitespace-pre-wrap break-words">{{ penaltyDetailValue(field) }}</div>
        </div>
      </div>
    </LavModal>

    <LavModal
      :show="penaltyAction.show"
      :title="penaltyAction.title"
      :subtitle="penaltyAction.name"
      :icon="penaltyAction.icon"
      :danger="penaltyAction.type === 'reject'"
      :error="penaltyAction.error"
      :loading="penaltyAction.loading"
      :submit-label="penaltyAction.submitLabel"
      :submit-icon="penaltyAction.icon"
      :submit-disabled="!penaltyActionValid"
      max-width="lg"
      @close="closePenaltyAction"
      @backdrop="closePenaltyAction"
      @submit="submitPenaltyAction"
    >
      <div class="space-y-3">
        <p class="font-body-md text-on-surface-variant">{{ penaltyAction.help }}</p>
        <label class="block">
          <span class="font-label-md text-label-md text-on-surface">{{ penaltyAction.fieldLabel }} <span class="text-error">*</span></span>
          <textarea
            v-model="penaltyAction.value"
            rows="4"
            class="mt-1 w-full rounded-lg border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary resize-none"
            :placeholder="penaltyAction.placeholder"
            :aria-label="penaltyAction.fieldLabel"
            required
          ></textarea>
        </label>
        <div class="rounded-lg bg-surface-container-low p-3 font-body-md text-on-surface-variant">
          This is advisory/operational only. No ERP posting, accounting entry, WhatsApp, or SMS is created by this action.
        </div>
      </div>
    </LavModal>

    <TicketDetail :ticketId="selectedTicket" @close="selectedTicket = null" @refresh="onRefresh" />
  </AppShell>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call, post } from '@/api'
import AppShell from '@/components/AppShell.vue'
import TicketDetail from '@/components/TicketDetail.vue'
import LavModal from '@/components/LavModal.vue'
import { COLORS, hexToRgba } from '@/utils'
import { useConfirm } from '@/utils/confirm'
import { useToast } from '@/utils/toast'

const router = useRouter()
const { confirm } = useConfirm()
const { show: showToast } = useToast()

const TABS = [
  { key: 'overview', label: 'Overview' },
  { key: 'brand_delay', label: 'Brand Delay' },
  { key: 'supplier', label: 'Supplier Control' },
  { key: 'followup_quality', label: 'Follow-up Quality' },
  { key: 'penalty', label: 'Penalty' },
  { key: 'notifications', label: 'Notifications' },
  { key: 'aging', label: 'Aging' },
  { key: 'reports', label: 'Reports' },
]
const activeTab = ref('overview')

const selectedTicket = ref(null)

// ── Overview ──
const overview = reactive({ allowed: false, series: [], by_status: [], by_closure_type: [], totals: {}, days: 30 })
const execCards = ref([])
const loadingExec = ref(false)

async function loadOverview() {
  try {
    const [t, b] = await Promise.all([
      call('lavanya_service.api.manager_reports.get_report_trends'),
      call('lavanya_service.api.manager_reports.get_report_breakdowns'),
    ])
    Object.assign(overview, t || {}, b || {}, { allowed: !!(t && t.allowed) })
  } catch (e) {
    overview.allowed = false
  }
}

async function loadExecSummary() {
  loadingExec.value = true
  try {
    const data = await call('lavanya_service.api.manager_reports.get_executive_summary')
    execCards.value = data?.cards || []
  } catch (e) {
    execCards.value = []
  } finally {
    loadingExec.value = false
  }
}

const trend = computed(() => {
  const s = overview.series || []
  if (!s.length) return null
  const W = 700, H = 130
  const max = Math.max(1, ...s.map(p => Math.max(p.created, p.resolved)))
  const x = i => s.length === 1 ? W / 2 : (i / (s.length - 1)) * W
  const y = v => H - 6 - (v / max) * (H - 12)
  const path = k => s.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(p[k]).toFixed(1)}`).join(' ')
  return { W, H, created: path('created'), resolved: path('resolved'), first: s[0].date, last: s[s.length - 1].date }
})

function barPct(count, list) {
  const max = Math.max(1, ...(list || []).map(x => x.count))
  return `${Math.round((count / max) * 100)}%`
}

function handleCardClick(key) {
  // Navigate to tickets with appropriate filter or relevant tab
  if (['escalated_cases', 'escalated'].includes(key)) {
    router.push('/tickets')
  } else if (['overdue_followup'].includes(key)) {
    router.push('/tickets')
  } else {
    router.push('/tickets')
  }
}

// ── Brand Delay ──
const brandData = reactive({ brands: [] })
const loadingBrand = ref(false)

async function loadBrandDelay() {
  loadingBrand.value = true
  try {
    const data = await call('lavanya_service.api.manager_reports.get_brand_delay_aggregated')
    brandData.brands = data?.brands || []
  } catch (e) {
    brandData.brands = []
  } finally {
    loadingBrand.value = false
  }
}

// ── Supplier Control ──
const supplierData = reactive({ suppliers: [] })
const loadingSupplier = ref(false)

async function loadSupplierControl() {
  loadingSupplier.value = true
  try {
    const data = await call('lavanya_service.api.manager_reports.get_supplier_control')
    supplierData.suppliers = data?.suppliers || []
  } catch (e) {
    supplierData.suppliers = []
  } finally {
    loadingSupplier.value = false
  }
}

// ── Follow-up Quality ──
const fqData = reactive({})
const loadingFQ = ref(false)

async function loadFQ() {
  loadingFQ.value = true
  try {
    const data = await call('lavanya_service.api.manager_reports.get_followup_quality')
    Object.assign(fqData, data || {})
  } catch (e) {
    Object.assign(fqData, {})
  } finally {
    loadingFQ.value = false
  }
}

// ── Aging ──
const agingData = reactive({ categories: [], buckets: [], aging: {} })
const loadingAging = ref(false)

const agingCategories = [
  { key: 'open_complaints', label: 'Open Complaints' },
  { key: 'part_pending', label: 'Part Pending' },
  { key: 'supplier_complaint', label: 'Supplier Complaint' },
  { key: 'replacement', label: 'Replacement' },
  { key: 'return_in_progress', label: 'Return' },
  { key: 'product_at_store', label: 'Product at Store' },
]

async function loadAging() {
  loadingAging.value = true
  try {
    const data = await call('lavanya_service.api.manager_reports.get_aging_data')
    Object.assign(agingData, data || {})
  } catch (e) {
    Object.assign(agingData, { categories: [], buckets: [], aging: {} })
  } finally {
    loadingAging.value = false
  }
}

function agingBarPct(count, catKey) {
  const bucket = agingData.aging?.[catKey] || []
  const max = Math.max(1, ...bucket.map(b => b.count))
  return `${Math.round((count / max) * 100)}%`
}

// ── Penalty ──
const penaltySummary = ref(null)
const penaltyList = ref([])
const loadingPenaltyList = ref(false)
const penaltyDetailOpen = ref(false)
const selectedPenaltyDetail = ref(null)
const loadingPenaltyDetail = ref(false)
const penaltyDetailError = ref('')

const penaltyAction = reactive({
  show: false,
  type: '',
  name: '',
  title: '',
  fieldLabel: '',
  placeholder: '',
  help: '',
  icon: 'check_circle',
  submitLabel: '',
  value: '',
  error: '',
  loading: false,
})

const penaltyActionConfig = {
  approve: {
    title: 'Approve Penalty',
    fieldLabel: 'Approval Narration',
    placeholder: 'Record why this advisory penalty should be approved...',
    help: 'Approve the computed advisory penalty amount. Manager narration is required for audit.',
    icon: 'check_circle',
    submitLabel: 'Approve Penalty',
    endpoint: 'lavanya_service.api.prep.approve_penalty',
    payloadKey: 'narration',
    success: 'Penalty approved',
  },
  waive: {
    title: 'Waive Penalty',
    fieldLabel: 'Waiver Reason',
    placeholder: 'Record why this advisory penalty should be waived...',
    help: 'Waive the computed advisory penalty. The backend sets final penalty to zero.',
    icon: 'block',
    submitLabel: 'Waive Penalty',
    endpoint: 'lavanya_service.api.prep.waive_penalty',
    payloadKey: 'reason',
    success: 'Penalty waived',
  },
  reject: {
    title: 'Reject Penalty',
    fieldLabel: 'Rejection Reason',
    placeholder: 'Record why this advisory penalty should be rejected...',
    help: 'Reject the computed advisory penalty. The record remains visible for audit.',
    icon: 'cancel',
    submitLabel: 'Reject Penalty',
    endpoint: 'lavanya_service.api.prep.reject_penalty',
    payloadKey: 'reason',
    success: 'Penalty rejected',
  },
}

const penaltyActionValid = computed(() => penaltyAction.value.trim().length > 0)

const penaltyDetailFields = [
  { key: 'name', label: 'Computation ID' },
  { key: 'ticket', label: 'Ticket' },
  { key: 'supplier', label: 'Supplier' },
  { key: 'brand', label: 'Brand' },
  { key: 'service_flow_type', label: 'Service Flow Type' },
  { key: 'linked_record_type', label: 'Linked Record Type' },
  { key: 'linked_record', label: 'Linked Record' },
  { key: 'breach_type', label: 'Breach Type' },
  { key: 'breach_start_date', label: 'Breach Start Date' },
  { key: 'breach_days', label: 'Breach Days' },
  { key: 'grace_days', label: 'Grace Days' },
  { key: 'chargeable_days', label: 'Chargeable Days' },
  { key: 'penalty_type', label: 'Penalty Type' },
  { key: 'base_amount', label: 'Base Amount', kind: 'currency' },
  { key: 'computed_penalty_amount', label: 'Computed Penalty Amount', kind: 'currency' },
  { key: 'max_penalty_amount', label: 'Max Penalty Amount', kind: 'currency' },
  { key: 'final_penalty_amount', label: 'Final Penalty Amount', kind: 'currency' },
  { key: 'status', label: 'Status' },
  { key: 'manager_review_required', label: 'Manager Review Required', kind: 'bool' },
  { key: 'payment_block_reference', label: 'Payment Block Reference' },
  { key: 'calculation_narration', label: 'Calculation Narration' },
]

async function loadPenaltyData() {
  loadingPenaltyList.value = true
  try {
    const [summary, list] = await Promise.all([
      call('lavanya_service.api.prep.get_penalty_summary'),
      call('lavanya_service.api.prep.get_penalty_list'),
    ])
    penaltySummary.value = summary || {}
    penaltyList.value = (list?.penalties || [])
  } catch (e) {
    penaltySummary.value = null
    penaltyList.value = []
  } finally {
    loadingPenaltyList.value = false
  }
}

async function viewPenaltyDetail(name) {
  penaltyDetailOpen.value = true
  selectedPenaltyDetail.value = null
  penaltyDetailError.value = ''
  loadingPenaltyDetail.value = true
  try {
    selectedPenaltyDetail.value = await call('lavanya_service.api.prep.get_penalty_detail', { penalty_name: name })
  } catch (e) {
    penaltyDetailError.value = errorMessage(e, 'Could not load penalty detail.')
    showToast(penaltyDetailError.value, 'error')
  } finally {
    loadingPenaltyDetail.value = false
  }
}

function closePenaltyDetail() {
  penaltyDetailOpen.value = false
  selectedPenaltyDetail.value = null
  penaltyDetailError.value = ''
}

function penaltyDetailValue(field) {
  const value = selectedPenaltyDetail.value?.[field.key]
  if (field.kind === 'currency') return formatCurrency(value)
  if (field.kind === 'bool') return value ? 'Yes' : 'No'
  return value == null || value === '' ? '—' : String(value)
}

function openPenaltyAction(type, name) {
  const config = penaltyActionConfig[type]
  Object.assign(penaltyAction, {
    show: true,
    type,
    name,
    title: config.title,
    fieldLabel: config.fieldLabel,
    placeholder: config.placeholder,
    help: config.help,
    icon: config.icon,
    submitLabel: config.submitLabel,
    value: '',
    error: '',
    loading: false,
  })
}

function closePenaltyAction() {
  if (penaltyAction.loading) return
  Object.assign(penaltyAction, { show: false, type: '', name: '', value: '', error: '', loading: false })
}

async function submitPenaltyAction() {
  const config = penaltyActionConfig[penaltyAction.type]
  const value = penaltyAction.value.trim()
  if (!config || !value) {
    penaltyAction.error = `${penaltyAction.fieldLabel} is required.`
    return
  }
  penaltyAction.loading = true
  penaltyAction.error = ''
  try {
    await post(config.endpoint, { penalty_name: penaltyAction.name, [config.payloadKey]: value })
    await loadPenaltyData()
    showToast(config.success)
    closePenaltyAction()
  } catch (e) {
    penaltyAction.error = errorMessage(e, 'Penalty action failed.')
    showToast(penaltyAction.error, 'error')
  } finally {
    penaltyAction.loading = false
  }
}

function errorMessage(error, fallback) {
  return error?.message || fallback
}

function formatCurrency(amount) {
  if (amount == null || amount === 0) return '₹0'
  return '₹' + Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 0 })
}

function penaltyStatusChip(status) {
  const map = {
    'Computed': COLORS.success,
    'Manager Review': COLORS.warning,
    'Approved': COLORS.success,
    'Waived': COLORS.tertiary,
    'Rejected': COLORS.error,
    'Applied': COLORS.info,
  }
  const hue = map[status] || COLORS.neutral
  return { background: hexToRgba(hue, 0.12), color: hue }
}

// ── Notifications ──
const notificationQueue = ref([])
const loadingNotifications = ref(false)

const notificationCards = computed(() => {
  const count = (status) => notificationQueue.value.filter(r => r.status === status).length
  return [
    { label: 'Queued', count: count('Queued'), color: COLORS.primary },
    { label: 'Approval Pending', count: count('Approval Pending'), color: COLORS.warning },
    { label: 'Approved', count: count('Approved'), color: COLORS.success },
    { label: 'Skipped', count: count('Skipped'), color: COLORS.outline },
    { label: 'Failed', count: count('Failed'), color: COLORS.error },
    { label: 'Dry Run', count: notificationQueue.value.filter(r => r.dry_run).length, color: COLORS.secondary },
  ]
})

async function loadNotifications() {
  loadingNotifications.value = true
  try {
    const data = await call('lavanya_service.api.notifications.get_notification_queue')
    notificationQueue.value = data?.queue || []
  } catch (e) {
    notificationQueue.value = []
  } finally {
    loadingNotifications.value = false
  }
}

function notificationStatusChip(status) {
  const map = {
    Queued: COLORS.primary,
    'Approval Pending': COLORS.warning,
    Approved: COLORS.success,
    Skipped: COLORS.outline,
    Sent: COLORS.success,
    Failed: COLORS.error,
    Cancelled: COLORS.outline,
  }
  const color = map[status] || COLORS.outline
  return { background: `${color}22`, color }
}

async function approveNotification(name) {
  const ok = await confirm('Approve this dry-run notification? This still will not send WhatsApp/SMS while live notifications are disabled.', 'Approve Notification')
  if (!ok) return
  try {
    await call('lavanya_service.api.notifications.approve_notification', { queue_name: name })
    await loadNotifications()
  } catch (e) {
    // handled by API
  }
}

async function cancelNotification(name) {
  const ok = await confirm('Cancel this queued notification?', 'Cancel Notification', true)
  if (!ok) return
  try {
    await call('lavanya_service.api.notifications.cancel_notification', { queue_name: name, reason: 'Cancelled from reports' })
    await loadNotifications()
  } catch (e) {
    // handled by API
  }
}

// ── Reports Catalog ──
const catalog = ref([])
const loadingCatalog = ref(true)
const catalogError = ref(false)

const reportActive = ref(null)
const loadingReport = ref(false)

async function loadCatalog() {
  loadingCatalog.value = true
  catalogError.value = false
  try {
    const res = await call('lavanya_service.api.manager_reports.get_report_catalog')
    catalog.value = res?.reports || []
  } catch (e) {
    catalogError.value = true
  } finally {
    loadingCatalog.value = false
  }
}

async function openReport(key) {
  loadingReport.value = true
  reportActive.value = { columns: [], rows: [], count: 0, title: '', description: '', icon: 'assessment' }
  try {
    reportActive.value = await call('lavanya_service.api.manager_reports.get_report', { report: key })
  } catch (e) {
    reportActive.value = null
  } finally {
    loadingReport.value = false
  }
}

function onRefresh() {
  if (reportActive.value) openReport(reportActive.value.key)
  loadCatalog()
  loadExecSummary()
}

function exportCsv() {
  if (!reportActive.value?.rows?.length) return
  const cols = reportActive.value.columns
  const esc = v => {
    const s = v == null ? '' : String(v)
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const raw = (row, key) => {
    const v = row[key]
    if (v == null || v === '') return ''
    return DATE_KEYS.test(key) ? String(v).slice(0, 10) : v
  }
  const lines = [cols.map(c => esc(c.label)).join(',')]
  for (const row of reportActive.value.rows) lines.push(cols.map(c => esc(raw(row, c.key))).join(','))
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = `${reportActive.value.key}-${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(a); a.click(); a.remove()
  URL.revokeObjectURL(url)
}

const DATE_KEYS = /(_date|_on|modified|closure_date|registration_date)$/
function cell(row, key) {
  const v = row[key]
  if (v == null || v === '') return '—'
  if (DATE_KEYS.test(key)) return String(v).slice(0, 10)
  return v
}

// ── Init ──
onMounted(() => {
  loadOverview()
  loadExecSummary()
  loadBrandDelay()
  loadSupplierControl()
  loadFQ()
  loadAging()
  loadPenaltyData()
  loadNotifications()
  loadCatalog()
})
</script>
