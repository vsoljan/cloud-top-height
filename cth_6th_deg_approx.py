# -*- coding: utf-8 -*-

# Copyright (c) 2024 Vinko Soljan
# vinko.soljan@crocontrol.hr
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Calculate deep moist convection top pressure level
from T [degC], Td [degC], p [hPa], and IR (10.8um) satellite BT temperature [degC],
where p is pressure level of T and Td.

This calculation uses "BT-parcel" method where you compare infrared satellite brightness
temperature (BT) with a calculated parcel curve temperature. The pressue where BT intersects
the parcel curve (moist adiabat) is theoretical cloud top pressure level (as convective
updraft temperature should equal temperature along the moist adiabat).

Moist adiabats are approximated with 6th degree polynomial. As moist adiabat shape changes
with temperature and dewpoint (which can be represented by wet bulb potential temperature
[theta_w]), approximation coefficients also depend on theta_w.
This dependency was further modelled with 4th degree polynomials.
So in total we have 5x7 coefficients with which we can approximate moist adiabats as:

C_i(theta_w) = a_i0 * theta_w^4 + a_i1 * theta_w^3 + a_i2 * theta_w^2 + a_i3 * theta_w + a_i4

p(t) = C_0(theta_w)*t^6 + C_1(theta_w)*t^5 + C_2(theta_w)*t^4 + C_3(theta_w)*t^3 + 
       C_4(theta_w)*t^2 + C_5(theta_w)*t + C_6(theta_w)

Moist adiabats are usually calculated iteratively, step by step, from cloud base
(defined by T and Td), to some pressure level or temperature, by solving thermodynamic equations
at each step. This can be computationaly demanding, so this polynomial approximation is much faster.
With 6th degree moist adiabat approximation and 4th degree coefficient approximation,
in range of BT temperatures from -15 to -75 deg C (the usual range of deep convective cloud top temperatures),
maximum absolute altitude error (when compared to iterative moist adiabat calculation) is 7.5m.

IMPORTANT NOTES:
This calculation will work only with convective clouds!

As this calculation is sensitive to starting temperature and dewpoint values, it's probably best to
take the most unstable parcel from some area (e.g. 30-40km radius) around the target BT pixel.
The best approach to find the most unstable parcel is to calculate equivalent potential temperature (theta_e)
from all temperatures and dewpoints in the area.

Also, in case of elevated convection (most of night and warm front convection), starting temperature and
dewpoint should not be taken from the surface, but from the most unstable level. This can also be found by
calculating theta_e from surface to 700hPa and taking the level with maximum theta_e.

