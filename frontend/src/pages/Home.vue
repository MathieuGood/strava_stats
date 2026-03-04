<script setup lang="ts">
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import MultiSelect from 'primevue/multiselect'
import { ref, computed, onMounted } from 'vue'
import { fetchMonthlyTotals, type MonthlyRow } from '@/fetch/fetchActivities'

// --- State ---

const allRows = ref<MonthlyRow[]>([])
const selectedSports = ref<string[]>([])

// --- Data fetching ---

onMounted(async () => {
    allRows.value = await fetchMonthlyTotals()
})

// --- Derived data ---

const MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const sportOptions = computed(() =>
    [...new Set(allRows.value.map((r) => r.sport_type))]
        .sort()
        .map((s) => ({ label: s, value: s })),
)

// Aggregate by (year, month) across selected sport types
const aggregatedByYearMonth = computed(() => {
    const source =
        selectedSports.value.length === 0
            ? allRows.value
            : allRows.value.filter((r) => selectedSports.value.includes(r.sport_type))

    const map = new Map<string, { year: number; month: number; total_km: number }>()
    for (const row of source) {
        const key = `${row.year}-${row.month}`
        if (map.has(key)) {
            const existing = map.get(key)!
            existing.total_km = parseFloat((existing.total_km + row.total_km).toFixed(1))
        } else {
            map.set(key, { year: row.year, month: row.month, total_km: row.total_km })
        }
    }
    return Array.from(map.values())
})

// Pivot: one row per year, 12 month columns
type PivotRow = { year: number; months: (number | null)[] }

const pivotRows = computed<PivotRow[]>(() => {
    const map = new Map<number, PivotRow>()
    for (const row of aggregatedByYearMonth.value) {
        if (!map.has(row.year)) {
            map.set(row.year, { year: row.year, months: Array(12).fill(null) })
        }
        map.get(row.year)!.months[row.month - 1] = row.total_km
    }
    return Array.from(map.values()).sort((a, b) => b.year - a.year)
})

function yearTotal(row: PivotRow): string {
    const total = row.months.reduce<number>((sum, v) => sum + (v ?? 0), 0)
    return total > 0 ? total.toFixed(1) : '-'
}
</script>

<template>
    <div class="p-4">
        <!-- Toolbar: sport filter -->
        <div class="flex items-center justify-center pb-4 gap-5 flex-wrap">
            <MultiSelect
                v-model="selectedSports"
                :options="sportOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="All Sports"
                display="chip"
                filter
                autoFilterFocus
                class="w-full md:w-80"
            />
        </div>

        <DataTable :value="pivotRows" class="text-sm">
            <Column field="year" header="Year" />
            <Column
                v-for="(label, i) in MONTH_LABELS"
                :key="i"
                :header="label"
                :pt="{ headerCell: { class: 'text-center' }, bodyCell: { class: 'text-center' } }"
            >
                <template #body="{ data }">
                    {{ data.months[i] !== null ? data.months[i] : '-' }}
                </template>
            </Column>
            <Column header="Total" :pt="{ headerCell: { class: 'text-center' }, bodyCell: { class: 'text-center font-semibold' } }">
                <template #body="{ data }">
                    {{ yearTotal(data) }}
                </template>
            </Column>
        </DataTable>
    </div>
</template>

<style scoped></style>
