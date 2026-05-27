#!/bin/bash
# Fake RTSP server for development/testing
# Streams a local video file as RTSP, simulating a camera
#
# Usage:
#   ./fake_rtsp_server.sh /path/to/renovation_video.mp4
#   Then use rtsp://localhost:8554/stream as camera URL in RemontERP
#
# Prerequisites:
#   - FFmpeg installed
#   - mediamtx (formerly rtsp-simple-server): https://github.com/bluenviern/mediamtx
#     or use docker: docker run --rm -p 8554:8554 bluenviron/mediamtx

VIDEO_FILE="${1:-test_video.mp4}"

if [ ! -f "$VIDEO_FILE" ]; then
    echo "Video file not found: $VIDEO_FILE"
    echo ""
    echo "To create a test video with color bars:"
    echo "  ffmpeg -f lavfi -i testsrc=duration=300:size=1920x1080:rate=1 -c:v libx264 test_video.mp4"
    echo ""
    echo "Or download renovation footage from YouTube (for personal testing only):"
    echo "  yt-dlp -f 'best[height<=1080]' -o renovation.mp4 'https://youtube.com/watch?v=XXXXX'"
    exit 1
fi

echo "Starting fake RTSP stream from: $VIDEO_FILE"
echo "RTSP URL: rtsp://localhost:8554/stream"
echo "Use this URL in RemontERP camera registration."
echo ""

# Stream video file as RTSP via FFmpeg → mediamtx
# Loop the video indefinitely (-stream_loop -1)
ffmpeg -re -stream_loop -1 \
    -i "$VIDEO_FILE" \
    -c:v libx264 -preset ultrafast -tune zerolatency \
    -f rtsp \
    rtsp://localhost:8554/stream
