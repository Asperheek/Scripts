# Manage Multi-Tenant blocks in the Tenant Allow/Block List
# Usage: & .\Update-TenantBlockList.ps1  "C:\Users\AsimAkram\Downloads\tenants.csv"

param (
    [string]$csvPath
)

# Load the PowerShell module for Exchange Online
Import-Module ExchangeOnlineManagement

# Display initial information
Write-Host "[info] This version of the script only works for senders and domains." -ForegroundColor Red
Write-Host "[info] Script version: v1.0.1" -ForegroundColor Cyan
Write-Host "[info] Author's GitHub: https://github.com/Asperheek/" -ForegroundColor Cyan

# Display banner
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "                       Tenant Allow / Block List          " -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "                     Manage Multi-Tenant Block List             " -ForegroundColor Yellow
Write-Host "---------------------------------------------------------------------" -ForegroundColor Cyan

# Check if CSV path was provided and exists
if (-not $csvPath -or -not (Test-Path -Path $csvPath)) {
    Write-Host "Tenant CSV file not provided or not found. Usage: .\Update-TenantBlockList.ps1 '<CSV file path>'" -ForegroundColor Red
    exit
}

# Import tenant information from CSV file
$CompanyList = Import-Csv -Path $csvPath

# Prompt user to select action: Add block or Remove block
$action = Read-Host -Prompt "Choose action:
1) Add Block for Sender/Domain
2) Remove Block for Sender/Domain
Enter choice (1 or 2)"

# Handle action choice
if ($action -eq "1") {
    # Add Block Section

    # Prompt user to input notes for the block
    $Notes = Read-Host "Enter the reason for the block request"

    # Choose input method
    $inputMethod = Read-Host "Choose input method:
    1) Manual Entry 
    2) CSV file
    Enter choice (1 or 2)"

    # Initialize blocked domains array
    $BlockedDomains = @()

    if ($inputMethod -eq "1") {
        # Manual entry: input domains separated by commas
        $domainInput = Read-Host "Enter domain or address to block, separated by commas (e.g., exampletest.com, test@exampletest.com)"
        $BlockedDomains = $domainInput -split ",\s*"
    } elseif ($inputMethod -eq "2") {
        # CSV file input: prompt for file path
        $domainCsvPath = Read-Host "Enter the full path to the CSV file (with a single 'IOC' column)"
        if (Test-Path -Path $domainCsvPath) {
            # Import domains from CSV file
            $BlockedDomains = Import-Csv -Path $domainCsvPath | ForEach-Object { $_.IOC }
        } else {
            Write-Host "CSV file not found. Exiting Script." -ForegroundColor Red
            exit
        }
    } else {
        Write-Host "Invalid input. Please select 1 or 2. Exiting Script." -ForegroundColor Red
        exit
    }

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

    # Initialize array to store block summary information
    $AllBlockSummary = @()

    # Loop through each tenant to apply blocks
    foreach ($Company in $CompanyList) {
        $UserName = $Company.UserName
        $TenantName = $Company.Tenant

        Write-Host ("[+] Connecting to tenant: {0}" -f $TenantName) -ForegroundColor Cyan
        Connect-ExchangeOnline -UserPrincipalName $UserName

        # Loop through each domain to apply blocks
        foreach ($Domain in $BlockedDomains) {
            Write-Host ("[+] Processing block for {0} in {1}" -f $Domain, $TenantName) -ForegroundColor Yellow

            try {
                # Set block status based on expiration choice
                if ($noExpiration) {
                    $Status = New-TenantAllowBlockListItems -ListType Sender -Entries $Domain -Block -NoExpiration -Notes $Notes
                } else {
                    $Status = New-TenantAllowBlockListItems -ListType Sender -Entries $Domain -Block -ExpirationDate $expirationDate -Notes $Notes
                }

                if ($Status) {
                    Write-Host ("[+] Block successfully applied for {0} in {1}" -f $Domain, $TenantName) -ForegroundColor Green
                    $BlockEntry = [PSCustomObject]@{
                        Timestamp  = Get-Date -Format s
                        Domain     = $Domain
                        Tenant     = $TenantName
                        Expiration = if ($noExpiration) { "Never" } else { $expirationDate }
                        Notes      = $Notes
                    }
                    # Add entry to block summary
                    $AllBlockSummary += $BlockEntry
                } else {
                    Write-Host "[x] Failed to add block for $Domain" -ForegroundColor Red
                }
            } catch {
                Write-Host "[!] Error occurred adding block for: $_" -ForegroundColor Red
            }
        }

        # Disconnect from tenant
        Disconnect-ExchangeOnline -Confirm:$false
        Write-Host ("[-] Disconnected from tenant: {0}" -f $TenantName) -ForegroundColor Cyan
    }

    # Display summary of all blocks applied across tenants
    Write-Host "Summary of all blocked items across tenants:" -ForegroundColor Cyan
    $AllBlockSummary | Format-Table -AutoSize

} elseif ($action -eq "2") {
    # Remove block for each tenant

    # Prompt for domains or addresses to remove from block list, separated by commas
    $RemoveDomains = Read-Host "Enter domain or address to remove from block list, separated by commas (e.g., exampletest.com, test@exampletest.com)"
    $RemoveDomainList = $RemoveDomains -split ",\s*"

    # Initialize an array to hold all removed block data across tenants
    $AllRemovedSummary = @()

    # Loop through each tenant to remove blocks
    foreach ($Company in $CompanyList) {
        $UserName = $Company.UserName
        $TenantName = $Company.Tenant

        Write-Host ("[+] Connecting to tenant: {0}" -f $TenantName) -ForegroundColor Cyan
        Connect-ExchangeOnline -UserPrincipalName $UserName

        # Loop through each domain to remove blocks
        foreach ($Domain in $RemoveDomainList) {
            Write-Host ("[+] Processing removal for {0} in {1}" -f $Domain, $TenantName) -ForegroundColor Yellow

            try {
                # Attempt to remove block for each specified domain
                $RemoveStatus = Remove-TenantAllowBlockListItems -ListType Sender -Entries $Domain
                if ($RemoveStatus) {
                    Write-Host ("[+] Successfully removed block for {0} in {1}" -f $Domain, $TenantName) -ForegroundColor Green
                    $RemovedEntry = [PSCustomObject]@{
                        Timestamp   = Get-Date -Format s
                        Domain      = $Domain
                        Tenant      = $TenantName
                        Action      = "Removed"
                    }
                    # Add entry to removed summary
                    $AllRemovedSummary += $RemovedEntry
                } else {
                    Write-Host "[x] Failed to remove block for $Domain in $TenantName" -ForegroundColor Red
                }
            } catch {
                Write-Host "[!] Error occurred removing block for: $Domain in $TenantName" -ForegroundColor Red
            }
        }

        # Disconnect from tenant
        Disconnect-ExchangeOnline -Confirm:$false
        Write-Host ("[-] Disconnected from tenant: {0}" -f $TenantName) -ForegroundColor Cyan
    }

    # Display summary of all removed blocks across tenants
    Write-Host "Summary of all removed items across tenants:" -ForegroundColor Cyan
    $AllRemovedSummary | Format-Table -AutoSize

} else {
    Write-Host "Invalid action. Please select 1 or 2. Exiting Script." -ForegroundColor Red
    exit
}
