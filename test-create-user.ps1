# Simple test for user creation
try {
    # Login
    $loginData = @{
        email = "achraf.zibouhee@gmail.com"
        mot_de_passe = "chevale11"
    } | ConvertTo-Json
    
    $login = Invoke-RestMethod -Uri "https://nginx-gateway.blackbush-661cc25b.spaincentral.azurecontainerapps.io/api/v1/login" -Method POST -Body $loginData -ContentType "application/json"
    $headers = @{ "Authorization" = "Bearer $($login.access_token)"; "Content-Type" = "application/json" }
    
    # Create student
    $student = @{
        nom_utilisateur = "student_test"
        email = "student@test.com"
        mot_de_passe = "pass123"
        nom = "Test"
        prenom = "Student"
        roles = @("student")
        semester = "S1"
        statut_compte = "actif"
    } | ConvertTo-Json
    
    Write-Host "Creating student..."
    $result = Invoke-RestMethod -Uri "https://nginx-gateway.blackbush-661cc25b.spaincentral.azurecontainerapps.io/api/v1/admin/users" -Method POST -Body $student -Headers $headers
    Write-Host "✅ Student created: $($result.nom_utilisateur)"
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $stream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        Write-Host "Details: $($reader.ReadToEnd())"
    }
}
