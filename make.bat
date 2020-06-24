@echo off

if not exist "%~dp0\build" (
    cmake -B "%~dp0\build" -A x64 "%~dp0"
)
cmake --build "%~dp0\build" --config Release -- /nologo
