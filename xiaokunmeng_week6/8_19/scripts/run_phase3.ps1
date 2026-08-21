$ErrorActionPreference = "Continue"
$root = "8_19"
function Run-Exp($name, $data, $lr0, $box) {
    Write-Output "=== START $name ==="
    New-Item -ItemType Directory -Force -Path "$root\runs\$name" | Out-Null
    python "$root\scripts\train_exp.py" --name $name --data $data --lr0 $lr0 --box $box --epochs 80 --imgsz 640 --optimizer SGD *> "$root\runs\$name\train_log.txt"
    Write-Output "=== END $name exit=$LASTEXITCODE ==="
    if ($LASTEXITCODE -ne 0) { throw "FAILED $name" }
}
# 阶段3: 数据量对比 (lr0=0.01, box=5.0, 增强数据集 313 图 vs 42 图)
Run-Exp "e6_data_x3" "data_x3.yaml"  0.01  5.0
Write-Output "PHASE3_ALL_DONE"
