#!/usr/bin/env python3
import os
import signal
import warnings

from pyVoIP.RTP import RTPParseError, PayloadType, RTPClient
from pyVoIP.VoIP import VoIPPhone, InvalidStateError, CallState
import wave
import time

def answer(call):
    try:
        # Load WAV file (8-bit, 8000 Hz, mono)
        f = wave.open(os.getenv("TASSE_KAFFEE", "tasse-lang.wav"), 'rb')
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
        warnings.warn(
            "call failed!",
            RuntimeWarning,
            stacklevel=2,
        )
        call.hangup()


def encode_packet(self, payload: bytes) -> bytes:
    if self.preference == PayloadType.PCMU:
        return self.encode_pcmu(payload)
    elif self.preference == PayloadType.PCMA:
#            return self.encode_pcmu(payload)
        return self.encode_pcma(payload)
    else:
        raise RTPParseError(
            "Unsupported codec (encode): " + str(self.preference)
        )


def trans(self) -> None:
    cycle = (1 / self.preference.rate) * 160  # 20 ms
    send_time = time.perf_counter()

    while self.NSD:
        payload = self.pmout.read()
        payload = self.encode_packet(payload)
        packet = b"\x80"  # RFC 1889 Version 2 No Padding Extension or CC.
        packet += chr(int(self.preference)).encode("utf8")
        try:
            packet += self.outSequence.to_bytes(2, byteorder="big")
        except OverflowError:
            self.outSequence = 0
            packet += self.outSequence.to_bytes(2, byteorder="big")
        try:
            packet += self.outTimestamp.to_bytes(4, byteorder="big")
        except OverflowError:
            self.outTimestamp = 0
            packet += self.outTimestamp.to_bytes(4, byteorder="big")
        packet += self.outSSRC.to_bytes(4, byteorder="big")
        packet += payload

        # debug(payload)

        while True:  # firstly wait non-CPU-intensive, but with time-sleep inaccuracy
            # (depending on OS, see https://stackoverflow.com/questions/1133857/how-accurate-is-pythons-time-sleep)
            to_wait = send_time - time.perf_counter()
            if (
            to_wait) <= 0:  # loop until no time due to the inaccuracy of time.sleep is remaining => always option b) below is taken
                break;
            time.sleep(to_wait)

        while True:  # now correct the time-sleep inaccuracy, by either:
            # a) waiting the remaining time accurately, but CPU-intensive - or
            # b) set delta > 0 to have the next packet sent earlier
            delta = time.perf_counter() - send_time
            if delta >= 0:
                break;

        send_time = time.perf_counter() + cycle - delta  # delta means to keep the 20 ms cycle: "send the next package earlier if his one was too late"
        if self.NSD:
            try:
                self.sout.sendto(packet, (self.outIP, self.outPort))
            except OSError:
                warnings.warn(
                    "RTP Packet failed to send!",
                    RuntimeWarning,
                    stacklevel=2,
                )

        self.outSequence += 1
        self.outTimestamp += len(payload)


if __name__ == "__main__":
    RTPClient.encode_packet = encode_packet
    RTPClient.trans = trans

    phone = VoIPPhone(
        os.getenv("TASSE_SIP", "sip.micropoc.de"),   # SIP server IP/hostname
        int(os.getenv("TASSE_PORT", 5060)),               # SIP port
        os.getenv("TASSE_USER", ""),             # Username
        os.getenv("TASSE_PASS", ""),     # Password
        myIP=os.getenv("TASSE_IP", ""),  # Local IP address
        callCallback=answer
    )


    def handler(signum, frame):
        print('Signal handler called with signal', signum)
        phone.stop()
        exit(0)

    signal.signal(signal.SIGQUIT, handler)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGHUP, handler)

    try:
        print(f"Starting the pbx ding listener")
        phone.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"Stopping the pbx ding")
        phone.stop()
        exit(0)
    finally:
        print(f"Stopping the pbx ding")
        phone.stop()
