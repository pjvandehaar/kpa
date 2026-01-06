
## TODO: Start playing as soon as we get the first audio chunk.

from kokoro import KPipeline
import soundfile as sf
import torch
import argparse, random, sys, json, warnings, time, threading, queue
from pathlib import Path

from .pypi_utils import print_and_run

def run_speak_local_command(args: list[str]) -> None:
    parser = argparse.ArgumentParser(
        description='Convert text to speech using Kokoro',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  clip | kpa speak-local
  clip | kpa speak-local --playspeed=2
        """
    )
    parser.add_argument('--playspeed', type=float, default=None,
                       help='Speed multiplier for playback, requires ffmpeg/ffplay (1.0 = normal, <1.0 = slower, >1.0 = faster)')
    cli_args = parser.parse_args(args)
    
    text = sys.stdin.read().strip()
    start_time = time.time()
    
    tmp_path_base = f'/tmp/kpa-kokoro-{random.randint(0, 2**32):08x}'
    Path(tmp_path_base+'.json').write_text(json.dumps({
        'text': text,
        'playspeed': cli_args.playspeed,
    }))

    print("=> Creating KPipeline...")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        pipeline = KPipeline(lang_code='en-us', repo_id='hexgrad/Kokoro-82M')
    print("=> Using KPipeline on text...")
    generator = pipeline(text, voice='af_heart')

    # Queue for audio files to be played
    audio_queue = queue.Queue()

    def playback_worker():
        while True:
            audio_file = audio_queue.get()
            if audio_file is None:
                break
            play_audio_file(audio_file, cli_args.playspeed)
            audio_queue.task_done()

    # Start playback thread
    playback_thread = threading.Thread(target=playback_worker, daemon=True)
    playback_thread.start()

    try:
        for i, (gs, ps, audio) in enumerate(generator):
            print(f'[{time.time() - start_time:.2f}s] Generated chunk#{i} ({len(gs)} chars) {gs[:50]=}', flush=True)
            audio_file = f'{tmp_path_base}-{i}.wav'
            sf.write(audio_file, audio, 24000)
            audio_queue.put(audio_file)

    except KeyboardInterrupt:
        print("\nInterrupted during generation.")

    # Signal playback to stop
    audio_queue.put(None)
    playback_thread.join()

def play_audio_file(audio_file: str, playspeed:float|None = None) -> None:
    command = [
        'ffplay',
        audio_file,
        '-vn', '-nodisp',
        '-hide_banner', '-loglevel', 'error',
        '-autoexit',
    ]
    if playspeed:
        command.append('-af')
        command.append(f'atempo={playspeed}')
    print_and_run(command)
