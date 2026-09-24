import platform
import subprocess
import sys

OS = platform.system()  # "Windows" | "Darwin" | "Linux"


def main() -> None:
    print(f"⚙  LangVis language tutor - setup (OS: {OS or 'unknown'})")

    # requirements.txt filters OS-specific extras by itself via pip markers.
    print("\n▶ Installing Python dependencies…")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                   check=True)

    print("\n✅ Setup complete!")
    print("   1) Launch it:  python main.py   (it opens in your browser)")
    print("   2) Paste your free Gemini API key when the page asks for it.")
    print("   3) Check ⚙ Settings: your level, your own language, the pace.")
    print("   4) Pick a topic, press Start lesson and talk.")


if __name__ == "__main__":
    main()
