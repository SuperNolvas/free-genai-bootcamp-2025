import React from 'react'
import { useNavigate } from 'react-router-dom'
import { MapPin, Book, Award, Settings, Menu } from 'lucide-react'
import {
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarFooter,
  SidebarTrigger
} from './ui/sidebar'

const AppSidebar = () => {
  const navigate = useNavigate()

  return (
    <>
      <SidebarTrigger className="fixed left-4 top-4 lg:hidden">
        <Menu className="h-6 w-6" />
      </SidebarTrigger>
      
      <Sidebar className="border-r bg-background">
        <SidebarHeader>
          <h2 className="text-lg font-semibold">Language Voyager</h2>
        </SidebarHeader>

        <SidebarContent>
          <nav className="space-y-2">
            <button
              onClick={() => navigate('/map')}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              <MapPin className="h-5 w-5" />
              <span>Map</span>
            </button>
            
            <button
              onClick={() => navigate('/lessons')}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              <Book className="h-5 w-5" />
              <span>Lessons</span>
            </button>
            
            <button
              onClick={() => navigate('/achievements')}
              className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              <Award className="h-5 w-5" />
              <span>Achievements</span>
            </button>
          </nav>
        </SidebarContent>

        <SidebarFooter>
          <button
            onClick={() => navigate('/settings')}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            <Settings className="h-5 w-5" />
            <span>Settings</span>
          </button>
        </SidebarFooter>
      </Sidebar>
    </>
  )
}

export default AppSidebar