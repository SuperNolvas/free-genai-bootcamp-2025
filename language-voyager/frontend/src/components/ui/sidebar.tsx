import * as React from "react"
import { createContext, useContext, useEffect, useState } from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const sidebarVariants = cva(
  "fixed left-0 top-0 z-40 h-screen transition-transform",
  {
    variants: {
      variant: {
        default: "w-64",
        slim: "w-16",
      },
      position: {
        left: "left-0",
        right: "right-0",
      },
    },
    defaultVariants: {
      variant: "default",
      position: "left",
    },
  }
)

interface SidebarContextValue {
  isOpen: boolean
  setIsOpen: (value: boolean) => void
}

const SidebarContext = createContext<SidebarContextValue>({
  isOpen: true,
  setIsOpen: () => undefined,
})

interface SidebarProviderProps {
  children: React.ReactNode
  defaultIsOpen?: boolean
}

export function SidebarProvider({
  children,
  defaultIsOpen = true,
}: SidebarProviderProps) {
  const [isOpen, setIsOpen] = useState(defaultIsOpen)

  return (
    <SidebarContext.Provider value={{ isOpen, setIsOpen }}>
      {children}
    </SidebarContext.Provider>
  )
}

export const useSidebar = () => {
  const context = useContext(SidebarContext)
  if (context === undefined) {
    throw new Error("useSidebar must be used within a SidebarProvider")
  }
  return context
}

interface SidebarProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof sidebarVariants> {
  className?: string
}

export function Sidebar({ className, variant, position, ...props }: SidebarProps) {
  const { isOpen } = useSidebar()

  return (
    <aside
      className={cn(
        sidebarVariants({ variant, position }),
        isOpen ? "translate-x-0" : "-translate-x-full",
        className
      )}
      {...props}
    />
  )
}

export function SidebarHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-4 py-3", className)} {...props} />
}

export function SidebarContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-4 py-2", className)} {...props} />
}

export function SidebarFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("mt-auto border-t px-4 py-3", className)} {...props} />
  )
}

export function SidebarInset({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("-mx-4", className)} {...props} />
}

export function SidebarTrigger({
  className,
  children,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { setIsOpen } = useSidebar()

  return (
    <button
      type="button"
      onClick={() => setIsOpen((prev) => !prev)}
      className={cn(
        "inline-flex h-10 w-10 items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export function SidebarRail({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("w-16 border-r", className)} {...props} />
}