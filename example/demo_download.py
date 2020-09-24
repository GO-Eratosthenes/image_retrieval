from image_retrieval.downloader import ImageDowloader
from satsearch import Search

if __name__ == "__main__":
    satsearch_args = dict(
        bbox=[-108, 39, -107, 40],
        datetime='2018-02-01/2018-02-04',
        url='https://earth-search.aws.element84.com/v0',
        collections= ['sentinel-s2-l1c']  # choose one from [sentinel-s2-l2a, sentinel-s2-l1c]
    )

    # Initiate downloader
    dl = ImageDowloader(outpath='./test_download')

    # Search for available data
    dl.search(**satsearch_args)

    # Download
    dl.download_aws(assets=['metadata', 'B02', 'B04'])
    
    dl.download_gcs(key_json = 'eratosthenes-4e03208fbcf9.json',
                    project_id = 'eratosthenes')

    pass