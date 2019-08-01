import os
import random

from lyricbot import make_tweet

from googleapi import make_snippet_list_from_sheet
from googleapi import make_snippet_list_from_doc

def make_botgenius_tweet(src="sheet", buffer=50):
    if src.lower() == "sheet":
        botgenius_list = make_snippet_list_from_sheet("16y8IedesHWbv-ncKOrgtcAOwbPar_lv4IK15zcx0euQ", "A1:2000")
    elif src.lower() == "doc":
        botgenius_list = make_snippet_list_from_doc("16WNStYc5qNLGFOujF8EBywvFtIQWq56hhYwrh9PLp8c")
    else:
        print("Source does not exist!")
        return

    with open(os.path.join(os.path.dirname(__file__), 'logs' + os.sep + 'botgenius.txt'), 'a+') as lf:
        lf.seek(0)
        lines = (lf.read()).split("\n")
        if len(lines) >= buffer:
            lines = lines[-buffer:]

        index = random.randint(0, len(botgenius_list) - 1)
        while lines.__contains__(index):
            index = random.randint(0, len(botgenius_list) - 1)

        lf.write(str(index)+"\n")


    make_tweet('bg_twitter', botgenius_list[index])

if __name__ == "__main__":
    make_botgenius_tweet()