import math
from scipy.optimize import least_squares, root_scalar
from scipy.integrate import quad

def bezierToPoly3(param):
  x3, y3, l0, l1, h0, h1 = param
  x1, y1 =    l0*math.cos(h0),    l0*math.sin(h0)
  x2, y2 = x3-l1*math.cos(h1), y3-l1*math.sin(h1)
  bU, cU, dU = 3*x1, -6*x1+3*x2, 3*x1-3*x2+x3
  bV, cV, dV = 3*y1, -6*y1+3*y2, 3*y1-3*y2+y3
  return [bU, cU, dU, bV, cV, dV]

def poly3ToXYH(bU, cU, dU, bV, cV, dV, l, tol=1e-8):
    def integrand(t):
      du = bU+2*cU*t+3*dU*t**2
      dv = bV+2*cV*t+3*dV*t**2
      return math.sqrt(du**2+dv**2)
    def objective(t):
        current_length, _ = quad(integrand, 0, t, epsabs=tol, epsrel=tol)
        return current_length-l
    sol = root_scalar(objective, bracket=[0.0, 1.0], method='bisect', xtol=tol)
    t = sol.root
    x = bU*t+cU*t**2+dU*t**3
    y = bV*t+cV*t**2+dV*t**3
    h = math.atan2(bV+2*cV*t+3*dV*t**2, bU+2*cU*t+3*dU*t**2)
    return x, y, h