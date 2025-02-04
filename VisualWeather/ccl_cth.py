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
temperature (BT) with a calculated parcel curve temperature. The pressure where BT intersects
the parcel curve (moist adiabat) is theoretical cloud top pressure level (as convective
updraft temperature should equal temperature along the moist adiabat).

Moist adiabats are approximated with 5th degree polynomial. As moist adiabat shape changes
with temperature and dewpoint (which can be represented by wet bulb potential temperature
[theta_w]), approximation coefficients also depend on theta_w.
This dependency was further modelled with 4th degree polynomials.
So in total we have 5x6 coefficients with which we can approximate moist adiabats as:

C_i(theta_w) = a_i0 * theta_w^4 + a_i1 * theta_w^3 + a_i2 * theta_w^2 + a_i3 * theta_w + a_i4

p(t) = C_0(theta_w)*t^5 + C_1(theta_w)*t^4 + C_2(theta_w)*t^3 + C_3(theta_w)*t^2 + C_4(theta_w)*t + C_5(theta_w)

Moist adiabats are usually calculated iteratively, step by step, from cloud base
(defined by T and Td), to some pressure level or temperature, by solving thermodynamic equations
at each step. This can be computationaly demanding, so this polynomial approximation is much faster.
With 5th degree moist adiabat approximation and 4th degree coefficient approximation,
in range of BT temperatures from -15 to -75 deg C (the usual range of deep convective cloud top temperatures),
maximum absolute altitude error (when compared to iterative moist adiabat calculation) is 28m.

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
08.10.2024.

NOTES (HOW TO USE):
1. Copy script to (every workstation!):
$METPATH/python/IBL/Plugins/Kernel/

2. Execute in shell:
iplugins --update
kutil f | grep ccl

