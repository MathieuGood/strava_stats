<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Select from 'primevue/select'
import { fetchCommuteMonths, downloadReport, type CommuteMonth } from '@/fetch/fetchActivities'

const MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December',
]

const months = ref<CommuteMonth[]>([])
const selectedMonth = ref<CommuteMonth | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

onMounted(async () => {
    months.value = await fetchCommuteMonths()
    if (months.value.length > 0) selectedMonth.value = months.value[0]
})

const periodLabel = computed(() => {
    if (!selectedMonth.value) return ''
    const { year, month } = selectedMonth.value
    const prevMonth = month === 1 ? 12 : month - 1
    const prevYear = month === 1 ? year - 1 : year
    return `21 ${MONTH_NAMES[prevMonth - 1]} ${prevYear} → 20 ${MONTH_NAMES[month - 1]} ${year}`
})

async function download() {
    if (!selectedMonth.value) return
    loading.value = true
    error.value = null
    try {
        await downloadReport(selectedMonth.value.year, selectedMonth.value.month)
    } catch (e) {
        error.value = e instanceof Error ? e.message : 'Download failed'
    } finally {
        loading.value = false
    }
}
</script>

<template>
    <div class="p-6 flex flex-col gap-6 max-w-md">
        <h2 class="text-lg font-semibold text-surface-0">Download Commute Report</h2>

        <div class="flex flex-col gap-2">
            <label class="text-sm text-surface-300">Select month</label>
            <Select
                v-model="selectedMonth"
                :options="months"
                optionLabel="label"
                placeholder="Select a month"
                class="w-full"
            />
            <span v-if="selectedMonth" class="text-xs text-surface-400">
                Period: {{ periodLabel }}
            </span>
        </div>

        <div class="flex items-center gap-4">
            <button
                @click="download"
                :disabled="loading || !selectedMonth"
                class="px-4 py-2 rounded bg-amber-500 hover:bg-amber-600 text-white text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {{ loading ? 'Generating...' : 'Download Excel' }}
            </button>
            <span v-if="error" class="text-red-400 text-sm">{{ error }}</span>
        </div>
    </div>
</template>

<style scoped></style>
