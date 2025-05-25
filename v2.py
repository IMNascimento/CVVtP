import os
import subprocess
import whisper
from deep_translator import GoogleTranslator
from gtts import gTTS
from moviepy import VideoFileClip, AudioFileClip, vfx
from pydub import AudioSegment

def extrair_audio(video_path, audio_path):
    print("[1/6] Extraindo áudio...")
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)
    return video

def transcrever_audio(audio_path):
    print("[2/6] Transcrevendo áudio...")
    model = whisper.load_model("small")  # pode mudar para "base" se quiser mais rápido
    result = model.transcribe(audio_path)
    return result["text"]

def traduzir_texto(texto, destino='pt'):
    print("[3/6] Traduzindo texto...")
    traducao = GoogleTranslator(source='auto', target=destino).translate(texto)
    return traducao

def gerar_audio_traduzido(texto_traduzido, audio_saida_path):
    print("[4/6] Gerando áudio em português...")
    tts = gTTS(text=texto_traduzido, lang='pt')
    tts.save(audio_saida_path)


def ajustar_velocidade_ffmpeg(audio_path, fator_velocidade, output_path):
    print(f"[5/6] Ajustando velocidade com FFmpeg (fator: {fator_velocidade:.2f})...")
    
    if fator_velocidade <= 2.0:
        command = [
            "ffmpeg", "-y", "-i", audio_path,
            "-filter:a", f"atempo={fator_velocidade}",
            output_path
        ]
    else:
        # ffmpeg só aceita de 0.5 a 2.0 por vez — então encadeia filtros
        # Ex: 2.5x → atempo=2.0,atempo=1.25
        steps = []
        remaining = fator_velocidade
        while remaining > 2.0:
            steps.append("2.0")
            remaining /= 2.0
        steps.append(f"{remaining:.2f}")
        atempo_filter = ",".join([f"atempo={s}" for s in steps])

        command = [
            "ffmpeg", "-y", "-i", audio_path,
            "-filter:a", atempo_filter,
            output_path
        ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def substituir_audio(video, novo_audio_path, video_saida_path):
    print("[6/6] Injetando novo áudio no vídeo...")
    novo_audio = AudioFileClip(novo_audio_path)
    novo_video = video.with_audio(novo_audio)
    novo_video.write_videofile(video_saida_path, codec='libx264', audio_codec='aac')

def main():
    caminho_video = "entrada.mp4"  # seu vídeo original
    caminho_audio_original = "audio_original.wav"
    caminho_audio_traduzido_bruto = "audio_traduzido_bruto.mp3"
    caminho_audio_traduzido_ajustado = "audio_traduzido_ajustado.mp3"
    caminho_video_saida = "saida_portugues_v2.mp4"

    # Passos
    video = extrair_audio(caminho_video, caminho_audio_original)
    texto = transcrever_audio(caminho_audio_original)
    texto_traduzido = traduzir_texto(texto)
    gerar_audio_traduzido(texto_traduzido, caminho_audio_traduzido_bruto)

    # Calcular fator de velocidade
    duracao_video = video.duration
    audio_segment = AudioSegment.from_file(caminho_audio_traduzido_bruto)
    duracao_audio = len(audio_segment) / 1000  # Correto: em segundos

    print(f"Duração vídeo: {duracao_video:.2f} segundos")
    print(f"Duração áudio bruto: {duracao_audio:.2f} segundos")

    fator_velocidade = duracao_audio / duracao_video
    print(f"Fator de ajuste: {fator_velocidade:.4f}")
    #duracao_audio = AudioFileClip(caminho_audio_traduzido_bruto).duration
    

    # Ajustar velocidade do áudio traduzido
    ajustar_velocidade_ffmpeg(caminho_audio_traduzido_bruto, fator_velocidade, caminho_audio_traduzido_ajustado)

    # Substituir áudio no vídeo
    substituir_audio(video, caminho_audio_traduzido_ajustado, caminho_video_saida)
    # Limpeza de arquivos temporários
    os.remove(caminho_audio_original)
    os.remove(caminho_audio_traduzido_bruto)
    os.remove(caminho_audio_traduzido_ajustado)

    print("✅ Processo concluído com sucesso!")

if __name__ == "__main__":
    main()