import * as React from "react"
import { useLocation, Link } from "react-router-dom"
import { WholeWord, Group, Home, Hourglass, BookOpenText, Settings, LogOut } from "lucide-react"
import { useAuth } from '@/hooks/useAuth'

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarFooter,
} from "@/components/ui/sidebar"

const navItems = [
  { icon: Home, name: 'Dashboard', path: '/dashboard' },
  { icon: BookOpenText, name: 'Study Activities', path: '/study-activities' },
  { icon: WholeWord, name: 'Words', path: '/words' },
  { icon: Group, name: 'Word Groups', path: '/groups' },
  { icon: Hourglass, name: 'Sessions', path: '/sessions' },
  { icon: Settings, name: 'Settings', path: '/settings' },
]

export default function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const location = useLocation()
  const { isAuthenticated, logout, user } = useAuth()
  
  const isActive = (path: string) => {
    if (path === '/dashboard' && location.pathname === '/') return true
    return location.pathname.startsWith(path)
  }
  
  if (!isAuthenticated) return null

  return (
    <Sidebar {...props}>
      <SidebarHeader>
        LangVoyager
        {user && (
          <div className="text-sm text-gray-500 mt-1">
            {user.username}
          </div>
        )}
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.name}>
                  <SidebarMenuButton asChild isActive={isActive(item.path)}>
                    <Link to={item.path}>
                      <item.icon />
                      <span>{item.name}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton onClick={logout}>
                  <LogOut />
                  <span>Logout</span>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}