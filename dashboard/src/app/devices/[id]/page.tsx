'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'

interface DeviceDetail {
  device_id: string
  os: string
  hostname: string
  status: string
  last_heartbeat: string | null
}

interface CommandResult {
  status: string
  result: any
  error?: string
}

export default function DeviceDetailPage() {
  const router = useRouter()
  const params = useParams()
  const deviceId = params.id as string

  const [device, setDevice] = useState<DeviceDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [command, setCommand] = useState('ping')
  const [executing, setExecuting] = useState(false)
  const [result, setResult] = useState<CommandResult | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      router.push('/login')
      return
    }

    fetchDevice(token, deviceId)
  }, [router, deviceId])

  const fetchDevice = async (token: string, id: string) => {
    try {
      const response = await fetch(`/api/devices/${id}?token=${token}`)
      if (!response.ok) {
        throw new Error('Failed to fetch device')
      }
      const data = await response.json()
      setDevice(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch device')
    } finally {
      setLoading(false)
    }
  }

  const executeCommand = async () => {
    const token = localStorage.getItem('token')
    if (!token) return

    setExecuting(true)
    setResult(null)

    try {
      const response = await fetch(`/api/devices/${deviceId}/command?token=${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command }),
      })

      if (!response.ok) {
        throw new Error('Command execution failed')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setResult({
        status: 'error',
        result: null,
        error: err instanceof Error ? err.message : 'Command failed',
      })
    } finally {
      setExecuting(false)
    }
  }

  if (loading) {
    return <div className="p-8">Loading device details...</div>
  }

  if (!device) {
    return <div className="p-8">Device not found</div>
  }

  return (
    <div className="p-8">
      <Link href="/devices" className="text-blue-600 hover:text-blue-700 mb-4 block">
        ← Back to Devices
      </Link>

      <div className="bg-white shadow rounded-lg p-6 mb-8">
        <h1 className="text-3xl font-bold mb-4">{device.hostname}</h1>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Device ID</p>
            <p className="font-mono text-sm">{device.device_id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Operating System</p>
            <p className="font-mono text-sm">{device.os}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Status</p>
            <p className="font-mono text-sm capitalize">{device.status}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Last Heartbeat</p>
            <p className="font-mono text-sm">
              {device.last_heartbeat
                ? new Date(device.last_heartbeat).toLocaleString()
                : 'Never'}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-bold mb-4">Execute Command</h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Command
            </label>
            <select
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="ping">Ping</option>
              <option value="get_system_info">Get System Info</option>
              <option value="list_processes">List Processes</option>
            </select>
          </div>

          <button
            onClick={executeCommand}
            disabled={executing}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {executing ? 'Executing...' : 'Execute'}
          </button>

          {result && (
            <div className="mt-4 p-4 bg-gray-50 rounded">
              <h3 className="font-bold mb-2">Result:</h3>
              <pre className="text-sm overflow-auto max-h-96">
                {JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