3. Test custom function:
equationd 'v350[2,1] v-65[2,0] Fccl_cth_theta_e_python$v21v20$v37'
"""

import numpy as np
import IBL.Kernel as K
import IBL.Kernel.Extensions as KE


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
Ka = R * gamma / g
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
        h = t_sfc / gamma * (1 - np.power((p / p_sfc), Ka))
    return h

# Vectorize above function so it can take arrays
#p2h = np.vectorize(p_to_h)


def p_to_fl(pressure):
    """
    Pressure to flight level (FL)
    INPUT:
        pressure [hPa]
    OUTPUT:
        flight level (FL) [hft]
    """
    h_m = p_to_h(pressure)
    h_fl = int(round(h_m * ftm / 100))
    return h_fl


def round_base(x, base=10):
    """
    Round number to defined base
    """
    # For Python 3 use:
    # base * round(x / base)
    return int(base * round(float(x) / base))


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
    mac = np.zeros(6)
    mac[0] = 1.34900172e-13 * tw4 - 9.43979160e-12 * tw3 + 1.87653668e-10 * tw2 - 7.65322959e-11 * tw + 2.92814658e-08
    mac[1] = 1.83574985e-11 * tw4 - 1.34431358e-09 * tw3 + 1.98697357e-08 * tw2 + 2.98476410e-07 * tw + 1.27504708e-05
    mac[2] = 9.71770820e-10 * tw4 - 6.82962603e-08 * tw3 - 2.29995000e-07 * tw2 + 5.36097021e-05 * tw + 2.28596093e-03
    mac[3] = 1.53207987e-08 * tw4 - 1.92972790e-07 * tw3 - 1.22319198e-04 * tw2 + 2.46185591e-03 * tw + 2.34738009e-01
    mac[4] = -1.69715923e-07 * tw4 + 7.78264909e-05 * tw3 - 5.65297782e-03 * tw2 - 1.58431571e-01 * tw + 1.86846195e+01
    mac[5] = 4.15209383e-05 * tw4 - 1.28889861e-04 * tw3 - 7.22894532e-02 * tw2 - 1.86535189e+01 * tw + 9.98111805e+02
    # Evaluate and return CT pressure: p(t)
    return np.polyval(mac, bt)

# Vectorize above function so it can take arrays
#ctp_from_theta_e_v = np.vectorize(ctp_from_theta_e)


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
    mac = np.zeros(6)
    mac[0] = 1.34900172e-13 * tw4 - 9.43979160e-12 * tw3 + 1.87653668e-10 * tw2 - 7.65322959e-11 * tw + 2.92814658e-08
    mac[1] = 1.83574985e-11 * tw4 - 1.34431358e-09 * tw3 + 1.98697357e-08 * tw2 + 2.98476410e-07 * tw + 1.27504708e-05
    mac[2] = 9.71770820e-10 * tw4 - 6.82962603e-08 * tw3 - 2.29995000e-07 * tw2 + 5.36097021e-05 * tw + 2.28596093e-03
    mac[3] = 1.53207987e-08 * tw4 - 1.92972790e-07 * tw3 - 1.22319198e-04 * tw2 + 2.46185591e-03 * tw + 2.34738009e-01
    mac[4] = -1.69715923e-07 * tw4 + 7.78264909e-05 * tw3 - 5.65297782e-03 * tw2 - 1.58431571e-01 * tw + 1.86846195e+01
    mac[5] = 4.15209383e-05 * tw4 - 1.28889861e-04 * tw3 - 7.22894532e-02 * tw2 - 1.86535189e+01 * tw + 9.98111805e+02
    # Evaluate and return CT pressure: p(t)
    return np.polyval(mac, bt)

# Vectorize above function so it can take arrays
#ctp_v = np.vectorize(ctp)


# python function that will be exposed to kernel
def ccl_cth(ctx, parcel_temp, parcel_dewpoint, parcel_pressure, brightness_temp):
    """
    Cloud top flight level [hft] form parcel T, Td, p and BT
    """
    t0 = parcel_temp.toValue(K.u.T_CELS)
    td0 = parcel_dewpoint.toValue(K.u.T_CELS)
    p0 = parcel_pressure.toValue(K.u.P_HPA)
    # Empirical correction of BT -5 C
    bt = brightness_temp.toValue(K.u.T_CELS) - 5
    ct_press = ctp(t0, td0, p0, bt)
    # ct_fl = round_base(p_to_fl(ct_press))
    ct_fl = p_to_fl(ct_press)
    return K.mkValue(ct_fl, K.u.D_FL)


# python function that will be exposed to kernel
def ccl_cth_theta_e(ctx, th_e, brightness_temp):
    """
    Cloud top FL form theta_e and BT
    """
    th_e_K = th_e.toValue(K.u.T_KELV)
    # Empirical correction of BT -5 C
    bt_C = brightness_temp.toValue(K.u.T_CELS) - 5
    ct_press = ctp_from_theta_e(th_e_K, bt_C)
    # ct_fl = round_base(p_to_fl(ct_press))
    ct_fl = p_to_fl(ct_press)
    return K.mkValue(ct_fl, K.u.D_FL)


class CclKernelExtension(K.KernelExtension):
    def __init__(self):
        K.KernelExtension.__init__(self)
        # register python function into kernel
        # v21 = temp [K], v20 = temp [C], v37 = distance [FL]
        self.exposePython("ccl_cth_theta_e_python$v21v20$v37", ccl_cth_theta_e, False)
        # register regular kernel function
        self.exposeExpression("ccl_cth_theta_e$v21v20$v37", "{ @0 @1 Fccl_cth_theta_e_python$v21v20$v37 }")

        # register python function into kernel
        # v20 = temp [C], v20 = dewpoint [C], v60 = pressure [hPa], v20 = b.temp [C], v37 = distance [FL]
        self.exposePython("ccl_cth_python$v20v20v60v20$v37", ccl_cth, False)
        # register regular kernel function
        self.exposeExpression("ccl_cth$v20v20v60v20$v37", "{ @0 @1 @2 @3 Fccl_cth_python$v20v20v60v20$v37 }")


__IMPLEMENTS__ = (CclKernelExtension,)
