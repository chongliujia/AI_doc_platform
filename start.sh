#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Docker是否安装
check_docker() {
    echo -e "${YELLOW}检查Docker是否安装...${NC}"
    if ! [ -x "$(command -v docker)" ]; then
        echo -e "${RED}Docker没有安装，正在安装Docker...${NC}"
        sudo apt-get update
        sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        sudo apt-get update
        sudo apt-get install -y docker-ce
        sudo systemctl enable docker
        sudo systemctl start docker
        sudo usermod -aG docker $USER
        echo -e "${GREEN}Docker安装完成!${NC}"
        echo -e "${YELLOW}请注销并重新登录以使Docker组权限生效，然后重新运行此脚本${NC}"
        exit 0
    else
        echo -e "${GREEN}Docker已安装!${NC}"
    fi
}

# 检查Docker Compose是否安装
check_docker_compose() {
    echo -e "${YELLOW}检查Docker Compose是否安装...${NC}"
    if ! [ -x "$(command -v docker-compose)" ]; then
        echo -e "${RED}Docker Compose没有安装，正在安装Docker Compose...${NC}"
        sudo curl -L "https://github.com/docker/compose/releases/download/v2.10.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        echo -e "${GREEN}Docker Compose安装完成!${NC}"
    else
        echo -e "${GREEN}Docker Compose已安装!${NC}"
    fi
}

# 检查Node.js和npm是否安装
check_nodejs() {
    echo -e "${YELLOW}检查Node.js是否安装...${NC}"
    if ! [ -x "$(command -v node)" ]; then
        echo -e "${RED}Node.js没有安装，正在安装Node.js...${NC}"
        curl -fsSL https://deb.nodesource.com/setup_16.x | sudo -E bash -
        sudo apt-get install -y nodejs
        echo -e "${GREEN}Node.js安装完成!${NC}"
    else
        echo -e "${GREEN}Node.js已安装!${NC}"
    fi
    
    echo -e "${YELLOW}检查npm是否安装...${NC}"
    if ! [ -x "$(command -v npm)" ]; then
        echo -e "${RED}npm没有安装，正在安装npm...${NC}"
        sudo apt-get install -y npm
        echo -e "${GREEN}npm安装完成!${NC}"
    else
        echo -e "${GREEN}npm已安装!${NC}"
    fi
}

# 创建环境变量文件
create_env_file() {
    if [ ! -f .env ]; then
        echo -e "${YELLOW}创建.env文件...${NC}"
        cat > .env << EOF
# AI服务配置
AI_API_KEY=your_api_key_here
AI_API_ENDPOINT=https://api.deepseek.com/v1

# 日志级别
LOG_LEVEL=INFO

# 其他配置
DEBUG=False
EOF
        echo -e "${GREEN}.env文件创建成功，请编辑填写正确的API密钥${NC}"
    else
        echo -e "${GREEN}.env文件已存在${NC}"
    fi
}

# 创建目录
create_directories() {
    echo -e "${YELLOW}创建必要的目录...${NC}"
    mkdir -p nginx/logs
    mkdir -p backend/generated_docs/downloads
    mkdir -p backend/generated_docs/previews
    chmod -R 777 backend/generated_docs
    echo -e "${GREEN}目录创建完成!${NC}"
}

# 启动前端开发服务器
start_frontend() {
    echo -e "${YELLOW}启动前端开发服务器...${NC}"
    cd frontend
    npm install
    nohup npm run serve > ../frontend.log 2>&1 &
    echo -e "${GREEN}前端开发服务器已启动! 访问地址: http://localhost:3000${NC}"
    cd ..
}

# 构建Docker镜像
build_images() {
    echo -e "${YELLOW}构建Docker镜像...${NC}"
    docker-compose build
    echo -e "${GREEN}Docker镜像构建完成!${NC}"
}

# 启动服务
start_services() {
    echo -e "${YELLOW}启动服务...${NC}"
    docker-compose up -d
    echo -e "${GREEN}服务已启动!${NC}"
    echo -e "${GREEN}访问地址: http://localhost:8080${NC}"
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}停止服务...${NC}"
    docker-compose down
    echo -e "${GREEN}服务已停止!${NC}"
    
    # 检查前端服务是否运行，如果是则停止
    if pgrep -f "npm run serve" > /dev/null; then
        echo -e "${YELLOW}停止前端开发服务器...${NC}"
        pkill -f "npm run serve"
        echo -e "${GREEN}前端开发服务器已停止!${NC}"
    fi
}

# 查看日志
view_logs() {
    echo -e "${YELLOW}查看服务日志...${NC}"
    docker-compose logs -f
}

# 查看前端日志
view_frontend_logs() {
    echo -e "${YELLOW}查看前端开发服务器日志...${NC}"
    tail -f frontend.log
}

# 显示菜单
show_menu() {
    echo -e "${YELLOW}=== AI文档平台管理 ===${NC}"
    echo -e "${GREEN}1.${NC} 检查环境并初始化"
    echo -e "${GREEN}2.${NC} 构建Docker镜像"
    echo -e "${GREEN}3.${NC} 启动服务 (包含前端开发服务器)"
    echo -e "${GREEN}4.${NC} 仅启动后端和Nginx服务 (不含前端)"
    echo -e "${GREEN}5.${NC} 仅启动前端开发服务器"
    echo -e "${GREEN}6.${NC} 停止所有服务"
    echo -e "${GREEN}7.${NC} 查看容器日志"
    echo -e "${GREEN}8.${NC} 查看前端日志"
    echo -e "${GREEN}0.${NC} 退出"
    echo -e "${YELLOW}======================${NC}"
    read -p "请选择操作 [0-8]: " choice
    
    case $choice in
        1)
            check_docker
            check_docker_compose
            check_nodejs
            create_env_file
            create_directories
            ;;
        2)
            build_images
            ;;
        3)
            start_frontend
            start_services
            ;;
        4)
            start_services
            ;;
        5)
            start_frontend
            ;;
        6)
            stop_services
            ;;
        7)
            view_logs
            ;;
        8)
            view_frontend_logs
            ;;
        0)
            echo -e "${GREEN}退出程序${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}无效选择，请重新输入${NC}"
            ;;
    esac
    
    # 显示菜单直到用户选择退出
    if [ "$choice" != "0" ]; then
        echo ""
        show_menu
    fi
}

# 主程序
echo -e "${GREEN}AI文档平台部署脚本${NC}"
show_menu 