import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: process.env.TAURI_ENV ? 'export' : undefined,
  allowedDevOrigins: ['127.0.0.1'],
  trailingSlash: true,
  async rewrites() {
    if (process.env.TAURI_ENV) {
      const publicApi = process.env.NEXT_PUBLIC_API_BASE_URL;
      if (!publicApi?.startsWith('https://')) {
        throw new Error('Desktop builds require NEXT_PUBLIC_API_BASE_URL with a public HTTPS API origin');
      }
      return [];
    }
    const backendUrl = process.env.MEDNARRATE_API_PROXY_URL ||
      (process.env.NODE_ENV === 'production' ? '' : 'http://127.0.0.1:8000');
    if (!backendUrl) {
      throw new Error('Production admin builds require MEDNARRATE_API_PROXY_URL');
    }
    if (process.env.NODE_ENV === 'production' && !backendUrl.startsWith('https://')) {
      throw new Error('Production admin API proxy must use HTTPS');
    }

    return [
      {
        source: '/api/v1/:path*',
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
