<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import Select from 'primevue/select'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { useActivities } from '@/composables/useActivities'
import { fetchActivitiesByMonth, type ActivityDetail } from '@/fetch/fetchActivities'

const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December']

const { allRows, reload } = useActivities()
const activities = ref<ActivityDetail[]>([])
const loading = ref(false)

const selectedYear = ref<number | null>(null)
const selectedMonth = ref<number | null>(null)

onMounted(async () => {
    if (allRows.value.length === 0) await reload()
    if (yearOptions.value.length > 0) selectedYear.value = yearOptions.value[0]?.value ?? null
})

const yearOptions = computed(() =>
    [...new Set(allRows.value.map((r) => r.year))]
        .sort((a, b) => b - a)
        .map((y) => ({ label: String(y), value: y }))
)

const monthOptions = computed(() => {
    if (!selectedYear.value) return []
    const months = [...new Set(
        allRows.value
            .filter((r) => r.year === selectedYear.value)
            .map((r) => r.month)
    )].sort((a, b) => b - a)
    return months.map((m) => ({ label: MONTH_NAMES[m - 1], value: m }))
})

watch(selectedYear, () => {
    selectedMonth.value = monthOptions.value[0]?.value ?? null
})

watch(selectedMonth, async (month) => {
    if (!selectedYear.value || !month) return
    loading.value = true
    try {
        activities.value = await fetchActivitiesByMonth(selectedYear.value, month)
    } finally {
        loading.value = false
    }
})

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
</script>

<template>
    <div class="p-4 flex flex-col gap-4">
        <div class="flex items-center gap-3 flex-wrap">
            <Select
                v-model="selectedYear"
                :options="yearOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Year"
                class="w-28"
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
            <Column field="date" header="Date" style="width: 100px" />
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
            <Column header="🚗" style="width: 50px"
                :pt="{ headerCell: { class: 'text-center' }, bodyCell: { class: 'text-center' } }">
                <template #body="{ data }">{{ data.commute ? '✓' : '' }}</template>
            </Column>
        </DataTable>
    </div>
</template>
