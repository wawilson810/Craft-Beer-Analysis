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

#Function to pull in the data
def webscrape():
    #Path to the csv files
    csv_path = './Resources/beer_reviews.csv'
    csv = './Resources/testing.csv'

    #Testing if the csv files already exist on the computer. This is to cut down on run time
    if exists('./Resources/breweries.csv') == True and exists('./Resources/avg_rating.csv') == True:
        #Reading the final csv files in if they already exist
        avg_rating_df = pd.read_csv('./Resources/avg_rating.csv')
        brewery_geo = pd.read_csv('./Resources/breweries.csv')
    else:
        #Reading in the full data set
        beer_db = pd.read_csv(csv_path)

        #If the brewery testing csv already exists, reads it in to skip the web scraping
        if exists(csv) == True:
            brewery_db = pd.read_csv(csv)
            brewery_db.drop(columns=['Unnamed: 0'], inplace=True)
        else:

            #Creating a dataframe with the list of breweries by name and their id, dropping duplicates
            brewery_db = beer_db[['brewery_id', 'brewery_name']]
            brewery_db.drop_duplicates(subset = ['brewery_id'],inplace=True)

            #Initializing columns in the dataframe for location information with null values which can easily be dropped later
            brewery_db['City'] = np.nan
            brewery_db['State'] = np.nan
            brewery_db['Address'] = np.nan
            brewery_db['Zip'] = np.nan
            brewery_db['Country'] = np.nan

            #Resetting the index due to the duplicates being dropped
            brewery_db.reset_index(drop = True, inplace = True)

            #Initializing the browser for splinter
            executable_path = {'executable_path': ChromeDriverManager().install()}
            browser = Browser('chrome', **executable_path, headless=True)

            #Iterating through the rows of the list of breweries and scraping from the BeerAdvocate page for each
            for n, row in brewery_db.iterrows():

                #Initializing the url in the correct format
                brewery_url = f"https://www.beeradvocate.com/beer/profile/{row['brewery_id']}/"

                #Visiting the url
                browser.visit(brewery_url)
                brewery_html = browser.html
                brewery_soup = bs(brewery_html, 'html.parser')

                #Locating the box with the brewery location
                info_box = brewery_soup.find_all('div', id = 'info_box')

                #Creating a dict to hold the information and feed it into the dataframe
                full_add = {}
                add_keys = ['City', 'State', 'Country']

                #Testing if the information box exists, if not nothing is entered into that row
                if len(info_box) > 0:

                    #Locating the individual links to Google Maps
                    add_details = info_box[0].find_all("a")

                    #US addresses have three links; city, state and country, so this is one test to see if the address is in the US
                    if len(add_details) >= 3:
                        #Tests if the zipcode is located after the state. The zipcode isn't in a html element so it has no element name.
                        #This is another test for proper formatting
                        if add_details[1].nextSibling.name is None:

                            #Iterating through the links to pull in the city, state, country
                            for m in range(3):
                                full_add[add_keys[m]] = add_details[m].text
                            
                            #The address is not in a html element though it is usually located after the 2nd <br> in US addresses on the site
                            #This finds what follows that break and removes the new line character
                            full_add['Address'] = info_box[0].find_all("br")[1].nextSibling.replace('\n', '')

                            #This pulls the zip code and deletes the comma at the beginning
                            full_add['Zip'] = add_details[1].nextSibling.replace(', ', '')

                            #Tests if the address is in the US and if that is true, it adds the value to the Dataframe
                            if full_add['Country'] == 'United States':
                                brewery_db.loc[n, 'City'] = full_add['City']
                                brewery_db.loc[n, 'State'] = full_add['State']
                                brewery_db.loc[n, 'Address'] = full_add['Address']
                                brewery_db.loc[n, 'Zip'] = full_add['Zip']
                                brewery_db.loc[n, 'Country'] = full_add['Country']
            browser.quit()	
            
            #Saving to a csv so that it doesn't have to run the webscraping again
            brewery_db.to_csv('./Resources/testing.csv', index=False)

        #Cleaning the dataset by dropping all null values which represent breweries which do not have valid US addresses on the site
        brewery_clean = brewery_db.copy()
        brewery_clean.dropna(inplace=True)
        brewery_clean.reset_index(drop = True, inplace = True)
        
        #Initializing geopy to pull in the geolocation data from the Google API
        geolocator = GoogleV3(api_key=g_key)
        brewery_geo = brewery_clean.copy()
        brewery_geo['Lat'] = np.nan
        brewery_geo['Lon'] = np.nan

        #Adding the latitude and longitude to each valid brewery using their address
        for n, row in brewery_geo.iterrows():
            location = geolocator.geocode(f"{row['Address']}, {row['City']}, {row['State']}, {row['Zip']}, {row['Country']}")
            brewery_geo.loc[n, 'Lat'] = location.latitude
            brewery_geo.loc[n, 'Lon'] = location.longitude
        brewery_geo.dropna(inplace=True)
        
        #Filtering out the columns we're using from the overall beer review dataframe
        beer_db = beer_db[['brewery_id', 'brewery_name', 'beer_style', 'beer_name', 'beer_beerid', 'review_overall']]

        #Getting the list of unique breweries in the US
        brewery_list = brewery_geo['brewery_id'].to_list()

        #Filtering out all beers that are not from one of the breweries in our list
        red_beer_df = beer_db.loc[beer_db['brewery_id'].isin(brewery_list)]
        red_beer_df.reset_index(drop = True, inplace = True)
        red_beer_df.rename(columns={'beer_beerid': 'beer_id'}, inplace=True)

        #Creating a list of unique beer ids. Avoiding beer names since duplicates could technically exist
        beer_id = red_beer_df['beer_id'].unique()

        avg_rating_df = pd.DataFrame(columns = ['brewery_id', 'brewery_name', 'beer_style', 'beer_name', 'beer_id', 'review_overall'])

        #Iterating through all of the beers and calculating their average rating
        for beer in beer_id:

            #Creating a temporary dataframe to store all of the rows which contain each individual beer id
            temp_beer_df = red_beer_df.loc[red_beer_df['beer_id'] == beer]

            #Taking the mean of their ratings
            mean_rating = temp_beer_df['review_overall'].mean()

            #Creating a dataframe with one row and setting the rating for that beer equal to the mean
            mean_df = temp_beer_df.drop(temp_beer_df.index.to_list()[1:] ,axis = 0)
            mean_df['review_overall'] = mean_rating

            #Concatanating to the overall dataframe
            avg_rating_df = pd.concat([avg_rating_df, mean_df], ignore_index = False, axis = 0)
        
        avg_rating_df.reset_index(drop = True, inplace = True)

        avg_rating_df.index.rename('index', inplace=True)
        brewery_geo.index.rename('index', inplace=True)

        #Saving the csv files
        avg_rating_df.to_csv('./Resources/avg_rating.csv')
        brewery_geo.to_csv('./Resources/breweries.csv')

    #Merging the dataframes together to create a json file
    combined_df = avg_rating_df.merge(brewery_geo, on = 'brewery_id')
    combined_df.drop(columns=['brewery_name_x'], axis=1, inplace=True)
    combined_df.rename(columns={'brewery_name_y':'brewery_name'}, inplace=True)
    combined_df.to_json("combined_df.json", orient='records')
    
    #Creating a csv in a format to make the plotting easier
    combinedData = avg_rating_df.merge(brewery_geo, on='brewery_id', how='outer')
    combinedData = combinedData.rename(columns={'brewery_name_x': 'brewery_name', 'city': 'City','state': 'State', 'address':'Address'})
    combinedData = combinedData[['brewery_id', 'brewery_name', 'beer_style', 'beer_name', 'beer_id', 'review_overall', 'City', 'State', 'Address']]
    combinedData = combinedData.loc[combinedData['review_overall']>4,:]
    combinedData.to_csv("./Resources/combinedData.csv")

    #Initializing the connection to the database
    rds_connection_string = "postgres:postgres@localhost:5432/beer_db"
    engine = create_engine(f'postgresql://{rds_connection_string}')

    #Fixing issues with data types
    avg_rating_df['brewery_id'] = avg_rating_df['brewery_id'].astype(np.int64)
    avg_rating_df['beer_id'] = avg_rating_df['beer_id'].astype(float)

    #Renaming columns to fit the sql formatting requirements
    brewery_geo.rename(columns={'City': 'city',
                             'State': 'state',
                             'Address': 'address',
                             'Zip': 'zip',
                             'Country': 'country',
                             'Lat': 'lat',
                             'Lon': 'lon'}, inplace=True)
                             
    #Adding the data to the sql database
    avg_rating_df.to_sql(name='beer_review', con=engine, if_exists='replace', index=False)
    brewery_geo.to_sql(name='brewery', con=engine, if_exists='replace', index=False)


#This function creates the bar chart which displays the top twenty states with the most breweries  
def barchart():
    path = './Resources/breweries.csv'
    breweries_df = pd.read_csv(path)
    #breweries_df.drop(columns=['Unnamed: 0'], inplace=True)

    grouped_df = breweries_df.groupby('state')
    updated = grouped_df['brewery_id'].count()
    updated_df = pd.DataFrame(updated)
    new_df = updated_df.sort_values('brewery_id', ascending=False)[0:20]

    chart = new_df.plot(kind="bar", title="Top Twenty States with Most Breweries", color="red", figsize=(10,6))
    chart.set_ylabel('Number of Breweries')
    chart.set_xlabel('State')
    plt.legend('')
    plt.savefig("Resources/barchart.png", format='png', bbox_inches = "tight")