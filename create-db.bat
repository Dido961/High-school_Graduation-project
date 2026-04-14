@echo off
SET /P MYSQL_USER=Enter MySQL username: 
SET /P MYSQL_PASSWORD=Enter MySQL password: 

echo Creating database 'ecommerce_db'...

"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u %MYSQL_USER% -p%MYSQL_PASSWORD% -e "CREATE DATABASE IF NOT EXISTS ecommerce_db;"

IF %ERRORLEVEL% EQU 0 (
    echo Database 'ecommerce_db' created successfully.
) ELSE (
    echo Failed to create the database.
)

pause
