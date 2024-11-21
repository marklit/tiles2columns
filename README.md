# tiles2columns

This package converts OpenStreetMap's (OSM) vector tiles to GPKG and Parquet format.

![QGIS](qgis-bin_EwGInUL32n.png)

## Installation

The following should work on Ubuntu and Ubuntu for Windows.

```bash
$ sudo apt update
$ sudo apt install \
    python3-pip \
    python3-virtualenv

$ python3 -m venv ~/.tiles2columns
$ source ~/.tiles2columns/bin/activate

$ git clone https://github.com/marklit/tiles2columns ~/tiles2columns
$ python -m pip install -r ~/tiles2columns/requirements.txt
```

If you're using a Mac, install [Homebrew](https://brew.sh/) and then run the following.

```bash
$ brew install \
    git \
    virtualenv

$ virtualenv ~/.tiles2columns
$ source ~/.tiles2columns/bin/activate

$ git clone https://github.com/marklit/tiles2columns ~/adsb_json
$ python -m pip install -r ~/tiles2columns/requirements.txt
```

## Usage Example

This will download an area around Northern Dubai with 42 tiles.

```bash
$ mkdir -p ~/dubai
$ cd ~/dubai

$ python3 ~/tiles2columns/main.py \
            --west=55.2112 \
            --south=25.17104 \
            --east=55.34279 \
            --north=25.2745
```

The data will be saved in GeoPackage format by default. Use ``--pq`` to produce spatially-sorted, ZStandard-compressed Parquet instead.

```bash
$ ls -lhS *.gpkg
```

```
6.8M .. streets.gpkg
6.2M .. buildings.gpkg
1.4M .. pois.gpkg
1.4M .. street_labels.gpkg
744K .. land.gpkg
372K .. sites.gpkg
248K .. addresses.gpkg
244K .. water_polygons.gpkg
216K .. ocean.gpkg
196K .. pier_polygons.gpkg
164K .. public_transport.gpkg
132K .. pier_lines.gpkg
124K .. streets_labels_points.gpkg
112K .. ferries.gpkg
104K .. bridges.gpkg
104K .. place_labels.gpkg
104K .. street_polygons.gpkg
104K .. water_lines.gpkg
 96K .. dam_polygons.gpkg
 96K .. water_lines_labels.gpkg
 96K .. water_polygons_labels.gpkg
```

Parquet files will generate faster than GeoPackage files but GeoPackage files can be dropped onto a QGIS projet whereas Parquet will need to be imported via the Add Vector Layers UI.

## Parameters

```bash
$ python main.py --help
```

```
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --west                                  FLOAT    [default: 55.2112]                                                               │
│ --south                                 FLOAT    [default: 25.17104]                                                              │
│ --east                                  FLOAT    [default: 55.34279]                                                              │
│ --north                                 FLOAT    [default: 25.2745]                                                               │
│ --zoom                                  INTEGER  [default: 14]                                                                    │
│ --verbose               --no-verbose             [default: no-verbose]                                                            │
│ --pq                    --no-pq                  [default: no-pq]                                                                 │
│ --install-completion                             Install completion for the current shell.                                        │
│ --show-completion                                Show completion for the current shell, to copy it or customize the installation. │
│ --help                                           Show this message and exit.                                                      │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
