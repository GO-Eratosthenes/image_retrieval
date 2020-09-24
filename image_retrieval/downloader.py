import hashlib
import satsearch
import os
import requests
from pathlib import Path
from google.cloud import bigquery
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

class ImageDowloader(object):
    def __init__(self,
                 outpath='.'):
        self.outpath = outpath
        Path(outpath).mkdir(parents=True, exist_ok=True)
        
    def search(self, export_json=True, **kwargs):
        search = satsearch.Search(**kwargs)
        self.items = search.items()
        if export_json:
            hash_search = hashlib.sha256()
            for key, value in kwargs.items():
                hash_search.update(str(value).encode('utf-8'))
            hash_search = hash_search.hexdigest()[:7]
            self.items.save(self.outpath+'/search_{}.json'.format(hash_search))
    
    def download_aws(self, assets='all', key_json=None, project_id=None):
        if assets=='all':
            self.items.download_assets(filename_template='test_download/${date}/${id}')
        elif isinstance(assets, list):
            for asset in assets:
                filenames = self.items.download(asset, filename_template='test_download/${date}/${id}')
        else:
            filenames = self.items.download(assets, filename_template='test_download/${date}/${id}')

    def download_gcs(self, assets='all', key_json=None, project_id=None):
        scene_list = _query_sentinel(key_json, project_id)
        for s in scene_list:
            _download_sentinel(s, outdir)

    def _query_sentinel(key_json, project_id, start, end, tile):
        credentials = service_account.Credentials.from_service_account_file(key_json)
        client = bigquery.Client(credentials=credentials, project=project_id)
        query = client.query("""
                    SELECT * FROM `bigquery-public-data.cloud_storage_geo_index.sentinel_2_index` 
                        WHERE (mgrs_tile = '{t}' AND 
                        CAST(SUBSTR(sensing_time, 1, 10) AS DATE) >= CAST('{s}' AS DATE) AND 
                        CAST(SUBSTR(sensing_time, 1, 10) AS DATE) < CAST('{e}' AS DATE))
                    """.format(t=tile, s=start, e=end))
        results = query.result()
        df = results.to_dataframe()
        good_scenes = []
        for i, row in df.iterrows():
            # print(row['product_id'], '; cloud cover:', row['cloud_cover'])
            if float(row['cloud_cover']) <= 100:
                good_scenes.append(row['base_url'].replace('gs://', BASE_URL))
        return good_scenes

    def _download_file(url, dst_name):
        try:
            data = requests.get(url, stream=True)
            with open(dst_name, 'wb') as out_file:
                for chunk in data.iter_content(chunk_size=100 * 100):
                    out_file.write(chunk)
        except:
            # print '\t ... {f} FAILED!'.format(f=url.split('/')[-1])
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
                    local_path = os.path.join(scene_path, *online_path.split('/')[1:])
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

    


    