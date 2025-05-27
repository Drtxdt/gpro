# install.ps1

# 强制设置输入输出编码为 UTF-8
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8
chcp 65001 | Out-Null

# 步骤 1：获取当前脚本所在目录（即项目根目录）
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

# 步骤 2：将项目路径添加到用户级环境变量 PATH
$envPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($envPath -notlike "*$projectPath*") {
    # 追加项目路径到 PATH
    [Environment]::SetEnvironmentVariable("Path", "$envPath;$projectPath", "User")
    Write-Host "[√] 已将项目路径添加到环境变量: $projectPath"
} else {
    Write-Host "[!] 环境变量已包含项目路径，无需重复添加"
}

# 步骤 3：配置 PowerShell 的别名
# 检查用户是否有 PowerShell 配置文件，若没有则创建
if (!(Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force
    Write-Host "[√] 已创建 PowerShell 配置文件: $PROFILE"
}

# 定义别名函数并写入配置文件
$aliasCode = @"
function Invoke-GppTranslator {
    python "$projectPath\cpp_translator.py" g++ @args
}
Set-Alias gpro Invoke-GppTranslator
"@

# 检查是否已存在别名配置，避免重复添加
$profileContent = Get-Content $PROFILE -ErrorAction SilentlyContinue
if ($profileContent -notlike "*Invoke-GppTranslator*") {
    Add-Content -Path $PROFILE -Value $aliasCode
    Write-Host "[√] 已添加 g++ 别名到 PowerShell 配置文件"
} else {
    Write-Host "[!] 别名配置已存在，无需重复添加"
}

# 步骤 4：提示用户生效方式
Write-Host "`n[完成] 请重启终端或执行以下命令立即生效:"
Write-Host "  . \$PROFILE"