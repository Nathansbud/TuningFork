import os
import random

from lyricbot import make_tweet

from googleapi import make_snippet_list_from_sheet
from googleapi import make_snippet_list_from_doc

def make_drive_tweet(name, src, kind="sheet", buffer=50):
    if kind.lower() == "sheet":
        snippet_list = make_snippet_list_from_sheet(src, "A1:2000")
    elif kind.lower() == "doc":
        snippet_list = make_snippet_list_from_doc(src)
    else:
        print("Source does not exist!")
        return

    with open(os.path.join(os.path.dirname(__file__), 'logs' + os.sep + name+'.txt'), 'a+') as lf:
        lf.seek(0)
        lines = (lf.read()).split("\n")
        if len(lines) >= buffer:
            lines = lines[-buffer:]

        index = random.randint(0, len(snippet_list) - 1)
        while lines.__contains__(index):
            index = random.randint(0, len(snippet_list) - 1)

        lf.write(str(index)+"\n")


    make_tweet(name, snippet_list[index])


if __name__ == "__main__":
    make_drive_tweet(name="bg_twitter", src="16y8IedesHWbv-ncKOrgtcAOwbPar_lv4IK15zcx0euQ")
    make_drive_tweet(name="mh_twitter", src="1YqkwrL8RyWsuQmdUbj_X-wqCHKIUDtiFCglVQe12lrE")