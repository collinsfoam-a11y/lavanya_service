<template>
  <div class="flex flex-wrap items-center gap-3 p-3 rounded-xl border border-outline-variant bg-surface" aria-label="Ticket action groups">
    <div class="flex flex-wrap items-center gap-2">
      <slot name="primary" />
    </div>
    <div class="flex-1" />
    <div class="flex flex-wrap items-center gap-2">
      <slot name="secondary" />
    </div>
    <div class="flex flex-wrap items-center gap-2 border-l border-outline-variant pl-3">
      <slot name="danger" />
    </div>
  </div>
</template>
