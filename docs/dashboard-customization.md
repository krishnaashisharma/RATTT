# Dashboard Customization Guide

This guide explains how to customize the React/Next.js dashboard for specific monitoring needs.

## 1. Adding Custom Monitoring Widgets

To add a new monitoring widget to the device detail page, create a component in `dashboard/src/components/`:

```tsx
// dashboard/src/components/CpuMonitor.tsx
'use client'
import { useEffect, useState } from 'react'

interface CpuData {
  usage: number[]
  timestamp: string
}

export function CpuMonitor({ deviceId }: { deviceId: string }) {
  const [data, setData] = useState<CpuData | null>(null)

  useEffect(() => {
    const interval = setInterval(async () => {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/devices/${deviceId}/command?token=${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: 'get_system_info' }),
      })
      const result = await res.json()
      setData(result)
    }, 5000) // Poll every 5 seconds

    return () => clearInterval(interval)
  }, [deviceId])

  return (
    <div className="bg-white rounded-lg p-4 shadow">
      <h3 className="font-bold mb-2">CPU Usage</h3>
      {data ? (
        <div className="text-2xl font-mono">{data.usage?.[0]?.toFixed(1)}%</div>
      ) : (
        <div className="text-gray-400">Loading...</div>
      )}
    </div>
  )
}
```

## 2. Customizing the Device List Columns

Edit `dashboard/src/app/devices/page.tsx` to add or remove columns:

```tsx
// Add custom columns to the device table
const columns = [
  { key: 'hostname', label: 'Hostname' },
  { key: 'os', label: 'OS' },
  { key: 'status', label: 'Status' },
  { key: 'last_heartbeat', label: 'Last Seen' },
  // Add your custom columns:
  { key: 'cpu_usage', label: 'CPU %' },
  { key: 'memory_usage', label: 'Memory %' },
  { key: 'disk_usage', label: 'Disk %' },
]
```

## 3. Adding Custom Command Types

To add new commands to the command panel:

```tsx
// In dashboard/src/app/devices/[id]/page.tsx
// Add to the command dropdown:
<select value={command} onChange={(e) => setCommand(e.target.value)}>
  <option value="ping">Ping</option>
  <option value="get_system_info">System Info</option>
  <option value="list_processes">List Processes</option>
  {/* Add custom commands: */}
  <option value="get_disk_usage">Disk Usage</option>
  <option value="get_network_stats">Network Stats</option>
  <option value="restart_service">Restart Service</option>
  <option value="check_updates">Check Updates</option>
</select>
```

## 4. Theming and Branding

Update the Tailwind configuration in `dashboard/tailwind.config.js`:

```js
module.exports = {
  theme: {
    extend: {
      colors: {
        // Replace with your brand colors
        primary: '#1E40AF',    // Deep blue
        secondary: '#7C3AED',  // Purple
        accent: '#10B981',     // Green
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
}
```

## 5. Adding Real-Time Charts

Install a charting library and create monitoring dashboards:

```bash
cd dashboard
npm install recharts
```

```tsx
// dashboard/src/components/MetricsChart.tsx
'use client'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts'

export function MetricsChart({ data }: { data: { time: string; value: number }[] }) {
  return (
    <LineChart width={600} height={300} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="time" />
      <YAxis />
      <Tooltip />
      <Line type="monotone" dataKey="value" stroke="#1E40AF" />
    </LineChart>
  )
}
```

## 6. Adding Alert Rules

Create a notification system for device monitoring:

```tsx
// dashboard/src/components/AlertRules.tsx
interface AlertRule {
  id: string
  name: string
  condition: 'cpu_above' | 'memory_above' | 'offline_for'
  threshold: number
  action: 'email' | 'push' | 'webhook'
}

// Store rules in the backend and evaluate them on each heartbeat
```

## 7. Role-Based Dashboard Views

Customize what different roles see:

```tsx
// In any page component:
const role = localStorage.getItem('role')

// Admin sees everything
// User sees limited view
{role === 'admin' && (
  <AdminPanel />
)}

{role === 'user' && (
  <UserPanel />
)}
```

## 8. Adding Remote Desktop Session Recording

To add session recording to the audit trail:

```tsx
// When a remote desktop session starts, log it:
await fetch(`/api/audit/log`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    device_id: deviceId,
    action: 'remote_desktop_start',
    details: {
      initiator: userId,
      ip_address: clientIp,
      session_id: sessionId,
    }
  }),
})
```

## 9. Custom Dashboard Layouts

Create different dashboard layouts for different use cases:

```
dashboard/src/app/
├── devices/          # Device management view
├── monitoring/       # Real-time monitoring view (add this)
│   └── page.tsx      # Grid of live metrics
├── security/         # Security overview (add this)
│   └── page.tsx      # Failed logins, policy violations
└── reports/          # Reports view (add this)
    └── page.tsx      # Historical data, exports
```

## 10. Embedding the Remote Desktop Viewer

To embed LeftDesk's web client in the dashboard:

```tsx
// dashboard/src/components/RemoteDesktopViewer.tsx
'use client'
import { useEffect, useRef } from 'react'

export function RemoteDesktopViewer({ deviceId, sessionToken }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Option A: Embed as iframe
    // const iframe = document.createElement('iframe')
    // iframe.src = `https://your-leftdesk-server/web?device=${deviceId}&token=${sessionToken}`
    // containerRef.current?.appendChild(iframe)

    // Option B: Use WebRTC directly
    // Initialize WebRTC peer connection
    // Connect to signaling server
    // Render video stream to canvas
  }, [deviceId, sessionToken])

  return (
    <div ref={containerRef} className="w-full h-full bg-black rounded-lg overflow-hidden">
      {/* Remote desktop stream renders here */}
    </div>
  )
}
```

## Summary

The dashboard is fully customizable through:
1. Adding new React components for widgets
2. Extending the REST API for new data sources
3. Using WebSocket for real-time updates
4. Tailwind CSS for theming
5. Role-based conditional rendering
6. Chart libraries for data visualization
7. Custom page routes for new views
