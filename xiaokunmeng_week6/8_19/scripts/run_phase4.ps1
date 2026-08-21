$ErrorActionPreference = "Continue"
$root = "8_19"
New-Item -ItemType Directory -Force -Path "$root\runs\e7_subset_full" | Out-Null
Write-Output "=== START e7_subset_full ==="
python "$root\scripts\train_exp.py" --name e7_subset_full --data data_full.yaml --lr0 0.01 --box 5.0 --epochs 80 --imgsz 640 --optimizer SGD *> "$root\runs\e7_subset_full\train_log.txt"
Write-Output "=== END e7 exit=$LASTEXITCODE ==="
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Output "PHASE4_ALL_DONE"
