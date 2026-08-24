# Signature-whistle peak frequency in male and female bottlenose dolphins

## What we asked

We wanted to know whether adult male and female bottlenose dolphins in our estuary differ in the
pitch of their signature whistles.

## The data

We worked from a single file, `whistle_recordings.csv`. **One row is one whistle recording of one
dolphin**: a single good-quality signature whistle captured during one encounter, with its peak
frequency measured. A row is not a dolphin. Each animal appears on six rows.

| Column | What it holds |
| --- | --- |
| `dolphin_catalogue_id` | Catalogue identifier of the photo-identified animal the recording came from, `EST-001` through `EST-018`. Rows that share an id are repeated recordings of the same dolphin. |
| `sex` | Sex of the animal, `male` or `female`. It is a property of the animal, so it is the same on all six of that dolphin's rows. |
| `recording_number` | Which of that animal's six retained recordings this row is, 1 to 6. It counts within the animal and restarts at 1 for each dolphin, so recording 3 of one animal has nothing to do with recording 3 of another. |
| `peak_frequency_khz` | Peak frequency of the whistle in kilohertz. This is the outcome we compared between the sexes. |

We had 18 photo-identified adult dolphins of known sex, nine males (`EST-001` to `EST-009`) and nine
females (`EST-010` to `EST-018`). Each animal contributed six recordings from separate encounters,
with nothing missing, giving 108 rows. Across all recordings, peak frequency ran from 8.18 to
15.98 kHz.

## How we analysed it

The dolphin is our unit of analysis. Six recordings of the same animal are repeated measurements of
that animal, not six independent observations, and the recordings of one dolphin do sit close
together: the spread of recordings within an animal was about 0.80 kHz, well under the spread
between animals. So **we averaged the six recordings within each animal first, and then compared the
sexes on those 18 animal averages**, one value per dolphin. In the script this reduction is a single
named step, `average_recordings_within_dolphin`, which takes the full recording table and hands back
one row per dolphin carrying that animal's sex and its mean peak frequency; the comparison runs only
on what that step returns.

For the comparison itself we used Welch's two-sample t-test, which does not assume the two sexes
have equal variances. The sample size for the test is **18 dolphins, nine of each sex**.

## What we found

Averaged over their six recordings, female dolphins whistled higher than males.

| Sex | Dolphins | Mean peak frequency (kHz) | SD of animal means (kHz) |
| --- | --- | --- | --- |
| Female | 9 | 12.63 | 2.06 |
| Male | 9 | 10.69 | 1.40 |

The difference was 1.94 kHz (females higher), with a 95% confidence interval of 0.16 to 3.72 kHz.
Welch's t-test gave t = 2.34 on 14.1 degrees of freedom, p = 0.035.

## What we take from it

In this sample of 18 animals, female signature whistles peaked about 1.9 kHz higher than male ones,
and the evidence for a real difference is modest rather than strong. The confidence interval is
wide, running from a difference of only about 0.2 kHz up to nearly 3.7 kHz, so we can say the
direction with reasonable confidence but not the size. Individual animals varied a lot on their own
account: animal averages ranged from 8.74 to 15.52 kHz, and the two distributions overlap, so
whistle pitch on its own would not tell us the sex of an unknown dolphin. With nine animals per sex
this is a small study, and it comes from one estuary, so it should be repeated on more animals and
in other populations before the difference is treated as general.
