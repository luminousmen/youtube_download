#!/usr/bin/env python
from __future__ import print_function

import re
import os
import sys
import json
import argparse
import signal

from urlparse import urlparse, parse_qs, unquote
from urllib2 import urlopen

chunk_size = 1024 * 1024 # 1 mb
sys_hault = False # shutdown gracefully switch

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
    response = urlopen(url)
    bytes_received = 0
    download_size = int(response.info().getheader("Content-Length"))

    with open(filename, 'wb') as dst_file:
        while True:
            # Don't read anymore data, caught by signal.
            if sys_hault:
                sys.exit(0)

            _buffer = response.read(chunk_size)
            if not _buffer and bytes_received == download_size:
                print("Video saved: %s" % os.path.join(os.getcwd(), filename))
                break
            bytes_received += len(_buffer)
            dst_file.write(_buffer)

def signal_handler(signal, frame):
    global sys_hault
    sys_hault = True
    print("Exiting...")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=str, required=False,
                       help='Read in file with video urls separated by newlines')
    parser.add_argument("-u", "--url", type=str, required=False,
                       help='URL to YouTube video')
    parser.add_argument("-c", "--chunksize", type=int, required=False,
                       help="Increase the chunksize (mb), 1MB is default (e.g. --chucksize 10 would be 10 mb) ")
    args = parser.parse_args()

    mb = 1024 * 1024
    if args.chunksize:
        chunk_size = args.chunksize * mb

    signal.signal(signal.SIGINT, signal_handler)

    if args.file:
        with open(args.file) as f:
           urls = f.readlines()

        for my_url in urls:
            try:
                get_videos(my_url)
                print("Done!")
            except ValueError:
                print("Url not correct:{}".format(my_url))

    elif args.url:
        get_videos(args.url)
        print("Done!")
