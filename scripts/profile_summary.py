"""
Created on Jun 10, 2011

@author: Matt Rodriguez
"""

import glob
import pstats

def print_stats(f, topN=50):
    s = pstats.Stats(f)
    s.sort_stats("time").print_stats(topN)
    s.sort_stats("calls").print_stats(topN)


if __name__ == "__main__":
    files = glob.glob("*.prof")
    for f in files:
        print_stats(f)
