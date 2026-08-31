# ============================================================
#  一键恢复公网隧道 + 自动更新 Demo 链接
#  用法：.\restore_tunnels.ps1
#  功能：
#    1) 停掉旧的 cpolar 隧道进程
#    2) 重新为 7 个服务建立隧道
#    3) 从日志提取新的公网地址
#    4) 自动更新 ask-my-resume 6 个项目 md 的 demo_url
#    5) 打印最终可发给 HR 的链接清单
#  说明：免费版 cpolar 每次重启地址会变，本脚本保证地址
#       变化后链接同步刷新，无需手动改文件。
# ============================================================

$ErrorActionPreference = 'Stop'

# ---------- 路径自动探测（无需硬编码本机盘符） ----------
$ROOT     = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$PROJECTS = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\content\projects'))
$TOOLS    = Join-Path $ROOT 'tools'

# 探测 cpolar.exe：优先 PATH，其次 tools 常见安装位置
$CPOLAR = (Get-Command cpolar.exe -ErrorAction SilentlyContinue).Source
if (-not $CPOLAR) {
  $candidates = @(
    (Join-Path $TOOLS 'cpolar_exe\cpolar\cpolar.exe'),
    (Join-Path $TOOLS 'cpolar\cpolar.exe'),
    (Join-Path $TOOLS 'cpolar\cpolar_win64\cpolar.exe')
  )
  $CPOLAR = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $CPOLAR) {
  Write-Host '错误：找不到 cpolar.exe。请把它加入 PATH，或放到 <项目根>\tools\cpolar_exe\cpolar\ 下。' -ForegroundColor Red
  exit 1
}

# 服务清单：端口 -> (显示名, 对应项目 md 文件名)
# 8001 是作品集本身，无 md，留空
$services = @(
  @{ port = 8001; name = '作品集';   md = '' },
  @{ port = 8000; name = 'OpsPilot';  md = 'ops-pilot.md' },
  @{ port = 8501; name = 'AgentHub';  md = 'agenthub.md' },
  @{ port = 8502; name = '法律助手';  md = 'legal-assistant.md' },
  @{ port = 8503; name = '智能工作台'; md = 'ai-workbench.md' },
  @{ port = 8504; name = '微调部署';  md = 'finetune-deploy.md' },
  @{ port = 8505; name = '多Agent';   md = 'multiagent.md' }
)

# ---------- 1. 停掉旧隧道 ----------
Write-Host ''
Write-Host '========== 1/5 停止旧隧道 ==========' -ForegroundColor Cyan
$old = Get-Process cpolar -ErrorAction SilentlyContinue
if ($old) {
  $old | Stop-Process -Force
  Write-Host ("已停止 {0} 个旧 cpolar 进程" -f $old.Count) -ForegroundColor Yellow
  Start-Sleep -Seconds 2
} else {
  Write-Host '没有运行中的 cpolar 进程' -ForegroundColor DarkGray
}

