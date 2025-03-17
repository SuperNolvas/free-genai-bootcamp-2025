import React from 'react'
import { Link } from 'react-router-dom'

const Login = () => {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-md space-y-6 p-6">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold">Welcome back</h1>
          <p className="text-muted-foreground">Enter your credentials to sign in</p>
        </div>
        <div className="space-y-4">
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
            Sign in
          </button>
          <div className="text-center text-sm">
            Don't have an account?{" "}
            <Link className="underline" to="/auth/register">
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login