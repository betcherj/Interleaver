# INTERLEAVER
The purpose of this code base is to establish and verify ownership over a digital asset. This is acheived by recording another 
audio segment, pitch shifting it so it is inaudible to humans and overlaying it with the original audio file. The ownership audio
can be recovered for verification purposes 

## Requirements 
In addition to requirements.txt, download the following and add them to your PATH
1. ffmpeg (https://ffmpeg.org/download.html)
2. Rubber Band library (https://breakfastquay.com/rubberband/) 


## Running 
1. Add mp3 files to the /input folder. Each audio file must have a coorisponding ownership audio. 
2. Run ```python audio.py```
3. Retreive outputs from /outputs

## TODOs
* Get pitch shifting to work without degredation
* Add front end 
* Add DB for audio files
* Speed up the pitch shifting (currently a bottleneck) -> probably will want to write our own pitch shift function
* Batch processing of files
