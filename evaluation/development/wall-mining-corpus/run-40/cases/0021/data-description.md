## Beer Fermentation Dataset

This dataset contains 11 daily measurements from a controlled beer fermentation experiment conducted over 10 days. Each row represents a single day's observation window during the active fermentation phase of the brewing process.

### Measurement Variables

**Day**: Sequential observation number (0-10), representing days elapsed from fermentation start.

**Temp_c**: Temperature in degrees Celsius, measured once daily at the same time. The fermentation vessel is temperature-controlled to maintain conditions optimal for ale yeast (18-22°C range). Values cluster closely around 20°C, indicating successful environmental control.

**pH**: The acidity-alkalinity measurement on a logarithmic scale. Beer fermentation begins near pH 4.8 (acidic) due to malt composition. The gradual decrease to pH 4.51 reflects organic acid production from yeast metabolism and lactic acid bacteria activity, which is normal and beneficial for flavor development and preservation.

**Gravity**: Specific gravity relative to water (dimensionless), measured using a hydrometer. This indicates the dissolved sugar content. The initial gravity of 1.0485 represents the wort (unfermented beer) composition. As yeast metabolizes sugars into alcohol and CO2, gravity decreases. Terminal gravity typically approaches 1.0000-1.0010 when fermentation is complete. The values show the characteristic sigmoidal fermentation curve: rapid initial decline (days 0-4), slower decline in mid-fermentation (days 5-8), and plateau (days 9-10) indicating complete sugar consumption.