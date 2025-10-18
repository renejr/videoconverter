#!/usr/bin/env python3
"""
Script de debug para detecção de hardware CUDA
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.hardware_detector import HardwareDetector
import subprocess

def debug_nvidia_smi():
    """Debug do nvidia-smi"""
    print("🔍 Debug nvidia-smi...")
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.free,driver_version,cuda_version', 
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=10
        )
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split('\n')
            for line in lines:
                parts = [part.strip() for part in line.split(',')]
                print(f"Partes: {parts}")
                
    except Exception as e:
        print(f"Erro: {e}")

def debug_ffmpeg():
    """Debug do FFmpeg"""
    print("\n🔍 Debug FFmpeg...")
    
    # Teste do caminho local
    local_ffmpeg = os.path.join(os.path.dirname(__file__), 'ffmpeg.exe')
    print(f"Caminho local: {local_ffmpeg}")
    print(f"Existe: {os.path.exists(local_ffmpeg)}")
    
    if os.path.exists(local_ffmpeg):
        try:
            result = subprocess.run([local_ffmpeg, '-encoders'], capture_output=True, text=True, timeout=10)
            print(f"Return code: {result.returncode}")
            
            if result.returncode == 0:
                # Procura por encoders NVENC
                lines = result.stdout.split('\n')
                nvenc_encoders = []
                for line in lines:
                    if 'nvenc' in line.lower():
                        nvenc_encoders.append(line.strip())
                        
                print(f"Encoders NVENC encontrados: {len(nvenc_encoders)}")
                for encoder in nvenc_encoders:
                    print(f"  - {encoder}")
                    
        except Exception as e:
            print(f"Erro ao executar FFmpeg: {e}")

def debug_detector():
    """Debug do detector completo"""
    print("\n🔍 Debug HardwareDetector...")
    
    detector = HardwareDetector()
    
    print(f"FFmpeg command: {detector.ffmpeg_command}")
    print(f"NVIDIA info: {detector.nvidia_info}")
    print(f"FFmpeg codecs: {detector.ffmpeg_codecs}")
    
    if detector.ffmpeg_codecs:
        print(f"Hardware encoders: {detector.ffmpeg_codecs.get('hardware_encoders', [])}")
        print(f"Hardware decoders: {detector.ffmpeg_codecs.get('hardware_decoders', [])}")

if __name__ == "__main__":
    debug_nvidia_smi()
    debug_ffmpeg()
    debug_detector()