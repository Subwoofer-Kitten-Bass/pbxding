import time
import subprocess
from python_sip_client import BareSIP

wav_file_path = "/home/jbuch/scrap/pbxding/tasse-lang.wav"

def handle_incoming_call(from_uri):
    print("Incoming call from", from_uri)
    bs.answer()
    print("Call answered, streaming WAV file to caller...")
    try:
        # Play WAV to system audio device which BareSIP is using for audio capture
        subprocess.Popen(["aplay","-D","pipewire", wav_file_path])
    except Exception as e:
        print("Error during WAV playback:", e)

bs = BareSIP(debug=True)
bs.on(BareSIP.Event.INCOMING_CALL, handle_incoming_call)

try:
    bs.start()
    bs.create_user_agent("2333", "f8b902148fc6", "sip.micropoc.de")
    
    while not bs.user_agents()[0].registered:
        time.sleep(0.1)

    print("Registered and ready to receive calls. Press Ctrl+C to exit.")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Shutting down.")
finally:
    bs.stop()
