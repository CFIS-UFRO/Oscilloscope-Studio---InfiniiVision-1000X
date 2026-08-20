@echo off
setlocal

REM ##################################################################################################
REM Launch Oscilloscope Studio on Windows with a project-local uv installation and Python environment.
REM ##################################################################################################

REM --------------------------------------------------------------------------------------------------
REM Paths
REM --------------------------------------------------------------------------------------------------
set "SCRIPT_DIR=%~dp0"
set "APP_DIR=%SCRIPT_DIR%app"
set "UV_DIR=%APP_DIR%\.uv"
set "UV_BIN=%UV_DIR%\uv.exe"
set "UV_CACHE_DIR=%UV_DIR%\cache"
set "UV_PYTHON_INSTALL_DIR=%UV_DIR%\python"
set "UV_PROJECT_ENVIRONMENT=%UV_DIR%\venv"
REM Require uv-managed Python
set "UV_MANAGED_PYTHON=1"
set "MAIN_FILE=%APP_DIR%\main.py"
set "RELEASE_MODULE=scripts.create_release"
set "UPDATE_MODULE=scripts.apply_update"
cd /d "%APP_DIR%"

REM --------------------------------------------------------------------------------------------------
REM Constants
REM --------------------------------------------------------------------------------------------------
set "RESTART_EXIT_CODE=42"
set "APPLY_UPDATE_EXIT_CODE=43"

REM --------------------------------------------------------------------------------------------------
REM uv installation
REM --------------------------------------------------------------------------------------------------
if not exist "%UV_BIN%" (
    mkdir "%UV_DIR%" 2>nul
    set "UV_INSTALL_DIR=%UV_DIR%"
    set "INSTALLER_NO_MODIFY_PATH=1"
    echo Installing uv...
    powershell -ExecutionPolicy ByPass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo Failed to install uv.
        pause
        exit /b 1
    )
)

REM --------------------------------------------------------------------------------------------------
REM Developer release
REM --------------------------------------------------------------------------------------------------
if /I "%~1"=="release" goto release
goto launch
:release
"%UV_BIN%" run python -m "%RELEASE_MODULE%"
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%

REM --------------------------------------------------------------------------------------------------
REM Application launch and restart
REM --------------------------------------------------------------------------------------------------
:launch
REM Run the supervisor, which starts the backend and frontend processes
"%UV_BIN%" run python "%MAIN_FILE%"
REM Record normal exits, application errors, and launcher control codes
set "EXIT_CODE=%ERRORLEVEL%"
REM Restart immediately when the application requests a regular restart
if "%EXIT_CODE%"=="%RESTART_EXIT_CODE%" (
    echo Restarting Oscilloscope Studio...
    goto launch
)
REM Continue to the updater when the application prepared an update
if "%EXIT_CODE%"=="%APPLY_UPDATE_EXIT_CODE%" goto update
REM Pause so application errors remain visible before the terminal closes
if not "%EXIT_CODE%"=="0" pause
REM Propagate normal exits and unhandled application errors to the calling terminal
exit /b %EXIT_CODE%

:update
REM Apply the prepared update after the supervisor has stopped both application processes
"%UV_BIN%" run python -m "%UPDATE_MODULE%"
REM Record the updater result separately from the application result
set "EXIT_CODE=%ERRORLEVEL%"
REM Stop the launcher and preserve the updater error when installation fails
if not "%EXIT_CODE%"=="0" (
    pause
    exit /b %EXIT_CODE%
)
REM Start the newly updated application
echo Restarting Oscilloscope Studio...
goto launch
