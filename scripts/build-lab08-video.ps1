$ErrorActionPreference = 'Stop'

$ffmpeg = 'C:\Users\Luis Angel\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe'
$python = 'C:\Users\Luis Angel\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$node = 'C:\Users\Luis Angel\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'
$root = Split-Path -Parent $PSScriptRoot
$tmp = Join-Path $root 'tmp\lab08-video'
$segments = Join-Path $tmp 'segments'
$outputDir = Join-Path $root 'output\video'
$output = Join-Path $outputDir 'TechStore_LAB08_Explicativo_1080p60.mp4'

New-Item -ItemType Directory -Force -Path $segments, $outputDir | Out-Null

Push-Location $root
try {
    docker compose up -d --build | Out-Host
    docker compose exec -T db psql -U lab07 -d lab07 -c "UPDATE users SET failed_attempts=0, locked_until=NULL WHERE username IN ('cliente','admin');" | Out-Null
    & $node (Join-Path $PSScriptRoot 'capture_lab08_video_assets.mjs') auth
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron capturar las escenas de autenticación.' }
    docker compose exec -T db psql -U lab07 -d lab07 -c "UPDATE users SET failed_attempts=0, locked_until=NULL WHERE username='cliente';" | Out-Null
    & $node (Join-Path $PSScriptRoot 'capture_lab08_video_assets.mjs') client
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo capturar el catálogo del cliente.' }

    & $python (Join-Path $PSScriptRoot 'build_lab08_video_assets.py')
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron generar las escenas visuales.' }

    Add-Type -AssemblyName System.Speech
    $voice = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $voice.SelectVoice('Microsoft Helena Desktop')
    $voice.Rate = -1
    $voice.Volume = 100
    Get-ChildItem (Join-Path $tmp 'audio') -Filter '*.txt' | Sort-Object Name | ForEach-Object {
        $wav = [IO.Path]::ChangeExtension($_.FullName, '.wav')
        $voice.SetOutputToWaveFile($wav)
        $voice.Speak([IO.File]::ReadAllText($_.FullName, [Text.Encoding]::UTF8))
        $voice.SetOutputToNull()
    }
    $voice.Dispose()

    & $python (Join-Path $PSScriptRoot 'create_lab08_video_timeline.py')
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear la línea de tiempo.' }
    $timeline = Get-Content -Raw (Join-Path $tmp 'timeline.json') | ConvertFrom-Json
    $authMarks = Get-Content -Raw (Join-Path $tmp 'web\auth-marks.json') | ConvertFrom-Json
    $clientMarks = Get-Content -Raw (Join-Path $tmp 'web\client-marks.json') | ConvertFrom-Json
    function Get-MarkTime($marks, $label) {
        return [double](($marks | Where-Object { $_.label -eq $label } | Select-Object -First 1).time)
    }
    $liveScenes = @{
        '03' = @{ file = (Join-Path $tmp 'web\auth-live.webm'); start = (Get-MarkTime $authMarks 'login-start'); end = (Get-MarkTime $authMarks 'failed-start') }
        '04' = @{ file = (Join-Path $tmp 'web\auth-live.webm'); start = (Get-MarkTime $authMarks 'failed-start'); end = (Get-MarkTime $authMarks 'lock-start') }
        '05' = @{ file = (Join-Path $tmp 'web\auth-live.webm'); start = (Get-MarkTime $authMarks 'lock-start'); end = (Get-MarkTime $authMarks 'admin-start') }
        '06' = @{ file = (Join-Path $tmp 'web\auth-live.webm'); start = (Get-MarkTime $authMarks 'admin-start'); end = (Get-MarkTime $authMarks 'roles-start') }
        '08' = @{ file = (Join-Path $tmp 'web\auth-live.webm'); start = (Get-MarkTime $authMarks 'roles-start'); end = (Get-MarkTime $authMarks 'social-start') }
        '12' = @{ file = (Join-Path $tmp 'web\client-live.webm'); start = (Get-MarkTime $clientMarks 'client-login-start'); end = (Get-MarkTime $clientMarks 'end') }
        '13' = @{ file = (Join-Path $tmp 'web\auth-live.webm'); start = (Get-MarkTime $authMarks 'social-start'); end = (Get-MarkTime $authMarks 'end') }
    }
    $concatLines = @()
    foreach ($scene in $timeline) {
        $segment = Join-Path $segments ("{0}.mp4" -f $scene.id)
        $fadeOut = [math]::Max(0.1, [double]$scene.duration - 0.45)
        if ($liveScenes.ContainsKey([string]$scene.id)) {
            $live = $liveScenes[[string]$scene.id]
            $sourceDuration = [math]::Max(0.5, [double]$live.end - [double]$live.start)
            $speedFactor = [double]$scene.duration / $sourceDuration
            $filter = "[0:v]trim=start=$($live.start):end=$($live.end),setpts=PTS-STARTPTS,setpts=$speedFactor*PTS,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=60,fade=t=in:st=0:d=0.35,fade=t=out:st=$fadeOut`:d=0.45,format=yuv420p[v];[1:a]apad=pad_dur=0.85,afade=t=in:st=0:d=0.15,afade=t=out:st=$fadeOut`:d=0.35[a]"
            & $ffmpeg -y -loglevel warning -i $live.file -i $scene.audio -filter_complex $filter -map '[v]' -map '[a]' -t ([string]$scene.duration) -r 60 -c:v libx264 -preset veryfast -crf 19 -c:a aac -b:a 192k -ar 48000 -movflags +faststart $segment
        }
        else {
            $filter = "[0:v]scale=2048:1152,zoompan=z='min(zoom+0.00008,1.045)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=60,fade=t=in:st=0:d=0.35,fade=t=out:st=$fadeOut`:d=0.45,format=yuv420p[v];[1:a]apad=pad_dur=0.85,afade=t=in:st=0:d=0.15,afade=t=out:st=$fadeOut`:d=0.35[a]"
            & $ffmpeg -y -loglevel warning -loop 1 -framerate 60 -i $scene.image -i $scene.audio -filter_complex $filter -map '[v]' -map '[a]' -t ([string]$scene.duration) -r 60 -c:v libx264 -preset veryfast -crf 19 -c:a aac -b:a 192k -ar 48000 -movflags +faststart $segment
        }
        if ($LASTEXITCODE -ne 0) { throw "FFmpeg falló en la escena $($scene.id)." }
        $safe = $segment.Replace("'", "''").Replace('\','/')
        $concatLines += "file '$safe'"
    }

    $concatFile = Join-Path $tmp 'concat.txt'
    $concatLines | Set-Content -Encoding utf8NoBOM $concatFile
    $base = Join-Path $tmp 'base.mp4'
    & $ffmpeg -y -loglevel warning -f concat -safe 0 -i $concatFile -c copy $base
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron concatenar las escenas.' }

    $subtitleFilter = "subtitles='tmp/lab08-video/subtitles.srt':force_style='FontName=Segoe UI,FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H90000000,BorderStyle=3,BackColour=&H78000000,Outline=1,Shadow=0,MarginV=18,Alignment=2'"
    & $ffmpeg -y -loglevel warning -i $base -vf $subtitleFilter -c:v libx264 -preset medium -crf 18 -r 60 -c:a copy -movflags +faststart $output
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron integrar los subtítulos.' }
}
finally {
    Pop-Location
}

Write-Output $output
