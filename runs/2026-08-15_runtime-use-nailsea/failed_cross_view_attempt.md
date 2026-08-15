# Failed first multi-reference build

The first multi-reference build passed its normalized front silhouette gates (IoU 0.852681; profile RMSE reduction 82.616%) but failed the independent cross-view/dimension verifier. Subdivision reduced the evaluated width to 7.430696 cm while the same-object listing states 9 cm; bbox normalization had hidden that absolute proportion error. The frozen dimension-ratio gate correctly rejected the result.

The independent top Solid-mode render visibly showed a circular hollow socket. The initial geometry predicate still reported false because it sampled only vertices at the absolute maximum Z; Solidify places the inward rim slightly lower. The verifier now samples the top 1% height band so it measures the annular rim rather than one z-slice.

Recovery keeps every frozen threshold unchanged. The next factory-startup build compensates the measured SubD shrink in the control-cage radius, then reruns the full front, topology, evaluated, top, and fresh-process checks.
