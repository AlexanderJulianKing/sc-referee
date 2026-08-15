# Nest-tube choice assay: what the data file contains

Over two weeks of late spring, twenty wild-caught female mason bees (*Osmia
bicornis*) were released one at a time into a private mesh arena. Each arena
held two otherwise identical nesting tubes: one whose entrance rim carried a
UV-reflective paint mark, and one left plain, with the left/right placement
alternated from arena to arena. The observer recorded which tube the female
landed on first and how long she took to get there, then retired both the bee
and the arena from the experiment. No bee was tested twice and no arena was
reused, so the file has exactly as many data lines as there were bees.

One row is: one wild-caught female mason bee tested once in her own two-tube choice arena
Independent unit column: bee_id
One trial is: one row

Columns:

- bee_id: label of the individual female; unique across the file.
- arena_id: label of the mesh arena she was tested in; also unique across the
  file, because each arena served a single bee.
- intertegular_span_mm: distance between the wing bases in millimetres, the
  usual body-size proxy for bees.
- latency_min: minutes from release until the first landing on either tube.
- first_choice: which tube she landed on first, either uv_marked (the tube with
  the UV-reflective rim) or plain (the unmarked tube).

The question asked of these data is whether first landings fall on the
UV-marked tube more often than the even split expected if the mark made no
difference. Because each bee supplies a single yes/no outcome, the twenty
outcomes can be counted straight into an exact binomial test without any
adjustment for grouping.
