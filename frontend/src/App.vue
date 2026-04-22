<script setup lang="ts">
import Header from '@/components/Header.vue'
import Toast from 'primevue/toast'
</script>

<template>
    <Toast position="bottom-right" />
    <Header />
    <router-view />
</template>

<style scoped></style>
