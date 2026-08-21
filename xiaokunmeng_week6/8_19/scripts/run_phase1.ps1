$ErrorActionPreference = "Continue"
$root = "8_19"
function Run-Exp($name, $data, $lr0, $box) {
    Write-Output "=== START $name ==="
    New-Item -ItemType Directory -Force -Path "$root\runs\$name" | Out-Null
    python "$root\scripts\train_exp.py" --name $name --data $data --lr0 $lr0 --box $box --epochs 80 --imgsz 640 --optimizer SGD *> "$root\runs\$name\train_log.txt"
    Write-Output "=== END $name exit=$LASTEXITCODE ==="
    if ($LASTEXITCODE -ne 0) { throw "FAILED $name" }
}
# 阶段1: 学习率对比 (box 固定 7.5)
Run-Exp "e1_base"    "data.yaml"  0.01  7.5
Run-Exp "e2_lr_low"  "data.yaml"  0.003 7.5
Run-Exp "e3_lr_high" "data.yaml"  0.03  7.5
Write-Output "PHASE1_ALL_DONE"
