from sefaria.model import *

import timeit

initstring = 'from sefaria.model import TextChunk, Ref'

for r in ["Genesis 1",
          "Genesis 4",
          "Genesis 1-5",
          "Genesis 4-6",
          "Genesis 4:5",
          "Genesis 4:5-12",
          "Shabbat 7b",
          "Shabbat 7b-9a",
          "New Zohar 1:3b",
          "New Zohar 1:3b-7a",
          "New Zohar 1:3b:2",
          "Rashi on Genesis 3",
          "Rashi on Shabbat 7a",
          "Genesis 4:5-7:12",
          "Shabbat 6b:2-8a:1",
          "Rashi on Genesis 4:5-5:2",
          "Rashi on Genesis 4:5:1-5:2:1",
          "New Zohar 1:15b-2:4a"
]:

    ref = Ref(r)
    for lang in ["en", "he"]:
        print "{}, {}".format(r, lang)
        agg = TextChunk(ref, lang, mr=True).text
        non = TextChunk(ref, lang, mr=False).text
        aggstring = 'TextChunk(Ref("{}"), "{}", mr=True)'.format(r, lang)  # replace mr=True with agg=True to test pipeline
        nonstring = 'TextChunk(Ref("{}"), "{}", mr=False)'.format(r, lang)
        if agg == non:
            agg_time = timeit.timeit(aggstring, initstring, number=10)
            non_time = timeit.timeit(nonstring, initstring, number=10)
            print "{} : Map-Reduce".format(agg_time)
            print "{} : Old Method".format(non_time)
            print "{0:.2f}%".format(agg_time/non_time*100)
        else:
            print "Missed Match!"
            print "With MR"
            print agg
            print
            print "Without"
            print non
            print


#print TextChunk(Ref("New Zohar 1:5b"), "he", agg=False).text