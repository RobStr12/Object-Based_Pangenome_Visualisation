@echo off

set TYPEDB_HOME=%cd%
set "G_CP=%TYPEDB_HOME%\server\conf\;%TYPEDB_HOME%\server\lib\common\*;%TYPEDB_HOME%\server\lib\prod\*"

java %SERVER_JAVAOPTS% -cp "%G_CP%" -Dtypedb.dir="%TYPEDB_HOME%" com.vaticle.typedb.core.server.TypeDBServer %2 %3 %4 %5 %6 %7 %8 %9
