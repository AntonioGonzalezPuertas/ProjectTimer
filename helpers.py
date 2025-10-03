def format_time_hm(seconds):
    """Format seconds into H:MM format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}:{minutes:02d}"

def format_time(seconds):
    """Format seconds into HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def convert_seconds_to_hms(total_seconds):
    total_seconds = int(total_seconds)  # Convert to integer
    
    hours = total_seconds // 3600
    remaining_seconds = total_seconds % 3600
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    
    return hours, minutes, seconds

