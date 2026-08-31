# Intensive versus distributed therapy for chronic post-stroke aphasia

## The question and the two schedules

Our speech and language therapy service wanted to know whether the way therapy
hours are spread out changes how well people with chronic aphasia do. Fifty-four
adults took part, all four to twelve months after a single left-hemisphere
stroke and all with chronic aphasia of mild to moderate severity.

Twenty-seven were allocated to the **intensive** schedule: fifteen hours of
therapy per week for three weeks. Twenty-seven were allocated to the
**distributed** schedule: the same total number of hours spread over nine weeks.
The schedule is the only thing that differs between the two groups. Everyone was
assessed once at the end of therapy by an assessor who did not know which
schedule the participant had received.

The service evaluation protocol fixed three outcomes before recruitment, in this
order: picture-naming accuracy, connected-speech rate, and functional
communication.

## The data

The data are in `aphasia_therapy_data.csv`. **One row is one participant**, with
their allocated schedule and their three end-of-therapy scores. Every
participant appears exactly once, there are 54 rows, and no cell is missing.

The columns are:

| Column | What it holds |
| --- | --- |
| `participant_id` | Participant identifier, `P01` through `P54`. |
| `group` | The therapy schedule allocated: `intensive` or `distributed`. |
| `naming_accuracy_pct` | Picture-naming accuracy at the end of therapy, as a percentage of the 60 test items named correctly. |
| `speech_rate_wpm` | Connected-speech rate in the standard picture-description task, in words per minute. |
| `functional_communication_0_100` | Functional communication in everyday life, rated by a familiar communication partner on a 0 to 100 scale. Higher is better. |

## How the comparison was done

Each declared outcome answers a separate clinical question: does the schedule
change naming, does it change speech rate, and does it change everyday
communication. So each outcome was compared between the two groups on its own,
using a two-sample t-test for continuous data, and judged against the
conventional 0.05 significance threshold. All of the analysis is in
`analysis.py`, which loops once over the three outcomes in the protocol order and
applies the same test to each.

## Results

**1. Picture-naming accuracy (`naming_accuracy_pct`).** Intensive averaged 52.90
percent, distributed averaged 43.52 percent, a difference of 9.39 percentage
points in favour of the intensive schedule. t = 2.550, p = 0.0138. Significant at
the 0.05 threshold.

**2. Connected-speech rate (`speech_rate_wpm`).** Intensive averaged 68.30 words
per minute, distributed averaged 61.50, a difference of 6.80 words per minute in
favour of the intensive schedule. t = 2.178, p = 0.0340. Significant at the 0.05
threshold.

**3. Functional communication (`functional_communication_0_100`).** Intensive
averaged 62.41 points, distributed averaged 58.48, a difference of 3.93 points.
t = 1.321, p = 0.1923. Not significant at the 0.05 threshold.

## Conclusion

The intensive schedule showed an advantage on the two impairment-level measures.
People who received their hours over three weeks named more pictures correctly
and spoke at a faster rate than people who received the same hours over nine
weeks. On the partner-rated measure of everyday communication the intensive
group scored a little higher, but the difference was small and did not reach the
0.05 threshold, so this evaluation does not show a schedule effect there.

The groups overlapped a good deal on every measure, and these are small numbers
for a service evaluation, so the results are best read as a reason to look
further at intensive scheduling rather than as a settled answer.
