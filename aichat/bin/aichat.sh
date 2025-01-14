#!/bin/sh
EXTENSION=/mnt/us/extensions/aichat
KTERM=/mnt/us/extensions/kterm
DPI=`cat /var/log/Xorg.0.log | grep DPI | sed -n 's/.*(\([0-9]\+\), [0-9]\+).*/\1/p'`

# Use different layouts for high-resolution devices
if [ ${DPI} -gt 290 ]; then
  PARAM="-l ${KTERM}/layouts/keyboard-300dpi.xml"
elif [ ${DPI} -gt 200 ]; then
  PARAM="-l ${KTERM}/layouts/keyboard-200dpi.xml"
fi

# Set the terminal environment
export TERM=xterm TERMINFO=${KTERM}/vte/terminfo

# Launch kterm with the selected layout and then run AI CHAT Python script
${KTERM}/bin/kterm ${PARAM} -e "python3.9 ${EXTENSION}/bin/geminikindle.py" "$@"
