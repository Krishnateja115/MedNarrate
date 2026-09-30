import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: process.env.TAURI_ENV ? 'export' : undefined,
  allowedDevOrigins: ['127.0.0.1'],
  trailingSlash: true,
  async rewrites() {
    if (process.env.TAURI_ENV) return [];
    const backendUrl = process.env.MEDNARRATE_API_PROXY_URL || 'http://127.0.0.1:8000';

    return [
      {
        source: '/api/v1/:path*',
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
