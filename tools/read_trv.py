#!/usr/bin/env python3
import sys
import struct
import zlib
import argparse
import numpy as np
import os

def read_trv(filepath, export_dir=None):
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return

    print(f"Reading {filepath}...")
    
    if export_dir and not os.path.exists(export_dir):
        os.makedirs(export_dir)

    with open(filepath, 'rb') as f:
        # Read Header
        header_data = f.read(16)
        if len(header_data) < 16:
            print("Error: File too short to contain header.")
            return

        magic, width, height, fps = struct.unpack('<4sIIf', header_data)
        
        if magic != b'TRV1':
            print("Error: Invalid magic number. Not a TRV1 file.")
            return

        print("-" * 30)
        print("TRV Header Metadata:")
        print(f"  Width:  {width}")
        print(f"  Height: {height}")
        print(f"  FPS:    {fps:.2f}")
        print("-" * 30)

        frame_count = 0
        total_uncompressed_bytes = 0
        
        while True:
            block_header_data = f.read(16)
            if not block_header_data:
                break # EOF
            
            if len(block_header_data) < 16:
                print("Warning: Incomplete block header at end of file.")
                break
                
            marker, timestamp, payload_size = struct.unpack('<4sdI', block_header_data)
            
            if marker != b'FRME':
                print(f"Warning: Expected FRME marker, got {marker}. Stopping read.")
                break
                
            compressed_payload = f.read(payload_size)
            if len(compressed_payload) < payload_size:
                print("Warning: Incomplete payload at end of file.")
                break
                
            try:
                raw_buffer = zlib.decompress(compressed_payload)
            except zlib.error as e:
                print(f"Error decompressing frame {frame_count}: {e}")
                break
                
            total_uncompressed_bytes += len(raw_buffer)
            frame_count += 1
            
            if export_dir:
                # Save as npz
                frame_array = np.frombuffer(raw_buffer, dtype=np.uint8)
                out_path = os.path.join(export_dir, f"frame_{frame_count:05d}.npz")
                np.savez_compressed(
                    out_path,
                    frame=frame_array,
                    width=width,
                    height=height,
                    stride=width * 2,
                    timestamp=timestamp
                )

        print(f"Successfully read {frame_count} frames.")
        print(f"Total uncompressed data: {total_uncompressed_bytes / (1024*1024):.2f} MB")
        
        if export_dir:
             print(f"Frames exported to {export_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Read and extract data from .trv (Thermal Raw Video) files.")
    parser.add_argument("file", help="Path to the .trv file")
    parser.add_argument("--export", "-e", help="Directory to export individual frames as .npz files", default=None)
    
    args = parser.parse_args()
    read_trv(args.file, args.export)
