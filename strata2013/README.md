Data lives here: https://dl.dropbox.com/u/22164876/fec.csv.zip

Unzip, use pandas.read_csv to import it as a DataFrame,

then do

store = pd.HDFStore('fec.h5')
store['fec'] = frame

to get the data into the format used in the demo notebook

You'll have to change the path from "~/Dropbox/data" to your own


:)
