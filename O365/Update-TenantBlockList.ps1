# Manage allows and blocks in the Tenant Allow/Block List

# Load the PowerShell module for Exchange Online
Import-Module ExchangeOnlineManagement
Connect-ExchangeOnline

# Information
Write-Host "[info] This version of the script only works for senders and domains." -ForegroundColor Red
Write-Host "[info] Script version: v1.0 
[info] Author's github: https://github.com/Asperheek/
"

# Display banner
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "                       Tenant Allow / Block List          " -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "                            Manage Block List             " -ForegroundColor Yellow
Write-Host "---------------------------------------------------------------------" -ForegroundColor Cyan


# Prompt user to select action: Add block or Remove block
$action = Read-Host -Prompt "Choose action:
1) Add Block for Sender/Domain
2) Remove Block for Sender/Domain
Enter choice (1 or 2)"

# Handle action choice
if ($action -eq "1") {
    # Proceed with block addition

    # Prompt user to input notes for the block
    $Notes = Read-Host "Enter the reason for the block"

    # Choose input method
    $inputMethod = Read-Host "Choose input method:
    1) Manual Entry 
    2) CSV file
    Enter choice (1 or 2)"

    # Initialize $BlockedDomains array
    $BlockedDomains = @()

    if ($inputMethod -eq "1") {
        # Manual entry: ask user to input domains separated by commas
        $domainInput = Read-Host "Enter domain or address to block, separated by commas (e.g., exampletest.com, test@exampletest.com)"
        $BlockedDomains = $domainInput -split ",\s*"
    } elseif ($inputMethod -eq "2") {
        # CSV file input: prompt for file path
        $csvPath = Read-Host "Enter the full path to the CSV file (with a single 'IOC' column)"
        if (Test-Path -Path $csvPath) {
            # Import domains from CSV file
            $BlockedDomains = Import-Csv -Path $csvPath | ForEach-Object { $_.IOC }
        } else {
            Write-Host "CSV file not found. Exiting Script." -ForegroundColor Red
            exit
        }
    } else {
        Write-Host "Invalid input. Please select 1 or 2. Exiting Script." -ForegroundColor Red
        exit
    }

    # Blocking each domain in TenantAllowBlockListItems as sender
    # Initialize an array to hold all block data
    $AllBlockData = @()

    # Prompt user for expiration option
    Write-Host "User Input Required" -ForegroundColor Yellow
    $expirationOption = Read-Host -Prompt "Choose expiration option:
    1) Never expire
    2) Expire after 30 days
    3) Expire after 60 days
    4) Expire after 90 days
    Enter choice (1, 2, 3, or 4)"

    # Calculate expiration date if needed
    $expirationDate = $null
    switch ($expirationOption) {
        "1" { $noExpiration = $true }
        "2" { $expirationDate = (Get-Date).AddDays(30).ToUniversalTime() }
        "3" { $expirationDate = (Get-Date).AddDays(60).ToUniversalTime() }
        "4" { $expirationDate = (Get-Date).AddDays(90).ToUniversalTime() }
        default {
            Write-Host "Invalid choice. Exiting script." -ForegroundColor Red
            exit
        }
    }

# Blocking each domain in TenantAllowBlockListItems as sender
    foreach ($Domain in $BlockedDomains) {
        Write-Host ("[+] Processing block for {0}" -f $Domain) -ForegroundColor Yellow

        try {
            # Set block status based on expiration choice
            if ($noExpiration) {
                $Status = New-TenantAllowBlockListItems -ListType Sender -Entries $Domain -Block -NoExpiration -Notes $Notes
            } else {
                $Status = New-TenantAllowBlockListItems -ListType Sender -Entries $Domain -Block -ExpirationDate $expirationDate -Notes $Notes
            }

            if ($Status) {
                Write-Host ("[+] Block successfully applied for {0}" -f $Domain) -ForegroundColor Green
                $BlockData = [PSCustomObject][Ordered]@{
                    Timestamp = Get-Date -Format s
                    Block     = $Domain
                    BlockType = 'Sender'
                    Expiration = if ($noExpiration) { "Never" } else { $expirationDate }
                }
                # Add the block data to the array for final output
                $AllBlockData += $BlockData
            } else {
                Write-Host "[x] Failed to add block for $Domain" -ForegroundColor Red
            }
        } catch {
            Write-Host "[!] Error occurred adding block for: $_" -ForegroundColor Red
        }
}

    # Output all block data at the end
    Write-Host "Summary of all blocked items:" -ForegroundColor Cyan
    $AllBlockData | Format-Table -AutoSize


} elseif ($action -eq "2") {
    # Remove block

    # Prompt for domains or addresses to remove from block list, separated by commas
    $RemoveDomains = Read-Host "Enter domain or address to remove from block list, separated by commas (e.g., exampletest.com, test@exampletest.com)"
    $RemoveDomain = $RemoveDomains -split ",\s*"

    # Initialize an array to hold all removed block data
    $AllRemovedData = @()

    foreach ($Domain in $RemoveDomain) {
        Write-Host ("[+] Processing removal for {0}" -f $Domain) -ForegroundColor Yellow

        try {
            $RemoveStatus = Remove-TenantAllowBlockListItems -ListType Sender -Entries $Domain
            if ($RemoveStatus) {
                Write-Host ("[+] Successfully removed block for {0}" -f $Domain) -ForegroundColor Green
                $RemovedData = [PSCustomObject][Ordered]@{
                    Timestamp = Get-Date -Format s
                    'Removed Block'     = $Domain
                    BlockType = 'Sender'
                }
                # Add the removed data to the array for final output
                $AllRemovedData += $RemovedData
            } else {
                Write-Host ("[x] Failed to remove block for {0}" -f $Domain) -ForegroundColor Red
            }
        } catch {
            Write-Host "[!] Error occurred removing block for: $Domain" -ForegroundColor Red
        }
    }

    # Output all removed block data at the end
    Write-Host "Summary of all removed items:" -ForegroundColor Cyan
    $AllRemovedData | Format-Table -AutoSize

} else {
    Write-Host "Invalid action. Please select 1 or 2. Exiting Script." -ForegroundColor Red
    exit
}

# Disconnect from Exchange Online
Disconnect-ExchangeOnline -Confirm:$false
