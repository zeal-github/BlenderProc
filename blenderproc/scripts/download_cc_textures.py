from sys import version_info, path
if version_info.major == 2:
    raise Exception("This script only works with python3.x!")

import os
import csv
import requests
import argparse

from blenderproc.python.utility.SetupUtility import SetupUtility
from requests.adapters import HTTPAdapter

session = requests.Session()
session.mount('http://', HTTPAdapter(max_retries=3))
session.mount('https://', HTTPAdapter(max_retries=3))

def cli():
    parser = argparse.ArgumentParser("Downloads textures from cc0textures.com")
    parser.add_argument('output_dir', help="Determines where the data is going to be saved.")
    args = parser.parse_args()

    # setting the default header, else the server does not allow the download
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    cc_texture_dir = args.output_dir
    csv_file_path = os.path.join(cc_texture_dir, "full_info.csv")
    if not os.path.exists(cc_texture_dir):
        os.makedirs(cc_texture_dir)
    else:
        if os.path.isfile(csv_file_path):
            print("Resume previous download")
        else:
            raise Exception("The folder already exists and does not contain cc_textures!")

    # download the csv file, which contains all the download links
    csv_url = "https://cc0textures.com/api/v1/downloads_csv"
    request = session.get(csv_url, headers=headers)
    with open(csv_file_path, "wb") as file:
        file.write(request.content)

    # extract the download links with the asset name
    data = {}
    with open(csv_file_path, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter=',')
        for line in csv_reader:
            if line["Filetype"] == "zip" and line["DownloadAttribute"] == "2K-JPG":
                data[line["AssetID"]] = line["PrettyDownloadLink"]

    excluding_list = ["sign", "roadlines", "manhole", "backdrop", "foliage", "TreeEnd", "TreeStump",
                      "3DBread", "3DApple", "FlowerSet", "FoodSteps", "PineNeedles", "Grate",
                      "PavingEdge", "Painting", "RockBrush", "WrinklesBrush", "Sticker", "3DRock"]

    # download each asset and create a folder for it (unpacking + deleting the zip included)
    for index, (asset, link) in enumerate(data.items()):
        do_not_use = False
        for exclude_element in excluding_list:
            if asset.lower().startswith(exclude_element.lower()):
                do_not_use = True
                break
        if do_not_use:
            continue
        current_folder =  os.path.join(cc_texture_dir, asset)
        if not os.path.exists(current_folder):
            os.makedirs(current_folder)
        elif os.listdir(current_folder):
            print("Already downloaded asset: {} of {}/{}".format(asset, index + 1, len(data)))
            continue
        try:
            response = session.get(link, headers=headers, timeout=20)
        except Exception as e:
            print(f"Get response from link:{link} failed, with error:{e}")
            raise e
        try:
            SetupUtility.extract_from_response(current_folder, response)
        except Exception as e:
            print(f"Cannot extract texture, because:{e}")
        print("Download and extract asset: {} of {}/{}".format(asset, index + 1, len(data)))
    print("Done downloading textures, saved in {}".format(cc_texture_dir))

if __name__ == "__main__":
    cli()