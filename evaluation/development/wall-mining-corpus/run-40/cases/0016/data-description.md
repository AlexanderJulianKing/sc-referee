# Enzyme Kinetics Experimental Dataset

## Overview
This dataset contains steady-state kinetic measurements of enzyme catalytic activity measured under two distinct thermal conditions. Reaction velocity was determined as a function of substrate concentration to characterize the enzyme's catalytic efficiency and thermal regulation.

## Variable Definitions

**substrate_concentration_mM**
- Independent variable representing substrate molarity in the reaction mixture
- Units: millimolar (mM)
- Range: 0.1 to 50 mM
- Represents nine logarithmically-spaced concentrations spanning physiologically relevant ranges

**reaction_rate_umol_per_min**
- Dependent variable quantifying enzyme activity as product formation velocity
- Units: micromoles of product per minute (µmol/min)
- Directly measured from reaction progress over time
- Represents steady-state velocity achieved after pre-incubation equilibration

**temperature_celsius**
- Experimental condition variable controlling reaction thermal environment
- Two conditions: 25°C (ambient reference) and 37°C (physiological temperature)
- Each temperature group contains nine independent measurements

## Experimental Design
Total observations: 18 enzyme kinetic measurements across 2×9 factorial design (2 temperatures × 9 substrate concentrations). Each measurement represents a single enzymatic reaction established under controlled conditions with constant temperature, pH, and reaction time. Substrate concentration varied systematically while enzyme concentration and other parameters remained invariant.

## Expected Kinetic Behavior
Enzyme velocity is anticipated to follow saturation kinetics characterized by the Michaelis-Menten model. At low substrate concentrations, reaction velocity increases approximately linearly with substrate availability (first-order kinetics). At higher substrate concentrations, the velocity approaches an asymptotic maximum (Vmax) as enzyme active sites become progressively saturated. The Michaelis constant (Km) indicates the substrate concentration producing half-maximal velocity and inversely reflects substrate binding affinity. Temperature elevation typically enhances both Vmax and enzyme-substrate interaction rates.