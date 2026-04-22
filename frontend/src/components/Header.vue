<script setup lang="ts">
import { ref } from 'vue'
import { useToast } from 'primevue/usetoast'
import { triggerFetch } from '../fetch/fetchActivities'
import { useActivities } from '@/composables/useActivities'

const loading = ref(false)
const toast = useToast()
const { reload } = useActivities()

async function fetchData() {
    loading.value = true
    toast.add({ severity: 'info', summary: 'Fetching data...', detail: 'Syncing with Strava API', life: 30000 })
    try {
        const { fetched } = await triggerFetch()
        await reload()
        toast.removeAllGroups()
        toast.add({ severity: 'success', summary: 'Done!', detail: `${fetched} activities loaded`, life: 4000 })
    } catch (e) {
        toast.removeAllGroups()
        toast.add({ severity: 'error', summary: 'Fetch failed', detail: e instanceof Error ? e.message : 'Unknown error', life: 5000 })
    } finally {
        loading.value = false
    }
}
</script>

<template>
    <div class="bg-surface-900 p-2 px-4 flex justify-between items-center border-b border-surface">
        <div class="text-xl text-yellow-500">Strava Stats</div>
        <nav class="flex gap-4 items-center">
            <router-link to="/" class="text-surface-0 hover:text-primary">Home</router-link>
            <router-link to="/charts" class="text-surface-0 hover:text-primary">Charts</router-link>
            <router-link to="/reports" class="text-surface-0 hover:text-primary">Reports</router-link>
            <button
                @click="fetchData"
                :disabled="loading"
                class="px-3 py-1 rounded bg-orange-500 hover:bg-orange-600 text-white text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {{ loading ? 'Fetching...' : 'Fetch new data' }}
            </button>
        </nav>
    </div>
</template>

<style scoped></style>
