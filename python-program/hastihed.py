import numpy as np
import matplotlib.pyplot as plt

# Constants
m = 0.25          # kg
g = 9.82          # m/s^2
rho = 1.2         # air density kg/m^3
Cd = 1.5          # drag coefficient

# Parachute geometry
r_parachute = 0.40/2        # m
r_hole = 0.06/2          # m 

A_parachute = np.pi * r_parachute**2
A_hole = np.pi * r_hole**2
A_full = A_parachute - A_hole  # effective area

# Deployment settings
deployment_time = 1     # seconds

# Time settings
dt = 0.01
t = np.arange(0, 2, dt)

# Arrays
v = np.zeros_like(t)

# Numerical simulation
for i in range(1, len(t)):

    # Gradual parachute deployment
    if t[i] < deployment_time:
        A = A_full * (t[i] / deployment_time)
    else:
        A = A_full

    drag = 0.5 * rho * Cd * A * v[i-1]**2
    a = g - drag / m
    v[i] = v[i-1] + a * dt

# Plot
plt.figure()
plt.plot(t, v)
plt.xlabel("Tid (s)")
plt.ylabel("Hastighed (m/s)")
plt.title("Hastighed som funktion af tid (hul + udfoldning)")
plt.show()
