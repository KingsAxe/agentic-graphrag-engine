$headers = @{
    Authorization = "Bearer rag-dev-123456789"
}

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8000/api/v1/documents/reset-workspace" `
    -Method Post `
    -Headers $headers | ConvertTo-Json -Depth 8
