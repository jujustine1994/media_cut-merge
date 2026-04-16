import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from main import validate_time, time_to_seconds, build_split_cmd, build_merge_list, build_convert_cmd


class TestValidateTime:
    def test_valid_times(self):
        assert validate_time("00:00:00") is True
        assert validate_time("01:30:45") is True
        assert validate_time("99:59:59") is True

    def test_invalid_minutes(self):
        assert validate_time("00:60:00") is False

    def test_invalid_seconds(self):
        assert validate_time("00:00:60") is False

    def test_wrong_format(self):
        assert validate_time("1:30") is False
        assert validate_time("abc") is False
        assert validate_time("") is False


class TestTimeToSeconds:
    def test_zero(self):
        assert time_to_seconds("00:00:00") == 0

    def test_minutes(self):
        assert time_to_seconds("00:01:30") == 90

    def test_hours(self):
        assert time_to_seconds("01:00:00") == 3600

    def test_combined(self):
        assert time_to_seconds("01:01:01") == 3661


class TestBuildSplitCmd:
    def test_with_end(self):
        cmd = build_split_cmd("in.mp4", "00:01:00", "00:02:00", "out.mp4")
        assert cmd == ['ffmpeg', '-y', '-ss', '00:01:00', '-i', 'in.mp4',
                       '-t', '60', '-c', 'copy', 'out.mp4']

    def test_no_end(self):
        cmd = build_split_cmd("in.mp4", "00:01:00", None, "out.mp4")
        assert cmd == ['ffmpeg', '-y', '-ss', '00:01:00', '-i', 'in.mp4',
                       '-c', 'copy', 'out.mp4']


class TestBuildMergeList:
    def test_creates_file_with_entries(self, tmp_path):
        files = [str(tmp_path / "a.mp4"), str(tmp_path / "b.mp4")]
        list_path = str(tmp_path / "list.txt")
        build_merge_list(files, list_path)
        content = open(list_path, encoding='utf-8').read()
        assert "file '" in content
        assert "a.mp4" in content
        assert "b.mp4" in content

    def test_uses_forward_slashes(self, tmp_path):
        files = [r"C:\Users\test\a.mp4"]
        list_path = str(tmp_path / "list.txt")
        build_merge_list(files, list_path)
        content = open(list_path, encoding='utf-8').read()
        assert "\\" not in content


class TestBuildConvertCmd:
    def test_mp3(self):
        cmd = build_convert_cmd("in.mp4", "out.mp3", "MP3")
        assert cmd == ['ffmpeg', '-y', '-i', 'in.mp4',
                       '-vn', '-acodec', 'libmp3lame', '-q:a', '2', 'out.mp3']

    def test_aac(self):
        cmd = build_convert_cmd("in.mp4", "out.aac", "AAC")
        assert cmd == ['ffmpeg', '-y', '-i', 'in.mp4',
                       '-vn', '-acodec', 'aac', '-b:a', '192k', 'out.aac']

    def test_wav(self):
        cmd = build_convert_cmd("in.mp4", "out.wav", "WAV")
        assert cmd == ['ffmpeg', '-y', '-i', 'in.mp4',
                       '-vn', '-acodec', 'pcm_s16le', 'out.wav']

    def test_flac(self):
        cmd = build_convert_cmd("in.mp4", "out.flac", "FLAC")
        assert cmd == ['ffmpeg', '-y', '-i', 'in.mp4',
                       '-vn', '-acodec', 'flac', 'out.flac']
