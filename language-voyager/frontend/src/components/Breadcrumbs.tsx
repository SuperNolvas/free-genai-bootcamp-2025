import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from './ui/breadcrumb'

// Define route mappings for breadcrumbs
const routeMappings: { [key: string]: string } = {
  '': 'Home',
  'map': 'Map',
  'lessons': 'Lessons',
  'achievements': 'Achievements',
  'settings': 'Settings'
}

const Breadcrumbs = () => {
  const location = useLocation()
  const paths = location.pathname.split('/').filter(Boolean)

  if (paths.length === 0) {
    return null
  }

  return (
    <Breadcrumb className="px-6 py-4">
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink as={Link} to="/">
            Home
          </BreadcrumbLink>
        </BreadcrumbItem>

        {paths.map((path, index) => {
          const isLast = index === paths.length - 1
          const href = `/${paths.slice(0, index + 1).join('/')}`
          const label = routeMappings[path] || path

          return (
            <React.Fragment key={path}>
              <BreadcrumbSeparator />
              <BreadcrumbItem>
                {isLast ? (
                  <BreadcrumbPage>{label}</BreadcrumbPage>
                ) : (
                  <BreadcrumbLink as={Link} to={href}>
                    {label}
                  </BreadcrumbLink>
                )}
              </BreadcrumbItem>
            </React.Fragment>
          )
        })}
      </BreadcrumbList>
    </Breadcrumb>
  )
}

export default Breadcrumbs