# Deploy updated NGINX configuration to Azure Container Apps
# This script updates the nginx-gateway container app with the new internal FQDNs

Write-Host "🔄 Updating NGINX Gateway with corrected internal service FQDNs..." -ForegroundColor Yellow

# Build and push the updated NGINX image (if you're using a custom image)
# docker build -t your-registry.azurecr.io/nginx-gateway:latest .
# docker push your-registry.azurecr.io/nginx-gateway:latest

# Update the container app with new configuration
Write-Host "📝 Updating container app revision..." -ForegroundColor Blue

az containerapp update `
  --name nginx-gateway `
  --resource-group elearning-rg-spain `
  --revision-suffix "internal-fqdn-fix" `
  --output table

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ NGINX Gateway updated successfully!" -ForegroundColor Green
    Write-Host "🌐 Public URL: https://nginx-gateway.blackbush-661cc25b.spaincentral.azurecontainerapps.io" -ForegroundColor Cyan
    
    Write-Host "`n🧪 Testing the connection..." -ForegroundColor Yellow
    
    # Wait a moment for the revision to be ready
    Start-Sleep -Seconds 30
    
    # Test the health endpoint
    Write-Host "Testing health endpoint..."
    curl.exe -i "https://nginx-gateway.blackbush-661cc25b.spaincentral.azurecontainerapps.io/health"
    
    Write-Host "`nTesting auth service through gateway..."
    curl.exe -i -X POST "https://nginx-gateway.blackbush-661cc25b.spaincentral.azurecontainerapps.io/api/v1/login" `
      -H "Content-Type: application/json" `
      -d '{"email":"test@example.com","mot_de_passe":"testpass"}'
    
} else {
    Write-Host "❌ Failed to update NGINX Gateway" -ForegroundColor Red
    Write-Host "Check the error messages above and try again." -ForegroundColor Red
}
