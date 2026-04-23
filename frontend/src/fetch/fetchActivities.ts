const API_URL = '/api/'
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

export interface CommuteMonth {
    year: number
    month: number
    label: string
}

export const fetchCommuteMonths = async (): Promise<CommuteMonth[]> => {
    const response = await fetch(`${API_URL}${ACTIVITIES_ENDPOINT}/commute-months`)
    if (!response.ok) throw new Error('Failed to fetch commute months')
    return response.json()
}

export interface ActivityDetail {
    id: number
    date: string
    name: string
    sport_type: string
    distance_km: number
    moving_time_s: number
    elevation_m: number
    avg_speed_kmh: number
    avg_heartrate: number | null
    commute: boolean
}

export const fetchActivitiesByMonth = async (year: number, month: number): Promise<ActivityDetail[]> => {
    const response = await fetch(`${API_URL}${ACTIVITIES_ENDPOINT}/by-month?year=${year}&month=${month}`)
    if (!response.ok) throw new Error('Failed to fetch activities')
    return response.json()
}

export const downloadReport = async (year: number, month: number): Promise<void> => {
    const response = await fetch(
        `${API_URL}${ACTIVITIES_ENDPOINT}/report?year=${year}&month=${month}`,
    )
    if (!response.ok) {
        const detail = await response.text()
        throw new Error(detail)
    }
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `Indemnite_KM_MB_${year}_${String(month).padStart(2, '0')}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
}
