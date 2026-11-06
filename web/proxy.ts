import { NextResponse, type NextRequest } from 'next/server'

const API_URL = process.env.API_URL ?? 'http://localhost:8000'
const PROXY_KEY = process.env.PROXY_KEY

export const config = { matcher: '/api/:path*' }

// forwards the visitor's IP so the api can rate limit per visitor, not per Vercel address
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl
  const target = `${API_URL}${pathname.slice('/api'.length)}${search}`

  const headers = new Headers(request.headers)
  // a visitor's own copy of these must never reach the api
  headers.delete('x-jst-proxy-key')
  headers.delete('x-jst-client-ip')
  const ip = clientIp(request)
  if (PROXY_KEY && ip) {
    headers.set('x-jst-proxy-key', PROXY_KEY)
    headers.set('x-jst-client-ip', ip)
  }
  return NextResponse.rewrite(target, { request: { headers } })
}

// vercel sets both from the connection and overwrites whatever the visitor sent
function clientIp(request: NextRequest) {
  return (
    request.headers.get('x-real-ip') ??
    request.headers.get('x-forwarded-for')?.split(',')[0].trim()
  )
}
