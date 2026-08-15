# Overnight respirometry log: beta-glucan feeding trial in juvenile Atlantic salmon

Twelve 400 L recirculating tanks were stocked with juvenile Atlantic salmon of similar
size. Six tanks were randomly assigned the standard ration and six the same ration with a
beta-glucan supplement blended in. After a two-week acclimation the tanks were placed on
an intermittent-flow respirometry loop and routine oxygen uptake was logged overnight.
Each tank was measured on up to four separate nights during one trial week; two tanks lost
a night to a chiller fault, so the log is unbalanced.

One row is: one overnight respirometry session for one tank
Independent unit column: tank_id

Columns

- tank_id: label of the tank (T01 to T12). Diet was assigned to whole tanks, and each tank
  has its own water loop, feeder and biofilter, so tanks share no fish, water or handling.
- diet: ration fed to that tank, either control or bglucan (beta-glucan supplemented). The
  value is fixed for a tank across all of its nights.
- night: index of the measurement night within the trial week, 1 to 4.
- water_temp_c: mean water temperature during the session, in degrees Celsius.
- n_fish: number of fish held in the tank during the session.
- mo2_mg_kg_h: mass-specific oxygen uptake of the tank during the session, in milligrams
  of oxygen per kilogram of fish per hour.

Because the same tank appears on several rows, the rows are repeated measurements of the
same unit: the 46 rows come from only 12 tanks, and six tanks per diet is the replication
available for any diet comparison. Session values should therefore be summarised within a
tank before a between-diet comparison is made.
