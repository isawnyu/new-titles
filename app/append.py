from newtitles import pad_bsn

# Read a txt file of isbns
# File should be named append-bsns.txt

# Make an argument?
append_infile = 'data/in/append-bsns.txt'

with open(append_infile, "r") as f:
    append_bsns = f.read().splitlines()

append_bsns = [pad_bsn(bsn) for bsn in append_bsns]
print(append_bsns)
