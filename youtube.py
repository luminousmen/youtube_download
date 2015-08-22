import sys
import re
import json
from urlparse import urlparse, parse_qs, unquote
from urllib2 import urlopen

ENCODING = {
    # Flash Video
    5: ["flv", "240p", "Sorenson H.263", "N/A", "0.25", "MP3", "64"],
    6: ["flv", "270p", "Sorenson H.263", "N/A", "0.8", "MP3", "64"],
    34: ["flv", "360p", "H.264", "Main", "0.5", "AAC", "128"],
    35: ["flv", "480p", "H.264", "Main", "0.8-1", "AAC", "128"],

    # 3GP
    36: ["3gp", "240p", "MPEG-4 Visual", "Simple", "0.17", "AAC", "38"],
    13: ["3gp", "N/A", "MPEG-4 Visual", "N/A", "0.5", "AAC", "N/A"],
    17: ["3gp", "144p", "MPEG-4 Visual", "Simple", "0.05", "AAC", "24"],

    # MPEG-4
    18: ["mp4", "360p", "H.264", "Baseline", "0.5", "AAC", "96"],
    22: ["mp4", "720p", "H.264", "High", "2-2.9", "AAC", "192"],
    37: ["mp4", "1080p", "H.264", "High", "3-4.3", "AAC", "192"],
    38: ["mp4", "3072p", "H.264", "High", "3.5-5", "AAC", "192"],
    82: ["mp4", "360p", "H.264", "3D", "0.5", "AAC", "96"],
    83: ["mp4", "240p", "H.264", "3D", "0.5", "AAC", "96"],
    84: ["mp4", "720p", "H.264", "3D", "2-2.9", "AAC", "152"],
    85: ["mp4", "1080p", "H.264", "3D", "2-2.9", "AAC", "152"],

    # WebM
    43: ["webm", "360p", "VP8", "N/A", "0.5", "Vorbis", "128"],
    44: ["webm", "480p", "VP8", "N/A", "1", "Vorbis", "128"],
    45: ["webm", "720p", "VP8", "N/A", "2", "Vorbis", "192"],
    46: ["webm", "1080p", "VP8", "N/A", "N/A", "Vorbis", "192"],
    100: ["webm", "360p", "VP8", "3D", "N/A", "Vorbis", "128"],
    101: ["webm", "360p", "VP8", "3D", "N/A", "Vorbis", "192"],
    102: ["webm", "720p", "VP8", "3D", "N/A", "Vorbis", "192"]
}

ENCODING_KEYS = (
    'extension',
    'resolution',
    'video_codec',
    'profile',
    'video_bitrate',
    'audio_codec',
    'audio_bitrate'
)

def _parse_stream_map(text):
        """Python's `parse_qs` can't properly decode the stream map
        containing video data so we use this instead.
        """
        videoinfo = {
            "itag": [],
            "url": [],
            "quality": [],
            "fallback_host": [],
            "s": [],
            "type": []
        }

        # Split individual videos
        videos = text.split(",")
        # Unquote the characters and split to parameters
        videos = [video.split("&") for video in videos]

        for video in videos:
            for kv in video:
                key, value = kv.split("=")
                videoinfo.get(key, []).append(unquote(value))

        return videoinfo

def _extract_fmt(text):
        """YouTube does not pass you a completely valid URLencoded form, I
        suspect this is suppose to act as a deterrent.. Nothing some regulular
        expressions couldn't handle.
        :params text: The malformed data contained within each url node.
        """
        itag = re.findall('itag=(\d+)', text)
        if itag and len(itag) is 1:
            itag = int(itag[0])
            attr = ENCODING.get(itag, None)
            if not attr:
                return itag, None
            return itag, dict(zip(ENCODING_KEYS, attr))

def get_videos(my_url):
	videos = []
	_fmt_values = []
	response = urlopen(my_url)
	if response:
		content = response.read().decode("utf-8")
		try:
			player_conf = content[18 + content.find("ytplayer.config = "):]
			bracket_count = 0
			for i, char in enumerate(player_conf):
				if char == "{":
					bracket_count += 1
				elif char == "}":
					bracket_count -= 1
					if bracket_count == 0:
						break
			else:
				print("Cannot get JSON from HTML")

			index = i + 1
			data = json.loads(player_conf[:index])

		except Exception as e:
			print("Cannot decode JSON: {0}".format(e))


		stream_map = _parse_stream_map(
            data["args"]["url_encoded_fmt_stream_map"])

		title = data["args"]["title"]
		print("title:" + title)
		js_url = "http:" + data["assets"]["js"]
		video_urls = stream_map["url"]

        for i, url in enumerate(video_urls):
		try:
	       		fmt, fmt_data = _extract_fmt(url)
			if fmt_data["extension"] == "mp4" and fmt_data["profile"] == "High":
	        		download(url, title)
		     	_fmt_values.append(fmt)
		except KeyError:
			continue

def download(url, filename):
	chunk_size = 8 * 1024
	response = urlopen(url)
	_bytes_received = 0

	with open(filename, 'wb') as dst_file :
		while True:
			_buffer = response.read(chunk_size)
			if not _buffer:
				break
			_bytes_received += len(_buffer)
			dst_file.write(_buffer)

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
       urls = f.readlines()

    for my_url in urls:
        if my_url:
            get_videos(my_url)
            print("Done!")
        else:
            print("Usage: python youtube.py http://www.youtube.com/watch?v=rKE6PCXZITM")
