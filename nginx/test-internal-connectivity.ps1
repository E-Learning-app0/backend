# Test script to verify NGINX can reach internal services
# Run this from the NGINX container to test connectivity

Write-Host "🧪 Testing internal service connectivity..." -ForegroundColor Yellow

# Test auth-service
Write-Host "`n🔐 Testing auth-service..." -ForegroundColor Blue
curl "http://auth-service.internal.blackbush-661cc25b.spaincentral.azurecontainerapps.io:8001/health"

# Test content-service  
Write-Host "`n📚 Testing content-service..." -ForegroundColor Blue
curl "http://content-service.internal.blackbush-661cc25b.spaincentral.azurecontainerapps.io:8002/health"

# Test agent-service
Write-Host "`n🤖 Testing agent-service..." -ForegroundColor Blue
curl "http://agent-service.internal.blackbush-661cc25b.spaincentral.azurecontainerapps.io:8004/health"

Write-Host "`n📝 DNS Resolution Test..." -ForegroundColor Blue
nslookup auth-service.internal.blackbush-661cc25b.spaincentral.azurecontainerapps.io
nslookup content-service.internal.blackbush-661cc25b.spaincentral.azurecontainerapps.io
nslookup agent-service.internal.blackbush-661cc25b.spaincentral.azurecontainerapps.io
