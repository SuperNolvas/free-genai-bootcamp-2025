import React from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { MapPin, Book, Award, Settings, Menu } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarTrigger
} from './ui/sidebar'

const navItems = [
  { path: '/map', icon: MapPin, label: 'Map' },
  { path: '/lessons', icon: Book, label: 'Lessons' },
  { path: '/achievements', icon: Award, label: 'Achievements' },
]

const AppSidebar = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { logout } = useAuth()

  const isActive = (path: string) => {
    return location.pathname === path
  }

  return (
    <>
      <SidebarTrigger className="fixed left-4 top-4 lg:hidden">
        <Menu className="h-6 w-6" />
      </SidebarTrigger>
      
      <Sidebar className="border-r">
        <SidebarHeader>
          <h2 className="text-lg font-semibold">Language Voyager</h2>
        </SidebarHeader>

        <SidebarContent>
          <nav className="space-y-2">
            {navItems.map((item) => (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 transition-colors hover:bg-accent hover:text-accent-foreground ${
                  isActive(item.path)
                    ? 'bg-accent text-accent-foreground'
                    : 'text-muted-foreground'
                }`}
              >
                <item.icon className="h-5 w-5" />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </SidebarContent>

        <SidebarFooter className="space-y-2">
          <button
            onClick={() => navigate('/settings')}
            className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 transition-colors hover:bg-accent hover:text-accent-foreground ${
              isActive('/settings')
                ? 'bg-accent text-accent-foreground'
                : 'text-muted-foreground'
            }`}
          >
            <Settings className="h-5 w-5" />
            <span>Settings</span>
          </button>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-destructive hover:text-destructive-foreground"
          >
            <span>Sign out</span>
          </button>
        </SidebarFooter>
      </Sidebar>
    </>
  )
}

export default AppSidebar