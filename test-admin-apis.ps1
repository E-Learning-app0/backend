# Admin API Testing Script

try {
    # Login to get admin token
    Write-Host "=== ADMIN API TESTING ==="
    Write-Host "Logging in..."
    
    $loginData = @{
        email = "achraf.zibouhee@gmail.com"
        mot_de_passe = "chevale11"
    } | ConvertTo-Json -Depth 3
    
    $loginResponse = Invoke-RestMethod -Uri "https://nginx-gateway.blackbush-661cc25b.spaincentral.azurecontainerapps.io/api/v1/login" -Method POST -Body $loginData -ContentType "application/json"
    
    Write-Host "✅ Login successful"
    
    $token = $loginResponse.access_token
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    
    # Test endpoints
    $endpoints = @(
        @{ name = "List Users"; url = "/api/v1/admin/users"; method = "GET" },
        @{ name = "User Statistics"; url = "/api/v1/admin/stats/users"; method = "GET" }
    )
    
    foreach ($endpoint in $endpoints) {
        Write-Host "`n--- Testing: $($endpoint.name) ---"
        Write-Host "URL: $($endpoint.url)"
        
        try {
            $response = Invoke-RestMethod -Uri "https://nginx-gateway.blackbush-661cc25b.spaincentral.azurecontainerapps.io$($endpoint.url)" -Method $endpoint.method -Headers $headers
            Write-Host "✅ SUCCESS"
            
            if ($endpoint.name -eq "List Users") {
                Write-Host "   Total users: $($response.total)"
                Write-Host "   Users returned: $($response.users.Count)"
                if ($response.users -and $response.users.Count -gt 0) {
                    Write-Host "   First user: $($response.users[0].nom_utilisateur)"
                }
            }
            elseif ($endpoint.name -eq "User Statistics") {
                Write-Host "   Total: $($response.total_users)"
                Write-Host "   Students: $($response.students)"
                Write-Host "   Teachers: $($response.teachers)"
                Write-Host "   Admins: $($response.admins)"
            }
            
        } catch {
            Write-Host "❌ FAILED"
            Write-Host "   Error: $($_.Exception.Message)"
            Write-Host "   Status Code: $($_.Exception.Response.StatusCode)"
            
            # Try to get more error details
            try {
                $errorStream = $_.Exception.Response.GetResponseStream()
                $reader = New-Object System.IO.StreamReader($errorStream)
                $errorBody = $reader.ReadToEnd()
                Write-Host "   Response Body: $errorBody"
            } catch {
                Write-Host "   Could not read error details"
            }
        }
    }
    
} catch {
    Write-Host "❌ Script failed: $($_.Exception.Message)"
}
