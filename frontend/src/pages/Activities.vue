<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import InputText from 'primevue/inputtext'
import IconField from 'primevue/iconfield'
import InputIcon from 'primevue/inputicon'
import MultiSelect from 'primevue/multiselect'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import { fetchAllActivitiesDetail, type ActivityDetail } from '@/fetch/fetchActivities'

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const allActivities = ref<ActivityDetail[]>([])
const loading = ref(false)

const search = ref('')
const selectedYears = ref<number[]>([])
const selectedMonths = ref<number[]>([])
const selectedSports = ref<string[]>([])
const commuteOnly = ref(false)

onMounted(async () => {
    loading.value = true
    try {
        allActivities.value = await fetchAllActivitiesDetail()
    } finally {
        loading.value = false
    }
})

const yearOptions = computed(() =>
    [...new Set(allActivities.value.map(getYear))]
        .sort((a, b) => b - a)
        .map((y) => ({ label: String(y), value: y }))
)

const monthOptions = computed(() =>
    [...new Set(allActivities.value.map(getMonth))]
        .sort((a, b) => a - b)
        .map((m) => ({ label: MONTH_NAMES[m - 1], value: m }))
)

const sportOptions = computed(() =>
    [...new Set(allActivities.value.map((a) => a.sport_type))]
        .sort()
        .map((s) => ({ label: s, value: s }))
)

function getYear(a: ActivityDetail) { return parseInt(a.datetime.slice(0, 4)) }
function getMonth(a: ActivityDetail) { return parseInt(a.datetime.slice(5, 7)) }

const filtered = computed(() => {
    let result = allActivities.value

    if (selectedYears.value.length > 0)
        result = result.filter((a) => selectedYears.value.includes(getYear(a)))
    if (selectedMonths.value.length > 0)
        result = result.filter((a) => selectedMonths.value.includes(getMonth(a)))
    if (selectedSports.value.length > 0)
        result = result.filter((a) => selectedSports.value.includes(a.sport_type))
    if (commuteOnly.value)
        result = result.filter((a) => a.commute)

    const q = search.value.trim().toLowerCase()
    if (q) result = result.filter((a) =>
        a.name.toLowerCase().includes(q) || a.sport_type.toLowerCase().includes(q)
    )

    return result
})

const totalKm = computed(() =>
    filtered.value.reduce((sum, a) => sum + a.distance_km, 0).toFixed(1)
)

function formatDuration(seconds: number): string {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return h > 0
        ? `${h}h${String(m).padStart(2, '0')}`
        : `${m}m${String(s).padStart(2, '0')}`
}

function clearFilters() {
    search.value = ''
    selectedYears.value = []
    selectedMonths.value = []
    selectedSports.value = []
    commuteOnly.value = false
}

const hasActiveFilters = computed(() =>
    search.value || selectedYears.value.length || selectedMonths.value.length ||
    selectedSports.value.length || commuteOnly.value
)
</script>

<template>
    <div class="p-4 flex flex-col gap-4">
        <!-- Filter bar -->
        <div class="flex flex-wrap gap-2 items-center">
            <IconField>
                <InputIcon class="pi pi-search" />
                <InputText
                    v-model="search"
                    placeholder="Search name, sport…"
                    class="w-48"
                />
                <InputIcon
                    v-if="search"
                    class="pi pi-times cursor-pointer"
                    style="pointer-events:auto"
                    @click="search = ''"
                />
            </IconField>

            <MultiSelect
                v-model="selectedYears"
                :options="yearOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Years"
                display="chip"
                class="w-48"
            />

            <MultiSelect
                v-model="selectedMonths"
                :options="monthOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Months"
                display="chip"
                class="w-52"
            />

            <MultiSelect
                v-model="selectedSports"
                :options="sportOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Sport types"
                display="chip"
                class="w-52"
            />

            <button
                :class="[
                    'px-3 py-1.5 rounded text-sm border transition-colors',
                    commuteOnly
                        ? 'bg-amber-500 border-amber-500 text-white'
                        : 'border-surface-600 text-surface-300 hover:border-amber-500'
                ]"
                @click="commuteOnly = !commuteOnly"
            >
                Commute only
            </button>

            <button
                v-if="hasActiveFilters"
                class="px-3 py-1.5 rounded text-sm text-surface-400 hover:text-surface-100 transition-colors"
                @click="clearFilters"
            >
                <i class="pi pi-times mr-1" />Clear
            </button>

            <span class="text-surface-400 text-sm ml-auto">
                {{ filtered.length }} activities — {{ totalKm }} km
            </span>
        </div>

        <!-- Table -->
        <DataTable
            :value="filtered"
            :loading="loading"
            size="small"
            stripedRows
            scrollable
            scrollHeight="calc(100vh - 180px)"
            :virtualScrollerOptions="{ itemSize: 36 }"
            sortField="datetime"
            :sortOrder="-1"
            class="text-sm"
        >
            <Column field="datetime" header="Date" sortable style="width: 145px" />
            <Column field="end_time" header="End" style="width: 70px"
                :pt="{ headerCell: { class: 'text-center' }, bodyCell: { class: 'text-center' } }" />
            <Column field="name" header="Name" sortable />
            <Column field="sport_type" header="Sport" sortable style="width: 120px" />
            <Column field="distance_km" header="Dist (km)" sortable style="width: 90px"
                :pt="{ headerCell: { class: 'text-right' }, bodyCell: { class: 'text-right' } }" />
            <Column field="moving_time_s" header="Duration" sortable style="width: 90px"
                :pt="{ headerCell: { class: 'text-right' }, bodyCell: { class: 'text-right' } }">
                <template #body="{ data }">{{ formatDuration(data.moving_time_s) }}</template>
            </Column>
            <Column field="avg_speed_kmh" header="km/h" sortable style="width: 75px"
                :pt="{ headerCell: { class: 'text-right' }, bodyCell: { class: 'text-right' } }" />
            <Column field="elevation_m" header="Elev (m)" sortable style="width: 80px"
                :pt="{ headerCell: { class: 'text-right' }, bodyCell: { class: 'text-right' } }" />
            <Column field="avg_heartrate" header="HR" sortable style="width: 65px"
                :pt="{ headerCell: { class: 'text-right' }, bodyCell: { class: 'text-right' } }">
                <template #body="{ data }">{{ data.avg_heartrate ?? '—' }}</template>
            </Column>
        </DataTable>
    </div>
</template>
