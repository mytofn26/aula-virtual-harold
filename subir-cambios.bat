@echo off
echo ============================================
echo   Subiendo cambios a GitHub / Render...
echo ============================================
echo.

git add .
git commit -m "Actualizacion %date% %time%"
git push

echo.
echo ============================================
echo   Listo. Render va a desplegar esto solo
echo   en 1-2 minutos.
echo ============================================
pause
