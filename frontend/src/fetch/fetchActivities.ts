const API_URL = 'http://localhost:8000/'
const ACTIVITIES_ENDPOINT = 'activities'

export interface MonthlyRow {
    year: number
    month: number
    month_name: string
    sport_type: string
    total_km: number
}

export const fetchMonthlyTotals = async (): Promise<MonthlyRow[]> => {
    const response = await fetch(`${API_URL}${ACTIVITIES_ENDPOINT}/monthly-totals`)
    return response.json()
}

export const triggerFetch = async (): Promise<{ fetched: number }> => {
    const response = await fetch(`${API_URL}${ACTIVITIES_ENDPOINT}/fetch`, { method: 'POST' })
    if (!response.ok) {
        const detail = await response.text()
        throw new Error(detail)
    }
    return response.json()
}
