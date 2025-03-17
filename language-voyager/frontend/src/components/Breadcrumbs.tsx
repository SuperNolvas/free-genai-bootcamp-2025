import { useLocation } from 'react-router-dom'
import { useSelector } from 'react-redux'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { useNavigation } from '@/context/NavigationContext'
import { RootState } from '../store/store'

// Define route mappings for breadcrumbs
const routeMappings: { [key: string]: string } = {
  '': 'Dashboard',
  'dashboard': 'Dashboard',
  'study-activities': 'Study Activities',
  'words': 'Words',
  'groups': 'Word Groups',
  'sessions': 'Study Sessions',
  'settings': 'Settings',
  'launch': 'Launch'
}

export default function Breadcrumbs() {
  const location = useLocation()
  const { currentGroup, currentWord, currentStudyActivity } = useNavigation()
  const { token } = useSelector((state: RootState) => state.auth)
  const pathnames = location.pathname.split('/').filter((x) => x)

  // Hide breadcrumbs on auth pages or when not authenticated
  if (!token || location.pathname.startsWith('/auth/')) {
    return null
  }
  
  // If we're at root, show dashboard
  if (pathnames.length === 0) {
    pathnames.push('')
  }

  const breadcrumbItems = pathnames.map((name, index) => {
    let displayName = routeMappings[name] || name
    
    // Use group, word, or activity name for the last item if available
    if (index === pathnames.length - 1 || (name !== 'launch' && index === pathnames.length - 2)) {
      if (currentGroup && name === currentGroup.id.toString()) {
        displayName = currentGroup.name
      } else if (currentWord && name === currentWord.id.toString()) {
        displayName = currentWord.kanji
      } else if (currentStudyActivity && name === currentStudyActivity.id.toString()) {
        displayName = currentStudyActivity.title
      }
    }

    const isLast = index === pathnames.length - 1
    const path = `/${pathnames.slice(0, index + 1).join('/')}`

    return {
      name: displayName,
      path,
      isLast,
    }
  })

  return (
    <div className="flex items-center gap-4 mb-8 px-4">
      <SidebarTrigger />
      <Breadcrumb>
        <BreadcrumbList>
          {breadcrumbItems.map((item, index) => (
            <React.Fragment key={item.path}>
              {index > 0 && <BreadcrumbSeparator />}
              <BreadcrumbItem>
                {item.isLast ? (
                  <BreadcrumbPage>{item.name}</BreadcrumbPage>
                ) : (
                  <BreadcrumbLink href={item.path}>
                    {item.name}
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
            </React.Fragment>
          ))}
        </BreadcrumbList>
      </Breadcrumb>
    </div>
  )
}