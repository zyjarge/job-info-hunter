# 依赖阶段
FROM node:18-alpine AS deps
WORKDIR /app

# 安装依赖所需的额外包
RUN apk add --no-cache libc6-compat

# 复制 package 文件
COPY package.json package-lock.json ./

# 安装依赖
RUN npm ci

# 开发阶段
FROM node:18-alpine AS dev
WORKDIR /app

# 安装依赖所需的额外包
RUN apk add --no-cache libc6-compat

# 复制 package 文件和依赖
COPY package.json package-lock.json ./
COPY --from=deps /app/node_modules ./node_modules

# 设置开发环境
ENV NODE_ENV development
ENV PATH /app/node_modules/.bin:$PATH

# 复制源代码
COPY . .

# 启动开发服务器
CMD ["npm", "run", "dev"]

# 构建阶段
FROM node:18-alpine AS builder
WORKDIR /app

# 从依赖阶段复制 node_modules
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 构建应用
ENV NEXT_TELEMETRY_DISABLED 1
ENV NEXT_LINT_IGNORE_ERRORS=true
ENV NODE_ENV=production
RUN npm run build

# 生产运行阶段
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# 添加非 root 用户
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 复制构建产物和必要文件
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 切换到非 root 用户
USER nextjs

# 暴露端口
EXPOSE 3000

# 环境变量
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# 启动命令
CMD ["node", "server.js"] 