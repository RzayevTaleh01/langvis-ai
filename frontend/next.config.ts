import type { NextConfig } from "next";

// Built as static files (out/) that the Python backend serves on its own
// port, next to its API and WebSocket - one server, one origin.
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
