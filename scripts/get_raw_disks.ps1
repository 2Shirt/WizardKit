# WizardKit: Get RAW disks

Get-Disk | Where-Object {$_.PartitionStyle -eq "RAW"} | Select FriendlyName,Size,PartitionStyle | ConvertTo-JSON