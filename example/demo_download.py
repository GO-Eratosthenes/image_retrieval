from image_retrieval.downloader import ImageDowloader
from satsearch import Search

if __name__ == "__main__":
    satsearch_args = dict(
            bbox=[-100.1, 39, -100, 39.1], # [W, S, E, N]
            datetime='2018-04-01/2018-05-06', # Start/End
            url='https://earth-search.aws.element84.com/v0', # Fixed end point for Sentinel-2
            collections= ['sentinel-s2-l1c', 'sentinel-s2-l2a']
        )

    # Initiate downloader
    dl = ImageDowloader(outpath='./results_download')

    # Search for available data
    dl.search(**satsearch_args)

    # Download
    dl.download()