VERSION:
16.09.2024.
"""

import numpy as np


# Constants
ZERO_C_K = 273.15
# Gas constant J/kg/K
Rd = 287
# kappa = Rd/Cpd
Rd_Cpd = 0.28571428571428564
# Epsilon (molecular weight ration)
epsilon = 0.6219569100577033

R1 = 8.31432  # [J / (K mol)]
M = 0.0289644  # [kg / mol]
R = R1 / M  # [J / (K kg)]
g = 9.80665  # [m / s^2]
gamma = 0.65 / 100  # [K / m]
t_sfc = 15.0 + 273.15  # [K]
p_sfc = 1013.25  # [hPa]
K = R * gamma / g
ftm = 3.28084  # [ft / m]


def p_to_h(p):
    """
    Calculate height in m from pressure [hPa]
    in ICAO standard atmophere
    """
    # Check if we are in tropopause (p = 226.32 hPa)
    if p <= 226.32:
        h = 11000 - Rd * (ZERO_C_K - 56.5) / g * np.log(p / 226.32)
    else:
        h = t_sfc / gamma * (1 - np.power((p / p_sfc), K))
    return h

# Vectorize above function so it can take arrays
p2h = np.vectorize(p_to_h)


def potential_temperature(press, temp):
    """
    Calculate potential temperature in C
    INPUT:
        temp (starting temperature) [degC]
        press (pressure level of starting temperature) [hPa]
    OUTPUT:
        potential temperature [degC]
    """
    theta = (temp + ZERO_C_K) * (1000 / press) ** Rd_Cpd
    return theta - ZERO_C_K


def mixing_ratio(v_p, t_p):
    """
    Mixing ratio from vapour pressure (partial pressure)
    and total pressure [Pa]
    """
    return epsilon * v_p / (t_p - v_p)


def e_sat(t_dew):
    """
    Calculates saturation vapor pressure using the Bolton equation.
    INPUT:
        t_dew: dewpoint temp [degC]
    OUTPUT:
        saturation vapor pressure [Pa]
    """
    e_sat = 611.2 * np.exp((17.67 * t_dew) / (t_dew + 243.5))
    return e_sat


def saturation_mixing_ratio(p, td):
    """
    Saturation mixing ratio from pressure and dewpoint
    Hobbs 1977 formula
    INPUT:
        td (dewpoint) [degC]
        p (pressure) [Pa]
    OUTPUT:
        saturation mixing ratio
    """
    e_s = e_sat(td)
    return mixing_ratio(e_s, p * 100)


def theta_e(t, td, p):
    """
    Bolton's approximation of Equivalent potential temperature
    INPUT:
        t, td (temperature, dewpoint)[degC]
        p (pressure level of t and td) [hPa]
    OUTPUT:
        theta_e [K]
    """
    r_s = saturation_mixing_ratio(p, td)
    e = e_sat(td)
    theta = potential_temperature(p - e / 100., t)
    # Convert to Kelvin and Pa
    t = t + ZERO_C_K
    td = td + ZERO_C_K
    p = p * 100
    theta = theta + ZERO_C_K
    t_l = 56 + 1. / (1. / (td - 56) + np.log(t / td) / 800.)
    th_l = theta * np.power((t / t_l), (0.28 * r_s))
    return th_l * np.exp(r_s * (1 + 0.448 * r_s) * (3036. / t_l - 1.78))


def theta_w_from_theta_e(th_e):
    """
    Davies Jones 2008 calculation of wet bulb potential temperature
    from equivalent potential temperature.
    INPUT:
        theta_e_val (equivalent potential temperature) [K]
    OUTPUT:
        theta_w [K]
    """
    x = th_e / 273.15
    x2 = x * x
    x3 = x2 * x
    x4 = x3 * x
    a = 7.101574 - 20.68208 * x + 16.11182 * x2 + 2.574631 * x3 - 5.205688 * x4
    b = 1 - 3.552497 * x + 3.781782 * x2 - 0.6899655 * x3 - 0.5929340 * x4
    th_w = th_e - np.exp(a / b)
    return np.where(th_e <= 173.15, th_e, th_w)


def theta_w(t, td, p):
    """
    Davies Jones 2008 calculation of wet bulb potential temperature
    from equivalent potential temperature.
    INPUT:
        t, td (temperature, dewpoint)[degC]
        p (pressure level of t and td) [hPa]
    OUTPUT:
        theta_w [K]
    """
    # Calculate theta-e [K]
    th_e = theta_e(t, td, p)
    return theta_w_from_theta_e(th_e)


def ctp_from_theta_e(theta_e_max, bt):
    """
    Cloud top pressure from theta_e and BT
    This can be useful if we find max theta_e in some 3D space
    (e.g. 30km radius around BT pixel and sfc-700hPa), so we get
    the moist adiabat of the most unstable parcel.
    INPUT:
        theta_e_max [degC]
        bt (IR brightness temp) [degC]
    OUTPUT:
        cloud top pressure [hPa]
    """
    # Evaluate wet bulb potential temp. from theta_e
    tw = theta_w_from_theta_e(theta_e_max) - ZERO_C_K
    tw2 = tw * tw
    tw3 = tw2 * tw
    tw4 = tw3 * tw
    # Evaluate moist adiabat polynomial coefficients
    mac = np.zeros(7)
    mac[0] =  1.34598934e-15 * tw4 - 6.95711517e-14 * tw3 + 7.06772534e-13 * tw2 + 3.27562146e-13 * tw + 2.14085111e-10
    mac[1] =  1.46826594e-13 * tw4 - 3.28095045e-12 * tw3 - 1.90355508e-10 * tw2 + 2.99865474e-09 * tw + 1.17192247e-07
    mac[2] = -4.03819245e-12 * tw4 + 1.04339580e-09 * tw3 - 5.57183537e-08 * tw2 + 5.66654023e-07 * tw + 2.72099202e-05
    mac[3] = -1.04764419e-09 * tw4 + 1.09514749e-07 * tw3 - 4.37757525e-06 * tw2 + 3.47578633e-05 * tw + 3.40521208e-03
    mac[4] = -4.13270841e-08 * tw4 + 3.51397283e-06 * tw3 - 1.36808612e-04 * tw2 - 2.81625246e-04 * tw + 2.74722979e-01
    mac[5] =  4.86347926e-08 * tw4 + 1.76182949e-05 * tw3 - 1.78557297e-03 * tw2 - 2.44625335e-01 * tw + 1.92406642e+01
    mac[6] =  5.64716869e-05 * tw4 - 1.62042578e-03 * tw3 - 2.23587882e-02 * tw2 - 1.92635339e+01 * tw + 9.99811121e+02
    # Evaluate and return CT pressure: p(t)
    return np.polyval(mac, bt)

# Vectorize above function so it can take arrays
ctp_from_theta_e_v = np.vectorize(ctp_from_theta_e)


def ctp(t0, td0, p0, bt):
    """
    Cloud top pressure from T, Td, p, and BT
    INPUT:
        t0 (temperature) [degC]
        Td0 (dewpoint)   [degC]
        p0 (pressure level of t0 and td0) [hPa]
        bt (IR brightness temp) [degC]
    OUTPUT:
        cloud top pressure [hPa]
    """
    # Evaluate wet bulb potential temp. for given T, Td and p
    tw = theta_w(t0, td0, p0) - ZERO_C_K
    tw2 = tw * tw
    tw3 = tw2 * tw
    tw4 = tw3 * tw
    # Evaluate moist adiabat polynomial coefficients
    mac = np.zeros(7)
    mac[0] =  1.34598934e-15 * tw4 - 6.95711517e-14 * tw3 + 7.06772534e-13 * tw2 + 3.27562146e-13 * tw + 2.14085111e-10
    mac[1] =  1.46826594e-13 * tw4 - 3.28095045e-12 * tw3 - 1.90355508e-10 * tw2 + 2.99865474e-09 * tw + 1.17192247e-07
    mac[2] = -4.03819245e-12 * tw4 + 1.04339580e-09 * tw3 - 5.57183537e-08 * tw2 + 5.66654023e-07 * tw + 2.72099202e-05
    mac[3] = -1.04764419e-09 * tw4 + 1.09514749e-07 * tw3 - 4.37757525e-06 * tw2 + 3.47578633e-05 * tw + 3.40521208e-03
    mac[4] = -4.13270841e-08 * tw4 + 3.51397283e-06 * tw3 - 1.36808612e-04 * tw2 - 2.81625246e-04 * tw + 2.74722979e-01
    mac[5] =  4.86347926e-08 * tw4 + 1.76182949e-05 * tw3 - 1.78557297e-03 * tw2 - 2.44625335e-01 * tw + 1.92406642e+01
    mac[6] =  5.64716869e-05 * tw4 - 1.62042578e-03 * tw3 - 2.23587882e-02 * tw2 - 1.92635339e+01 * tw + 9.99811121e+02
    # Evaluate and return CT pressure: p(t)
    return np.polyval(mac, bt)

# Vectorize above function so it can take arrays
ctp_v = np.vectorize(ctp)


if __name__ == '__main__':
    # Test parallel computation for multiple points
    t = np.arange(10, 35)
    td = t - 8
    p = np.arange(990, 990+t.size)
    bt = np.arange(-75, -75+t.size)
    tops_p = ctp_v(t, td, p, bt)
    isa_heights = p2h(tops_p)
    print(tops_p)
    print()
    print(isa_heights)
    print("="*80)

    # Example of finding the most unstable parcel
    # For one BT value
    bt = -65
    # We take spatial data e.g. 30km around the lat/lon of above BT pixel
    # and also multiple levels from surface to 700hPa in the same radius.
    # So we have arrays of temps, dewpoints, and pressure (representing different levels)
    # We just have to calculate max theta_e and we don't care about it's exact location! 
    np.random.seed(42)
    # Surface level arrays simulation
    t = np.random.randint(10, 28, size=30)
    td = t - np.random.randint(2, 11, size=30)
    p = np.ones(30) * 1000

    # 900 hPa level simulation
    t_900 = np.random.randint(0, 25, size=30)
    td_900 = t_900 - np.random.randint(2, 11, size=30)
    t = np.append(t, t_900)
    td = np.append(td, td_900)
    p = np.append(p, np.ones(30) * 900)

    # 850 hPa level simulation
    t_850 = np.random.randint(-10, 20, size=30)
    td_850 = t_850 - np.random.randint(2, 8, size=30)
    t = np.append(t, t_850)
    td = np.append(td, td_850)
    p = np.append(p, np.ones(30) * 850)    

    # 800 hPa level simulation
    t_800 = np.random.randint(-10, 15, size=30)
    td_800 = t_800 - np.random.randint(1, 8, size=30)
    t = np.append(t, t_800)
    td = np.append(td, td_800)
    p = np.append(p, np.ones(30) * 800)

    print(t)
    print(td)
    print(p)

    # Find the most unstable parcel in all levels
    th_e = theta_e(t, td, p)
    th_e_max = th_e.max()
    # Just to check which level and values
    th_e_max_idx = th_e.argmax()
    print(f"Most unstable parcel p: {p[th_e_max_idx]} hPa, T: {t[th_e_max_idx]} C, Td: {td[th_e_max_idx]} C")

    # Calculate top pressure from this parcel
    ct_press = ctp_from_theta_e(th_e_max, bt)
    print(f"Cloud top pressure {ct_press:.1f} hPa => ISA altitude: {p2h(ct_press):.0f} m")
