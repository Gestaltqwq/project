$ErrorActionPreference = "Continue"
$root = "8_19"
function Run-Exp($name, $data, $lr0, $box) {
    Write-Output "=== START $name ==="
    New-Item -ItemType Directory -Force -Path "$root\runs\$name" | Out-Null
    python "$root\scripts\train_exp.py" --name $name --data $data --lr0 $lr0 --box $box --epochs 80 --imgsz 640 --optimizer SGD *> "$root\runs\$name\train_log.txt"
    Write-Output "=== END $name exit=$LASTEXITCODE ==="
    if ($LASTEXITCODE -ne 0) { throw "FAILED $name" }
}
# 阶段2: box 损失权重对比 (lr0 取阶段1最优 0.01)
Run-Exp "e4_box_low"  "data.yaml"  0.01  5.0
Run-Exp "e5_box_high" "data.yaml"  0.01  12.0
Write-Output "PHASE2_ALL_DONE"
