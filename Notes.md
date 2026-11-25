# Notes

14/11 
1) Open csv with pandas
2) Add categories names to one table
3) In production table translate columns
4) Create 2 new csv
17/11
1) Drop unnecessary column in plant and production table
2) Pick up year in plant column

## Steps
**1. Prepare the data**

* Load the plant register and the electricity balance.
* Clean the columns. Match technology names across both files.
* Note the file names and the download date for the sources.
2. Pick the insight to test

* Question 2: does solar capacity growth give a similar share of produced electricity?
* Question 1 (cantons) can add the space dimension.

**3. Explore (B.1)**

* Figure A: installed capacity by technology per year, from the register.
* Figure B: the same data summed per decade, or as a running total. This gives your two levels of detail.
* Figure C: capacity by canton and technology, as a map or bars.
Add a share-of-capacity vs share-of-production view from the balance, from 1960.
* Use at least 3 of the 4 dimensions: space, time, capacity and production, technology.
* Use static plots. Dynamic ones are optional. If you make one, add a screenshot and a working URL.
* Check the insight

**4. Recompute the key numbers a second way.**
* Compare capacity and production in the same units. Convert kW to GWh with capacity factors, or compare shares.
* Look for traps. Examples: plants not yet built, old plants removed, canton gaps, missing years.
* Write down each check. You need it for the text.

**5. Write the text page (max 500 words)**
* hat you looked at, and what you saw.
* How this led to the B.2 insight.
* How you checked it.
* Design choices: colors, scales, labels, order.
* Put the source list outside the word count.

**6. Design the information graphic (B.2)**
* One page. One clear message in the title.
* Show the capacity share against the production share.
* Add a short note that explains why they differ.
* Use one color per technology across all figures.
* Keep text large enough to read.
* Build the PDF

Mix portrait and landscape pages if it helps.
Page 4 must make sense without the other pages. Add sources and a legend on it.
Count the pages and the words.
B.3

**Before you submit**
4 pages or fewer.
Text has 500 words or fewer.
Both detail levels are visible.
At least 3 dimensions are used.
Sources are listed.


**IDEAS:**
Example: solar may be 30% of power but only 5% of electricity. That is your story.
Zbuduj z pliku 1 własną oś czasu.

Plik 1 (elektrownie)	Plik 2 (produkcja)
Moc dodana w roku X	Prąd wyprodukowany w roku X
Moc zainstalowana do roku X (suma narastająca)	to samo, ten sam rok
Suma narastająca mówi, ile mocy stało w kraju w roku X. To już da się porównać z produkcją w roku X.

python



installed = (plants.groupby(["Year", "Technology"])["TotalPower"].sum()
                   .groupby(level="Technology").cumsum()
                   .reset_index(name="InstalledKW"))


### Good practices
Remember: Communicating data visually requires you to know exactly what **message you want to communicate**. Change the software defaults so that your message is communicated more clearly and follows Tufte’s principles of graphical excellence (more on this in the following weeks). In exploring the options for changing the software default, you might want to try to:

- Change (increase!) the font size of any texts in the graphic (do not forget small axes labels, legends, source information, etc.)
- Remove border lines, remove background grey/colour, and change axis scales and ranges
- Remove or reduce the number of the often ‘countless’ tick marks and reference lines
- Change colour, size and thickness of symbols and lines
- Add labels, pointers, annotations, selected lines, explanation texts,…(more on this in the following weeks)
- Edit the legend, remove borders, re-position the legend
- Edit the grid lines, e.g., grey in the background or maybe white in the foreground
- Use a different colour scheme. Is it possible to change only some elements, for example the median line of a box plot, to a different colour?
- What are the options for creating non-standard graphics? For example, could you add the mean and standard deviations to the axes of a scatter plot?

Encoding decisions explained

- Colour accent: the orange hue against a field of neutral grey recruits the pre-attentive colour channel. The viewer does not need to read the legend or search the chart; Honda models are immediately salient.
- Z-ordering: plotting the grey background layer first ensures Honda points are drawn on top and not partially hidden. If both layers were plotted simultaneously via colour mapping in aes(), overlap would be arbitrary and some highlighted points might be concealed.
- Direct annotation: a text label placed near the Honda cluster replaces a colour legend. The viewer’s eye goes from the salient orange points directly to the adjacent label, eliminating the memory-mediated legend lookup that costs working memory.
- Grey tone choice (grey75): light enough to recede to background but not so light as to disappear. The contrast between orange and grey75 is sufficient for pre-attentive pop-out without being harsh.