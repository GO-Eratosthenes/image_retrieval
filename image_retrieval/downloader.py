import hashlib
import satsearch
import os
import requests
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account


class ImageDowloader(object):
    def __init__(self, outpath='.'):
        self.outpath = Path(outpath)
        self.logpath = (Path(outpath)/'log')
        self.cachepath = (Path(outpath)/'cache')
        self.downloadpath = (Path(outpath)/'download')
        
        self.outpath.mkdir(parents=True, exist_ok=True)
        self.logpath.mkdir(parents=True, exist_ok=True)
        self.cachepath.mkdir(parents=True, exist_ok=True)
        self.downloadpath.mkdir(parents=True, exist_ok=True)

    def search(self, cache=True, **kwargs):
        # By defaulte search for Sentinel-2 level 1C data
        if 'collections' not in kwargs.keys():
            kwargs['collections'] = ['sentinel-s2-l1c']
        
        # Separate collections per search
        satsearch_args = []
        for collection in kwargs['collections']:
            collection_kwargs = kwargs.copy()
            collection_kwargs['collections'] = [collection]
            satsearch_args.append(collection_kwargs)

        # Search per collection
        self.items = dict()
        for kw in satsearch_args:
            search = satsearch.Search(**kw)
            self.items[kw['collections'][0]] = search.items()
            # Cache searching results
            if cache:
                hash_search = hashlib.sha256()
                for key, value in kw.items():
                    hash_search.update(str(value).encode('utf-8'))
                hash_search = hash_search.hexdigest()[:7]
                search.items().save(self.cachepath / 'search_{}.json'.format(hash_search))

    def download(self, assets='all'):
        for key, item in self.items.items():
            if key == 'sentinel-s2-l1c': # Download S2 level 1C from Google Cloud storage
                BASE_URL = 'http://storage.googleapis.com/gcp-public-data-sentinel-2/tiles'
                scene_list = []
                for item in item._items:
                    scene_list.append('{}/{}/{}/{}/{}.SAFE'.format(
                        BASE_URL, 
                        item.properties['sentinel:utm_zone'],
                        item.properties['sentinel:latitude_band'],
                        item.properties['sentinel:grid_square'], 
                        item.properties['sentinel:product_id']))
                for s in scene_list:
                    _download_sentinel(s, self.downloadpath)
            else: 
                item.download_assets(filename_template= self.downloadpath.as_posix()+'/${sentinel:product_id}/')


def _download_file(url, dst_name):
    try:
        data = requests.get(url, stream=True)
        with open(dst_name, 'wb') as out_file:
            for chunk in data.iter_content(chunk_size=100 * 100):
                out_file.write(chunk)
    except:
        print('{} FAILED!'.format(url.split('/')[-1]))
        return

def _make_safe_dirs(scene, outpath):
    scene_name = os.path.basename(scene)
    scene_path = os.path.join(outpath, scene_name)
    manifest = os.path.join(scene_path, 'manifest.safe')
    manifest_url = scene + '/manifest.safe'
    if os.path.exists(manifest):
        os.remove(manifest)
    _download_file(manifest_url, manifest)
    with open(manifest, 'r') as f:
        manifest_lines = f.read().split()
    download_links = []
    load_this = False
    for line in manifest_lines:
        if 'href' in line:
            online_path = line[7:line.find('><') - 2]
            tile = scene_name.split('_')[-2]
            if online_path.startswith('/GRANULE/'):
                if '_' + tile + '_' in online_path:
                    load_this = True
            else:
                load_this = True
            if load_this:
                local_path = os.path.join(scene_path,
                                            *online_path.split('/')[1:])
                online_path = scene + online_path
                download_links.append((online_path, local_path))
        load_this = False
    for extra_dir in ('AUX_DATA', 'HTML'):
        if not os.path.exists(os.path.join(scene_path, extra_dir)):
            os.makedirs(os.path.join(scene_path, extra_dir))
    return download_links

def _download_sentinel(scene, dst):
    scene_name = scene.split('/')[-1]
    scene_path = os.path.join(dst, scene_name)
    if not os.path.exists(scene_path):
        os.mkdir(scene_path)
    download_links = sorted(_make_safe_dirs(scene, dst))
    for l in download_links:
        if not os.path.exists(os.path.dirname(l[1])):
            os.makedirs(os.path.dirname(l[1]))
        if os.path.exists(l[1]):
            os.remove(l[1])
        if _download_file(l[0], l[1]) is False:
            return
