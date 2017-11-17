# WK-OS Check
#
# Set some OS specific variables.

$win_info = gp hklm:"\SOFTWARE\Microsoft\Windows NT\CurrentVersion"
if ($win_info.CurrentVersion -match "6.0") {
    $win_version = "Vista"
} elseif ($win_info.CurrentVersion -match "6.1") {
    $win_version = "7"
} elseif ($win_info.CurrentVersion -match "6.2") {
    $win_version = "8"
} elseif ($win_info.CurrentVersion -match "6.3") {
    if ($win_info.CurrentBuildNumber -match "9200") {
        $win_version = "8"
    } elseif ($win_info.CurrentBuildNumber -match "9600") {
        $win_version = "8"
    } elseif ($win_info.CurrentBuildNumber -match "10240") {
        $win_version = "10"
    } elseif ($win_info.CurrentBuildNumber -match "10586") {
        $win_version = "10"
    }
}
$arch = (gci env:processor_architecture).value
$arch = $arch -ireplace 'x86', '32'
$arch = $arch -ireplace 'AMD64', '64'

#$win_info.CurrentBuild
# == vista ==
# 6.0.6000
# 6.0.6001
# 6.0.6002
# ==== 7 ====
# 6.1.7600
# 6.1.7601
# 6.1.7602
# ==== 8 ====
# 6.2.9200
# === 8.1 ===
# 6.3.9200
# === 8.1u ==
# 6.3.9600
# === 10 ==
# 6.3.10240
# === 10 v1511 ==
# 6.3.10586

$os_name = $win_info.ProductName
$os_name += " " + $win_info.CSDVersion
$os_name = $os_name -replace 'Service Pack ', 'SP'
if ($win_info.CurrentBuild -match "9600") {
    $os_name += " Update"
} elseif ($win_info.CurrentBuild -match "10586") {
    $os_name += " Release 1511"
}

# Get activation status
$slmgr = (gci env:windir).value + "\System32\slmgr.vbs"
$win_act = (cscript /nologo $slmgr /xpr) -imatch '^\s'
