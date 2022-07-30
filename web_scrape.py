from splinter import Browser
from bs4 import BeautifulSoup as bs
from webdriver_manager.chrome import ChromeDriverManager
import requests
import pandas as pd
import numpy as np
from geopy.geocoders import GoogleV3
from config import g_key
from sqlalchemy import create_engine
from sqlalchemy import inspect
from os.path import exists
import matplotlib.pyplot as plt

def webscrape():
    csv_path = './Resources/beer_reviews.csv'
    csv = './Resources/testing.csv'
    if exists('./Resources/breweries.csv') == True and exists('./Resources/avg_rating.csv') == True:
        avg_rating_df = pd.read_csv('./Resources/avg_rating.csv')
        brewery_geo = pd.read_csv('./Resources/breweries.csv')
    else:
        beer_db = pd.read_csv(csv_path)
        if exists(csv) == True:
            brewery_db = pd.read_csv(csv)
            brewery_db.drop(columns=['Unnamed: 0'], inplace=True)
        else:
            brewery_db = beer_db[['brewery_id', 'brewery_name']]
            brewery_db.drop_duplicates(subset = ['brewery_id'],inplace=True)

            brewery_db['City'] = np.nan
            brewery_db['State'] = np.nan
            brewery_db['Address'] = np.nan
            brewery_db['Zip'] = np.nan
            brewery_db['Country'] = np.nan
            brewery_db.reset_index(drop = True, inplace = True)

            executable_path = {'executable_path': ChromeDriverManager().install()}
            browser = Browser('chrome', **executable_path, headless=True)

            for n, row in brewery_db.iterrows():
                brewery_url = f"https://www.beeradvocate.com/beer/profile/{row['brewery_id']}/"
                browser.visit(brewery_url)
                brewery_html = browser.html
                brewery_soup = bs(brewery_html, 'html.parser')
                info_box = brewery_soup.find_all('div', id = 'info_box')
                full_add = {}
                add_keys = ['City', 'State', 'Country']
                if len(info_box) > 0:
                    add_details = info_box[0].find_all("a")
                    if len(add_details) >= 3:
                        if add_details[1].nextSibling.name is None:
                            for m in range(3):
                                full_add[add_keys[m]] = add_details[m].text
                            full_add['Address'] = info_box[0].find_all("br")[1].nextSibling.replace('\n', '')
                            full_add['Zip'] = add_details[1].nextSibling.replace(', ', '')
                            if full_add['Country'] == 'United States':
                                brewery_db.loc[n, 'City'] = full_add['City']
                                brewery_db.loc[n, 'State'] = full_add['State']
                                brewery_db.loc[n, 'Address'] = full_add['Address']
                                brewery_db.loc[n, 'Zip'] = full_add['Zip']
                                brewery_db.loc[n, 'Country'] = full_add['Country']
            browser.quit()	
            
            brewery_db.to_csv('./Resources/testing.csv', index=False)

        brewery_clean = brewery_db.copy()
        brewery_clean.dropna(inplace=True)
        brewery_clean.reset_index(drop = True, inplace = True)
        
        geolocator = GoogleV3(api_key=g_key)
        brewery_geo = brewery_clean.copy()
        brewery_geo['Lat'] = np.nan
        brewery_geo['Lon'] = np.nan

        for n, row in brewery_geo.iterrows():
            location = geolocator.geocode(f"{row['Address']}, {row['City']}, {row['State']}, {row['Zip']}, {row['Country']}")
            brewery_geo.loc[n, 'Lat'] = location.latitude
            brewery_geo.loc[n, 'Lon'] = location.longitude
        brewery_geo.dropna(inplace=True)
        
        beer_db = beer_db[['brewery_id', 'brewery_name', 'beer_style', 'beer_name', 'beer_beerid', 'review_overall']]

        brewery_list = brewery_geo['brewery_id'].to_list()

        red_beer_df = beer_db.loc[beer_db['brewery_id'].isin(brewery_list)]
        red_beer_df.reset_index(drop = True, inplace = True)
        red_beer_df.rename(columns={'beer_beerid': 'beer_id'}, inplace=True)

        beer_id = red_beer_df['beer_id'].unique()

        avg_rating_df = pd.DataFrame(columns = ['brewery_id', 'brewery_name', 'beer_style', 'beer_name', 'beer_id', 'review_overall'])

        for beer in beer_id:
            temp_beer_df = red_beer_df.loc[red_beer_df['beer_id'] == beer]
            mean_rating = temp_beer_df['review_overall'].mean()
            mean_df = temp_beer_df.drop(temp_beer_df.index.to_list()[1:] ,axis = 0)
            mean_df['review_overall'] = mean_rating
            avg_rating_df = pd.concat([avg_rating_df, mean_df], ignore_index = False, axis = 0)
        
        avg_rating_df.reset_index(drop = True, inplace = True)

        avg_rating_df.index.rename('index', inplace=True)
        brewery_geo.index.rename('index', inplace=True)

        avg_rating_df.to_csv('./Resources/avg_rating.csv')
        brewery_geo.to_csv('./Resources/breweries.csv')

    combined_df = avg_rating_df.merge(brewery_geo, on = 'brewery_id')
    combined_df.drop(columns=['brewery_name_x'], axis=1, inplace=True)
    combined_df.rename(columns={'brewery_name_y':'brewery_name'}, inplace=True)
    combined_df.to_json('./Resources/combined_df.json', orient='records')
    
    rds_connection_string = "postgres:postgres@localhost:5432/beer_db"
    engine = create_engine(f'postgresql://{rds_connection_string}')

    avg_rating_df['brewery_id'] = avg_rating_df['brewery_id'].astype(np.int64)
    avg_rating_df['beer_id'] = avg_rating_df['beer_id'].astype(float)

    combinedData = avg_rating_df.merge(brewery_geo, on='brewery_id', how='outer')
    combinedData = combinedData[['brewery_id', 'brewery_name_x', 'beer_style', 'beer_name', 'beer_id', 'review_overall', 'City', 'State', 'Address']]
    combinedData = combinedData.rename(columns={'brewery_name_x': 'brewery_name'})
    combinedData = combinedData.loc[combinedData['review_overall']>4,:]
    combinedData.to_csv("./Resources/combinedData.csv")

    brewery_geo.rename(columns={'City': 'city',
                             'State': 'state',
                             'Address': 'address',
                             'Zip': 'zip',
                             'Country': 'country',
                             'Lat': 'lat',
                             'Lon': 'lon'}, inplace=True)
                             
    avg_rating_df.to_sql(name='beer_review', con=engine, if_exists='replace', index=False)
    brewery_geo.to_sql(name='brewery', con=engine, if_exists='replace', index=False)

    
def barchart():
    path = './Resources/breweries.csv'
    breweries_df = pd.read_csv(path)
    breweries_df.drop(columns=['Unnamed: 0'], inplace=True)

    grouped_df = breweries_df.groupby('State')
    updated = grouped_df['brewery_id'].count()
    updated_df = pd.DataFrame(updated)
    new_df = updated_df.sort_values('brewery_id', ascending=False)[0:20]

    chart = new_df.plot(kind="bar", title="Top Twenty States with Most Breweries", color="red", figsize=(10,6))
    chart.set_ylabel('Number of Breweries')
    plt.legend('')
    plt.savefig("Resources/barchart.png")