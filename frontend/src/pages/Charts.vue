<script setup lang="ts">
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import {
    TitleComponent,
    TooltipComponent,
    LegendComponent,
    GridComponent,
    DataZoomComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import MultiSelect from 'primevue/multiselect'
import { ref, computed, onMounted } from 'vue'
import { fetchMonthlyTotals, type MonthlyRow } from '@/fetch/fetchActivities'

// ECharts tree-shaking: register only the modules this page needs
use([CanvasRenderer, LineChart, BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, DataZoomComponent])

const MONTH_LABELS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const CHART_COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc']

// --- State ---

const allRows = ref<MonthlyRow[]>([])
const selectedSportsLine = ref<string[]>([])
const selectedSportsBar = ref<string[]>([])

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

/** Filter raw rows by selected sport types. Empty selection = all sports. */
const filteredBySports = (selectedSports: string[]): MonthlyRow[] => {
    if (selectedSports.length === 0) return allRows.value
    return allRows.value.filter((r) => selectedSports.includes(r.sport_type))
}

// --- Line chart: monthly km per year ---

const lineChartOption = computed(() => {
    const source = filteredBySports(selectedSportsLine.value)

    // Group by year → month → summed km
    const byYear = new Map<number, Map<number, number>>()
    for (const row of source) {
        if (!byYear.has(row.year)) byYear.set(row.year, new Map())
        const monthMap = byYear.get(row.year)!
        monthMap.set(row.month, (monthMap.get(row.month) ?? 0) + row.total_km)
    }

    const years = [...byYear.keys()].sort()
    const series = years.map((year, idx) => {
        const monthMap = byYear.get(year)!
        return {
            name: String(year),
            type: 'line',
            showSymbol: true,
            smooth: false,
            connectNulls: false,
            color: CHART_COLORS[idx % CHART_COLORS.length],
            data: Array.from({ length: 12 }, (_, i) => {
                const val = monthMap.get(i + 1)
                return val !== undefined ? parseFloat(val.toFixed(1)) : null
            }),
        }
    })

    return {
        tooltip: { trigger: 'axis' },
        legend: { show: true, bottom: 0 },
        grid: { left: 60, right: 30, top: 20, bottom: 55 },
        xAxis: { type: 'category', data: MONTH_LABELS },
        yAxis: { type: 'value', name: 'km', min: 0 },
        dataZoom: [
            { type: 'inside', xAxisIndex: 0 },
            { type: 'slider', xAxisIndex: 0, bottom: 5, height: 20 },
        ],
        series,
    }
})

// --- Bar chart: total km per year ---

const barChartOption = computed(() => {
    const source = filteredBySports(selectedSportsBar.value)

    const byYear = new Map<number, number>()
    for (const row of source) {
        byYear.set(row.year, (byYear.get(row.year) ?? 0) + row.total_km)
    }

    const years = [...byYear.keys()].sort()

    return {
        tooltip: { trigger: 'axis' },
        grid: { left: 60, right: 30, top: 20, bottom: 40 },
        xAxis: { type: 'category', data: years.map(String) },
        yAxis: { type: 'value', name: 'km', min: 0 },
        series: [
            {
                name: 'Total km',
                type: 'bar',
                color: CHART_COLORS[0],
                data: years.map((y) => parseFloat((byYear.get(y)!).toFixed(1))),
                label: { show: true, position: 'top' },
            },
        ],
    }
})
</script>

<template>
    <div class="p-4 flex flex-col gap-10">
        <!-- Line chart: monthly distances per year -->
        <div class="flex flex-col gap-3">
            <div class="flex items-center gap-4">
                <MultiSelect
                    v-model="selectedSportsLine"
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
            <div class="h-96">
                <v-chart :option="lineChartOption" autoresize class="w-full h-full" />
            </div>
        </div>

        <!-- Bar chart: total km per year -->
        <div class="flex flex-col gap-3">
            <div class="flex items-center gap-4">
                <MultiSelect
                    v-model="selectedSportsBar"
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
            <div class="h-80">
                <v-chart :option="barChartOption" autoresize class="w-full h-full" />
            </div>
        </div>
    </div>
</template>

<style scoped></style>
