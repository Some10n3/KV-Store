@echo off
title KV Store Demo - Part 1 Version and Errors
echo.
echo [Part 1] PUT with correct ifVersion (expect success)
curl.exe -X PUT "http://localhost:7000/kv/user:1001?ifVersion=1" -H "Content-Type: application/json" -d "{\"name\":\"Ari\",\"points\":20}"
echo.
echo [Part 1] PUT with wrong ifVersion (expect 409)
curl.exe -X PUT "http://localhost:7000/kv/user:1001?ifVersion=99" -H "Content-Type: application/json" -d "{\"name\":\"Ari\",\"points\":99}"
echo.
echo [Part 1] GET after conflict (prove value was not overwritten)
curl.exe "http://localhost:7000/kv/user:1001"
echo.
echo [Part 1] GET missing key (expect 404)
curl.exe "http://localhost:7000/kv/doesnotexist"
echo.
echo Done.
pause
