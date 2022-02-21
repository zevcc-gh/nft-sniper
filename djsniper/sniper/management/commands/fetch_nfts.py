from django.core.management.base import BaseCommand
import requests
from web3.main import Web3
from djsniper.sniper.models import NFTProject, NFT, NFTAttribute, NFTTrait
from djsniper.sniper.tasks import fetch_and_rank_nfts_task
from celery import group


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--input_file_path', nargs='?', type=str, default='')
        parser.add_argument('--output_file_path', nargs='?', type=str, default='download/tmp')
        parser.add_argument('--aria_params', nargs='?', type=str, default='')

    def handle(self, *args, **options):
        self.fetch_nfts(options['input_file_path'], aria_params=options['aria_params'], output_file_path=options['output_file_path'])

    def fetch_nfts(self, input_file_path , **kwargs):
        print(f"GETTING {input_file_path}")
        # result = fetch_and_rank_nfts_task.apply_async(args=(uri, number_of_nfts), kwargs=kwargs)
        fetch_and_rank_nfts_task(input_file_path, **kwargs)
