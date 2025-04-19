A user-friendly tool for fast, customizable video conversion. Convert multiple files at once, choose your output format, and even enter custom FFMPEG commands for advanced control. Supports hardware acceleration for faster processing.

creating commands:
just replace input and output formats with "<input>"  "<output>" 
Example #1
regular ffmpeg command 
ffmpeg -hwaccel cuvid -i input.mkv -codec copy output.mp4

convert it like this to work with Simple_FFMPEG_Video_Converter 
ffmpeg -hwaccel cuvid -i "<input>" -codec copy "<output>"

Example #2
regular ffmpeg command
ffmpeg -hwaccel cuvid -i input.mp4 -c:v hevc_nvenc -preset slow -qp 23 -c:a aac output.mp4

convert it like this to work with Simple_FFMPEG_Video_Converter 
ffmpeg -hwaccel cuvid -i "<input>" -c:v hevc_nvenc -preset slow -qp 23 -c:a aac "<output>"

Example #3: Convert MKV to MP4, re-encode video with H.264 and audio with AAC
Regular:
ffmpeg -i input.mkv -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 192k output.mp4

Simple_FFMPEG_Video_Converter:
ffmpeg -i "<input>" -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 192k "<output>"
