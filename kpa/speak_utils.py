#!/usr/bin/env python3

import os, datetime, shutil, sys, argparse, time, requests, subprocess as subp, tempfile, json
from pathlib import Path
from typing import Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

DEFAULT_VOICE_ID = "cgSgspJ2msm6clMCkdW9"  # Jessica, see <https://elevenlabs.io/app/default-voices>
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_SEED = 9373


def run_speak_command(args: list[str]) -> None:
    """Run speak command with ElevenLabs API."""
    parser = argparse.ArgumentParser(
        description='Convert text to speech using ElevenLabs API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kpa speak text.txt -
  kpa speak text.txt out.mp3
  echo "Hello world" | kpa speak
  kpa speak --voice-id "pNInz6obpgDQGcFmaJgB" --stability 0.3 text.txt
  kpa speak --speed 1.2 --style 0.5 text.txt
  kpa speak --seed 12345 --stability 0.5 text.txt
  kpa speak --previous-text "Hello there." --next-text "How are you?" text.txt
  kpa speak --parallel text.txt out.mp3
  kpa speak --list-voices
        """
    )
    
    # Positional arguments
    parser.add_argument('input', nargs='?', default='-', help='Input text file or "-" for stdin (default: -)')
    parser.add_argument('output', nargs='?', default='-', help='Output audio file or "-" to play directly (default: -)')
    
    # Voice settings
    parser.add_argument('--voice-id', default="21m00Tcm4TlvDq8ikWAM", 
                       help='Voice ID to use (default: Rachel voice)')
    parser.add_argument('--model-id', default="eleven_multilingual_v2",
                       help='Model ID to use (default: eleven_multilingual_v2)')
    parser.add_argument('--stability', type=float, 
                       help='Voice stability (0.0-1.0). Lower values introduce broader emotional range')
    parser.add_argument('--similarity-boost', type=float,
                       help='How closely AI should adhere to original voice (0.0-1.0)')
    parser.add_argument('--style', type=float,
                       help='Style exaggeration of the voice (0.0-1.0)')
    parser.add_argument('--use-speaker-boost', action='store_true',
                       help='Boost similarity to original speaker (increases latency)')
    parser.add_argument('--speed', type=float,
                       help='Speed of the voice (1.0 = normal, <1.0 = slower, >1.0 = faster)')
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED,
                       help=f'Seed for deterministic generation (0-4294967295). Default: {DEFAULT_SEED}. Same seed with same parameters should produce similar results')
    
    # Text continuity settings
    parser.add_argument('--previous-text', 
                       help='Text that came before the current text. Improves speech continuity when concatenating multiple generations')
    parser.add_argument('--next-text',
                       help='Text that comes after the current text. Improves speech continuity when concatenating multiple generations')
    
    # Processing options
    parser.add_argument('--parallel', action='store_true',
                       help='Split text at newlines and generate audio for each line in parallel, then concatenate')
    
    # Voice management
    parser.add_argument('--list-voices', action='store_true',
                       help='List all available voices in JSON format and exit')
    
    # API settings
    parser.add_argument('--api-key', help='ElevenLabs API key (overrides ELEVENLABS_API_KEY env var)')
    
    try:
        cli_args = parser.parse_args(args)
    except SystemExit:
        return
    
    # Handle --list-voices option
    if cli_args.list_voices:
        voices = list_voices(cli_args.api_key)
        print(json.dumps(voices, indent=2))
        return
    
    input_source = cli_args.input
    output_file = cli_args.output
    
    # Read text from input source
    if input_source == "-":
        # Read from stdin
        try:
            text = sys.stdin.read().strip()
        except Exception as e:
            print(f"Error reading from stdin: {e}")
            return
    else:
        # Read from file
        input_file = Path(input_source)
        if not input_file.exists():
            print(f"Error: Input file '{input_file}' does not exist")
            return
        
        try:
            text = input_file.read_text().strip()
        except Exception as e:
            print(f"Error reading input file: {e}")
            return
    
    if not text:
        print("Error: No text to convert")
        return
    
    # Validate seed parameter
    if not (0 <= cli_args.seed <= 4294967295):
        print("Error: Seed must be between 0 and 4294967295")
        return
    
    # Build voice settings
    voice_settings = {
        'use_speaker_boost': bool(cli_args.use_speaker_boost),
        'speed': float(cli_args.speed) or 1.0,
    }
    if cli_args.stability is not None:
        voice_settings['stability'] = cli_args.stability
    if cli_args.similarity_boost is not None:
        voice_settings['similarity_boost'] = cli_args.similarity_boost
    if cli_args.style is not None:
        voice_settings['style'] = cli_args.style

    # Convert text to speech
    try:
        if cli_args.parallel:
            audio_data = text_to_speech_parallel(
                text=text,
                api_key=cli_args.api_key,
                voice_id=cli_args.voice_id,
                model_id=cli_args.model_id,
                voice_settings=voice_settings,
                seed=cli_args.seed
            )
        else:
            audio_data = text_to_speech(
                text=text,
                api_key=cli_args.api_key,
                voice_id=cli_args.voice_id,
                model_id=cli_args.model_id,
                voice_settings=voice_settings,
                seed=cli_args.seed,
                previous_text=cli_args.previous_text,
                next_text=cli_args.next_text
            )
        
        if output_file == "-":
            # Play audio directly
            play_audio(audio_data)
        else:
            # Write audio data to output file
            output_path = Path(output_file)
            output_path.write_bytes(audio_data)
            print(f"Successfully generated audio: {output_path}")
        
    except Exception as e:
        print(f"Error generating audio: {e}")

def get_api_key(api_key: Optional[str] = None) -> str:
    if api_key: return api_key
    api_key = os.environ.get('ELEVENLABS_API_KEY', '')
    assert api_key, "ELEVENLABS_API_KEY environment variable not set and --api-key not provided"
    return api_key


def list_voices(api_key: Optional[str] = None) -> dict:
    """
    List all available voices from ElevenLabs API.
    
    Args:
        api_key: ElevenLabs API key
    
    Returns:
        Dictionary containing voices data
    """
    url = "https://api.elevenlabs.io/v1/voices"
    
    headers = {
        "Accept": "application/json",
        "xi-api-key": get_api_key(api_key)
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text}")
    
    return response.json()


def text_to_speech_parallel(
    text: str,
    api_key: Optional[str] = None,
    voice_id: str = DEFAULT_VOICE_ID,
    model_id: str = DEFAULT_MODEL_ID,
    voice_settings: Optional[dict] = None,
    seed: int = DEFAULT_SEED,
    max_workers: int = 5
) -> bytes:
    """
    Convert text to speech by splitting at newlines and processing in parallel.
    
    Args:
        text: Text to convert to speech
        api_key: ElevenLabs API key
        voice_id: Voice ID to use
        model_id: Model ID to use
        voice_settings: Voice settings dictionary
        seed: Base seed for deterministic generation
        max_workers: Maximum number of parallel workers
    
    Returns:
        Concatenated audio data as bytes
    """
    # Split text into lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        raise Exception("No non-empty lines found in text")    
    print(f"Processing {len(lines)} lines in parallel...")
        
    # Generate audio for each line in parallel
    def generate_line_audio(line_index: int) -> tuple[int, bytes]:
        audio_data = text_to_speech(
            text=lines[line_index],
            api_key=api_key,
            voice_id=voice_id,
            model_id=model_id,
            voice_settings=voice_settings,
            seed=seed,
            previous_text=lines[line_index - 1] if line_index > 0 else None,
            next_text=lines[line_index + 1] if line_index < len(lines) - 1 else None
        )
        return line_index, audio_data
    audio_for_line: dict[int, bytes] = {}
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(generate_line_audio, i) for i in range(len(lines))]
        for future in as_completed(futures):
            line_index = -100
            try:
                line_index, audio_data = future.result()
                audio_for_line[line_index] = audio_data
                print(f" - Completed line {line_index+1}/{len(lines)} after {time.time() - start_time:.2f}s")
            except Exception as e:
                print(f"Error processing line {line_index + 1}: {e}")
                raise
    
    # Concatenate audio segments
    print("Concatenating audio segments...")
    audio_segments = [audio_for_line[i] for i in range(len(lines))]
    return concatenate_audio_segments(audio_segments)


def concatenate_audio_segments(audio_segments: list[bytes]) -> bytes:
    """
    Concatenate multiple MP3 audio segments using ffmpeg.
    
    Args:
        audio_segments: List of audio data as bytes
    
    Returns:
        Concatenated audio data as bytes
    """
    if not audio_segments:
        raise Exception("No audio segments to concatenate")
    
    if len(audio_segments) == 1:
        return audio_segments[0]
    
    # Create temporary files for each segment
    temp_files: list[Path] = []
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Write each segment to a temporary file
        for i, audio_data in enumerate(audio_segments):
            temp_file = Path(temp_dir) / f"segment_{i:03d}.mp3"
            temp_file.write_bytes(audio_data)
            temp_files.append(temp_file)
        
        # Create concat file list for ffmpeg
        filelist_file = Path(temp_dir) / "concat_list.txt"
        with open(filelist_file, 'w') as f:
            for temp_file in temp_files:
                f.write(f"file '{temp_file.absolute()}'\n")
        
        # Output file
        output_file = Path(temp_dir) / "concatenated.mp3"
        
        # Run ffmpeg to concatenate
        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-f', 'concat', '-safe', '0', 
            '-i', str(filelist_file), 
            '-c', 'copy', 
            str(output_file),
            '-y'  # Overwrite output file
        ]
        
        subp.run(
            cmd, 
            capture_output=True, 
            text=True,
            check=True
        )
        
        # Read the concatenated result
        return output_file.read_bytes()
        
    except subp.CalledProcessError as e:
        raise Exception(f"ffmpeg concatenation failed: {e.stderr}")
    except FileNotFoundError:
        raise Exception("ffmpeg not found. Please install ffmpeg to use --parallel option")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def text_to_speech(
    text: str, 
    api_key: Optional[str] = None, 
    voice_id: str = DEFAULT_VOICE_ID,
    model_id: str = DEFAULT_MODEL_ID,
    voice_settings: Optional[dict] = None,
    seed: int = DEFAULT_SEED,
    previous_text: Optional[str] = None,
    next_text: Optional[str] = None
) -> bytes:
    """
    Convert text to speech using ElevenLabs API.
    
    Args:
        text: Text to convert to speech
        api_key: ElevenLabs API key
        voice_id: Voice ID to use (default is Rachel voice)
        model_id: Model ID to use (default is eleven_multilingual_v2)
        voice_settings: Voice settings dictionary
        seed: Seed for deterministic generation
        previous_text: Text that came before the current text
        next_text: Text that comes after the current text
    
    Returns:
        Audio data as bytes
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": get_api_key(api_key),
    }
    
    data: dict[str,Any] = {
        "text": text,
        "model_id": model_id,
        "voice_settings": voice_settings,
    }
    
    # Only include seed if provided
    if seed is not None:
        data["seed"] = seed
    
    # Add text continuity parameters
    if previous_text is not None:
        data["previous_text"] = previous_text
    
    if next_text is not None:
        data["next_text"] = next_text
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text}")
    
    return response.content


def play_audio(audio_data: bytes, verbose:bool=True) -> None:
    """
    Play audio data directly using system audio player.
    """
    # Create a temporary file to store the audio
    temp_path = Path('/tmp/kpa-speak-{get_datetimestr()}.mp3')
    temp_path.write_bytes(audio_data)
    if verbose: print(f" - Wrote {temp_path}")

    try:
        if sys.platform == "darwin" or sys.platform.startswith("linux"):  # Mac/Linux
            # Try common Mac/Linux audio players
            players = ["afplay", "mpg123", "mpv", "vlc", "mplayer", "xdg-open"]
            for player in players:
                try:
                    subp.run([player, temp_path], check=True, stdout=subp.DEVNULL, stderr=subp.DEVNULL)
                    break
                except (subp.CalledProcessError, FileNotFoundError):
                    pass
            else:
                raise Exception("No suitable audio player found. Please install mpg123, mpv, vlc, or mplayer.")
        else:
            raise Exception(f"Unsupported platform: {sys.platform}")

    except Exception as e:
        raise Exception(f"Error playing {temp_path}: {e}")


def get_datetimestr() -> str: return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')