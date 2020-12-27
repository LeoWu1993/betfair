import logging

import betfairlightweight

"""
Historic is the API endpoint that can be used to
download data betfair provide.

https://historicdata.betfair.com/#/apidocs
"""

# setup logging
logging.basicConfig(level=logging.INFO)  # change to DEBUG to see log all updates

# create trading instance
trading = betfairlightweight.APIClient("wutianyao01@gmail.com", "Wty200801=",
                                       certs="C:/Program Files/OpenSSL-Win64/bin/",
                                       app_key="nN9lYWTm3zB44oXY",
                                       cert_files=['C:/Program Files/OpenSSL-Win64/bin/client-2048.crt',
                                                   'C:/Program Files/OpenSSL-Win64/bin/client-2048.key'])

# login
trading.login()

# get my data
my_data = trading.historic.get_my_data()
for i in my_data:
    print(i)

# get collection options (allows filtering)
collection_options = trading.historic.get_collection_options(
    "Horse Racing", "Basic Plan", 1, 3, 2017, 1, 3, 2017
)
print(collection_options)

# get advance basket data size
basket_size = trading.historic.get_data_size(
    "Horse Racing", "Basic Plan", 1, 3, 2017, 1, 3, 2017
)
print(basket_size)

# get file list
file_list = trading.historic.get_file_list(
    "Soccer",
    "Basic Plan",
    from_day=1,
    from_month=3,
    from_year=2020,
    to_day=31,
    to_month=3,
    to_year=2020,
    #market_types_collection=["WIN", "PLACE"],
    countries_collection=["GB", ],
    #file_type_collection=["M"],
)
print(file_list)

# download the files
# for file in file_list:
#     print(file)
#     download = trading.historic.download_file(file_path=file)
#     print(download)
