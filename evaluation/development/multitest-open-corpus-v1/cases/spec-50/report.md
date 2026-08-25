# Sensor-driven ventilation against conventional minimum ventilation

Two adjacent broiler houses on the same farm ran the same cycle, one on the conventional
minimum-ventilation strategy and one on a sensor-driven variable strategy. 80 sampling
records were collected across the cycle, 40 per strategy, each record covering one
sampling station. Six outcomes were compared with a two-sample Welch t-test on the
difference in means.

## Correction

All six raw p-values were held as one family and corrected together with **multipy**
(version 0.16, pinned in `requirements.txt`), a package written specifically for multiple
hypothesis testing. The procedure used is `multipy.fdr.lsu`, the Benjamini-Hochberg linear
step-up method, which controls the **false discovery rate** at q = 0.05. That is a
different guarantee from a family-wise error rate: it holds the expected share of false
calls among the outcomes we declare different to 5 percent, rather than the chance of any
false call at all. Air quality, welfare, and energy outcomes all went into the same
correction, and only multipy's decisions are used below.

## Results

| Outcome | conventional | sensor_driven | difference | raw p | adjusted p | decision |
|---|---|---|---|---|---|---|
| ammonia (ppm) | 18.0 | 11.3 | 6.7 | 1.3e-08 | 7.6e-08 | significant |
| carbon dioxide (ppm) | 2844 | 2255 | 590 | 8.6e-08 | 1.7e-07 | significant |
| dust PM10 (mg/m3) | 3.68 | 2.40 | 1.27 | 4.4e-08 | 1.3e-07 | significant |
| litter moisture (%) | 33.9 | 28.1 | 5.7 | 5.7e-06 | 8.5e-06 | significant |
| footpad score (0-4) | 1.36 | 0.89 | 0.48 | 0.00911 | 0.01093 | significant |
| heating (kWh/1000 birds) | 419 | 467 | -48 | 0.01144 | 0.01144 | significant |

All six survive the correction, so every claim below rests on a corrected decision.

## Air quality against heating cost

The air-quality gains are large and they hang together. Ammonia drops by 6.7 ppm, about a
third, and that is the number that matters most for both bird welfare and stockworker
exposure. Carbon dioxide is 590 ppm lower and dust 1.27 mg/m3 lower, both consistent with
simply moving more air when the sensors call for it.

The welfare chain is visible in the litter. Litter moisture is 5.7 percentage points lower
under the sensor strategy, and wet litter is what produces both ammonia and footpad burns.
The footpad score follows, 0.89 against 1.36 on the 0 to 4 scale, a third of a scale point
better. On a processing line that is the difference between a flock being paid on and a
flock being downgraded, so it carries real money as well as welfare weight.

The cost is heat. The sensor houses used 48 kWh more per 1000 birds, about 11 percent more
heating energy, which is exactly what more air exchange should cost in a cold shed. Whether
that trade is worth taking is an arithmetic question the farm can settle with its own
numbers: multiply 48 kWh by the flock size in thousands and the local fuel price, then set
it against the footpad downgrade risk and the ammonia exposure it buys down. At current
energy prices in most of the region we would expect the footpad gain alone to cover it,
but that judgement is the farm's to make with its own contract price.

Two limits worth stating. The comparison is one house against one house, so anything that
differs between the two buildings travels with the strategy, and the sampling stations
within a house are not independent of one another. And this is a single cycle, so it says
nothing about how the strategies compare in a different season.
