import datetime

def format_time(seconds):
    """Convert seconds to SRT time format."""
    return str(datetime.timedelta(seconds=seconds)).replace('.', ',')[:-3]

def generate_srt(transcript):
    """Generate SRT formatted subtitles from transcript."""
    srt_content = ""
    for index, segment in enumerate(transcript, start=1):
        start_time = format_time(segment['start'])
        end_time = format_time(segment['end'])
        text = segment['text'].strip()
        
        srt_content += f"{index}\n{start_time} --> {end_time}\n{text}\n\n"
    
    return srt_content.strip()

def save_srt(content, filename):
    """Save SRT content to a file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)