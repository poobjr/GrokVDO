"""
FFmpeg Assembly Pipeline.

Video stitching, audio mixing, and final assembly.
"""

import subprocess
from pathlib import Path
from typing import Optional

import ffmpeg


class FFmpegAssembly:
    """
    Handles video assembly using FFmpeg.

    Features:
    - Concatenate clips (demuxer and filter methods)
    - Audio mixing and sync
    - Format conversion
    - Quality optimization
    """

    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize FFmpeg assembly.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir or Path("./output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def concat_clips(
        self,
        clips: list[Path],
        output_path: Path,
        same_codec: bool = True,
    ) -> Path:
        """
        Concatenate multiple video clips.

        Args:
            clips: List of clip paths in order
            output_path: Output file path
            same_codec: If True, use fast concat demuxer; else use filter

        Returns:
            Path to output file
        """
        if not clips:
            raise ValueError("No clips provided")

        if len(clips) == 1:
            # Single clip - just copy
            clips[0].rename(output_path)
            return output_path

        if same_codec:
            return self._concat_demuxer(clips, output_path)
        else:
            return self._concat_filter(clips, output_path)

    def _concat_demuxer(
        self,
        clips: list[Path],
        output_path: Path,
    ) -> Path:
        """
        Concatenate using demuxer (fast, same codec).

        Creates a concat file and uses -f concat.
        """
        # Create concat file
        concat_file = self.output_dir / "concat_list.txt"
        with open(concat_file, "w") as f:
            for clip in clips:
                # Escape single quotes in path
                path_str = str(clip).replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")

        # Run FFmpeg
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(output_path),
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        # Cleanup
        concat_file.unlink()

        return output_path

    def _concat_filter(
        self,
        clips: list[Path],
        output_path: Path,
    ) -> Path:
        """
        Concatenate using filter (slower, different codecs).

        Uses concat filter with re-encoding.
        """
        # Build input arguments
        inputs = []
        for clip in clips:
            inputs.extend(["-i", str(clip)])

        # Build filter complex
        n = len(clips)
        video_inputs = "".join(f"[{i}:v]" for i in range(n))
        audio_inputs = "".join(f"[{i}:a]" for i in range(n))
        filter_complex = f"{video_inputs}{audio_inputs}concat=n={n}:v=1:a=1[outv][outa]"

        # Run FFmpeg
        cmd = [
            "ffmpeg",
            "-y",
        ] + inputs + [
            "-filter_complex",
            filter_complex,
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(output_path),
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        return output_path

    def add_audio(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
        sync_offset: float = 0.0,
    ) -> Path:
        """
        Add or replace audio in a video.

        Args:
            video_path: Input video path
            audio_path: Audio file path
            output_path: Output file path
            sync_offset: Audio delay in seconds (positive = delay audio)

        Returns:
            Path to output file
        """
        # Build audio delay filter if needed
        audio_filter = ""
        if sync_offset != 0:
            delay_ms = int(sync_offset * 1000)
            audio_filter = f"adelay={delay_ms}|{delay_ms}"

        # Run FFmpeg
        input_args = ["-i", str(video_path), "-i", str(audio_path)]

        filter_args = []
        if audio_filter:
            filter_args = ["-af", audio_filter]

        cmd = [
            "ffmpeg",
            "-y",
        ] + input_args + filter_args + [
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            str(output_path),
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        return output_path

    def mix_audio(
        self,
        audio_files: list[Path],
        output_path: Path,
        weights: Optional[list[float]] = None,
    ) -> Path:
        """
        Mix multiple audio files.

        Args:
            audio_files: List of audio file paths
            output_path: Output file path
            weights: Optional volume weights for each file

        Returns:
            Path to output file
        """
        if not audio_files:
            raise ValueError("No audio files provided")

        if len(audio_files) == 1:
            # Single file - just copy
            import shutil

            shutil.copy2(audio_files[0], output_path)
            return output_path

        # Build input arguments
        inputs = []
        for audio in audio_files:
            inputs.extend(["-i", str(audio)])

        # Build amix filter
        n = len(audio_files)
        filter_args = f"amix=inputs={n}:duration=longest"
        if weights:
            # Normalize weights
            total = sum(weights)
            normalized = [w / total for w in weights]
            weights_str = " ".join(str(w) for w in normalized)
            filter_args += f":weights={weights_str}"

        # Run FFmpeg
        cmd = [
            "ffmpeg",
            "-y",
        ] + inputs + [
            "-filter_complex",
            filter_args,
            "-c:a",
            "aac",
            str(output_path),
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        return output_path

    def create_silence(
        self,
        duration: float,
        output_path: Path,
    ) -> Path:
        """
        Create a silence audio file.

        Args:
            duration: Duration in seconds
            output_path: Output file path

        Returns:
            Path to output file
        """
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"anullsrc=r=44100:cl=stereo",
            "-t",
            str(duration),
            "-c:a",
            "aac",
            str(output_path),
        ]

        subprocess.run(cmd, check=True, capture_output=True)

        return output_path

    def get_video_info(self, video_path: Path) -> dict:
        """
        Get video file information.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video info
        """
        probe = ffmpeg.probe(str(video_path))
        video_stream = next(
            (s for s in probe["streams"] if s["codec_type"] == "video"), None
        )
        audio_stream = next(
            (s for s in probe["streams"] if s["codec_type"] == "audio"), None
        )

        return {
            "duration": float(probe["format"].get("duration", 0)),
            "width": int(video_stream.get("width", 0)) if video_stream else 0,
            "height": int(video_stream.get("height", 0)) if video_stream else 0,
            "fps": eval(video_stream.get("r_frame_rate", "0/1"))
            if video_stream
            else 0,
            "has_audio": audio_stream is not None,
        }

    def assemble_timeline(
        self,
        clips: list[tuple[Path, Optional[Path]]],
        output_path: Path,
    ) -> Path:
        """
        Assemble timeline with video and optional audio.

        Args:
            clips: List of (video_path, audio_path) tuples
            output_path: Output file path

        Returns:
            Path to assembled video
        """
        if not clips:
            raise ValueError("No clips provided")

        # First, add audio to clips that need it
        processed_clips = []
        temp_files = []

        for i, (video, audio) in enumerate(clips):
            if audio:
                # Add audio to video
                output = self.output_dir / f"temp_{i}.mp4"
                self.add_audio(video, audio, output)
                processed_clips.append(output)
                temp_files.append(output)
            else:
                processed_clips.append(video)

        # Concatenate all clips
        result = self.concat_clips(processed_clips, output_path, same_codec=False)

        # Cleanup temp files
        for temp in temp_files:
            temp.unlink()

        return result
