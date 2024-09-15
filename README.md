# Fast Approximation for Calculating Deep Convection Cloud Top Heights from Satellite Brightness Temperature

Deep convection cloud top height diagnosis is very important in aviation meteorology. One of the methods to estimate altitude of existing convective cloud tops is to compare infrared satellite brightness temperature (BT) with a calculated parcel curve temperature („BT-parcel” method). The pressue where BT intersects the parcel curve (moist adiabat) is theoretical cloud top pressure level (as convective updraft temperature should equal temperature along the moist adiabat).

Moist adiabats are usually calculated iteratively from surface temperature and dewpoint, but this calculation can be computationally quite intensive. Inspired by previous work on non-iterative calculations of moist adiabats (Bakhshaii and Stull 2013, Moisseeva and Stull 2017.) we wanted to test even simpler approximations, which are still accurate enough for estimating cloud top pressure level.

In this code, moist adiabats are approximated with 5th degree polynomial. As moist adiabat shape changes with temperature and dewpoint (which can be represented by wet bulb potential temperature theta_w), approximation coefficients also depend on theta_w. This dependency was further modelled with 4th degree polynomials.

Coefficient dependency on $\theta_w$ approximation:
$C_i(\theta_w) = \sum_{j=0}^{4} a_{ij} \theta_w^i$

Moist adiabat (pressure as function of temperature) approximation:
$p(t) = \sum_{i=0}^{5} C_{i}(\theta_w)t^i$

With 5th degree moist adiabat approximation and 4th degree coefficient approximation, in range of BT temperatures from -15 to -75 °C (the usual range of deep convective cloud top temperatures),
maximum absolute altitude error (when compared to iterative moist adiabat calculation) is 28m.

## IMPORTANT NOTES:

This calculation will work only with convective clouds!

As this calculation is sensitive to starting temperature and dewpoint values, it's probably best to
take the most unstable parcel from some area (e.g. 30-40km radius) around the target BT pixel.
The best approach to find the most unstable parcel is to calculate equivalent potential temperature ($\theta_e$)
from all temperatures and dewpoints in the area.

Also, in case of elevated convection (most of night and warm front convection), starting temperature and
dewpoint should not be taken from the surface, but from the most unstable level. This can also be found by
calculating $\theta_e$ from surface to 700hPa and taking the level with maximum $\theta_e$.

For more details see the attached conference poster.

How to cite: Šoljan, V., Jurković, J., and Babić, N.: Fast approximation for calculating deep convection cloud top heights from satellite brightness temperature, EMS Annual Meeting 2024, Barcelona, Spain, 1–6 Sep 2024, EMS2024-861, https://doi.org/10.5194/ems2024-861, 2024. 
