/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // 开发阶段禁用一些严格检查
  eslint: {
    ignoreDuringBuilds: true,
    // 开发时也忽略 ESLint 错误
    ignoreDevelopment: true
  },
  typescript: {
    ignoreBuildErrors: true,
    // 开发时也忽略类型错误
    ignoreDevelopment: true
  },
  // 允许在开发时进行热更新
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      config.watchOptions = {
        ...config.watchOptions,
        poll: 800,
        aggregateTimeout: 300,
      }
    }
    return config
  },
  // 开发时的额外配置
  experimental: {
    // 允许更大的页面大小
    largePageDataBytes: 128 * 100000,
  }
}

module.exports = nextConfig 