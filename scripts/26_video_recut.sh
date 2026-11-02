#!/usr/bin/env bash
# Re-cut segment 5 (the results chart card) of the 120 s submission video from the current docs/results_full_record.png
# and re-concatenate. Segments s1..s6 live in $VID (the scratch folder used to build the video); only s5 changes.
#   VID=/path/to/vid2 scripts/26_video_recut.sh
set -euo pipefail
VID="${VID:?folder with s1.mp4..s6.mp4 and list.txt}"
python3 - "$VID" <<'PY'
import sys; from PIL import Image
vid=sys.argv[1]
chart=Image.open("docs/results_full_record.png").convert("RGB")
W,H=1440,900; card=Image.new("RGB",(W,H),(255,255,255))
scale=min((W-80)/chart.width,(H-80)/chart.height); chart=chart.resize((int(chart.width*scale),int(chart.height*scale)), Image.LANCZOS)
card.paste(chart,((W-chart.width)//2,(H-chart.height)//2)); card.save(f"{vid}/c3.png")
PY
ffmpeg -y -loglevel error -loop 1 -i "$VID/c3.png" -t 24 -r 25 -vf "scale=1440:900,format=yuv420p" -c:v libx264 -preset medium -crf 20 "$VID/s5.mp4"
(cd "$VID" && ffmpeg -y -loglevel error -f concat -safe 0 -i list.txt -c copy gmaps_fireworks_120s.mp4)
cp "$VID/gmaps_fireworks_120s.mp4" docs/video/gmaps_fireworks_120s.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 docs/video/gmaps_fireworks_120s.mp4
