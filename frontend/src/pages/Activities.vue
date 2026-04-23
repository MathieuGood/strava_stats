<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import Select from 'primevue/select'
import MultiSelect from 'primevue/multiselect'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { useActivities } from '@/composables/useActivities'
import { fetchActivitiesByMonth, type ActivityDetail } from '@/fetch/fetchActivities'

const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December']

const { allRows, reload } = useActivities()
const activities = ref<ActivityDetail[]>([])
const loading = ref(false)

const selectedYears = ref<number[]>([])
const selectedMonth = ref<number | null>(null)

onMounted(async () => {
    if (allRows.value.length === 0) await reload()
    if (yearOptions.value.length > 0) selectedYears.value = [yearOptions.value[0]?.value ?? 0]
})

const yearOptions = computed(() =>
    [...new Set(allRows.value.map((r) => r.year))]
        .sort((a, b) => b - a)
        .map((y) => ({ label: String(y), value: y }))
)

const monthOptions = computed(() => {
    const months = [...new Set(allRows.value.map((r) => r.month))].sort((a, b) => b - a)
    return months.map((m) => ({ label: MONTH_NAMES[m - 1], value: m }))
})

watch(monthOptions, (opts) => {
    if (selectedMonth.value === null && opts.length > 0) {
        selectedMonth.value = opts[0]?.value ?? null
    }
}, { immediate: true })

async function loadActivities() {
    if (!selectedMonth.value || selectedYears.value.length === 0) return
    loading.value = true
    try {
        const results = await Promise.all(
            selectedYears.value.map((y) => fetchActivitiesByMonth(y, selectedMonth.value!))
        )
        activities.value = results.flat().sort((a, b) => a.date.localeCompare(b.date))
    } finally {
        loading.value = false
    }
}

watch([selectedYears, selectedMonth], loadActivities, { deep: true })

function formatDuration(seconds: number): string {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return h > 0
        ? `${h}h${String(m).padStart(2, '0')}`
        : `${m}m${String(s).padStart(2, '0')}`
}

const totalKm = computed(() =>
    activities.value.reduce((sum, a) => sum + a.distance_km, 0).toFixed(1)
)

function getYear(date: string) { return date.slice(0, 4) }
function getMonth(date: string) { return (MONTH_NAMES[parseInt(date.slice(5, 7)) - 1] ?? '').slice(0, 3) }
function getDay(date: string) { return date.slice(8, 10) }
</script>

<template>
    <div class="p-4 flex flex-col gap-4">
        <div class="flex items-center gap-3 flex-wrap">
            <MultiSelect
                v-model="selectedYears"
                :options="yearOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Years"
                display="chip"
                class="w-60"
            />
            <Select
                v-model="selectedMonth"
                :options="monthOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Month"
                class="w-36"
            />
            <span v-if="activities.length > 0" class="text-surface-400 text-sm ml-2">
                {{ activities.length }} activities — {{ totalKm }} km total
            </span>
        </div>

        <DataTable
            :value="activities"
            :loading="loading"
            size="small"
            class="text-sm"
            stripedRows
        >
            <Column header="Year" style="width: 70px">
                <template #body="{ data }">{{ getYear(data.date) }}</template>
            </Column>
            <Column header="Month" style="width: 80px">
                <template #body="{ data }">{{ getMonth(data.date) }}</template>
            </Column>
            <Column header="Day" style="width: 60px"
                :pt="{ headerCell: { class: 'text-center' }, bodyCell: { class: 'text-center' } }">
                <template #body="{ data }">{{ getDay(data.date) }}</template>
            </Column>
            <Column header="Start" style="width: 70px"
                :pt="{ headerCell: { class: 'text-center' }, bodyCell: { class: 'text-center' } }">
                <template #body="{ data }">{{ data.start_time }}</template>
            </Column>
            <Column header="End" style="width: 70px"
                :pt="{ headerCell: { class: 'text-center' }, bodyCell: { class: 'text-center' } }">
                <template #body="{ data }">{{ data.end_time }}</template>
            </Column>
            <Column field="name" header="Name" />
            <Column field="sport_type" header="Sport" style="width: 120px" />
            <Column field="distance_km" header="Dist (km)" style="width: 90px"
                :pt="{ headerCell: { class: 'text-right' }, bodyCell: { class: 'text-right' } }" />
            <Column header="Duration" style="width: 90px"
                :pt="{ headerCell: { class: 'text-right' }, bodyCell: { class: 'text-right' } }">
                <template #body="{ data }">{{ formatDuration(data.moving_time_s) }}</template>
            </Column>
            <Column field="avg_speed_kmh" header="Avg km/h" style="width: 90px"
                :pt="{ headerCell: { class: 'text-right' }, bodyCell: { class: 'text-right' } }" />
            <Column field="elevation_m" header="Elev (m)" style="width: 80px"
                :pt="{ headerCell: { class: 'text-right' }, bodyCell: { class: 'text-right' } }" />
            <Column field="avg_heartrate" header="HR" style="width: 70px"
                :pt="{ headerCell: { class: 'text-right' }, bodyCell: { class: 'text-right' } }">
                <template #body="{ data }">{{ data.avg_heartrate ?? '—' }}</template>
            </Column>
            <Column header="Commute" style="width: 80px"
                :pt="{ headerCell: { class: 'text-center' }, bodyCell: { class: 'text-center' } }">
                <template #body="{ data }">{{ data.commute ? '✓' : '' }}</template>
            </Column>
        </DataTable>
    </div>
</template>
