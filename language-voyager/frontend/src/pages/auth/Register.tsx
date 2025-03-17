import React from 'react'
import { Link } from 'react-router-dom'

const Register = () => {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-6 p-6">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold">Create an account</h1>
          <p className="text-muted-foreground">Enter your details to get started</p>
        </div>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium" htmlFor="name">
              Name
            </label>
            <input
              id="name"
              className="w-full rounded-md border p-2"
              placeholder="John Doe"
            />
          </div>
          <div>
            <label className="text-sm font-medium" htmlFor="email">
              Email
            </label>
            <input
              id="email"
              className="w-full rounded-md border p-2"
              placeholder="m@example.com"
              type="email"
            />
          </div>
          <div>
            <label className="text-sm font-medium" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              className="w-full rounded-md border p-2"
              type="password"
            />
          </div>
          <button className="w-full rounded-md bg-primary p-2 text-white">
            Sign up
          </button>
          <div className="text-center text-sm">
            Already have an account?{" "}
            <Link className="underline" to="/auth/login">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Register