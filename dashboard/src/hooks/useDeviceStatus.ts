'use client'

import { useEffect, useState, useCallback } from 'react'

interface DeviceStatus {
  device_id: string
  status: string
  last_update: string
}

export function useDeviceStatus(deviceId: string | null) {
  const [status, setStatus] = useState<DeviceStatus | null>(null)
  const [connected, setConnected] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)

  useEffect(() => {
    if (!deviceId) return

    const token = localStorage.getItem('token')
    if (!token) return

    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard?token=${token}`

    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      setConnected(true)
      // Subscribe to device updates
      websocket.send(JSON.stringify({
        type: 'subscribe',
        device_id: deviceId,
      }))
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'device_status_change' && data.device_id === deviceId) {
        setStatus({
          device_id: deviceId,
          status: data.status,
          last_update: new Date().toISOString(),
        })
      } else if (data.type === 'device_update' && data.device_id === deviceId) {
        setStatus({
          device_id: deviceId,
          status: data.data.status,
          last_update: new Date().toISOString(),
        })
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnected(false)
    }

    websocket.onclose = () => {
      setConnected(false)
    }

    setWs(websocket)

    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close()
      }
    }
  }, [deviceId])

  return { status, connected }
}

export function useDeviceList() {
  const [statuses, setStatuses] = useState<Map<string, DeviceStatus>>(new Map())
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) return

    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard?token=${token}`

    const websocket = new WebSocket(wsUrl)

    websocket.onopen = () => {
      setConnected(true)
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'device_status_change') {
        setStatuses((prev) => {
          const newMap = new Map(prev)
          newMap.set(data.device_id, {
            device_id: data.device_id,
            status: data.status,
            last_update: new Date().toISOString(),
          })
          return newMap
        })
      }
    }

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error)
      setConnected(false)
    }

    websocket.onclose = () => {
      setConnected(false)
    }

    return () => {
      if (websocket.readyState === WebSocket.OPEN) {
        websocket.close()
      }
    }
  }, [])

  return { statuses, connected }
}
