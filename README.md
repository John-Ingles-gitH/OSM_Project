# OSM_Project

In this Udacity course project, I audit and fix OpenStreetMap data of Portland,
Oregon and the surrounding area.  I then convert it into csv format and upload it to
an sqlite3 database.

## Installation

Clone the GitHub repository.

```
$ git clone https://github.com/John-Ingles-gitH/OSM_Project.git
$ cd OSM_Project
```
Go to the webpage linked in `map_link.txt` and download the XML data for Portland,
Or and save it as `portland_oregon.osm`.

**UPDATE: Mapzen ceased operations at the end of January 2018.  Their migration
page indicates that they intend to make their existing extracts available in the
future.  I can't provide the full data, but I can provide the 1/10 size sample
of the data in sample.rar.**

## Usage

Run `OSM_resize.py` to create a 1/10 size sample of the data.  It will be named
`sample.osm`.

Run `process_map.py` in its current state to fix the data according to the
replacement maps hard coded (based on info from the audit programs) in **street_ending_map**, **street_direction_map**, **minor_changes_map**, and 
**nodes_to_remove**.

The fixed data will be written to the following csv files:

* nodes.csv
* nodes_tags.csv
* ways.csv
* ways_tags.csv
* ways_nodes.csv

Running with validate = True will use the **cerberus** validator to verify that 
the data follows the database schema in `schema.py`. **Warning**: This will slow 
down the run time significantly.

The data can be inserted into an sqlite3 database using a suitable csv to sqlite3
program.  I used **csv2sqlite** by Rufus Pollock https://github.com/rufuspollock/csv2sqlite.

The code in this repository requires Python 3.x and the following libraries:

* unicodecsv
* codecs
* cerberus
* schema
* re
* xml.etree.cElementTree
* pprint

You can view the process I took to audit the data and some example database
queries by navigating to this repository's [GitHub Page](https://john-ingles-gith.github.io/OSM_Project/).

## License

GNU General Public License v3.0