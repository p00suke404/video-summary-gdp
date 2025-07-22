import subprocess
import os
import openai
import boto3
import json

# --- Secrets ManagerからAPIキー取得 ---
def get_openai_api_key(secret_name="openai/api-key", region_name="ap-northeast-1"):
    client = boto3.client("secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])
    return secret["OPENAI_API_KEY"]

# --- YouTube音声抽出 ---
def download_audio(youtube_url, output_path="/tmp/audio.mp3"):
    command = [
        "/opt/bin/yt-dlp",  # Layerの場所に合わせて修正
        "-x",
        "--audio-format", "mp3",
        "-o", output_path,
        youtube_url
    ]
    subprocess.run(command, check=True)
    return output_path

# --- Whisper APIで文字起こし ---
def transcribe_audio(file_path, api_key):
    openai.api_key = api_key
    with open(file_path, "rb") as f:
        transcript = openai.Audio.transcribe("whisper-1", f)
    return transcript["text"]

# --- Lambdaハンドラー ---
def lambda_handler(event, context):
    print(os.listdir("/opt/bin"))  # ← これで中身が確認できる！
    try:
        youtube_url = event.get("youtube_url")
        if not youtube_url:
            return {
                "statusCode": 400,
                "body": "youtube_url is required"
            }

        # Secrets ManagerからAPIキー取得
        api_key = get_openai_api_key()

        # 音声抽出
        audio_path = download_audio(youtube_url)

        # 文字起こし
        result_text = transcribe_audio(audio_path, api_key)

        # ログ出力（CloudWatchで確認できる！）
        print("==== Transcription Result ====")
        print(result_text)
        print("==============================")

        return {
            "statusCode": 200,
            "body": result_text
        }

    except Exception as e:
        print("Error:", str(e))
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        }