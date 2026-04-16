import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_PATHS = ["/login", "/signup"];

function buildRedirectUrl(path: string, request: NextRequest): URL {
  // nginx 역방향 프록시 뒤에서 실행되므로 X-Forwarded-* 헤더로 실제 외부 URL을 재구성
  const proto = request.headers.get("x-forwarded-proto") ?? "https";
  const host  = request.headers.get("x-forwarded-host") ?? request.headers.get("host") ?? "localhost";
  return new URL(path, `${proto}://${host}`);
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("maple_token")?.value;

  if (PUBLIC_PATHS.some((p) => pathname.startsWith(p))) {
    if (token) return NextResponse.redirect(buildRedirectUrl("/dashboard", request));
    return NextResponse.next();
  }

  if (!token) {
    return NextResponse.redirect(buildRedirectUrl("/login", request));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api).*)"],
};
