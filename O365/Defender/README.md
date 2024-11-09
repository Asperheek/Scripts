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
