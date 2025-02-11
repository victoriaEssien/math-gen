import * as React from "react"
import * as ToastPrimitive from "@radix-ui/react-toast"

export function useToast() {
  const [toasts, setToasts] = React.useState<Array<{
    id: string
    title?: string
    description?: string
    variant?: "default" | "destructive"
  }>>([])

  const toast = React.useCallback(
    ({ title, description, variant = "default" }: {
      title?: string
      description?: string
      variant?: "default" | "destructive"
    }) => {
      const id = Math.random().toString(36).slice(2)
      setToasts((prevToasts) => [...prevToasts, { id, title, description, variant }])

      setTimeout(() => {
        setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id))
      }, 5000)
    },
    []
  )

  return { toast, toasts }
}