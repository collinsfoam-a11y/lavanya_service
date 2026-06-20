<template>
  <div class="flex flex-wrap items-center gap-3 p-3 rounded-xl border bg-surface">
    <slot name="primary" />
    <div class="flex-1" />
    <slot name="secondary" />
    <slot name="danger" />
  </div>
</template>
