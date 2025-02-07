/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // 开发阶段禁用一些严格检查
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // 实验性功能配置
  experimental: {
    // 允许更大的页面大小
    largePageDataBytes: 128 * 100000,
  },
  // Webpack 配置（生产环境使用）
  webpack: (config, { dev, isServer }) => {
    if (dev) {
      config.watchOptions = {
        ignored: ['**/.git/**', '**/node_modules/**'],
        poll: false,
      }
    }
    return config
  }
}

module.exports = nextConfig 