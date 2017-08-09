[![codebeat badge](https://codebeat.co/badges/de3339f0-ebcd-4fed-b7aa-16d69c818f9b)](https://codebeat.co/projects/github-com-luminousmen-youtube_download)

youtube_download
======

#### Dependencies

- python-slugify

It's a simple Python script for downloading videos from youtube.com.

### Usage
You need to add links of desired videos to file.txt and use script as:
```bash
$ ./youtube.py -f file.txt
```
OR with single video url:
```bash
$ ./youtube.py -u youtube_url
```

Also you can specify needed chunk size in Kbs, default chunk size is 16Kb:
```bash
$ ./youtube.py -c 1024
```
