A user-friendly tool for fast, customizable video conversion. Convert multiple files at once, choose your output format, and even enter custom FFMPEG commands for advanced control. Supports hardware acceleration for faster processing.

https://encode-performance.com/


Create a Json file past in and import
you can also restore default commands under the help menu on Bulk Video Converter
use "", for spacing
last line does not need a comma , at the end 
open & close each json file with [  ]

example 1

default.json
[
    "AMD",
    "ffmpeg -i \"<input>\" -c:v h264_amf -quality balanced -b:v 4M \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v h264_amf -quality speed -b:v 4M \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v h264_amf -quality quality -b:v 4M \"<output>\"",
    "",
    "Copy Subtitles",
    "ffmpeg -i \"<input>\" -map 0 -c:v h264_amf -quality speed -b:v 4M -c:s mov_text \"<output>\"",
    "ffmpeg -i \"<input>\" -map 0 -c:v libx264 -preset fast -crf 23 -c:a aac -c:s mov_text \"<output>\"",
    "ffmpeg -i \"<input>\" -map 0 -c:v h264_qsv -preset veryfast -b:v 5M -c:s mov_text \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -map 0 -c:v hevc_nvenc -preset fast -c:a copy -c:s mov_text \"<output>\"",
    "",
    "CPU",
    "ffmpeg -i \"<input>\" -c:v libx264 -preset slow -crf 23 -c:a aac \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v libx264 -preset medium -crf 23 -c:a aac \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v libx264 -preset fast -crf 23 -c:a aac \"<output>\"",
    "",
    "INTEL",
    "ffmpeg -i \"<input>\" -c:v h264_qsv -preset veryfast -b:v 5M \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v h264_qsv -preset faster -b:v 5M \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v h264_qsv -preset medium -b:v 5M \"<output>\"",
    "",
    "NVIDIA",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -b:v 2M -maxrate 2M -bufsize 2M -preset fast -c:a copy \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -b:v 3M -maxrate 3M -bufsize 3M -preset fast -c:a copy \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset slow -qp 23 -c:a aac \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset medium -qp 23 -c:a aac \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset fast -qp 23 -c:a aac \"<output>\""
]


example 2

default2.json

[
    "AMD",
    "ffmpeg -i \"<input>\" -c:v h264_amf -quality balanced -b:v 4M \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v h264_amf -quality speed -b:v 4M \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v h264_amf -quality quality -b:v 4M \"<output>\"",
    "Copy Subtitles",
    "ffmpeg -i \"<input>\" -map 0 -c:v h264_amf -quality speed -b:v 4M -c:s mov_text \"<output>\"",
    "ffmpeg -i \"<input>\" -map 0 -c:v libx264 -preset fast -crf 23 -c:a aac -c:s mov_text \"<output>\"",
    "ffmpeg -i \"<input>\" -map 0 -c:v h264_qsv -preset veryfast -b:v 5M -c:s mov_text \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -map 0 -c:v hevc_nvenc -preset fast -c:a copy -c:s mov_text \"<output>\"",
    "CPU",
    "ffmpeg -i \"<input>\" -c:v libx264 -preset slow -crf 23 -c:a aac \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v libx264 -preset medium -crf 23 -c:a aac \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v libx264 -preset fast -crf 23 -c:a aac \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v libx264 -preset ultrafast -crf 23 -c:a aac \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v libx264 -preset veryslow -crf 23 -c:a aac \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v libx265 -preset slow -x265-params crf=23 -c:a aac \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v libx265 -preset medium -x265-params crf=23 -c:a aac \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v libx265 -preset fast -x265-params crf=23 -c:a aac \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v libx265 -preset ultrafast -x265-params crf=23 -c:a aac \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v libx265 -preset veryslow -x265-params crf=23 -c:a aac \"<output>\"",
    "INTEL",
    "ffmpeg -i \"<input>\" -c:v h264_qsv -preset veryfast -b:v 5M \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v h264_qsv -preset faster -b:v 5M \"<output>\"",
    "ffmpeg -i \"<input>\" -c:v h264_qsv -preset medium -b:v 5M \"<output>\"",
    "NVIDIA",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -b:v 2M -maxrate 2M -bufsize 2M -preset fast -c:a copy \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -b:v 3M -maxrate 3M -bufsize 3M -preset fast -c:a copy \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset slow -qp 23 -c:a aac \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset medium -qp 23 -c:a aac \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset fast -qp 23 -c:a aac \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset hq -crf 18 -c:a aac \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset hp -crf 18 -c:a aac \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset llhp -crf 18 -c:a aac \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset lossless -cq 0 -c:a aac \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset llhp -rc vbr_hq -b:v 5M -c:a aac \"<output>\"",
    "ffmpeg -hwaccel cuvid -i \"<input>\" -c:v hevc_nvenc -preset llhp -rc cbr -b:v 5M -c:a aac \"<output>\""
]
