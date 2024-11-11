# Overview
This script manages sender and domain blocks in Microsoft Exchange Online across multiple tenants. With multi-tenancy support, the script can perform bulk operations on various tenants listed in a CSV file, adding or removing blocked domains and senders with flexible expiration settings.

# Prerequisites
> PowerShell 5.1 or later
> 
> ExchangeOnlineManagement module installed.

Run the following to install it:

```
Install-Module ExchangeOnlineManagement
```
# Permissions
Ensure the provided accounts in each tenant have the necessary permissions to manage the Tenant Allow/Block List.

# CSV Format for Tenant Information
The script accepts a CSV file containing tenant information to connect and perform actions. The CSV should have the following format:

```
UserName,Tenant
user1@tenant1.onmicrosoft.com,Tenant 1
user2@tenant2.onmicrosoft.com,Tenant 2
```

# Usage
### Run the script with the path to your tenant CSV file as an argument:


```
.\Update-TenantBlockList.ps1 "C:\path\to\tenants.csv"
```

# References
```
https://learn.microsoft.com/en-us/powershell/module/exchange/connect-exchangeonline?view=exchange-ps
https://learn.microsoft.com/nl-nl/exchange/standalone-eop/sample-script-standalone-eop-settings-to-multiple-tenants
https://practical365.com/tenant-block-list-automation/
```
