import sys
import re

from lxml import etree


class QuoteTokenizer:

    """
    Extracts quotes from literary texts and annotates the text
    with XML milestones to indicate where quotes start.

    The QuoteTokenizer can either be imported and used as such
    or this file can be run with as an argument on the commandline
    the text file you want to tokenize:

        python quotes.py bh_sentence_tagged.xml > bh_quote_tagged.xml

    Rein's notes:
    -------------
    PROCEDURE:
    1) Use pre-defined regular expressions to identify quotation pairs
        (single and double)
    2) Books with single and double quotations are currently distinguished in
        hard-coding - TO IMPROVE?
    3) Write function to insert quote tags in text string. Only deals with
        within-paragraph quote pairs (for cross-paragraph quote tagging, see 6))
    4) Apply function in 3) to each paragraph, read as text string
        a) Each paragraph is processed as text string
        b) process paragraph as xml and insert new tagged paragraph content
    5) If paragraph contains qs tag, insert attribute type="speech" to current
        paragraph
    6) Extended cross-paragraph quotes: Two for loops sort out these

    NEW IN V3:
    - #1: Modified 6d) - COND A.2a. Dealing with extended paragraphs which begin
        with one type of quote (e.g. double) and end in another (single)
        (problem for Frankenstein - see e.g. frank.c15.p36)

    To fix/improve:
    - I don't yet understand the process of assigning "beginning" attributes
    - Make definition of pid in 6d.1 more readable?
    """

    def __init__(self, text):

        # 1) Define quotations
        # Uses double quotation marks (")
        self.quote_regex_double = re.compile(
            "(^| |--|<s[^>]+>|\(|,|\')((&quot;)(?:<s[^>]+>|.(?!quot;))+(?:\\3(?= --)|\\3(?=--)|[,?.!-;_]\\3))( |--|</s>|$|[\w]|\))")
        self.quote_regex_single = re.compile(
            "(^| |--|<qs/>\"|<s[^>]+>|\(|,)((['])(?:(?<![,?.!])'[ edstvyrlamoEDSTVYRLAMO]|[^'])+(?:\\3(?= --)|\\3(?=--)|[,?.!-;_]\\3))( |--|</s>|$|[\w]|\))")
        self.text = text
        # This tree is modified by the tokenizer.
        self.tree = etree.fromstring(self.text)

        # print self.text[0:100]
        # print self.tree
        # print self.tree.xpath('//p')[0:10]

        # 2) hard-code books with double quotations:
        # NOTE - Look into Frankenstein: Normally double, but single when inside written texts
        # any new books with double quotation marks must be added to this list
        self.double = [
            'bh',
            'cc',
            'ge',
            'hm',
            'ttc',
            'na',
            'ss',
            'per',
            'prpr',
            'mp',
            'emma',
            'wwhite',
            'viviang',
            'vanity',
            'tess',
            'sybil',
            'prof',
            'pride',
            'persuasion',
            'native',
            'mill',
            'mary',
            'ladyaud',
            'jude',
            'jekyll',
            'jane',
            'frank',
            'dracula',
            'dorian',
            'deronda',
            'cran',
            'basker',
            'arma',
            'alli']

    def compute_quote_consistence(self):
        """
        Shows a number of examples where quotes might have been
        opened, but not closed, or vice versa.
        """
        raise NotImplementedError

    def single_or_double(self):

        # TODO only get the first paragraph element
        # this need not be repeated for every paragraph
        for paragraph in self.tree.xpath('//p'):
            id = paragraph.get('id')
            # get id name until first '.' - find() looks for matching string
            # position
            book = id[:id.find('.')]
            if book.lower() in self.double:
                # this is thus the opposite because embedded quotes use the
                # different quote style
                quote_style = 'single'
            else:
                # idem
                quote_style = 'double'
        self.quote_style = quote_style
        return quote_style

    def annotate_quotes(self, text, quote_style):
        # 3) function for tagging quotes
        # deals only with quote pairs within paragraphs
        # quotes that extend across paragraphs are dealt with in
        self.single_or_double()
        if self.quote_style == 'single':
            # replace location following the first matched group with <qs/>,
            # etc.
            return re.sub(self.quote_regex_single, '\\1<alt-qs/>\\2<alt-qe/>\\4', text)
        else:
            # deal with the problem of xml attributes containing " in double
            # quoted books
            # replace each in-text " with '&quot'. Regular expression says that if " precedes < before the occurrence of any >
            # then label '&quot'. This excludes any " in attributes.
            s = re.sub('"(?=[^>]*<)', '&quot;', text)
            t = re.sub(self.quote_regex_double, '\\1<alt-qs/>\\2<alt-qe/>\\4', s)
            return t.replace('&quot;', '"')

            # FIXME does this add <qs/> to open quotes (paragraphs that only have an opening quote)?

            # Rein goes about it as follows:

            # NEW: we can disregard paragraph if there is only one &quot; label (these are dealt with below)
            # if len(re.findall('&quot;', s)) != 1:
            #    t = re.sub(quoteD,'\\1<qs/>\\2<qe/>\\4', s)
            #    return t.replace('&quot;', '"')
            # else:
            # return s.replace('&quot;', '"') # return string with quotation
            # tags, and " re-inserted

    def first_run(self):
        # print "starting the first run"
        # FIXME weird to call it here:
        self.single_or_double()
        # print self.quote_style
        # 4) Apply function in 3) to each paragraph
        # a) Each paragraph is processed as text string
        for paragraph in self.tree.xpath('//p'):
            text = etree.tostring(paragraph)
            # print text
            # process only text following first > (paragraph element) and
            # preceding final <
            text = text[text.find('>') + 1:text.rfind('<')]
            # print text
            # Tag text string according to function 3)
            tagged = self.annotate_quotes(text, self.quote_style)
            # print tagged

            # b) process paragraph as xml and insert new tagged paragraph content
            # replace beginning and end of tagged string with <foo>
            # (representing parent element)
            nodetree = etree.fromstring('<foo>%s</foo>' % tagged)
            # run loop over each sub-element of <p> (each sentence)...
            for c in paragraph.getchildren():
                paragraph.remove(c)
            # ... and insert new sentence (n) to current paragraph instead
            for n in nodetree:
                paragraph.append(n)

        # 5) If paragraph contains qs tag, insert attribute type="speech" to
        # current paragraph
        for paragraph in self.tree.xpath('//p[s/qs]'):
            paragraph.set('type', 'speech')

        # print self.tree

    def tokenize(self):
        self.first_run()
        return etree.tostring(self.tree)

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as a_file:
        text = a_file.read()
    tokenizer = QuoteTokenizer(text)
    print tokenizer.tokenize()
