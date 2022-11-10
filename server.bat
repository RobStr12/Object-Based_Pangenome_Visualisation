@echo off

set TYPEDB_HOME=%cd%
set "G_CP=%TYPEDB_HOME%\server\conf\;%TYPEDB_HOME%\server\lib\win32\common\*;%TYPEDB_HOME%\server\lib\win32\prod\*"

where java >NUL 2>NUL
if %ERRORLEVEL% GEQ 1 (
    echo Java is not installed on this machine.
    echo TypeDB needs Java 11+ in order to run. See the following setup guide: http://docs.vaticle.com/docs/get-started/setup-guide
    pause
    exit 1
)

java %SERVER_JAVAOPTS% -cp "%G_CP%" -Dtypedb.dir="%TYPEDB_HOME%" com.vaticle.typedb.core.server.TypeDBServer %2 %3 %4 %5 %6 %7 %8 %9