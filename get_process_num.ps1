$numbrofprc=(Get-Process | Where {$_.ProcessName -eq "WIReportServer"}).count

if ($numbrofprc -eq 2) {
    write-host "OK" nombre de process est $numbrofprc
	exit 0   
    }

if ($numbrofprc -ge 3) {
    write-host "Critical" nombre de process est $numbrofprc
    exit 2   
    }

if ($numbrofprc -eq 0 -OR $numbrofprc -eq 1) {
    write-host "Warning" nombre de process est $numbrofprc
    exit 1   
    }