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

const sportOptions = computed(() =>
    [...new Set(allRows.value.map((r) => r.sport_type))]
        .sort()
        .map((s) => ({ label: s, value: s })),
)

const filteredRows = computed(() => {
    const source =
        selectedSports.value.length === 0
            ? allRows.value
            : allRows.value.filter((r) => selectedSports.value.includes(r.sport_type))

    // Aggregate by (year, month) across selected sport types
    const map = new Map<string, { year: number; month: number; month_name: string; total_km: number }>()
    for (const row of source) {
        const key = `${row.year}-${row.month}`
        if (map.has(key)) {
            const existing = map.get(key)!
            existing.total_km = parseFloat((existing.total_km + row.total_km).toFixed(1))
        } else {
            map.set(key, { year: row.year, month: row.month, month_name: row.month_name, total_km: row.total_km })
        }
    }

    return Array.from(map.values()).sort((a, b) => b.year - a.year || b.month - a.month)
})
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

        <DataTable :value="filteredRows" sortMode="multiple" paginator :rows="50" :rowsPerPageOptions="[50, 100, 200]">
            <Column field="year" header="Year" sortable />
            <Column field="month" header="Month" sortable>
                <template #body="slotProps">
                    {{ slotProps.data.month_name }}
                </template>
            </Column>
            <Column field="total_km" header="Distance (km)" sortable />
        </DataTable>
    </div>
</template>

<style scoped></style>
