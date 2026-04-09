param(
    [Parameter(Mandatory = $true)]
    [string]$JobId
)

$headers = @{
    Authorization = "Bearer rag-dev-123456789"
}

$statusUrl = "http://127.0.0.1:8000/api/v1/documents/$JobId/status"

Invoke-RestMethod -Uri $statusUrl -Headers $headers | ConvertTo-Json -Depth 8
