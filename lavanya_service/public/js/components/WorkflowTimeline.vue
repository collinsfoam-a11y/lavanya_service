<template>
  <div class="wf-timeline">
    <div v-for="(step, i) in steps" :key="step.key" class="wf-step">
      <div class="wf-node" :class="nodeClass(step)">
        <span class="ms wf-node-icon">{{ step.icon }}</span>
      </div>
      <div v-if="i < steps.length - 1" class="wf-connector" :class="{ 'wf-connector--done': step.state === 'done' }"></div>
      <div class="wf-label" :class="{ 'wf-label--active': step.state === 'active', 'wf-label--done': step.state === 'done' }">
        {{ step.label }}
        <span v-if="step.state === 'active'" class="wf-current-dot">●</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({ currentStage: { type: String, default: 'new' } })

const STAGES = [
  { key: 'new', label: 'New', icon: 'fiber_new' },
  { key: 'registered', label: 'Registered', icon: 'app_registration' },
  { key: 'tech_called', label: 'Tech Called', icon: 'phone_in_talk' },
  { key: 'tech_visited', label: 'Tech Visited', icon: 'engineering' },
  { key: 'in_progress', label: 'In Progress', icon: 'sync' },
  { key: 'informed', label: 'Informed', icon: 'campaign' },
  { key: 'confirmation', label: 'Confirmation', icon: 'thumbs_up_down' },
  { key: 'closed', label: 'Closed', icon: 'task_alt' },
]

const stageIdx = (key) => STAGES.findIndex(s => s.key === key)
const currentIdx = stageIdx(props.currentStage)

const steps = STAGES.map((s, i) => ({
  ...s,
  state: i < currentIdx ? 'done' : i === currentIdx ? 'active' : 'future',
}))

const nodeClass = (step) => ({
  'wf-node--done': step.state === 'done',
  'wf-node--active': step.state === 'active',
  'wf-node--future': step.state === 'future',
})
</script>

<style scoped>
.wf-timeline { display: flex; align-items: flex-start; gap: 0; overflow-x: auto; padding-bottom: 4px; }
.wf-step { display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 1; min-width: 72px; position: relative; }
.wf-connector { position: absolute; top: 14px; left: 50%; width: 100%; height: 2px; background: #E4E4DF; z-index: 0; }
.wf-connector--done { background: #0D9488; }
.wf-node { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; z-index: 1; flex: none; }
.wf-node-icon { font-size: 15px; }
.wf-node--done { background: #0D9488; }
.wf-node--done .wf-node-icon { color: #fff; font-variation-settings: 'FILL' 1; }
.wf-node--active { background: #fff; border: 2px solid #0D9488; }
.wf-node--active .wf-node-icon { color: #0D9488; }
.wf-node--future { background: #F4F4F1; }
.wf-node--future .wf-node-icon { color: #BDBDB6; }
.wf-label { font-size: 10.5px; font-weight: 600; color: #BDBDB6; text-align: center; line-height: 1.2; }
.wf-label--done { color: #0F766E; font-weight: 700; }
.wf-label--active { color: #0F766E; font-weight: 800; }
.wf-current-dot { color: #0D9488; margin-left: 2px; }
</style>
