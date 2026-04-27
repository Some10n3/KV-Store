@echo off
title KV Store Demo - Part 1 Concurrency Test
echo.
echo [Part 1] Required concurrency proof
echo Running 3 concurrent clients x 100 increments each...
echo.
python tests/test_part1_concurrency.py
if errorlevel 1 (
	echo.
	echo Concurrency proof failed.
) else (
	echo.
	echo Concurrency proof completed successfully.
)
pause
