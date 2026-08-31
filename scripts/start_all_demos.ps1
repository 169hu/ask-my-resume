# ============================================================
#  Ask My Resume : 作品集 + 6 个在线演示  一键启动器
#  用法：右键 "以 PowerShell 运行"，或执行 .\start_all_demos.ps1
#  已占用端口的服务自动跳过（不会重复启动）
# ============================================================

# 自动探测项目根目录（脚本位于 <根>\ask-my-resume\scripts 下，无需硬编码盘符）
$ROOT = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))

# 服务清单：(显示名, 端口, 工作目录, 启动命令, 备注)
$services = @(
    @{ name = "作品集后端";    port = 8001; cwd = "$ROOT\ask-my-resume";        cmd = ".venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001"; note = "" },
    @{ name = "OpsPilot 演示"; port = 8000; cwd = "$ROOT\ops-pilot";            cmd = "docker compose up -d --build"; note = "Docker" },
    @{ name = "AgentHub 演示"; port = 8501; cwd = "$ROOT\agenthub";             cmd = ".venv\Scripts\python.exe -m streamlit run app.py --server.port 8501 --server.headless true"; note = "" },
    @{ name = "法律助手演示";  port = 8502; cwd = "$ROOT\legal-assistant";      cmd = ".venv\Scripts\python.exe -m streamlit run ui/app.py --server.port 8502 --server.headless true"; note = "" },
    @{ name = "智能工作台演示"; port = 8503; cwd = "$ROOT\ai-workbench";        cmd = ".venv\Scripts\python.exe -m streamlit run app.py --server.port 8503 --server.headless true"; note = "" },
    @{ name = "微调部署演示";  port = 8504; cwd = "$ROOT\FinetuningProject";    cmd = ".venv\Scripts\python.exe -m streamlit run app.py --server.port 8504 --server.headless true"; note = "首次模型加载约1-2分钟" },
    @{ name = "多Agent 演示";  port = 8505; cwd = "$ROOT\MultiAgentPlayground"; cmd = ".venv\Scripts\python.exe -m streamlit run app.py --server.port 8505 --server.headless true"; note = "" }
)

function Test-PortListening([int]$port) {
    try {
        return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop)
    } catch {
        return $false
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Ask My Resume : 作品集 + 6 个在线演示  一键启动器" -ForegroundColor Cyan
Write-Host "  已占用端口的服务自动跳过（不会重复启动）" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

foreach ($svc in $services) {
    $url = "http://127.0.0.1:$($svc.port)"
    if (Test-PortListening $svc.port) {
        Write-Host ("[SKIP]  {0,-12} {1}  (已在运行)" -f $svc.name, $url) -ForegroundColor DarkGray
    } else {
        $extra = if ($svc.note) { "  ($($svc.note))" } else { "" }
        Write-Host ("[START] {0,-12} {1}{2}" -f $svc.name, $url, $extra) -ForegroundColor Green
        $psi = Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "cd /d `"$($svc.cwd)`" && $($svc.cmd)" -WindowStyle Normal
        Start-Sleep -Milliseconds 800
    }
    Write-Host ""
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  启动完成！访问地址：" -ForegroundColor Cyan
Write-Host "  ------------------------------------------------"
Write-Host "  作品集     http://127.0.0.1:8001/"
Write-Host "  OpsPilot   http://127.0.0.1:8000/   (Docker)"
Write-Host "  AgentHub   http://127.0.0.1:8501/"
Write-Host "  法律助手   http://127.0.0.1:8502/"
Write-Host "  智能工作台 http://127.0.0.1:8503/"
Write-Host "  微调部署   http://127.0.0.1:8504/   (首次模型加载约1-2分钟)"
Write-Host "  多Agent    http://127.0.0.1:8505/"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "提示：每个服务有独立窗口，关闭对应窗口即停止该服务。" -ForegroundColor Yellow
Write-Host ""
Pause