# ---------- 2. 建立 7 条新隧道 ----------
Write-Host ''
Write-Host '========== 2/5 建立新隧道 ==========' -ForegroundColor Cyan
foreach ($svc in $services) {
  $log = Join-Path $TOOLS "cpolar_$($svc.port).log"
  $err = Join-Path $TOOLS "cpolar_$($svc.port)_err.log"
  Remove-Item $log, $err -ErrorAction SilentlyContinue
  Start-Process -FilePath $CPOLAR -ArgumentList 'http', "$($svc.port)", '--log', 'stdout' `
    -RedirectStandardOutput $log -RedirectStandardError $err -WindowStyle Hidden
  Write-Host ("[启动] {0}  端口 {1}" -f $svc.name, $svc.port) -ForegroundColor Green
  Start-Sleep -Milliseconds 1200
}

# ---------- 3. 轮询等待地址 ----------
Write-Host ''
Write-Host '========== 3/5 等待公网地址分配 ==========' -ForegroundColor Cyan
$deadline = (Get-Date).AddSeconds(90)
$urlMap = @{}
while ($urlMap.Count -lt $services.Count -and (Get-Date) -lt $deadline) {
  foreach ($svc in $services) {
    if ($urlMap.ContainsKey($svc.port)) { continue }
    $log = Join-Path $TOOLS "cpolar_$($svc.port).log"
    if (Test-Path $log) {
      $m = Select-String -Path $log -Pattern 'Tunnel established at (https://\S+)' -ErrorAction SilentlyContinue | Select-Object -Last 1
      if (-not $m) {
        $m = Select-String -Path $log -Pattern 'PublicUrl":"(https://[^"]+)"' -ErrorAction SilentlyContinue | Select-Object -Last 1
      }
      if ($m) {
        $urlMap[$svc.port] = $m.Matches[0].Groups[1].Value.TrimEnd('"')
        Write-Host ("[成功] {0} -> {1}" -f $svc.name, $urlMap[$svc.port]) -ForegroundColor Green
      }
    }
  }
  if ($urlMap.Count -lt $services.Count) { Start-Sleep -Seconds 2 }
}

if ($urlMap.Count -lt $services.Count) {
  $missing = ($services | Where-Object { -not $urlMap.ContainsKey($_.port) } | ForEach-Object { "$($_.name):$($_.port)" }) -join ', '
  Write-Host ("警告：部分隧道未获取到地址 -> {0}（可稍后重跑脚本）" -f $missing) -ForegroundColor Red
}

# ---------- 4. 更新 md 的 demo_url ----------
Write-Host ''
Write-Host '========== 4/5 更新 Demo 链接 ==========' -ForegroundColor Cyan
foreach ($svc in $services) {
  if (-not $svc.md -or -not $urlMap.ContainsKey($svc.port)) { continue }
  $file = Join-Path $PROJECTS $svc.md
  if (-not (Test-Path $file)) { Write-Host ("跳过，找不到 {0}" -f $file) -ForegroundColor DarkGray; continue }
  $content = Get-Content $file -Raw -Encoding UTF8
  if ($content -match 'demo_url:') {
    # 兼容旧值两种格式：http://127.0.0.1:port 或 上次的 https://xxx.cpolar.cn / .top
    $content = $content -replace 'demo_url: http://127\.0\.0\.1:\d+', "demo_url: $($urlMap[$svc.port])"
    $content = $content -replace 'demo_url: https://[a-z0-9.]+\.(cpolar\.cn|cpolar\.top)', "demo_url: $($urlMap[$svc.port])"
    [System.IO.File]::WriteAllText($file, $content, (New-Object System.Text.UTF8Encoding $false))
    Write-Host ("[更新] {0,-8} {1}" -f $svc.name, $urlMap[$svc.port]) -ForegroundColor Green
  } else {
    Write-Host ("跳过，{0} 中没有 demo_url 字段" -f $svc.md) -ForegroundColor DarkGray
  }
}

# ---------- 5. 输出链接清单 ----------
Write-Host ''
Write-Host '========== 5/5 公网链接清单 ==========' -ForegroundColor Cyan
$portfolio = $urlMap[8001]
if ($portfolio) {
  Write-Host "  作品集 : $portfolio" -ForegroundColor White
  Write-Host ''
  Write-Host '  以下 Demo 链接已写入项目详情页，点开即玩：' -ForegroundColor DarkGray
}
foreach ($svc in $services) {
  if ($svc.port -eq 8001) { continue }
  if ($urlMap.ContainsKey($svc.port)) {
    Write-Host ("  {0,-8} : {1}" -f $svc.name, $urlMap[$svc.port]) -ForegroundColor White
  } else {
    Write-Host ("  {0,-8} : (未获取到地址)" -f $svc.name) -ForegroundColor Red
  }
}
Write-Host ''
Write-Host '提示：作品集详情页的 Demo 按钮会读取上面地址，直接可用。' -ForegroundColor Yellow
Write-Host ''