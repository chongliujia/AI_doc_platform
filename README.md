# AI 文档生成平台

智能文档生成平台，支持Word文档、PPT演示文稿和PDF报告的自动生成。

## 系统功能

- 自动生成专业PPT演示文稿
- 创建结构良好的Word文档
- 生成格式规范的PDF报告
- 支持多种模板和自定义选项
- 提供实时文档生成进度反馈

## 部署指南 (Ubuntu推荐)

### 前置条件

- Ubuntu 20.04 LTS 或更高版本 (推荐)
- Docker 和 Docker Compose
- 可用的AI服务API密钥

### 快速部署

本项目提供了一键部署脚本，可以自动安装所需依赖并启动服务：

```bash
# 克隆代码库
git clone https://github.com/yourusername/AI_doc_platform.git
cd AI_doc_platform

# 给脚本执行权限
chmod +x start.sh

# 运行部署脚本
./start.sh
```

按照脚本提示操作，首先选择"1"检查环境并初始化，然后选择"2"构建镜像，最后选择"3"启动服务。

### 修改配置

1. 编辑 `.env` 文件，配置AI服务API密钥:
```
AI_API_KEY=your_api_key_here
AI_API_ENDPOINT=https://api.deepseek.com/v1
```

2. 如果需要修改端口映射，编辑 `docker-compose.yml` 文件。

### 手动部署步骤

如果不想使用自动脚本，也可以手动执行以下步骤：

1. 安装Docker和Docker Compose
```bash
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install -y docker-ce
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.10.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. 创建必要的目录和配置文件
```bash
mkdir -p nginx/logs
mkdir -p backend/generated_docs/downloads
mkdir -p backend/generated_docs/previews
chmod -R 777 backend/generated_docs
```

3. 创建环境变量文件
```bash
cat > .env << EOF
# AI服务配置
AI_API_KEY=your_api_key_here
AI_API_ENDPOINT=https://api.deepseek.com/v1

# 日志级别
LOG_LEVEL=INFO

# 其他配置
DEBUG=False
EOF
```

4. 构建和启动服务
```bash
docker-compose build
docker-compose up -d
```

## 访问服务

部署完成后，通过以下地址访问服务：

- Web界面: http://localhost:8080
- API文档: http://localhost:8080/api/docs

## 常见问题

### 服务无法启动

检查以下几点：
- Docker和Docker Compose是否正确安装
- 端口8080和8001是否被占用
- 查看日志：`docker-compose logs`

### 文档生成超时

如果遇到文档生成超时问题：
- 检查API密钥是否正确
- 编辑`frontend/src/services/api.js`，增加请求超时时间
- 检查`nginx/nginx.conf`中的超时设置

## 开发指南

参考各目录下的README文件获取更多开发信息：
- `frontend/README.md` - 前端开发指南
- `backend/README.md` - 后端API开发指南

## 许可证

[MIT License](LICENSE)
