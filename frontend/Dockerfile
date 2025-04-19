# 构建阶段
FROM registry.npmmirror.com/node:16 as build-stage

WORKDIR /app

# 设置npm镜像
ARG NPM_REGISTRY=https://registry.npmmirror.com
ENV NPM_CONFIG_REGISTRY=${NPM_REGISTRY}

# 设置环境变量
ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}
ARG NODE_OPTIONS=--max-old-space-size=2048
ENV NODE_OPTIONS=${NODE_OPTIONS}

# 复制package.json和package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制项目文件
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine

# 复制nginx配置
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf

# 从构建阶段复制构建结果到nginx html目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 确保文件夹权限正确
RUN chmod -R 755 /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 