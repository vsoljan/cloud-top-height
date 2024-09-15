# cloud-top-height
Deep convection cloud top height diagnosis is very important in aviation meteorology. One of the methods to estimate altitude of existing convective cloud tops is to compare infrared satellite brightness temperature (BT) with a calculated parcel curve temperature („BT-parcel” method). The pressue where BT intersects the parcel curve (moist adiabat) is theoretical cloud top pressure level (as convective updraft temperature should equal temperature along the moist adiabat).

Moist adiabats are usually calculated iteratively from surface temperature and dewpoint, but this calculation can be computationally quite intensive. Inspired by previous work on non-iterative calculations of moist adiabats (Bakhshaii and Stull 2013, Moisseeva and Stull 2017.) we wanted to test even simpler approximations, which are still accurate enough for estimating cloud top pressure level.

In this code, moist adiabats are approximated with 5th degree polynomial. As moist adiabat shape changes with temperature and dewpoint (which can be represented by wet bulb potential temperature theta_w), approximation coefficients also depend on theta_w. This dependency was further modelled with 4th degree polynomials.

$C_i(\theta_w) = \sum_{j=0}^{4} a_{ij} \theta_w^i  \quad  p(t) = \sum_{i=0}^{5} C_{i}(\theta_w)t^i$

\begin{tabular}{lrrrrr}
\toprule
%{} &   $a_4$ &    $a_3$ &        $a_2$ &        $a_1$ &           $a_0$ \\
%\midrule
%$C_5$ &  1.349002e-13 & -9.439792e-12 &  1.876537e-10 & -7.653230e-11 &  2.928147e-08 \\
%$C_4$ &  1.835750e-11 & -1.344314e-09 &  1.986974e-08 &  2.984764e-07 &  1.275047e-05 \\
%$C_3$ &  9.717708e-10 & -6.829626e-08 & -2.299950e-07 &  5.360970e-05 &  2.285961e-03 \\
%$C_2$ &  1.532080e-08 & -1.929728e-07 & -1.223192e-04 &  2.461856e-03 &  2.347380e-01 \\
%$C_1$ & -1.697159e-07 &  7.782649e-05 & -5.652978e-03 & -1.584316e-01 &  1.868462e+01 \\
%$C_0$ &  4.152094e-05 & -1.288899e-04 & -7.228945e-02 & -1.865352e+01 &  9.981118e+02 \\

$C_i$ &      $a_{i0}$ &      $a_{i1}$ &      $a_{i2}$ &      $a_{i3}$ &         $a_{i4}$ \\
\midrule
$C_0$ &  9.981118e+02 & -1.865352e+01 & -7.228945e-02 & -1.288899e-04 &  4.152094e-05 \\
$C_1$ &  1.868462e+01 & -1.584316e-01 & -5.652978e-03 &  7.782649e-05 & -1.697159e-07 \\
$C_2$ &  2.347380e-01 &  2.461856e-03 & -1.223192e-04 & -1.929728e-07 &  1.532080e-08 \\
$C_3$ &  2.285961e-03 &  5.360970e-05 & -2.299950e-07 & -6.829626e-08 &  9.717708e-10 \\
$C_4$ &  1.275047e-05 &  2.984764e-07 &  1.986974e-08 & -1.344314e-09 &  1.835750e-11 \\
$C_5$ &  2.928147e-08 & -7.653230e-11 &  1.876537e-10 & -9.439792e-12 &  1.349002e-13 \\

\bottomrule
\end{tabular}
