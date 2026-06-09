import random
import os
from pathlib import Path

def read_extxyz_frames(filename):
    """
    Read all frames from an extended XYZ file.
    Returns a list of frames, where each frame is a list of strings.
    """
    frames = []
    current_frame = []
    atom_count = 0
    atoms_read = 0
    in_frame = False
    
    print(f"Reading {filename}...")
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this line contains just a number (atom count)
        if line.isdigit():
            # If we were already reading a frame, save it
            if current_frame:
                frames.append(current_frame)
                current_frame = []
            
            # Start new frame
            atom_count = int(line)
            current_frame.append(lines[i])
            in_frame = True
            atoms_read = 0
            i += 1
            
            # Read the properties/comment line (next line after atom count)
            if i < len(lines):
                current_frame.append(lines[i])
                i += 1
        elif in_frame and atoms_read < atom_count:
            # Read atom lines
            current_frame.append(lines[i])
            atoms_read += 1
            i += 1
            
            # If we've read all atoms for this frame, mark it as complete
            if atoms_read == atom_count:
                in_frame = False
        else:
            # This might be a continuation line or unexpected format
            # For safety, just skip it
            i += 1
    
    # Don't forget the last frame
    if current_frame:
        frames.append(current_frame)
    
    print(f"Read {len(frames)} frames")
    return frames

def split_extxyz_frames(frames, train_ratio=0.8, seed=42):
    """
    Split frames into training and testing sets.
    """
    random.seed(seed)
    random.shuffle(frames)
    
    split_idx = int(len(frames) * train_ratio)
    train_frames = frames[:split_idx]
    test_frames = frames[split_idx:]
    
    print(f"Split: {len(train_frames)} training frames ({train_ratio*100:.0f}%)")
    print(f"       {len(test_frames)} testing frames ({(1-train_ratio)*100:.0f}%)")
    
    return train_frames, test_frames

def write_extxyz_frames(frames, filename):
    """
    Write frames to an extended XYZ file.
    """
    with open(filename, 'w') as f:
        for frame in frames:
            f.writelines(frame)
    print(f"Written {len(frames)} frames to {filename}")

def validate_extxyz_file(filename):
    """
    Validate that the file has proper extended XYZ format.
    """
    print(f"Validating {filename}...")
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    i = 0
    frame_count = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # First line of frame should be atom count
        if not line.isdigit():
            print(f"Warning: Line {i+1} is not an integer (atom count): '{line[:50]}...'")
            print("This might not be a standard extended XYZ file.")
            return False
        
        atom_count = int(line)
        frame_count += 1
        
        # Skip to next frame
        i += 1  # Skip atom count line
        if i < len(lines):
            i += 1  # Skip properties/comment line
        
        # Skip atom lines
        atoms_to_skip = min(atom_count, len(lines) - i)
        i += atoms_to_skip
        
        if atoms_to_skip < atom_count:
            print(f"Warning: Frame {frame_count} truncated. Expected {atom_count} atoms, got {atoms_to_skip}")
    
    print(f"File contains {frame_count} frames")
    return True

def main():
    # Configuration
    input_file = "data.extxyz"
    train_file = "training.extxyz"
    test_file = "testing.extxyz"
    train_ratio = 0.8
    seed = 42
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"Error: Input file '{input_file}' not found!")
        return
    
    # Validate file format first
    if not validate_extxyz_file(input_file):
        print("\nTrying to read anyway with robust parser...")
    
    # Read all frames
    frames = read_extxyz_frames(input_file)
    
    if not frames:
        print("Error: No frames found in the file!")
        return
    
    # Split frames
    train_frames, test_frames = split_extxyz_frames(frames, train_ratio, seed)
    
    # Write output files
    write_extxyz_frames(train_frames, train_file)
    write_extxyz_frames(test_frames, test_file)
    
    # Verification
    print("\nVerification:")
    print(f"Training file: {len(train_frames)} frames")
    print(f"Testing file: {len(test_frames)} frames")
    print(f"Total: {len(train_frames) + len(test_frames)} frames")
    
    # Check file sizes
    if Path(train_file).exists():
        size = os.path.getsize(train_file) / (1024*1024)
        print(f"\nTraining file size: {size:.2f} MB")
    
    if Path(test_file).exists():
        size = os.path.getsize(test_file) / (1024*1024)
        print(f"Testing file size: {size:.2f} MB")

def alternative_method():
    """
    Alternative method using a simpler approach.
    This assumes each frame starts with the number of atoms on a line by itself.
    """
    print("\n--- Alternative Method ---")
    
    input_file = "data.extxyz"
    train_file = "training.extxyz"
    test_file = "testing.extxyz"
    train_ratio = 0.8
    seed = 42
    
    # Set random seed
    random.seed(seed)
    
    # Read all lines
    with open(input_file, 'r') as f:
        all_lines = f.readlines()
    
    # Find frame boundaries (lines that contain only a number)
    frame_starts = []
    for i, line in enumerate(all_lines):
        stripped = line.strip()
        if stripped and stripped.isdigit():
            frame_starts.append(i)
    
    print(f"Found {len(frame_starts)} frames")
    
    # Group frames
    frames = []
    for start_idx in frame_starts:
        # Find the end of this frame
        atom_count = int(all_lines[start_idx].strip())
        
        # Each frame has: atom count line + properties line + atom_count atom lines
        end_idx = start_idx + 1 + 1 + atom_count  # +1 for atom count line, +1 for properties, +atom_count
        
        # Handle the last frame which might not have complete lines
        if end_idx > len(all_lines):
            print(f"Warning: Frame starting at line {start_idx+1} is incomplete")
            continue
        
        frames.append(all_lines[start_idx:end_idx])
    
    # Shuffle and split
    random.shuffle(frames)
    split_idx = int(len(frames) * train_ratio)
    
    # Write training frames
    with open(train_file, 'w') as f:
        for frame in frames[:split_idx]:
            f.writelines(frame)
    
    # Write testing frames
    with open(test_file, 'w') as f:
        for frame in frames[split_idx:]:
            f.writelines(frame)
    
    print(f"Split: {len(frames[:split_idx])} training, {len(frames[split_idx:])} testing")
    print(f"Written to {train_file} and {test_file}")

if __name__ == "__main__":
    # Try the main method first
    print("=" * 60)
    print("Extended XYZ File Splitter")
    print("=" * 60)
    
    try:
        main()
    except Exception as e:
        print(f"\nError in main method: {e}")
        print("\nTrying alternative method...")
        alternative_method()
