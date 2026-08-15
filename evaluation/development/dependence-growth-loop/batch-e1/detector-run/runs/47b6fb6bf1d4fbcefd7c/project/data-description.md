# Screen-printed graphene electrode scans

Twelve screen-printed graphene sensor strips were fabricated: six were coated
with carbon ink formulation GX7 and six with formulation GX9. Each strip was
mounted once in the flow cell and then scanned four times in a row against a
fixed ferrocyanide standard, so every strip contributes four consecutive
oxidation-peak readings taken from the same piece of hardware in the same
sitting.

One row is: a single amperometric scan of one sensor strip, giving the oxidation peak current recorded on that scan
Independent unit column: electrode_id

## Columns

- electrode_id: label of the sensor strip that produced the scan. There are
  twelve distinct strips and each label appears on four rows.
- ink_formulation: which carbon ink the strip was coated with, GX7 or GX9.
  The formulation is a property of the strip, so it is identical across all
  four rows that share an electrode_id.
- scan_index: position of the scan within that strip's run, 1 through 4.
- peak_current_ua: oxidation peak current measured on that scan, in
  microamperes.
- cell_temp_c: flow-cell temperature at the time of the scan, in degrees
  Celsius.

## Reading the file

The file is plain ASCII CSV with a header line and 48 data rows. Readings
from the same electrode_id are repeat measurements of one strip rather than
measurements of separate strips.
