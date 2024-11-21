#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# pylint: disable=C0103 C0114 C0115 C0116 C0123 C0201 C0207 C0209 C0301 C0302 C3001
# pylint: disable=R0911 R0912 R0913 R0914 R0915 R0916 R0917 R1702 R1729 R1732 R1718
# pylint: disable=W0105 W0640 W0707 W0718 W1514

from   glob                   import glob
import json
import math
from   os                     import chdir, getcwd
from   random                 import randint
from   shutil                 import rmtree
import sys
from   tempfile               import mkdtemp
from   time                   import sleep

import duckdb
import mapbox_vector_tile
import morecantile
import requests
from   rich.progress          import track
from   shapely.geometry.point import Point
import typer


app = typer.Typer(rich_markup_mode='rich')


def pixel2deg(xtile, ytile, zoom, xpixel, ypixel, extent=4096):
    n       = 2.0 ** zoom
    xtile   = xtile + (xpixel / extent)
    ytile   = ytile + ((extent - ypixel) / extent)
    lon_deg = (xtile / n) * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)

    return (lon_deg, lat_deg)


@app.command()
def bbox(west:float,
         south:float,
         east:float,
         north:float,
         zoom:int     = typer.Option(14),
         verbose:bool = typer.Option(False),
         pq:bool      = typer.Option(False)):
    assert 0 <= zoom <= 14

    con = duckdb.connect(database=':memory:')
    con.sql('INSTALL spatial; LOAD spatial')
    con.sql('INSTALL parquet; LOAD parquet')
    con.sql('INSTALL lindel FROM community; LOAD lindel')

    tms = morecantile.tms.get('WebMercatorQuad')
    url = 'https://vector.openstreetmap.org/shortbread_v1/%(z)d/%(x)d/%(y)d.mvt'

    current_folder = getcwd()

    temp_folder = mkdtemp()
    chdir(temp_folder)

    tiles = list(tms.tiles(west=west,
                           south=south,
                           east=east,
                           north=north,
                           zooms=zoom))

    for tile in track(tiles,
                      'Downloading {:,} tile(s)'.format(len(tiles))):
        sleep(randint(1, 2))

        url_ = url % {'x': tile.x, 'y': tile.y, 'z': tile.z}

        if verbose:
            print('Downloading %s' % url_, file=sys.stderr)

        resp = requests.get(url_,
                            timeout=60)
        assert resp.status_code == 200, 'Unexpected HTTP %d' % resp.status_code

        filename = '%(z)d_%(x)d_%(y)d.mvt.json' % {
                        'x': tile.x,
                        'y': tile.y,
                        'z': tile.z}
        open(filename, 'w').write(
            json.dumps(
                mapbox_vector_tile.decode(
                    tile=resp.content,
                    transformer=lambda x, y: pixel2deg(tile.x,
                                                       tile.y,
                                                       tile.z,
                                                       x,
                                                       y))))

    keys = set()

    for filename in glob('*.mvt.json'):
        for key in json.loads(open(filename, 'r').read()).keys():
            keys.add(key)

    features = {}

    for key in track(keys,
                     'Grouping records by type'):
        for filename in glob('*.mvt.json'):
            if key not in features:
                features[key] = []

            rec = json.loads(open(filename, 'r').read()).get(key, {})
            if 'features' in rec:
                for feature in rec['features']:
                    features[key].append(feature)

        open('%s.osm.json' % key, 'w')\
            .write(json.dumps({'type': 'FeatureCollection',
                               'features': features[key]}))

    if pq:
        sql = """COPY (
                     SELECT   *
                     FROM     ST_READ(?)
                     ORDER BY HILBERT_ENCODE([
                                 ST_Y(ST_CENTROID(geom)),
                                 ST_X(ST_CENTROID(geom))]::DOUBLE[2])
                 ) TO '%(folder)s/%(key)s.pq' (
                         FORMAT            'PARQUET',
                         CODEC             'ZSTD',
                         COMPRESSION_LEVEL 22,
                         ROW_GROUP_SIZE    15000);"""
    else:
        sql = """COPY (
                     SELECT   *
                     FROM     ST_READ(?)
                     ORDER BY HILBERT_ENCODE([
                                 ST_Y(ST_CENTROID(geom)),
                                 ST_X(ST_CENTROID(geom))]::DOUBLE[2])
                 ) TO '%(folder)s/%(key)s.gpkg'
                   WITH (FORMAT GDAL,
                         DRIVER 'GPKG',
                         LAYER_CREATION_OPTIONS 'WRITE_BBOX=YES');"""

    for filename in track(glob('*.osm.json'),
                          'Converting to %s' %
                                str('Parquet' if pq else 'GeoPackage')):
        key = filename.split('.')[0]
        con.sql(sql % {'folder': current_folder,
                       'key': key},
                params=(filename,))

    chdir(current_folder)
    rmtree(temp_folder)


@app.command()
def centroid(lon:float,
             lat:float,
             distance:float = typer.Option(0.05),
             zoom:int       = typer.Option(14),
             verbose:bool   = typer.Option(False),
             pq:bool        = typer.Option(False)):
    west, south, east, north = Point(lon, lat).buffer(distance).bounds
    return bbox(west,
                south,
                east,
                north,
                zoom,
                verbose,
                pq)


if __name__ == "__main__":
    app()
