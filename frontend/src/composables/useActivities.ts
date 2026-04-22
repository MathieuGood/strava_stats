import { ref } from 'vue'
import { fetchMonthlyTotals, type MonthlyRow } from '@/fetch/fetchActivities'

const allRows = ref<MonthlyRow[]>([])
const loading = ref(false)

async function reload() {
    loading.value = true
    try {
        allRows.value = await fetchMonthlyTotals()
    } finally {
        loading.value = false
    }
}

export function useActivities() {
    return { allRows, loading, reload }
}
