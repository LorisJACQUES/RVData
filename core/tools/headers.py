import unicodedata
from astropy.io import fits
import pandas as pd


# def initialize_header(header_csv):
#     header_df = pd.read_csv(header_csv)



def to_ascii_safe(input_string):
    # Normalize the string to NFKD form
    normalized_string = unicodedata.normalize("NFKD", input_string)

    # Encode to ASCII bytes, ignoring errors
    ascii_bytes = normalized_string.encode("ascii", "ignore")

    # Convert bytes back to string
    ascii_string = ascii_bytes.decode("ascii")

    return ascii_string

