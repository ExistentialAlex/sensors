
import multiprocessing as mp


def main():
    try:
        # Start process to send data to
        mp.set_start_method('spawn')
        q = mp.Queue()
        p = mp.Process()

    except KeyboardInterrupt:
        GPIO.cleanup()