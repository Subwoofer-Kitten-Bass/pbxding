#!/usr/bin/env python3
import os
from pyVoIP.VoIP import VoIPPhone, InvalidStateError, CallState
import wave
import time

def answer(call):
    try:
        # Load WAV file (8-bit, 8000 Hz, mono)
        f = wave.open('tasse-lang.wav', 'rb')
        frames = f.getnframes()
        data = f.readframes(frames)
        f.close()

        # Answer the call
        call.answer()

        # Transmit audio data bytes
        call.write_audio(data)
        print(f"got a call from: {call.request.headers["From"]["raw"]}")


        # Wait while call is answered and audio duration not exceeded
        stop = time.time() + (frames / 8000)  # frames / sample rate in seconds
        while time.time() <= stop and call.state == CallState.ANSWERED:
            time.sleep(0.1)

        # Hang up after playing
        call.hangup()

    except InvalidStateError:
        pass
    except Exception:
        call.hangup()

if __name__ == "__main__":
    phone = VoIPPhone(
        os.getenv("TASSE_SIP", "sip.micropoc.de"),   # SIP server IP/hostname
        int(os.getenv("TASSE_PORT", 5060)),               # SIP port
        os.getenv("TASSE_USER", ""),             # Username
        os.getenv("TASSE_PASS", ""),     # Password
        myIP=os.getenv("TASSE_IP", ""),  # Local IP address
        callCallback=answer
    )
    phone.start()
    input("Press enter to disable the phone\n")
    phone.stop()
