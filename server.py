import sys, threading, time, subprocess
import RPi.GPIO as GPIO
import socket

worker_thread = None
shutdown = False
ledpins = [18, 17, 27] # R, G, B
volume = int(subprocess.check_output('amixer get Master | egrep -o "[0-9]+%" | head -1 | egrep -o "[0-9]*"', shell=True)) # Inital volume

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in ledpins:
    GPIO.setup(pin, GPIO.OUT)

HOST = ''
PORT = 50007

def lightsoff():
    for pin in ledpins:
        GPIO.output(pin, GPIO.LOW)

def volume_worker(delta):
    global shutdown, volume
    print('start worker, ' + str(shutdown) + ' ' + str(delta))
    volume = max(0, min(64, volume))
    while not shutdown and volume >= 0 and volume <= 64:
        print(volume)
        subprocess.call(['amixer', '-q', 'sset', 'Master', str(int(volume)) + '%'])
        volume = volume + delta / 2
        time.sleep(0.5)

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen(3)
        while True:
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                while True:
                    try:
                        data = conn.recv(2)
                    except:
                        lightsoff()
                        sys.exit()
                    if not data: break
                    print(data[0], data[1])
                    if data[0] == 255:
                        global worker_thread, shutdown
                        if data[1] <= 1:
                            shutdown = True
                            worker_thread.join()
                            worker_thread = None
                        else:
                            if worker_thread is not None and worker_thread.is_alive():
                                shutdown = True
                                worker_thread.join()
                            elif data[1] == 2: # Start decreasing volume
                                worker_thread = threading.Thread(name='volume_worker', target=volume_worker, args=(-8,))
                                shutdown = False
                                worker_thread.start()
                            elif data[1] == 3: # Start increasing volume
                                worker_thread = threading.Thread(name='volume_worker', target=volume_worker, args=(8,))
                                shutdown = False
                                worker_thread.start()
                    else:
                        light = ledpins[data[0]]
                        state = data[1]
                        GPIO.output(light, GPIO.HIGH if state else GPIO.LOW)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Shutting down...')
    finally:
        lightsoff()
