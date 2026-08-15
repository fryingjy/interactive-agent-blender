# Held-out candlestick reference

The selected object is a museum-photographed, opalescent blown-glass candlestick with a broad foot, narrow stem, central bulb and beads, broad drip pan, tall socket cup, and flared lip. The component reading supports a single rotational profile rather than an assembly of stacked cylinder primitives.

Source: [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Opalescent_white_candlestick,_c._1828,_blown_glass_-_Sandwich_Glass_Museum_-_Sandwich,_MA_-_DSC07971.jpg), CC0/public-domain dedication by Daderot.

The photograph is not orthographic and a display tray obstructs part of one side. `reference_silhouette.png` therefore uses the smaller visible half-width on each row and mirrors it about the observed centerline. The red-contour preview was visually inspected after an earlier GrabCut result incorrectly included the tray and was rejected. This mask is suitable for a normalized silhouette experiment, but it is not claimed as exact physical ground truth.

Two setup failures are retained in the report trail: the first JSON export exposed a NumPy boolean serialization error, and the first valid mask included the tray. Both were corrected before the acceptance contract was frozen and before modeling began.
