#!/bin/bash

set -o nounset
set -o errexit

mv /tmpfs/src/gfile/settings_ggrc_rmc /tmpfs/src/gfile/settings

CURRENT_SCRIPTPATH=$( cd "$(dirname "$0")" ; pwd -P )
export CURRENT_SCRIPTPATH
$CURRENT_SCRIPTPATH/ggrc_release.sh
