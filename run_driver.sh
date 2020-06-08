#!/bin/sh
# Script for execution of compiled driver applications
#
# Sets up the MATLAB Runtime environment for the current $ARCH and executes 
# the specified command.
#
exe_name=$0
exe_dir=`dirname "$0"`
echo "------------------------------------------"
if [ "x$1" = "x" ] || [ "x$2" = "x" ]; then
  echo Usage:
  echo    $0 \<deployedMCRroot\> \<applicationName\> args
else
  echo Setting up environment variables
  MCRROOT="$1"
  APPNAME="$2"
  echo ---
  DYLD_LIBRARY_PATH=.:${MCRROOT}/runtime/maci64 ;
  DYLD_LIBRARY_PATH=${DYLD_LIBRARY_PATH}:${MCRROOT}/bin/maci64 ;
  DYLD_LIBRARY_PATH=${DYLD_LIBRARY_PATH}:${MCRROOT}/sys/os/maci64;
  export DYLD_LIBRARY_PATH;
  echo DYLD_LIBRARY_PATH is ${DYLD_LIBRARY_PATH};
  shift 2
  args=
  while [ $# -gt 0 ]; do
      token=$1
      args="${args} \"${token}\"" 
      shift
  done
  eval "\"${exe_dir}/${APPNAME}.app/Contents/MacOS/${APPNAME}\"" $args
fi
exit

