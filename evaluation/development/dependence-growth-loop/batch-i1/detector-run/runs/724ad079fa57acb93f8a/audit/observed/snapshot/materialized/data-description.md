# Laugafell geothermal spring survey

During the 2024 summer season a two-person crew visited 24 geothermal springs in
the Laugafell field. Each spring was visited once. At the vent the crew recorded
the host rock the outflow cuts through (basalt or rhyolite), the water
temperature, dissolved sulfate, the discharge rate, and whether a visible
cyanobacterial filament mat was growing in the outflow channel.

One row is: one geothermal spring, visited and scored a single time
Independent unit column: spring_id
One trial is: one row

Each spring is a separate water body with its own outflow channel. No spring was
visited twice, nothing was measured in replicate, and no reading is copied across
rows, so the spring label appears exactly once and the 24 rows stand for 24
independent springs.

Columns:
- spring_id: unique label for the spring, LGF-01 through LGF-24
- bedrock_class: host rock at the outflow, either basalt or rhyolite
- outflow_temp_c: vent water temperature in degrees Celsius
- sulfate_mg_l: dissolved sulfate in milligrams per litre
- discharge_l_s: outflow discharge in litres per second
- filament_mat: yes if a visible filament mat was present, no otherwise
