import React from 'react'
import { useTheme } from '@/components/theme-provider'

const Settings = () => {
  const { theme, setTheme } = useTheme()

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Settings</h1>
      <div className="space-y-4">
        <div className="p-4 rounded-lg border">
          <h2 className="text-lg font-semibold mb-2">Theme</h2>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value as "light" | "dark" | "system")}
            className="w-full p-2 rounded-md border bg-background"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">System</option>
          </select>
        </div>
      </div>
    </div>
  )
}

export default Settings