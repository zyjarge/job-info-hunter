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
  // 禁用热更新
  webpackDevMiddleware: config => {
    config.watchOptions = {
      ignored: ['**/'],  // 忽略所有文件的监视
      poll: false,       // 禁用轮询
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