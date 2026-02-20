<script setup lang="ts">
import { ref } from 'vue'
import { triggerFetch } from '../fetch/fetchActivities'

const loading = ref(false)
const success = ref(false)
const error = ref<string | null>(null)

async function fetchData() {
    loading.value = true
    error.value = null
    success.value = false
    try {
        await triggerFetch()
        success.value = true
        setTimeout(() => {
            success.value = false
        }, 3000)
    } catch (e) {
        error.value = e instanceof Error ? e.message : 'Failed'
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
            <span v-if="success" class="text-green-400 text-sm">Done!</span>
            <span v-if="error" class="text-red-400 text-sm">Error</span>
        </nav>
    </div>
</template>

<style scoped></style>
