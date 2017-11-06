import os, sys, inspect, thread, time, socket, math
from subprocess import call
src_dir = os.path.dirname(inspect.getfile(inspect.currentframe()))
# Windows and Linux
arch_dir = '../lib/x64' if sys.maxsize > 2**32 else '../lib/x86'
# Mac
#arch_dir = os.path.abspath(os.path.join(src_dir, '../lib'))

sys.path.insert(0, os.path.abspath(os.path.join(src_dir, arch_dir)))

import Leap

s = socket.socket()
host = '192.168.43.194'# ip of raspberry pi
port = 50007
s.connect((host, port))
circling = False

class SampleListener(Leap.Listener):
	lastFrameID = 0

	def on_connect(self, controller):
		print "Connected"

	def on_frame(self, controller):
		frame = controller.frame()

		for gesture in frame.gestures():
			if gesture.type is Leap.Gesture.TYPE_SWIPE and gesture.state is Leap.Gesture.STATE_START :
				swipe = Leap.SwipeGesture(gesture)
				swiper = swipe.pointable
				direction = swipe.direction
				if(swiper.is_finger and Leap.Finger(swiper).type == Leap.Finger.TYPE_INDEX and direction.z < -0.1):
					if(direction.x < -0.2 and direction.y > 0.1):
						print "Red light on"
						s.sendall(bytearray([0,1]))
					elif(direction.x < -0.2 and direction.y < -0.1):
						print "Red light off"
						s.sendall(bytearray([0,0]))

					if(abs(direction.x) <= 0.2 and direction.y > 0.1):
						print "Green light on"
						s.sendall(bytearray([1,1]))
					elif(abs(direction.x) <=0.2 and direction.y < -0.1):
						print "Green light off"
						s.sendall(bytearray([1,0]))

					if(direction.x > 0.2 and direction.y > 0.1):
						print "Blue light on"
						s.sendall(bytearray([2,1]))
					elif(direction.x > 0.2 and direction.y < -0.1):
						print "Blue light off"
						s.sendall(bytearray([2,0]))

				if(direction.y < -0.80 and len(frame.hands) == 2): #Universal turn off all lights function
					print "Lights out!"
					s.sendall(bytearray([0,0]))
					s.sendall(bytearray([1,0]))
					s.sendall(bytearray([2,0]))


			if gesture.type is Leap.Gesture.TYPE_CIRCLE:
				circle = Leap.CircleGesture(gesture)
				clockwise = circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2

				global circling
				completedTurns = (math.floor(circle.progress) >= 2)
				if not completedTurns:
					continue
				if(circling and gesture.state is Leap.Gesture.STATE_STOP and not clockwise):
					print "Counterclockwise / Volume decreased / STOP"
					s.sendall(bytearray([255,0]))
					circling = False
				elif(circling and gesture.state is Leap.Gesture.STATE_STOP and clockwise):
					print "Clockwise / Volume increased / STOP"
					s.sendall(bytearray([255,1]))
					circling = False
				elif(not circling and not clockwise):
					print "Counterclockwise / Volume decreased / START"
					s.sendall(bytearray([255,2]))
					circling = True
				elif(not circling and clockwise):
					print "Clockwise / Volume increased / START"
					s.sendall(bytearray([255,3]))
					circling = True


def main():
	listener = SampleListener()
	controller = Leap.Controller()
	controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);
	controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE)
	controller.config.set("Gesture.Circle.MinArc", 500)
	controller.config.set("Gesture.Circle.MinRadius", 50.0)

	controller.config.save()
	controller.add_listener(listener)
	frame = controller.frame()


	print "Press Enter to quit.."
	try:
		sys.stdin.readline()
	except KeyboardInterrupt:
		print "Interrupted"
		pass
	finally:
		controller.remove_listener(listener)
		print "Process terminated"
		s.close()


if __name__=="__main__":
	main()
