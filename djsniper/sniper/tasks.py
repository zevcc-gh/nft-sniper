import json
import requests
from time import time, sleep, perf_counter
from web3.main import Web3

from celery import shared_task
from celery_progress.backend import ProgressRecorder

from django.db.models import OuterRef, Func, Subquery

from djsniper.sniper.models import NFTProject, NFT, NFTAttribute, NFTTrait
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from threading import Lock
from functools import wraps
import subprocess

def print_timing(func):
    '''
    create a timing decorator function
    use
    @print_timing
    just above the function you want to time
    '''
    @wraps(func)  # improves debugging
    def wrapper(*args, **kwargs):
        start = perf_counter()  # needs python3.3 or higher
        result = func(*args, **kwargs)
        end = perf_counter()
        fs = '{} took {:.3f} seconds'
        print(fs.format(func.__name__, (end - start)))
        return result
    return wrapper

@shared_task
@print_timing
def rank_nfts_task(project_id):
    project = NFTProject.objects.get(id=project_id)

    # calculate sum of NFT trait types
    trait_count_subquery = (
        NFTTrait.objects.filter(attribute=OuterRef("id"))
        .order_by()
        .annotate(count=Func("id", function="Count"))
        .values("count")
    )
    attributes = NFTAttribute.objects.all().annotate(
        trait_count=Subquery(trait_count_subquery)
    )

    # Group traits under each type
    trait_type_map = {}
    for i in attributes:
        if i.name in trait_type_map.keys():
            trait_type_map[i.name][i.value] = i.trait_count
        else:
            trait_type_map[i.name] = {i.value: i.trait_count}

    # Calculate rarity
    """
    [Rarity Score for a Trait Value] = 1 / ([Number of Items with that Trait Value] / [Total Number of Items in Collection])
    """

    for nft in project.nfts.all():
        # fetch all traits for NFT
        total_score = 0

        for nft_attribute in nft.nft_attributes.all():
            trait_name = nft_attribute.attribute.name
            trait_value = nft_attribute.attribute.value

            # Number of Items with that Trait Value
            trait_sum = trait_type_map[trait_name][trait_value]

            rarity_score = 1 / (trait_sum / project.number_of_nfts)

            nft_attribute.rarity_score = rarity_score
            nft_attribute.save()

            total_score += rarity_score

        nft.rarity_score = total_score
        nft.save()
    print('rarity_score updated')

    # Rank NFTs
    for index, nft in enumerate(project.nfts.all().order_by("-rarity_score")):
        nft.rank = index + 1
        nft.save()
    print('ranking done')

# @shared_task(bind=True)
# def fetch_nfts_task(self, project_id):
#     progress_recorder = ProgressRecorder(self)
#     project = NFTProject.objects.get(id=project_id)

#     w3 = Web3(Web3.HTTPProvider(INFURA_ENDPOINT))
#     contract_instance = w3.eth.contract(
#         address=project.contract_address, abi=project.contract_abi
#     )

#     for i in range(0, project.number_of_nfts):
#         print("Fetching NFT ...", i)
#         ipfs_uri = contract_instance.functions.tokenURI(i).call()
#         data = requests.get(
#             f"https://ipfs.io/ipfs/{ipfs_uri.split('ipfs://')[1]}"
#         ).json()
#         nft = NFT.objects.create(
#             nft_id=i, project=project, image_url=data["image"].split("ipfs://")[1]
#         )
#         attributes = data["attributes"]
#         for attribute in attributes:
#             nft_attribute, created = NFTAttribute.objects.get_or_create(
#                 project=project, name=attribute["trait_type"], value=attribute["value"]
#             )
#             NFTTrait.objects.create(nft=nft, attribute=nft_attribute)
#         progress_recorder.set_progress(i + 1, project.number_of_nfts)
#         sleep(1)

#     # Call rank function
#     rank_nfts_task(project_id)


# @shared_task(bind=True)
# @print_timing
# def fetch_and_rank_nfts_task(self, uri, number_of_nfts, **kwargs):
#     protocol = uri.split("://")[0]

#     if not uri.endswith("/"):
#         uri += "/"
#     project = NFTProject.objects.create(number_of_nfts=number_of_nfts)

#     lock = Lock()
#     def task(item_id, nft_list, nft_attribute_dict, nft_trait_list):
#         data = requests.get(
#             f"{uri}{item_id}"
#         ).json()
#         nft = NFT(nft_id=item_id, project=project, image_url=data["image"].split(protocol)[1])
#         nft_list.append(nft)

