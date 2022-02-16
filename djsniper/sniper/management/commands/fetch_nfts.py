from django.core.management.base import BaseCommand
import requests
from web3.main import Web3
from djsniper.sniper.models import NFTProject, NFT, NFTAttribute, NFTTrait
from djsniper.sniper.tasks import fetch_and_rank_nfts_task
from celery import group


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--input_file_path', nargs='?', type=str)
        parser.add_argument('--aria_params', nargs='?', type=str)

    def handle(self, *args, **options):
        self.fetch_nfts(options['uri'], options['number_of_nfts'], aria_params=options['aria_params'])

    # def fetch_nfts(self, uri, number_of_nfts, **kwargs):
    #     print(f"GETTING {uri}")
    #     # result = fetch_and_rank_nfts_task.apply_async(args=(uri, number_of_nfts), kwargs=kwargs)
    #     fetch_and_rank_nfts_task(uri, number_of_nfts, **kwargs)
    def fetch_nfts(self, input_file_path , **kwargs):
        print(f"GETTING {input_file_path}")
        # result = fetch_and_rank_nfts_task.apply_async(args=(uri, number_of_nfts), kwargs=kwargs)
        fetch_and_rank_nfts_task(input_file_path, **kwargs)
