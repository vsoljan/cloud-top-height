# Fast Approximation for Calculating Deep Convection Cloud Top Heights from Satellite Brightness Temperature

Deep convection cloud top height diagnosis is very important in aviation meteorology. One of the methods to estimate altitude of existing convective cloud tops is to compare infrared satellite brightness temperature (BT) with a calculated parcel curve temperature („BT-parcel” method). The pressue where BT intersects the parcel curve (moist adiabat) is theoretical cloud top pressure level (as convective updraft temperature should equal temperature along the moist adiabat).

Moist adiabats are usually calculated iteratively from surface temperature and dewpoint, but this calculation can be computationally quite intensive. Inspired by previous work on non-iterative calculations of moist adiabats (Bakhshaii and Stull 2013, Moisseeva and Stull 2017.) we wanted to test even simpler approximations, which are still accurate enough for estimating cloud top pressure level.

In this code, moist adiabats are approximated with 5th degree polynomial. As moist adiabat shape changes with temperature and dewpoint (which can be represented by wet bulb potential temperature theta_w), approximation coefficients also depend on theta_w. This dependency was further modelled with 4th degree polynomials.

Coefficient dependency on $\theta_w$ approximation:
$C_i(\theta_w) = \sum_{j=0}^{4} a_{ij} \theta_w^i$

Moist adiabat (pressure as function of temperature) approximation:
$p(t) = \sum_{i=0}^{5} C_{i}(\theta_w)t^i$

