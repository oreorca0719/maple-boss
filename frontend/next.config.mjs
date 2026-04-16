/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",   // Docker 배포용
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "open.api.nexon.com",
      },
    ],
  },
  // 브라우저 → Next.js(same-origin) → FastAPI(내부) : CORS 완전 제거
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
