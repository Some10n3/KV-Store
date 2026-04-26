@echo off
title KV Store Demo - Part 1 Basic
echo.
echo [Part 1 Basic] PUT new key
curl.exe -X PUT "http://localhost:7000/kv/user:1001" -H "Content-Type: application/json" -d "{\"name\":\"Ari\",\"points\":10}"
echo.
echo [Part 1 Basic] GET key
curl.exe "http://localhost:7000/kv/user:1001"
echo.
echo [Part 1 Basic] PATCH key (merge field)
curl.exe -X PATCH "http://localhost:7000/kv/user:1001" -H "Content-Type: application/json" -d "{\"rank\":\"gold\"}"
echo.
echo Done.
pause