#         for attribute in data["attributes"]:
#             with lock:
#                 if nft_attribute_dict[f'{attribute["trait_type"]}|{attribute["value"]}']:
#                     nft_attribute = nft_attribute_dict[f'{attribute["trait_type"]}|{attribute["value"]}']
#                 else:
#                     nft_attribute = NFTAttribute(project=project, name=attribute["trait_type"], value=attribute["value"])
#                     nft_attribute_dict[f'{attribute["trait_type"]}|{attribute["value"]}'] = nft_attribute
#                 nft_trait_list.append(NFTTrait(nft=nft, attribute=nft_attribute))
#         # nft = NFT.objects.create(
#         #     nft_id=item_id, project=project, image_url=data["image"].split(protocol)[1]
#         # )
#         # attributes = data["attributes"]
#         # for attribute in attributes:
#         #     nft_attribute, created = NFTAttribute.objects.get_or_create(
#         #         project=project, name=attribute["trait_type"], value=attribute["value"]
#         #     )
#         #     NFTTrait.objects.create(nft=nft, attribute=nft_attribute)
#         # s4 = perf_counter()
#         #print(f"store DB need {s4-s3} secs")
#         # print(f"total need {s4-s1} secs")
        
#     nft_list = []
#     nft_attribute_dict = defaultdict(lambda : None)
#     nft_trait_list = []

#     workers = kwargs.get("workers") or 64
#     with ThreadPoolExecutor(max_workers=workers) as executor:
#         for i in range(number_of_nfts):
#             executor.submit(task, i, nft_list, nft_attribute_dict, nft_trait_list)
#             if (i+1) % 100 == 0:
#                 print(f"{i+1} records done")
#     print(f"All records done ({i+1})")
#     print("start insert DB")
#     NFT.objects.bulk_create(nft_list)
#     NFTAttribute.objects.bulk_create(list(nft_attribute_dict.values()))
#     NFTTrait.objects.bulk_create(nft_trait_list)
#     print("finished insert DB")
#     # Call rank function
#     rank_nfts_task(project.id)


@shared_task(bind=True)
@print_timing
def fetch_and_rank_nfts_task(self, input_file_path, **kwargs):
    output_file_path = kwargs["output_file_path"]
    #cmd for gather all json files to one file
    cmd = f"""                                                  
        rm -rf {output_file_path}
        aria2c --input-file=input.txt --dir {output_file_path} && \
        awk 1 {output_file_path}/* > {output_file_path}/output.txt                                           
        """
    subprocess.run(cmd, capture_output=True, shell=True)


    nfts=[]
    trait_type_value_map = {}

    with open(f"{output_file_path}/output.txt", "r") as f:
        for j in f:
            data = json.loads(j)
            attributes = data["attributes"]
            nfts.append(attributes)
            for attribute in attributes:
                trait_type = attribute["trait_type"]
                value = attribute["value"]
                if trait_type not in trait_type_value_map:
                    trait_type_value_map[trait_type] = {}
                trait_value_map = trait_type_value_map[trait_type]
                if value not in trait_value_map:
                    trait_value_map[value] = 0
                trait_value_map[value] += 1

    # For normalization
    trait_type_categories_count_map = {}
    for trait_type in trait_type_value_map:
        categories_count = len(trait_type_value_map[trait_type])
        trait_type_categories_count_map[trait_type] = categories_count
    # trait_type_count = len(trait_type_categories_count_map)

    all_nfts_rarity = {}
    for idx, nft in enumerate(nfts):
        attributes_len = len(nft)
        rarity = 0
        for attribute in nft:
            trait_sum = trait_type_value_map[attribute["trait_type"]][attribute["value"]]
            # Without normalization
            # rarity_score = 1 / (trait_sum / NUM_OF_NFTS)
            # With normalizeation, normalized by num of traits and num of categories in that trait
            rarity_score = 1000000 / (attributes_len * trait_type_categories_count_map[attribute["trait_type"]]) / (trait_sum / len(nfts))
            rarity += rarity_score
        all_nfts_rarity[str(idx)] = rarity

    sort_orders = sorted(all_nfts_rarity.items(), key=lambda x: x[1], reverse=True)

    for i in sort_orders:
        print("NFT id: %s, rarity_score: %d" % (i[0], i[1]))
