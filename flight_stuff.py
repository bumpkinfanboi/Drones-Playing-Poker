from codrone_edu.drone import *

drone = Drone()
drone.pair()
print("paired!")
drone.takeoff()
drone.hover(5)
drone.land()
drone.close()