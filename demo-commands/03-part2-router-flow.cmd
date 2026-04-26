@echo off
title KV Store Demo - Part 2 Router Flow
echo.
echo [Part 2] PUT keys through router
curl.exe -X PUT "http://localhost:7000/kv/user:1001" -H "Content-Type: application/json" -d "{\"v\":1}"
curl.exe -X PUT "http://localhost:7000/kv/user:1002" -H "Content-Type: application/json" -d "{\"v\":2}"
curl.exe -X PUT "http://localhost:7000/kv/user:1003" -H "Content-Type: application/json" -d "{\"v\":3}"
echo.
echo [Part 2] GET keys through router
curl.exe "http://localhost:7000/kv/user:1002"
curl.exe "http://localhost:7000/kv/user:1003"
curl.exe "http://localhost:7000/kv/user:1001"
echo.
echo [Part 2] List all keys across nodes
curl.exe "http://localhost:7000/kv"
echo.
echo Done.
pause
