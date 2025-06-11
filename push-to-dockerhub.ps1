param(
    [Parameter(Mandatory=$true)]
    [string]$DockerHubUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$ImageName = "dbgpt-enhanced",
    
    [Parameter(Mandatory=$false)]
    [string]$Tag = "latest"
)

# 设置错误处理
$ErrorActionPreference = "Stop"

Write-Host "=== DB-GPT Enhanced Docker 镜像推送脚本 ===" -ForegroundColor Green
Write-Host "Docker Hub 用户名: $DockerHubUsername" -ForegroundColor Yellow
Write-Host "镜像名称: $ImageName" -ForegroundColor Yellow
Write-Host "标签: $Tag" -ForegroundColor Yellow
Write-Host ""

# 检查Docker是否运行
Write-Host "检查 Docker 是否运行..." -ForegroundColor Cyan
try {
    docker version | Out-Null
    Write-Host "✓ Docker 运行正常" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker 未运行或未安装，请先启动 Docker" -ForegroundColor Red
    exit 1
}

# 检查Dockerfile是否存在
if (-not (Test-Path "Dockerfile.enhanced")) {
    Write-Host "✗ Dockerfile.enhanced 文件不存在" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 找到 Dockerfile.enhanced" -ForegroundColor Green

# 构建镜像
$localImageName = "$ImageName`:$Tag"
$remoteImageName = "$DockerHubUsername/$ImageName`:$Tag"

Write-Host ""
Write-Host "步骤 1: 构建 Docker 镜像..." -ForegroundColor Cyan
Write-Host "构建命令: docker build -f Dockerfile.enhanced -t $localImageName ." -ForegroundColor Gray

try {
    docker build -f Dockerfile.enhanced -t $localImageName .
    if ($LASTEXITCODE -ne 0) {
        throw "Docker build failed"
    }
    Write-Host "✓ 镜像构建成功: $localImageName" -ForegroundColor Green
} catch {
    Write-Host "✗ 镜像构建失败" -ForegroundColor Red
    exit 1
}

# 标记镜像
Write-Host ""
Write-Host "步骤 2: 标记镜像用于推送..." -ForegroundColor Cyan
Write-Host "标记命令: docker tag $localImageName $remoteImageName" -ForegroundColor Gray

try {
    docker tag $localImageName $remoteImageName
    if ($LASTEXITCODE -ne 0) {
        throw "Docker tag failed"
    }
    Write-Host "✓ 镜像标记成功: $remoteImageName" -ForegroundColor Green
} catch {
    Write-Host "✗ 镜像标记失败" -ForegroundColor Red
    exit 1
}

# 登录 Docker Hub
Write-Host ""
Write-Host "步骤 3: 登录 Docker Hub..." -ForegroundColor Cyan
Write-Host "请输入您的 Docker Hub 密码:" -ForegroundColor Yellow

try {
    docker login -u $DockerHubUsername
    if ($LASTEXITCODE -ne 0) {
        throw "Docker login failed"
    }
    Write-Host "✓ Docker Hub 登录成功" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Hub 登录失败" -ForegroundColor Red
    exit 1
}

# 推送镜像
Write-Host ""
Write-Host "步骤 4: 推送镜像到 Docker Hub..." -ForegroundColor Cyan
Write-Host "推送命令: docker push $remoteImageName" -ForegroundColor Gray

try {
    docker push $remoteImageName
    if ($LASTEXITCODE -ne 0) {
        throw "Docker push failed"
    }
    Write-Host "✓ 镜像推送成功!" -ForegroundColor Green
} catch {
    Write-Host "✗ 镜像推送失败" -ForegroundColor Red
    exit 1
}

# 显示成功信息
Write-Host ""
Write-Host "=== 推送完成 ===" -ForegroundColor Green
Write-Host "镜像已成功推送到: $remoteImageName" -ForegroundColor Yellow
Write-Host ""
Write-Host "使用以下命令拉取镜像:" -ForegroundColor Cyan
Write-Host "docker pull $remoteImageName" -ForegroundColor White
Write-Host ""
Write-Host "使用以下命令运行容器:" -ForegroundColor Cyan
Write-Host "docker run -d --name dbgpt-enhanced -p 5670:5670 $remoteImageName" -ForegroundColor White
Write-Host ""

# 清理本地标记的镜像（可选）
$cleanup = Read-Host "是否删除本地标记的镜像 $remoteImageName? (y/N)"
if ($cleanup -eq "y" -or $cleanup -eq "Y") {
    try {
        docker rmi $remoteImageName
        Write-Host "✓ 本地标记镜像已删除" -ForegroundColor Green
    } catch {
        Write-Host "⚠ 删除本地标记镜像失败，但不影响推送结果" -ForegroundColor Yellow
    }
}

Write-Host "脚本执行完成!" -ForegroundColor Green 