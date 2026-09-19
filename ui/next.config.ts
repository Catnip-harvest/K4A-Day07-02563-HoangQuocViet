import type { NextConfig } from "next";

// The Python API in ui/api_server.py holds the only copy of the lab logic, so the
// browser talks to it through this proxy rather than the UI re-implementing any
// of src/. Same origin, so no CORS handling on the client side.
const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://127.0.0.1:8791/api/:path*" }];
  },
};

export default nextConfig;
