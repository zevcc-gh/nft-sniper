from django.core.management.base import BaseCommand
from django.db.models import OuterRef, Func, Subquery
from djsniper.sniper.models import NFTProject, NFTAttribute, NFTTrait
from djsniper.sniper.tasks import rank_nfts_task


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--project_id', nargs='?', type=int)

    def handle(self, *args, **options):
        self.rank_nfts(options['project_id'])

    def rank_nfts(self, project_id):
        print("ranking start")
        rank_nfts_task(project_id)