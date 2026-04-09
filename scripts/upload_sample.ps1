$headers = @{
    Authorization = "Bearer rag-dev-123456789"
}

$samplePath = Join-Path $PSScriptRoot "..\\sample.txt"

curl.exe -s `
    -X POST `
    -H "Authorization: $($headers.Authorization)" `
    -F "file=@$samplePath;type=text/plain" `
    http://127.0.0.1:8000/api/v1/documents/upload
