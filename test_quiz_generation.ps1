$timeoutSec = 900  # 15 minutes timeout
$uri = "https://nginx-gateway.blackbush-661cc25b.spaincentral.azurecontainerapps.io/api/v1/lessonfiles/upload-and-create"
$filePath = "c:\Users\ASUS\Desktop\E-learning_app\backend\test_quiz.pdf"

# Test parameters
$boundary = [System.Guid]::NewGuid().ToString()
$contentType = "multipart/form-data; boundary=$boundary"

# Create multipart form data
$bodyLines = @()
$bodyLines += "--$boundary"
$bodyLines += 'Content-Disposition: form-data; name="lesson_id"'
$bodyLines += ''
$bodyLines += '1'
$bodyLines += "--$boundary"
$bodyLines += 'Content-Disposition: form-data; name="file"; filename="test_quiz.pdf"'
$bodyLines += 'Content-Type: application/pdf'
$bodyLines += ''

# Read file content
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileContent = [System.Text.Encoding]::Latin1.GetString($fileBytes)

$bodyLines += $fileContent
$bodyLines += "--$boundary--"

$body = ($bodyLines -join "`r`n")

# Headers
$headers = @{
    "Authorization" = "Bearer fake-token-for-testing"
    "Content-Type" = $contentType
}

Write-Host "Testing AI quiz generation through NGINX gateway..."
Write-Host "URI: $uri"
Write-Host "Timeout: $timeoutSec seconds"
Write-Host "Starting test at: $(Get-Date)"

try {
    $response = Invoke-WebRequest -Uri $uri -Method POST -Body $body -Headers $headers -TimeoutSec $timeoutSec -UseBasicParsing
    Write-Host "SUCCESS! Status Code: $($response.StatusCode)"
    Write-Host "Response: $($response.Content)"
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        Write-Host "Status Code: $($_.Exception.Response.StatusCode)"
        Write-Host "Status Description: $($_.Exception.Response.StatusDescription)"
    }
}

Write-Host "Test completed at: $(Get-Date)"
