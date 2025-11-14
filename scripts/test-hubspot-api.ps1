# HubSpot API Testing - Personal Access Key Version
# Set your HubSpot Personal Access Key as an environment variable:
# $env:HUBSPOT_ACCESS_TOKEN = "your-token-here"
$token = $env:HUBSPOT_ACCESS_TOKEN

if (-not $token) {
    Write-Host "❌ Error: HUBSPOT_ACCESS_TOKEN environment variable not set" -ForegroundColor Red
    Write-Host "Set it with: `$env:HUBSPOT_ACCESS_TOKEN = 'your-token-here'" -ForegroundColor Yellow
    exit 1
}

function Test-HubSpotAPI {
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [object]$Body = $null
    )
    
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    try {
        if ($Body) {
            $jsonBody = $Body | ConvertTo-Json -Depth 10
            $result = Invoke-RestMethod -Uri $Endpoint -Method $Method -Headers $headers -Body $jsonBody
        } else {
            $result = Invoke-RestMethod -Uri $Endpoint -Method $Method -Headers $headers
        }
        return $result
    }
    catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "Response: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
        }
        return $null
    }
}

Write-Host "🔍 HubSpot API Testing Tool" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Test 1: Get Portal Info
Write-Host "Test 1: Getting Portal Information..." -ForegroundColor Yellow
$portalInfo = Test-HubSpotAPI -Endpoint "https://api.hubapi.com/account-info/v3/details"
if ($portalInfo) {
    Write-Host "✅ Success! Portal ID: $($portalInfo.portalId)" -ForegroundColor Green
    Write-Host "   Portal Name: $($portalInfo.name)" -ForegroundColor Gray
    Write-Host ""
}

# Test 2: Get Contacts
Write-Host "Test 2: Getting Contacts..." -ForegroundColor Yellow
$contacts = Test-HubSpotAPI -Endpoint "https://api.hubapi.com/crm/v3/objects/contacts?limit=5"
if ($contacts) {
    Write-Host "✅ Success! Found $($contacts.results.Count) contacts" -ForegroundColor Green
    Write-Host ""
}

# Test 3: CTF Challenge - Try to access portal 46962361
Write-Host "🎯 CTF Challenge Test" -ForegroundColor Cyan
Write-Host "Target Portal: 46962361" -ForegroundColor Yellow
Write-Host "Testing: Can we access CTF portal?..." -ForegroundColor Yellow
$ctfTest = Test-HubSpotAPI -Endpoint "https://api.hubapi.com/crm/v3/objects/contacts?limit=10"
if ($ctfTest -and $ctfTest.results) {
    Write-Host "Got data, but likely from our own portal (expected)" -ForegroundColor Gray
}

Write-Host "`n✅ API is working! Ready to start bug hunting!" -ForegroundColor Green