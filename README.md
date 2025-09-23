# Fast Approximation for Calculating Deep Convection Cloud Top Heights from Satellite Brightness Temperature

Deep convection cloud top height diagnosis is very important in aviation meteorology. One of the methods to estimate altitude of existing convective cloud tops is to compare infrared satellite brightness temperature (BT) with a calculated parcel curve temperature („BT-parcel” method). The pressure where BT intersects the parcel curve (moist adiabat) is theoretical cloud top pressure level (as convective updraft temperature should equal temperature along the moist adiabat).

Moist adiabats are usually calculated iteratively from surface temperature and dewpoint, but this calculation can be computationally quite intensive. Inspired by previous work on non-iterative calculations of moist adiabats (Bakhshaii and Stull 2013, Moisseeva and Stull 2017.) we wanted to test even simpler approximations, which are still accurate enough for estimating cloud top pressure level.

In this code, moist adiabats are approximated with 5th degree polynomial. As moist adiabat shape changes with temperature and dewpoint (which can be represented by wet bulb potential temperature $\theta_w$), approximation coefficients also depend on $\theta_w$. This dependency was further modelled with 4th degree polynomials.

Coefficient dependency on $\theta_w$ approximation:
$C_i(\theta_w) = \sum_{j=0}^{4} a_{ij} \theta_w^j$

Moist adiabat (pressure as function of temperature) approximation:
$p(t) = \sum_{i=0}^{5} C_{i}(\theta_w)t^i$

With 5th degree moist adiabat approximation and 4th degree coefficient approximation (5x6 coefficients in total, evaluating 7 polynomials), in range of BT temperatures from -15 to -75 °C (the usual range of deep convective cloud top temperatures), maximum absolute altitude error (when compared to iterative moist adiabat calculation) is 28m.
For even more precise calculation, you can use cth_6th_deg_approx.py which uses 6th degree main approximation and 4th degree coefficient approximation (5x7 coefficients in total, evaluating 8 polynomials), and has maximum absolute altitude error of 7.5m!

## IMPORTANT NOTES:

This calculation will work only with convective clouds! For other clouds, you should take NWP vertical temperature profile and search from tropopause downward to find the closest or equal temperature to BT. Non-convective cloud top pressure should be at that pressure level (but bare in mind than only for optically thick clouds BT is a good approximation for cloud top temperature!).

As this calculation is sensitive to starting temperature and dewpoint values, it's probably best to
take the most unstable parcel from some area (e.g. 30-40km radius) around the target BT pixel.
The best approach to find the most unstable parcel is to calculate equivalent potential temperature ($\theta_e$)
from all temperatures and dewpoints in the area and just take the maximum value.

Also, in case of elevated convection (most of night and warm front convection), starting temperature and
dewpoint should not be taken from the surface, but from the most unstable level. This can also be found by
calculating $\theta_e$ from surface to 700hPa and taking the level with maximum $\theta_e$.

For more details see the attached conference poster.

How to cite: Šoljan, V., Jurković, J., and Babić, N.: Fast approximation for calculating deep convection cloud top heights from satellite brightness temperature, EMS Annual Meeting 2024, Barcelona, Spain, 1–6 Sep 2024, EMS2024-861, https://doi.org/10.5194/ems2024-861, 2024.


### References:

Bakhshaii, Atoossa, and Roland Stull. “Saturated Pseudoadiabats—A Noniterative Approximation.” Journal of Applied Meteorology and Climatology 52, no. 1 (2013): 5–15.

Bolton, David. “The Computation of Equivalent Potential Temperature.” Monthly Weather Review 108, no. 7 (July 1, 1980): 1046–53. https://doi.org/10.1175/1520-0493(1980)108<1046:TCOEPT>2.0.CO;2.

Davies-Jones, Robert. “An Efficient and Accurate Method for Computing the Wet-Bulb Temperature along Pseudoadiabats.” Monthly Weather Review 136, no. 7 (2008): 2764–85. https://doi.org/10.1175/2007MWR2224.1.

Moisseeva, Nadya, and Roland Stull. “Technical Note: A Noniterative Approach to Modelling Moist Thermodynamics.” Atmospheric Chemistry and Physics 17, no. 24 (December 19, 2017): 15037–43. https://doi.org/10.5194/acp-17-15037-2017.
